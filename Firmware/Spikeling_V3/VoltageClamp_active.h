/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
// Educational HH backend; Na/K kinetics follow NEURON hh.mod at 6.3 C.
// Maximal conductances are deliberately reduced to 240/72 nS for clear currents
// in a 20 pF teaching cell. This is not a fitted squid or mammalian preparation.
#include "VoltageClamp_passive.h"
#include "VoltageClamp_gate_table.h"

namespace vc {
struct Gates { double m = 0, h = 1, n = 0; };
struct Kinetics {
  Gates infinity, rate;
  static double trap(double x, double scale) {
    const double z = x / scale;
    return std::fabs(z) < 1e-6 ? scale*(1-z/2+z*z/12) : x/std::expm1(z);
  }
  static Kinetics at(double v) {
    const double am = .1*trap(-(v+40),10), bm = 4*std::exp(-(v+65)/18);
    const double ah = .07*std::exp(-(v+65)/20), bh = 1/(std::exp(-(v+35)/10)+1);
    const double an = .01*trap(-(v+55),10), bn = .125*std::exp(-(v+65)/80);
    return {{am/(am+bm), ah/(ah+bh), an/(an+bn)}, {am+bm,ah+bh,an+bn}};
  }
  void advance(Gates& g, double dt) const {
    g.m = infinity.m+(g.m-infinity.m)*std::exp(-dt*rate.m);
    g.h = infinity.h+(g.h-infinity.h)*std::exp(-dt*rate.h);
    g.n = infinity.n+(g.n-infinity.n)*std::exp(-dt*rate.n);
  }
};

struct FastKinetics {
  Gates infinity, fraction;
  // Caller validates finite -250..250 mV. Endpoint selection stays in bounds.
  static FastKinetics at(double voltage) {
    const float position = (static_cast<float>(voltage)+250.0f)*4.0f;
    const unsigned index = position >= gate_table_size-1 ? gate_table_size-2 :
                           static_cast<unsigned>(position);
    const float part = position-index;
    const auto& a = gate_table[index]; const auto& b = gate_table[index+1];
    const auto interpolate = [part](float x,float y) { return x+(y-x)*part; };
    return {{interpolate(a.infinity[0],b.infinity[0]),
             interpolate(a.infinity[1],b.infinity[1]),
             interpolate(a.infinity[2],b.infinity[2])},
            {interpolate(a.fraction[0],b.fraction[0]),
             interpolate(a.fraction[1],b.fraction[1]),
             interpolate(a.fraction[2],b.fraction[2])}};
  }
  void advance(Gates& g) const {
    g.m += (infinity.m-g.m)*fraction.m;
    g.h += (infinity.h-g.h)*fraction.h;
    g.n += (infinity.n-g.n)*fraction.n;
  }
};

inline void advanceGates(Gates& gates,double voltage,double half_step_ms) {
#ifndef VC_ANALYTIC_GATES
  if (std::fabs(half_step_ms-.0125) < 1e-9) {
    FastKinetics::at(voltage).advance(gates);
    return;
  }
#endif
  // Preserve the general portable API for nonstandard numerical timesteps.
  // VC_ANALYTIC_GATES is a host-regression switch, not the production default.
  Kinetics::at(voltage).advance(gates,half_step_ms);
}

class ActiveCell {
 public:
  static constexpr double sodium_uS = .240, potassium_uS = .072;
  static constexpr double sodium_E = 50, potassium_E = -77;
  const Sample& sample() const { return sample_; }
  const Gates& gates() const { return gates_; }
  bool configure(const Parameters& p) { return membrane_.configure(p); }
  bool reset(float v) {
    if (!std::isfinite(v) || v < -250 || v > 250) return false;
    membrane_.reset(v); sample_ = membrane_.sample(); gates_ = Kinetics::at(v).infinity;
    return true;
  }
  bool step(float cmd, float dt, const Inputs& input, Mode mode,
            float sodium_reserve = 1, float potassium_reserve = 1) {
    if (!std::isfinite(dt) || dt <= 0 || dt > 1 || !input.valid() ||
        !std::isfinite(sodium_reserve) || sodium_reserve < 0 || sodium_reserve > 1 ||
        !std::isfinite(potassium_reserve) || potassium_reserve < 0 || potassium_reserve > 1)
      return false;
    // Work on a copy: a rejected command/failed substep cannot partly advance gates.
    ActiveCell next = *this;
    const unsigned count = static_cast<unsigned>(std::ceil(double(dt)/.025000001));
    const double h = double(dt)/count;
    double clamp=0, cap=0, leak=0, receptor=0, na=0, k=0, saturated=0;
    for (unsigned j=0;j<count;++j) {
      const double old = next.membrane_.sample().voltage_mV;
      const double gate_v = mode == Mode::Ideal ? cmd : old;
      if (!std::isfinite(gate_v) || gate_v < -250 || gate_v > 250) return false;
      advanceGates(next.gates_,gate_v,h/2);
      const auto& g = next.gates_;
      const double gn = sodium_uS*sodium_reserve*g.m*g.m*g.m*g.h;
      const double gk = potassium_uS*potassium_reserve*g.n*g.n*g.n*g.n;
      Inputs total = input;
      total.conductance_uS += gn+gk;
      total.conductance_E_nA += gn*sodium_E+gk*potassium_E;
      if (!next.membrane_.step(cmd,static_cast<float>(h),total,mode)) return false;
      const auto& s = next.membrane_.sample();
      if (s.voltage_mV < -250 || s.voltage_mV > 250) return false;
      // Cell gives the exact voltage mean for frozen conductances through leak.
      const double mean_v = s.leak_nA*next.membrane_.parameters().membrane_MOhm+
                            next.membrane_.parameters().reversal_mV;
      const double ina = gn*(mean_v-sodium_E), ik = gk*(mean_v-potassium_E);
      clamp += s.clamp_nA; cap += s.capacitive_nA; leak += s.leak_nA;
      receptor += input.conductance_uS*mean_v-input.conductance_E_nA;
      na += ina; k += ik; saturated += s.saturated_fraction;
      advanceGates(next.gates_,mode == Mode::Ideal ? cmd : s.voltage_mV,h/2);
    }
    next.sample_ = next.membrane_.sample();
    next.sample_.clamp_nA = clamp/count; next.sample_.capacitive_nA = cap/count;
    next.sample_.leak_nA = leak/count; next.sample_.receptor_nA = receptor/count;
    next.sample_.sodium_nA = na/count; next.sample_.potassium_nA = k/count;
    next.sample_.input_nA = input.inward_nA; next.sample_.saturated_fraction = saturated/count;
    *this = next;
    return true;
  }
 private:
  Cell membrane_;
  Sample sample_;
  Gates gates_ = Kinetics::at(-70).infinity;
};
} // namespace vc
