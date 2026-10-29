/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
// Portable passive VC prototype. Units: mV, ms, nA, pF, MOhm, uS.
// No Arduino, IO, random sampling or pharmacology state belongs in this file.
#include <cmath>
#include <cstdint>

namespace vc {
constexpr float command_min = -110.0f;
constexpr float command_max = 80.0f;
enum class Mode : uint8_t { Access = 0, Ideal = 1 };

struct Parameters {
  float capacitance_pF = 20.0f;
  float membrane_MOhm = 500.0f;
  float access_MOhm = 5.0f;
  float reversal_mV = -70.0f;
  float minimum_nA = -20.0f;
  float maximum_nA = 20.0f;
  bool valid() const {
    return std::isfinite(capacitance_pF) && capacitance_pF >= 1 && capacitance_pF <= 1000 &&
           std::isfinite(membrane_MOhm) && membrane_MOhm >= 10 && membrane_MOhm <= 10000 &&
           std::isfinite(access_MOhm) && access_MOhm >= .1f && access_MOhm <= 100 &&
           std::isfinite(reversal_mV) && reversal_mV >= command_min && reversal_mV <= command_max &&
           std::isfinite(minimum_nA) && std::isfinite(maximum_nA) &&
           minimum_nA >= -100 && maximum_nA <= 100 && minimum_nA < 0 && maximum_nA > 0;
  }
};

struct Inputs {
  float inward_nA = 0;          // Positive depolarising current; sampled once per model tick.
  float conductance_uS = 0;     // Future receptor interface: positive sum(g).
  float conductance_E_nA = 0;   // Future receptor interface: sum(g*E), never another injected current.
  bool valid() const {
    return std::isfinite(inward_nA) && std::isfinite(conductance_uS) &&
           conductance_uS >= 0 && std::isfinite(conductance_E_nA);
  }
};

struct Sample {
  float voltage_mV = -70;
  float clamp_nA = 0;
  float capacitive_nA = 0;
  float leak_nA = 0;
  float receptor_nA = 0;
  float sodium_nA = 0, potassium_nA = 0;
  float input_nA = 0;
  float saturated_fraction = 0;
};

class Cell {
 public:
  const Parameters& parameters() const { return parameters_; }
  const Sample& sample() const { return sample_; }
  bool configure(const Parameters& p) {
    if (!p.valid()) return false;
    parameters_ = p;            // Atomic: parameter changes never reset membrane charge.
    return true;
  }
  bool reset(float voltage) {
    if (!std::isfinite(voltage)) return false;
    sample_ = Sample{};
    sample_.voltage_mV = voltage;
    return true;
  }
  bool step(float command, float dt_ms, const Inputs& input, Mode mode) {
    if (!std::isfinite(command) || command < command_min || command > command_max ||
        !std::isfinite(dt_ms) || dt_ms <= 0 || !input.valid()) return false;
    const auto& p = parameters_;
    const double cm = p.capacitance_pF / 1000.0;
    const double gl = 1.0 / p.membrane_MOhm;
    const double gi = gl + input.conductance_uS;
    const double bi = gl*p.reversal_mV + input.conductance_E_nA + input.inward_nA;
    const double initial = sample_.voltage_mV;
    double v = initial, mean = command, saturated = 0;
    if (mode == Mode::Ideal) {
      v = command;              // Ideal step charge is represented as an output-bin mean.
    } else {
      double remaining = dt_ms, integral_v = 0;
      const double left = command - p.maximum_nA*p.access_MOhm;
      const double right = command - p.minimum_nA*p.access_MOhm;
      for (unsigned segment = 0; segment < 6 && remaining > 1e-12; ++segment) {
        const double access = clip((command-v)/p.access_MOhm, p.minimum_nA, p.maximum_nA);
        const double derivative = (access + bi - gi*v)/cm;
        const bool high = v < left-1e-9 || (std::fabs(v-left) <= 1e-9 && derivative < 0);
        const bool low = v > right+1e-9 || (std::fabs(v-right) <= 1e-9 && derivative > 0);
        const double a = gi + ((high || low) ? 0 : 1.0/p.access_MOhm);
        const double b = bi + (high ? p.maximum_nA : low ? p.minimum_nA : command/p.access_MOhm);
        const double boundary = high ? left : low ? right : derivative > 0 ? right : left;
        double duration = remaining, end, average;
        linear(v, a, b, duration, cm, end, average);
        if ((v-boundary)*(end-boundary) < 0 && std::fabs(v-boundary) > 1e-9) {
          const double equilibrium = b/a;
          duration = -cm/a*std::log((boundary-equilibrium)/(v-equilibrium));
          linear(v, a, b, duration, cm, end, average);
          end = boundary;
        }
        integral_v += average*duration;
        if (high || low) saturated += duration;
        remaining -= duration;
        v = end;
      }
      if (remaining > 1e-9) return false;
      mean = integral_v/dt_ms;
    }
    Sample next;
    next.voltage_mV = static_cast<float>(v);
    next.capacitive_nA = static_cast<float>(cm*(v-initial)/dt_ms);
    next.leak_nA = static_cast<float>(gl*(mean-p.reversal_mV));
    next.receptor_nA = static_cast<float>(input.conductance_uS*mean-input.conductance_E_nA);
    next.input_nA = input.inward_nA;
    next.clamp_nA = next.capacitive_nA + next.leak_nA + next.receptor_nA - next.input_nA;
    next.saturated_fraction = static_cast<float>(saturated/dt_ms);
    if (!std::isfinite(next.voltage_mV) || !std::isfinite(next.clamp_nA)) return false;
    sample_ = next;             // Failed steps leave the last valid state intact.
    return true;
  }
 private:
  Parameters parameters_;
  Sample sample_;
  static double clip(double value, double minimum, double maximum) {
    return value < minimum ? minimum : value > maximum ? maximum : value;
  }
  static void linear(double v, double a, double b, double dt, double cm,
                     double& end, double& mean) {
    const double equilibrium = b/a;
    const double z = a*dt/cm;
    end = equilibrium+(v-equilibrium)*std::exp(-z);
    mean = equilibrium+(v-equilibrium)*(-std::expm1(-z))/z;
  }
};

} // namespace vc
