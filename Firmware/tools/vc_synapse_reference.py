#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Independent fixed-voltage synaptic reference and event-response analysis.

Uses exponential impulse superposition / linear regression, not the firmware's
state update functions. Incoming events are inferred from resolved fast jumps;
this does not count electrically missed presynaptic spikes or release failures.
"""
from dataclasses import dataclass, asdict
import math
import numpy as np

DT_MS = .1
DECAY = .99
GAIN = 10.
IC50 = {4: .30, 5: .90, 6: 3.7, 7: 10.}


@dataclass(frozen=True)
class Phase:
    name: str
    voltage: float = -70.
    drug: int = 4
    dose: float = 0.


def phases(case):
    if case == '14_synaptic_input':
        return [Phase('baseline'), Phase('active'), Phase('recovery')]
    if case in ('17_ampa_reversal', '18_gaba_reversal'):
        voltages = (-70., -20., 20.) if case == '17_ampa_reversal' else (-90., -70., -50.)
        return [Phase('voltage_' + str(int(v)), v) for v in voltages]
    drug = {'15_nbqx': 4, '16_gabazine': 5, '19_nmda_apv': 6, '20_gvia': 7}[case]
    voltage = -20. if drug == 6 else -70.
    return [Phase('control', voltage, drug), Phase('drug', voltage, drug, IC50[drug]),
            Phase('washout', voltage, drug)]


def configuration(case):
    gaba = case in ('16_gabazine', '18_gaba_reversal')
    return {'receptor': 'GABA-A' if gaba else 'AMPA', 'receptor_index': 2 if gaba else 1,
            'gain_legacy': -GAIN if gaba else GAIN, 'decay_per_tick': DECAY,
            'reversal_mV': -80. if gaba else 0., 'nmda': case == '19_nmda_apv',
            'presynaptic': case == '20_gvia', 'ntype_fraction': .35,
            'release': 'deterministic', 'phases': [asdict(p) for p in phases(case)]}


def expected_amplitudes(phase, config):
    reserve = 1 - phase.dose / (IC50[phase.drug] + phase.dose)
    release = (1 - .35 * (1 - reserve))**3 if config['presynaptic'] else 1.
    # Calibrated event conductance in uS. GABA calibration remains at E=-80.
    g = GAIN / (10. if config['receptor_index'] == 2 else 70.) * .01
    fast_block = reserve if phase.drug in (4, 5) else 1.
    fast = g * (phase.voltage - config['reversal_mV']) * release * fast_block * DECAY
    tr, td = 4., 100.
    peak_t = tr * td / (td - tr) * math.log(td / tr)
    norm = 1 / (math.exp(-peak_t / td) - math.exp(-peak_t / tr))
    mg = 1 / (1 + math.exp(-.062 * phase.voltage) / 3.57)
    nmda_block = reserve if phase.drug == 6 else 1.
    slow = g * phase.voltage * release * 2 * norm * mg * nmda_block if config['nmda'] else 0.
    return float(fast), float(slow)


def settled_rows(rows, phase):
    group = [r for r in rows if r['phase'] == phase.name]
    if not group:
        raise ValueError('Missing phase: ' + phase.name)
    selected = [r for r in group if group[0]['wall_s'] + 1 <= r['wall_s']
                < group[-1]['wall_s'] - .25]
    if len(selected) < 500:
        raise ValueError('Too few settled samples: ' + phase.name)
    if any(abs(r['command_mV'] - phase.voltage) > .0001 for r in selected):
        raise ValueError('Wrong holding voltage in ' + phase.name)
    return selected


def event_response(rows, phase, config):
    selected = settled_rows(rows, phase)
    y = np.array([r['receptor_nA'] for r in selected], dtype=float)
    expected_fast, expected_slow = expected_amplitudes(phase, config)
    if abs(expected_fast) < .001:
        raise ValueError('This protocol requires resolvable, nonzero fast driving force')
    sign = 1 if expected_fast > 0 else -1
    innovations = y[1:] - DECAY * y[:-1]
    events = np.r_[0., (sign * innovations > .35 * abs(expected_fast)).astype(float)]
    indices = np.flatnonzero(events)
    # At this 500 Hz wall clock, 50 samples = 100 ms. Bursts faster than 10 Hz
    # make the deliberately simple input-event inference unsuitable for this test.
    intervals = np.diff(indices) * .002
    regular_enough = len(intervals) == 0 or bool(np.min(intervals) >= .1 - 1e-9)
    n = len(y)
    age = np.arange(n, dtype=float)
    convolution = np.zeros(n)
    for i in range(1, n):
        convolution[i] = DECAY * convolution[i-1] + events[i]
    columns = [DECAY**age, convolution]
    if config['nmda']:
        rise, decay = math.exp(-DT_MS / 4), math.exp(-DT_MS / 100)
        rconv, dconv = np.zeros(n), np.zeros(n)
        for i in range(1, n):
            rconv[i] = rise * (rconv[i-1] + events[i])
            dconv[i] = decay * (dconv[i-1] + events[i])
        columns = [DECAY**age, rise**age, decay**age, convolution, dconv-rconv]
    matrix = np.column_stack(columns)
    coefficients, _, rank, _ = np.linalg.lstsq(matrix, y, rcond=None)
    fitted_fast = float(coefficients[-2] if config['nmda'] else coefficients[-1])
    fitted_slow = float(coefficients[-1]) if config['nmda'] else 0.
    residual = float(np.max(np.abs(y - matrix @ coefficients)))
    fast_ok = abs(fitted_fast - expected_fast) <= max(5e-6, .02 * abs(expected_fast))
    slow_ok = (not config['nmda'] or
               abs(fitted_slow - expected_slow) <= max(1e-5, .05 * abs(expected_slow)))
    passed = (len(indices) >= 5 and regular_enough and rank == len(columns) and
              fast_ok and slow_ok and residual <= .00002)
    return {'passed': bool(passed), 'resolved_events': int(len(indices)),
            'minimum_event_interval_wall_s': float(np.min(intervals)) if len(intervals) else None,
            'source_rate_acceptable': bool(regular_enough),
            'expected_fast_event_nA': expected_fast, 'fitted_fast_event_nA': fitted_fast,
            'expected_nmda_coefficient_nA': expected_slow, 'fitted_nmda_coefficient_nA': fitted_slow,
            'max_synaptic_waveform_residual_nA': residual,
            'fast_amplitude_passed': bool(fast_ok), 'nmda_amplitude_passed': bool(slow_ok),
            'fit_rank': int(rank), 'mean_receptor_nA': float(np.mean(y)),
            'note': 'Resolved received events; not ground-truth source spike counts or release-failure statistics.'}


def quiet(rows, phase):
    group = [r for r in rows if r['phase'] == phase]
    if not group:
        raise ValueError('Missing quiet phase: ' + phase)
    selected = [r for r in group if group[0]['wall_s'] + 1 <= r['wall_s']
                < group[-1]['wall_s'] - .25]
    if len(selected) < 500:
        raise ValueError('Too few quiet samples')
    maximum = max(abs(r['receptor_nA']) for r in selected)
    return {'passed': maximum <= .003, 'max_receptor_nA': maximum}


def analyse(rows, case):
    config = configuration(case)
    results = {}
    for phase in phases(case):
        if case == '14_synaptic_input' and phase.name != 'active':
            results[phase.name] = quiet(rows, phase.name)
        else:
            results[phase.name] = event_response(rows, phase, config)
    summary = {'passed': all(r['passed'] for r in results.values()), 'phases': results}
    if case in ('17_ampa_reversal', '18_gaba_reversal'):
        volts = np.array([p.voltage for p in phases(case)])
        amps = np.array([results[p.name]['fitted_fast_event_nA'] / DECAY for p in phases(case)])
        slope, intercept = np.polyfit(volts, amps, 1)
        reversal = float(-intercept / slope) if abs(slope) > 1e-12 else None
        ok = slope > 0 and reversal is not None and abs(reversal-config['reversal_mV']) <= 1.
        summary['reversal'] = {'passed': bool(ok), 'estimated_mV': reversal,
                               'expected_mV': config['reversal_mV'], 'event_conductance_uS': float(slope)}
        summary['passed'] &= bool(ok)
    if case in ('15_nbqx', '16_gabazine', '19_nmda_apv', '20_gvia'):
        key = 'fitted_nmda_coefficient_nA' if config['nmda'] else 'fitted_fast_event_nA'
        control, drug, washout = (results[k][key] for k in ('control', 'drug', 'washout'))
        expected_ratio = (1-.35*.5)**3 if config['presynaptic'] else .5
        ratio = drug / control if abs(control) > 1e-9 else None
        recovered = washout / control if abs(control) > 1e-9 else None
        ok = (ratio is not None and abs(ratio-expected_ratio) <= .04 and
              recovered is not None and abs(recovered-1) <= .04)
        summary['drug_effect'] = {'passed': bool(ok), 'event_amplitude_ratio': ratio,
                                 'expected_ratio': expected_ratio, 'washout_ratio': recovered,
                                 'comparison': 'per resolved event; not unnormalised mean current'}
        summary['passed'] &= bool(ok)
    return summary
