/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "VoltageClamp_passive.h"
#include "VoltageClamp_active.h"
#include "VoltageClamp_trace.h"
namespace vc {
enum class Source : uint8_t { Hardware = 0, Direct = 1, Step = 2 };
enum Flag : uint16_t {
  Compliance = 1, RejectedCommand = 2, SolverFault = 4,
  DisplayRange = 8, PacketRange = 16, UnsupportedPharmacology = 32, LoopDeadline = 64
};

struct Runtime {
  Cell cell;
  ActiveCell active_cell;
  bool active = false;
  const Sample& sample() const { return active ? active_cell.sample() : cell.sample(); }
  bool reset(float v) {
    return cell.reset(v) && active_cell.reset(v);
  }
  bool selectActive(bool enabled) {
    if (active == enabled) return true;
    const float v = sample().voltage_mV;
    if (enabled && !active_cell.configure(cell.parameters())) return false;
    if (!(enabled ? active_cell.reset(v) : cell.reset(v))) return false;
    active = enabled;
    return true;
  }
  Mode mode = Mode::Access;
  Source source = Source::Hardware;
  bool diagnostic = false;
  TimingTrace trace;
  bool cc_pot_enabled = true;
  bool rearm_spike_output = false;
  bool command_ok = true;
  uint64_t tick = 0;
  uint32_t solve_us = 0;
  uint32_t previous_loop_us = 0;
  bool missed_wall_period = false;
  uint16_t flags = 0;
  // Explicit teaching conversion, not a measurement of biological current.
  static constexpr float nA_per_legacy_unit = 0.01f;
  float step_hold_mV = -70, step_target_mV = -60;
  uint64_t step_start = 0, step_end = 0;
  float command(float hardware, float holding) const {
    if (source == Source::Direct) return holding;
    if (source == Source::Step)
      return tick >= step_start && tick < step_end ? step_target_mV : step_hold_mV;
    return hardware;
  }
};
} // namespace vc
