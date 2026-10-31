/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
// Included after SCmd and General_settings.h. Commands are short enough for the
// existing 32-byte SerialCommand buffer; no unsolicited text enters binary mode.
#include <cstdlib>

inline bool vcReadFloat(float& value) {
  char* token = SCmd.next();
  if (!token) return false;
  char* end = nullptr;
  value = strtof(token, &end);
  return end != token && *end == '\0' && std::isfinite(value);
}
inline void VCInfo() {
  // Explicit query only. Do not send while the desktop GUI owns the binary stream.
  if (voltageClamp.active)
    Serial.println(vc::usb_tx_ready ?
      "VC-ACTIVE-1,mV,ms,nA,pF,MOhm,clock=2,gates=2,voltage=2,trace=2,tx=guarded4096" :
      "VC-ACTIVE-1,mV,ms,nA,pF,MOhm,clock=2,gates=2,voltage=2,trace=2,tx=unavailable");
  else Serial.println("VC-PASSIVE-1,mV,ms,nA,pF,MOhm,clock=2");
}
inline bool vcNoMoreArguments() { return SCmd.next() == nullptr; }
inline void VCProfile() {
  char* token = SCmd.next();
  auto& t = voltageClamp.trace;
  if (!token || !vcNoMoreArguments()) { voltageClamp.command_ok = false; return; }
  if (strcmp(token,"1") == 0 && clampMode == ClampMode::VoltageClamp && voltageClamp.active) {
    t.start();
  } else if (strcmp(token,"0") == 0) {
    t.stop();
  } else if (strcmp(token,"?") == 0) {
    // Explicit query freezes collection before any potentially blocking output.
    t.stop();
    char line[320];
    int n = snprintf(line,sizeof(line),"VCPR2,%lu,%u,%lu,%lu,%lu,%lu,%lu,%lu\n",
      (unsigned long)t.ticks,t.count,(unsigned long)t.overruns,
      (unsigned long)t.late_starts,(unsigned long)t.short_writes,
      (unsigned long)t.format_errors,(unsigned long)t.overflow,(unsigned long)t.capacity_skips);
    Serial.write(reinterpret_cast<const uint8_t*>(line),n);
    for (unsigned i=0;i<t.count;++i) {
      const auto& r=t.records[i];
      n=snprintf(line,sizeof(line),
        "VCE1,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu\n",
        (unsigned long)r.sequence,(unsigned long)r.elapsed_us,(unsigned long)r.total_us,
        (unsigned long)r.stage_us[0],(unsigned long)r.stage_us[1],
        (unsigned long)r.stage_us[2],(unsigned long)r.stage_us[3],
        (unsigned long)r.stage_us[4],(unsigned long)r.stage_us[5],
        (unsigned long)r.stage_us[6],(unsigned long)r.stage_us[7],
        (unsigned long)r.expected_bytes,(unsigned long)r.written_bytes,
        (unsigned long)r.solve_us,(unsigned long)r.reason);
      Serial.write(reinterpret_cast<const uint8_t*>(line),n);
    }
    Serial.print("VCPMAX");
    for (unsigned i=0;i<vc::trace_stage_count;++i) {
      Serial.print(','); Serial.print(t.maximum_stage_us[i]);
    }
    Serial.println();
    Serial.print("VCPREND,"); Serial.println(t.count);
  } else { voltageClamp.command_ok = false; return; }
  voltageClamp.command_ok = true;
}
inline bool vcValidCommand(float value) {
  return std::isfinite(value) && value >= vc::command_min && value <= vc::command_max;
}
inline void VCActive() {
  float value;
  voltageClamp.command_ok = vcReadFloat(value) && (value == 0 || value == 1) &&
    vcNoMoreArguments() && voltageClamp.selectActive(value != 0);
  vc::diagnosticUsbMode(clampMode == ClampMode::VoltageClamp && voltageClamp.active && voltageClamp.diagnostic);
}
inline bool vcSetHolding(float value, vc::Source source) {
  if (!vcValidCommand(value)) return voltageClamp.command_ok = false;
  pot.use_patch_pot = false;
  patch.v_hold = value;
  patch.v_cmd = value;
  patch.v_step = 0;
  voltageClamp.source = source;
  return voltageClamp.command_ok = true;
}
inline void VCommand() {
  float value;
  voltageClamp.command_ok = clampMode == ClampMode::VoltageClamp && vcReadFloat(value) &&
                            vcNoMoreArguments() && vcSetHolding(value, vc::Source::Direct);
}
inline void VCParameters() {
  auto p = voltageClamp.cell.parameters();
  voltageClamp.command_ok = vcReadFloat(p.capacitance_pF) && vcReadFloat(p.membrane_MOhm) &&
    vcReadFloat(p.access_MOhm) && vcReadFloat(p.reversal_mV) && vcNoMoreArguments() &&
    voltageClamp.cell.configure(p);
}
inline void VCLimits() {
  auto p = voltageClamp.cell.parameters();
  voltageClamp.command_ok = vcReadFloat(p.minimum_nA) && vcReadFloat(p.maximum_nA) &&
                            vcNoMoreArguments() && voltageClamp.cell.configure(p);
}
inline void VCIdeal() {
  float value;
  voltageClamp.command_ok = vcReadFloat(value) && (value == 0 || value == 1) && vcNoMoreArguments();
  if (voltageClamp.command_ok) voltageClamp.mode = value ? vc::Mode::Ideal : vc::Mode::Access;
}
inline void VCDiagnostics() {
  float value;
  voltageClamp.command_ok = vcReadFloat(value) && (value == 0 || value == 1) && vcNoMoreArguments();
  if (voltageClamp.command_ok) voltageClamp.diagnostic = value != 0;
  vc::diagnosticUsbMode(clampMode == ClampMode::VoltageClamp && voltageClamp.active && voltageClamp.diagnostic);
}
inline void VCStep() {
  float target, delay_ms, duration_ms;
  if (clampMode != ClampMode::VoltageClamp || !vcReadFloat(target) || !vcReadFloat(delay_ms) ||
      !vcReadFloat(duration_ms) || !vcNoMoreArguments() || !vcValidCommand(target) ||
      delay_ms < 0 || duration_ms <= 0 || delay_ms > 60000 || duration_ms > 60000 ||
      !std::isfinite(neuron.dt_ms) || neuron.dt_ms <= 0) {
    voltageClamp.command_ok = false;
    return;
  }
  const uint64_t delay_ticks = static_cast<uint64_t>(llround(delay_ms/neuron.dt_ms));
  const uint64_t duration_ticks = static_cast<uint64_t>(llround(duration_ms/neuron.dt_ms));
  if (!duration_ticks || std::fabs(delay_ticks*double(neuron.dt_ms)-delay_ms) > 1e-4 ||
      std::fabs(duration_ticks*double(neuron.dt_ms)-duration_ms) > 1e-4) {
    voltageClamp.command_ok = false;
    return;
  }
  voltageClamp.step_hold_mV = patch.v_hold;
  voltageClamp.step_target_mV = target;
  voltageClamp.step_start = voltageClamp.tick + delay_ticks;
  voltageClamp.step_end = voltageClamp.step_start + duration_ticks;
  voltageClamp.source = vc::Source::Step;
  pot.use_patch_pot = false;
  voltageClamp.command_ok = true;
}
