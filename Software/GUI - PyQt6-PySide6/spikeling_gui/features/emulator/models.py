# SPDX-License-Identifier: GPL-3.0-or-later
"""Desktop numerical counterparts of the Spikeling V3 firmware models."""

from functools import lru_cache
from math import ceil, exp, expm1, log

IC50 = (9.2, 0.5, 2.3, 0.88, 0.30, 0.90, 3.7, 10.0)
RELEASE_SEED = 20261028
CURRENT_TO_NA = 0.01
MASK32 = 0xffffffff
NMDA_PEAK_TIME = 400 / 96 * log(25)
NMDA_NORMALISATION = 1 / (exp(-NMDA_PEAK_TIME / 100) - exp(-NMDA_PEAK_TIME / 4))


def drug_block(concentrations):
    return tuple(value / (value + half) for value, half in zip(concentrations, IC50))


def sigmoid(value):
    if value >= 0:
        return 1 / (1 + exp(-value))
    factor = exp(value)
    return factor / (1 + factor)


def unit_interval(value):
    return min(1.0, max(0.0, value))


def izhikevich(v, u, current, parameters, dt):
    a, b, c, d = parameters
    v += dt * (0.04 * v * v + 5 * v + 140 - u + current)
    u += dt * a * (b * v - u)
    if v >= 30:
        v, u = c, u + d
    return max(-110, v), u, v >= -30


class IntrinsicPharmacology:
    """Izhikevich excitability corrections and verified spike events."""

    def __init__(self, voltage):
        self.h_na = sigmoid(-(voltage + 55) / 6)
        self.h_a = sigmoid(-(voltage + 78) / 6)
        self.sk = 0.0
        self.armed = True
        self.committed = False
        self.aborted = False

    def recover_na(self, v, dt):
        self.h_na += (sigmoid(-(v + 55) / 6) - self.h_na) * -expm1(
            -dt / (2 if v <= -62 else 9)
        )

    def recover_a(self, v, dt):
        self.h_a += (sigmoid(-(v + 78) / 6) - self.h_a) * -expm1(
            -dt / (35 if v >= -78 else 80)
        )

    def hold(self, v, dt):
        self.sk *= exp(-dt / 120)
        self.recover_na(v, dt)
        self.recover_a(v, dt)
        self.armed, self.committed, self.aborted = True, False, False

    def step(self, v, u, current, parameters, dt, block):
        a, b, c, d = parameters
        ttx, tea, apamin, four_ap = block[:4]
        self.sk *= exp(-dt / 120)
        self.recover_na(v, dt)
        correction = apamin * 0.25 * self.sk * (v + 90)
        if four_ap:
            self.recover_a(v, dt)
            correction += four_ap * 2.5 * sigmoid((v + 55) / 7) * self.h_a * (v + 90)

        izhi = 0.04 * v * v + 5 * v + 140 - u
        reserve_ttx = unit_interval((1 - ttx - 0.14) / 0.86)
        if ttx or tea or apamin or four_ap:
            rho_k = unit_interval(1.25 * tea + 0.25 * apamin + 0.17 * four_ap)
            reserve1 = reserve_ttx * (1 - unit_interval(0.15 * ttx * (1 - self.h_na)))
            reserve2 = 1 - unit_interval(1.10 * rho_k * (1 - self.h_na))
            product = reserve1 * reserve2
            reserve = product / (reserve1**3 + reserve2**3 - product**3)**(1 / 3) if product else 0
            q = unit_interval((reserve_ttx - 0.10) / 0.11)
            weight = q * q * (3 - 2 * q) if ttx else 1.0
            if self.aborted and ttx:
                weight = 0.0
            active = izhi - 0.04 * (1 - reserve) * max(0, v + 70)**2
            passive = -0.8 * (v + 70) - 0.12 * max(0, v + 45)**2
            derivative = weight * active + (1 - weight) * passive + current + correction
        else:
            derivative = izhi + current

        previous = v
        v += dt * derivative
        u += dt * a * (b * v - u)
        if not ttx:
            verified = v >= 30
            self.armed, self.committed, self.aborted = True, False, False
        else:
            if self.armed and previous < -30 <= v:
                self.committed = reserve_ttx > 0.12
                self.armed = False
                self.aborted = not self.committed
            verified = self.committed and v >= 30
            if self.committed and not verified and (derivative <= 0 or v < -35):
                self.committed, self.aborted = False, True
            if not self.committed and v < -40:
                self.armed, self.aborted = True, False

        if verified:
            v, u = c, u + d
            self.h_na *= exp(-(0.30 + 0.85 * tea + 0.12 * apamin))
            self.sk += 0.4 * (1 - self.sk)
            self.armed, self.committed, self.aborted = True, False, False
        return max(-110, v), u, verified


class Synapse:
    """One independent STP, release and receptor state driven by spike edges."""

    def __init__(self, channel, seed):
        self.channel = channel
        self.polarity = 0
        self.high = False
        self.configure_stp((1.0, 0, 0))
        self.reseed(seed)
        self.clear_currents()

    def reseed(self, seed):
        word = (seed ^ (0x9e3779b9 * (self.channel + 1))) & MASK32
        word = ((word ^ (word >> 16)) * 0x7feb352d) & MASK32
        word = ((word ^ (word >> 15)) * 0x846ca68b) & MASK32
        self.random_word = (word ^ (word >> 16)) or 0xa341316c

    def clear_currents(self):
        self.legacy_current = 0.0
        self.clear_receptors()

    def clear_receptors(self):
        self.released_current = self.conductance = 0.0
        self.nmda_rise = self.nmda_decay = 0.0

    def configure_stp(self, parameters):
        self.stp_parameters = parameters
        self.utilisation, self.resources = parameters[0], 1.0
        self.last_event = None

    def stp_multiplier(self, time):
        resting, facilitation, recovery = self.stp_parameters
        if self.last_event is not None:
            elapsed = time - self.last_event
            if facilitation:
                self.utilisation = resting + (self.utilisation - resting) * exp(-elapsed / facilitation)
            if recovery:
                self.resources = 1 - (1 - self.resources) * exp(-elapsed / recovery)
        multiplier = self.utilisation / resting * self.resources
        if recovery:
            self.resources *= 1 - self.utilisation
        if facilitation:
            self.utilisation += resting * (1 - self.utilisation)
        self.last_event = time
        return multiplier

    def release(self, probability, sites, calcium):
        if probability is None:
            return calcium
        threshold = probability * calcium * (1 << 32)
        released = 0
        word = self.random_word
        for _ in range(sites):
            word ^= (word << 13) & MASK32
            word ^= word >> 17
            word ^= (word << 5) & MASK32
            released += word < threshold
        self.random_word = word
        return released / (sites * probability)

    def step(self, high, gain, decay, time, dt, voltage, block, pharmacology, nmda, probability, sites):
        polarity = (gain > 0) - (gain < 0)
        if polarity and polarity != self.polarity:
            self.polarity = polarity
            self.clear_receptors()
        if high and not self.high:
            event = gain * self.stp_multiplier(time)
            self.legacy_current += event
            if pharmacology:
                event *= self.release(probability, sites, (1 - 0.35 * block[7])**3)
                self.released_current += event
                if self.polarity:
                    conductance = event / (70 if self.polarity > 0 else -10)
                    self.conductance += conductance
                    if nmda and self.polarity > 0:
                        self.nmda_rise += 2 * conductance
                        self.nmda_decay += 2 * conductance
        self.high = high
        self.legacy_current *= decay
        if not pharmacology:
            return self.legacy_current, 0.0, 0.0

        self.released_current *= decay
        self.conductance *= decay
        self.nmda_rise *= exp(-dt / 4)
        self.nmda_decay *= exp(-dt / 100)
        fast_availability = 1 - (block[4] if self.polarity > 0 else block[5] if self.polarity < 0 else 0)
        if not nmda:
            return self.released_current * fast_availability, 0.0, 0.0

        conductance = self.conductance * fast_availability
        reversal = 0 if self.polarity > 0 else -80
        weighted_reversal = conductance * reversal
        if self.polarity > 0:
            mg_unblock = 1 / (1 + exp(-0.062 * voltage) / 3.57)
            conductance += (1 - block[6]) * NMDA_NORMALISATION * max(
                0.0, self.nmda_decay - self.nmda_rise
            ) * mg_unblock
        return weighted_reversal - conductance * voltage, conductance, weighted_reversal


def _linear_step(v, conductance, drive, dt):
    equilibrium = drive / conductance
    rate = conductance * dt / 0.020  # 20 pF, in nA·ms/mV.
    change = expm1(-rate)
    return v + (v - equilibrium) * change, equilibrium - (v - equilibrium) * change / rate


def _access_step(v, command, dt, inward, conductance, weighted_reversal):
    """Exact RC segments with the V3 defaults of 5 MΩ access and ±20 nA compliance."""
    initial = v
    leak = 1 / 500
    internal = leak + conductance
    drive = -70 * leak + weighted_reversal + inward
    left, right = command - 100, command + 100
    remaining = dt
    integrated = 0.0
    for _ in range(6):
        if remaining <= 1e-12:
            break
        access = min(20, max(-20, (command - v) / 5))
        derivative = access + drive - internal * v
        high = v < left - 1e-9 or (abs(v - left) <= 1e-9 and derivative < 0)
        low = v > right + 1e-9 or (abs(v - right) <= 1e-9 and derivative > 0)
        total_g = internal if high or low else internal + 0.2
        total_drive = drive + (20 if high else -20 if low else command / 5)
        boundary = left if high else right if low or derivative > 0 else left
        duration = remaining
        end, mean = _linear_step(v, total_g, total_drive, duration)
        if (v - boundary) * (end - boundary) < 0 and abs(v - boundary) > 1e-9:
            equilibrium = total_drive / total_g
            duration = -0.020 / total_g * log((boundary - equilibrium) / (v - equilibrium))
            _, mean = _linear_step(v, total_g, total_drive, duration)
            end = boundary
        integrated += mean * duration
        v = end
        remaining -= duration
    mean_v = integrated / dt
    current = 0.020 * (v - initial) / dt + internal * mean_v - drive
    return v, current, mean_v


def _trap(value):
    scaled = value / 10
    return 10 * (1 - scaled / 2 + scaled**2 / 12) if abs(scaled) < 1e-6 else value / expm1(scaled)


@lru_cache(maxsize=2048)
def _kinetics(voltage):
    am, bm = 0.1 * _trap(-(voltage + 40)), 4 * exp(-(voltage + 65) / 18)
    ah, bh = 0.07 * exp(-(voltage + 65) / 20), sigmoid((voltage + 35) / 10)
    an, bn = 0.01 * _trap(-(voltage + 55)), 0.125 * exp(-(voltage + 65) / 80)
    return tuple((a / (a + b), a + b) for a, b in ((am, bm), (ah, bh), (an, bn)))


class VoltageClamp:
    """Passive and Na/K active membranes with the V3 access-resistance defaults."""

    def __init__(self, voltage):
        self.gates = tuple(target for target, _ in _kinetics(voltage))

    def advance_gates(self, voltage, dt):
        # The device uses interpolated gate tables. Rounded voltages cache the
        # equivalent analytic rates with <0.005 mV input error on the desktop.
        kinetics = _kinetics(round(voltage, 2))
        self.gates = tuple(target + (gate - target) * exp(-dt * rate)
                           for gate, (target, rate) in zip(self.gates, kinetics))

    def step(self, voltage, command, dt, inward, conductance, reversal, active, block):
        if not active:
            voltage, current, _ = _access_step(voltage, command, dt, inward, conductance, reversal)
            return voltage, current
        count = ceil(dt / 0.025000001)
        substep = dt / count
        total_current = 0.0
        for _ in range(count):
            self.advance_gates(voltage, substep / 2)
            m, h, n = self.gates
            sodium = 0.240 * (1 - block[0]) * m**3 * h
            potassium = 0.072 * (1 - block[1]) * n**4
            voltage, current, _ = _access_step(
                voltage, command, substep, inward, conductance + sodium + potassium,
                reversal + sodium * 50 - potassium * 77,
            )
            total_current += current
            self.advance_gates(voltage, substep / 2)
        return voltage, total_current / count
