#pragma once     

#include "General_settings.h"
#include <math.h>                                        // Reject NaN and non-finite serial values
#include <errno.h>                                       // Detect numerical overflow while parsing
#include <limits.h>                                      // Bounds-check integer arguments
#include <stdlib.h>                                      // strtof / strtol are strict token parsers


inline SerialCommand SCmd;

// All PH and VC handlers are defined below and registered by SerialFunctions().





/* Parse an entire floating-point argument; never treat malformed tokens as zero.
   Input/output: next ASCII parameter and floating result, in the receiving command's units.
   Rejected commands preserve their previous settings; extra tokens are checked by callers. */
static inline bool readNextFloat(float &out) {
  char *arg = SCmd.next();                             // Receive exactly one ASCII token.
  if (!arg || !*arg) return false;                     // Missing and empty arguments are invalid.
  errno = 0;                                          // Clear the previous numeric conversion status.
  char *end = nullptr;                                // Capture any unconsumed suffix.
  const float parsed = strtof(arg, &end);              // Convert only a valid finite decimal number.
  if (errno == ERANGE || end == arg || *end || !isfinite(parsed)) return false; // Reject overflow, suffixes and NaN/Inf.
  out = parsed;                                       // Commit the checked result only after validation.
  return true;
}

/* Parse one complete signed integer without atoi's silent zero-on-error behaviour.
   Input/output: command token and int; returns false on overflow or a non-integral token. */
static inline bool readNextInt(int &out) {
  char *arg = SCmd.next();                             // Receive exactly one ASCII argument.
  if (!arg || !*arg) return false;                      // Do not interpret missing arguments as zero.
  errno = 0;                                           // Clear conversion error status.
  char *end = nullptr;                                 // Detect trailing text or decimal fractions.
  const long parsed = strtol(arg, &end, 10);            // Convert signed base-ten integer.
  if (errno == ERANGE || end == arg || *end || parsed < INT_MIN || parsed > INT_MAX) return false; // Reject malformed/out-of-range input.
  out = static_cast<int>(parsed);                      // Commit only the validated integer.
  return true;
}






/* ================= Original validated module: Pharmacology_serial.h ================= */
/* SPDX-License-Identifier: GPL-3.0-or-later */
/* ========================================================================================================
  Spikeling V3 - Validated optional pharmacology serial commands
  ---------------------------------------------------------------------------------------------------------
  Include AFTER Serial_functions.h, General_settings.h and pharmacology model headers.
  All PH commands are silent: no diagnostic text is interleaved with binary samples.
  Only valid complete argument lists can change live settings; invalid commands do nothing.
  Syntax is documented in docs/SERIAL_COMMANDS.md; this module never changes legacy commands.
  (c) 2026 Open Source Neuro contributors. GPL-3.0-or-later.
  ====================================================================================================== */
#include <stdlib.h>
#include <string.h>
#include <errno.h>
/* Parse one strict decimal argument, rejecting NaN, infinity, suffixes and missing arguments.
   Input/output: float result; output: success. Called only inside the PH command dispatcher. */
inline bool pharmNextFloat(float &v) {
  char *arg = SCmd.next();
  if (!arg || !*arg) return false;
  errno = 0;
  char *end = nullptr;
  const float candidate = strtof(arg, &end);
  if (errno == ERANGE || end == arg || *end || !isfinite(candidate)) return false;
  v = candidate;
  return true;
}

/* Parse one signed decimal integer with complete-string validation and no wrap-around.
   Input/output: long; output success. Used for booleans, receptor/mode indices and site counts. */
inline bool pharmNextInt(long &v) {
  char *arg = SCmd.next();
  if (!arg || !*arg) return false;
  errno = 0;
  char *end = nullptr;
  const long candidate = strtol(arg, &end, 10);
  if (errno == ERANGE || end == arg || *end) return false;
  v = candidate;
  return true;
}

/* Parse uint32 seed without losing the low bits through float conversion.
   Input/output: 32-bit seed. Missing or out-of-range values leave the existing seed unchanged. */
inline bool pharmNextSeed(uint32_t &seed) {
  char *arg = SCmd.next();
  if (!arg || !*arg || *arg == '-') return false;
  errno = 0;
  char *end = nullptr;
  const unsigned long candidate = strtoul(arg, &end, 10);
  if (errno == ERANGE || end == arg || *end || candidate > 4294967295UL) return false;
  seed = (uint32_t)candidate;
  return true;
}

/* Reject trailing tokens to avoid accepting misspelt or partially transmitted commands.
   Called only after all expected arguments have been parsed into temporary variables. */
inline bool pharmNoMoreArgs() { return SCmd.next() == nullptr; }

/* Apply a change in the optional PH command family, leaving legacy commands unmodified.
   PH E 0|1: global enable. PH D index concentration: drug in predefined units.
   PH M 0|1: current/conductance. PH R syn 0|1|2: manual legacy/AMPA/GABA-A; 3: automatic polarity.
   PH N 0|1: NMDA; PH G value: E_GABA in mV; PH C 0|1: presyn CaV2.2.
   PH F syn fraction: CaV2.2 fraction; PH L syn 0|1: release mode.
   PH S syn N: sites 1..128; PH P syn p0: probability in (0,1]; PH Z seed: RNG.
   PH X: reset numerical pharmacology and synaptic states without changing user configuration.
   The syn argument is 1 or 2, not zero-based; every argument is checked before mutation.
   All commands remain silent to preserve uninterrupted binary sample packet parsing. */
inline void PharmSerialCommand() {
  char *operation = SCmd.next();
  if (!operation || !*operation || operation[1]) return;
  const char op = operation[0];
  float value;
  long a, b;
  uint32_t seed;
  switch (op) {
    case 'E':
      if (!pharmNextInt(a) || (a != 0 && a != 1) || !pharmNoMoreArgs()) return;
      if (a && !pharmacology.enabled) {
        pharmResetIntrinsic(neuron.v);                             // Initialise auxiliary states at current voltage.
        pharmAdoptLegacyCurrents(syn1.current, syn2.current);     // Preserve ongoing current when enabling optional mode.
      }
      pharmacology.enabled = a == 1;
      return;
    case 'D':
      if (!pharmNextInt(a) || !pharmNextFloat(value) || !pharmNoMoreArgs()) return;
      if (a < 0 || a > 7) return;
      pharmSetDrug(uint8_t(a), value);                          // Concentration -> cached blockade, with range checking.
      return;
    case 'M':
      if (!pharmNextInt(a) || (a != 0 && a != 1) || !pharmNoMoreArgs()) return;
      if (pharmacology.mode != PharmSynapseMode(a)) {
        pharmacology.mode = PharmSynapseMode(a);
        if (a == 0) pharmacology.nmda_enabled = false;       // NMDA is unavailable in current-based mode.
        pharmResetSynapses();                                   // Explicit mode changes never reinterpret old activation.
      }
      return;
    case 'R':
      if (!pharmNextInt(a) || !pharmNextInt(b) || !pharmNoMoreArgs()) return;
      if (a < 1 || a > 2 || b < 0 || b > 3) return;             // Require Synapse 1/2 and a supported receptor or automatic-mode index.
      if (b == 3) {                                             // PH R synapse 3: return control to effective-gain polarity.
        pharmacology.syn[a-1].auto_receptor = true;              // Restore automatic identity tracking for this synapse.
        return;                                                 // The next model loop reads the latest knob/GUI gain before synchronising.
      }
      pharmacology.syn[a-1].auto_receptor = false;               // PH R synapse 0/1/2: legacy explicit receptor override.
      if (pharmacology.syn[a-1].receptor != PharmReceptor(b)) {   // Avoid unnecessary resets when manual identity is unchanged.
        pharmacology.syn[a-1].receptor = PharmReceptor(b);       // Commit the explicitly requested receptor identity.
        pharmResetSynapse(uint8_t(a-1));                       // Clear only this synapse's incompatible current/conductance tails.
      }
      return;
    case 'N':
      if (!pharmNextInt(a) || (a != 0 && a != 1) || !pharmNoMoreArgs()) return;
      if (a && pharmacology.mode != PharmSynapseMode::Conductance) return;
      pharmacology.nmda_enabled = a == 1;
      return;
    case 'G':
      if (!pharmNextFloat(value) || !pharmNoMoreArgs()) return;
      if (value < -110.0f || value > 30.0f) return;
      pharmacology.e_gaba = value;                              // Advanced shunting/depolarising GABA demonstrations.
      return;
    case 'C':
      if (!pharmNextInt(a) || (a != 0 && a != 1) || !pharmNoMoreArgs()) return;
      pharmacology.presyn_enabled = a == 1;
      return;
    case 'F':
      if (!pharmNextInt(a) || !pharmNextFloat(value) || !pharmNoMoreArgs()) return;
      if (a < 1 || a > 2 || value < 0.0f || value > 1.0f) return;
      pharmacology.syn[a-1].ntype_fraction = value;
      return;
    case 'L':
      if (!pharmNextInt(a) || !pharmNextInt(b) || !pharmNoMoreArgs()) return;
      if (a < 1 || a > 2 || b < 0 || b > 1) return;
      pharmacology.syn[a-1].release_mode = PharmReleaseMode(b);
      return;
    case 'S':
      if (!pharmNextInt(a) || !pharmNextInt(b) || !pharmNoMoreArgs()) return;
      if (a < 1 || a > 2 || b < 1 || b > 128) return;
      pharmacology.syn[a-1].sites = uint8_t(b);
      return;
    case 'P':
      if (!pharmNextInt(a) || !pharmNextFloat(value) || !pharmNoMoreArgs()) return;
      if (a < 1 || a > 2 || value <= 0.0f || value > 1.0f) return;
      pharmacology.syn[a-1].p0 = value;                          // Preserve baseline normalisation when future STP changes p.
      return;
    case 'Z':
      if (!pharmNextSeed(seed) || !pharmNoMoreArgs()) return;
      pharmSeed(seed);                                           // Seed command intentionally restarts BOTH RNG streams.
      return;
    case 'X':
      if (!pharmNoMoreArgs()) return;
      pharmResetIntrinsic(neuron.v);
      pharmResetSynapses();
      syn1.current = 0.0f; syn2.current = 0.0f;                 // Explicit reset also clears original current states.
      pharmSeed(pharmacology.seed);                            // Deterministic reset reruns same stochastic sequences.
      return;
    default: return;
  }
}



/* Return an on-demand binary receptor-status frame without corrupting normal AA 55 packets.
   Command: PHS ? (no other operands). Status is unavailable during VC1/VC2 ASCII streaming.
   Hardware CDC writes are bounded by output capacity; failed requests may be retried by GUI.
   This is read-only and does not change receptor configuration, membrane or drug state. */
inline void PharmStatusSerialCommand() {
  char *operation = SCmd.next();                           // Read the single diagnostic operation token.
  if (!operation || strcmp(operation, "?") != 0 || SCmd.next() != nullptr) return; // Reject malformed, missing and extra arguments.
  if (clampMode == ClampMode::VoltageClamp && voltageClamp.diagnostic) return; // Never intermix a binary response with the VC1/VC2 CSV stream.
  uint8_t frame[11];                                        // Allocate one small fixed-size status record on the stack.
  pharmEncodeReceptorStatus(frame, syn1.gain, syn2.gain, syn1.use_syn_pot, syn2.use_syn_pot); // Encode the last completed effective-gain sample.
#if VC_GUARDED_HWCDC
  if (Serial.availableForWrite() < int(sizeof(frame))) return; // Never block a real-time model step on a slow or absent host.
  if (Serial.write(frame, sizeof(frame)) != sizeof(frame)) vc::usb_tx_fault = true; // Record unexpected partial USB writes without retrying fragments.
#else
  Serial.write(frame, sizeof(frame));                       // Preserve Arduino Serial semantics for non-validated transports.
#endif
}

/* Opt-in quantal-release audit. All commands are silent except explicit frozen queries.
   PHQ 1 resets/arms, PHQ 0 freezes, PHQ ? reports the summary, PHQ P offset reads 12 records.
   The host MUST stop VC2 streaming and freeze logging before querying any page. */
inline void PharmAuditSerialCommand() {
  char *operation = SCmd.next();                                     // Read sub-command within the existing 32-byte serial buffer.
  if (!operation || !*operation) return;                             // Ignore empty requests without affecting ordinary telemetry.
  if (strcmp(operation,"1") == 0 && pharmNoMoreArgs()) {             // Start a fresh experiment without touching the RNG.
    pharmAuditSet(true);                                            // Clear old records and capture incoming TTL rising edges.
    return;
  }
  if (strcmp(operation,"0") == 0 && pharmNoMoreArgs()) {             // Freeze the captured events for a consistent query.
    pharmAuditSet(false);                                           // Retain counters and event array unchanged.
    return;
  }
  if (pharmReleaseAudit.armed) return;                               // Never perform serial dumps during real-time recording.
  char line[200];                                                   // Bounded serial response buffer on stack.
  if (strcmp(operation,"?") == 0 && pharmNoMoreArgs()) {
    int n=snprintf(line,sizeof(line),"PHQS1,%u,%u,%lu,%lu,%lu,%lu,%lu,%u\n",
      unsigned(PharmReleaseAudit::capacity),unsigned(pharmReleaseAudit.count),
      (unsigned long)pharmReleaseAudit.overflow,
      (unsigned long)pharmReleaseAudit.received[0],(unsigned long)pharmReleaseAudit.received[1],
      (unsigned long)pharmReleaseAudit.failures[0],(unsigned long)pharmReleaseAudit.failures[1],
      unsigned(pharmReleaseAudit.armed));
    if (n>0 && size_t(n)<sizeof(line)) Serial.write(reinterpret_cast<const uint8_t*>(line),size_t(n));
    Serial.print("PHQEND,S\n");                                    // Explicit LF terminator for bounded host reads.
    return;
  }
  if (strcmp(operation,"P") == 0) {
    long start;                                                     // Index within the frozen event array.
    if (!pharmNextInt(start) || start<0 || start>PharmReleaseAudit::capacity || !pharmNoMoreArgs()) return;
    const uint16_t first=uint16_t(start);                           // The bounded index cannot overflow uint16_t.
    const uint16_t final=uint16_t(first+12)<pharmReleaseAudit.count ? uint16_t(first+12) : pharmReleaseAudit.count;
    int n=snprintf(line,sizeof(line),"PHQP1,%u,%u\n",unsigned(first),unsigned(final));
    if (n>0 && size_t(n)<sizeof(line)) Serial.write(reinterpret_cast<const uint8_t*>(line),size_t(n));
    for (uint16_t k=first;k<final;++k) {
      const auto &e=pharmReleaseAudit.events[k];                     // Read only a fully frozen event.
      n=snprintf(line,sizeof(line),"PHQE1,%u,%u,%lu,%u,%u,%.8f,%.8f,%.8f\n",
        unsigned(k),unsigned(e.synapse),(unsigned long)e.tick,unsigned(e.quanta),unsigned(e.sites),
        double(e.calcium_efficiency),double(e.stp_multiplier),double(e.release_multiplier));
      if (n>0 && size_t(n)<sizeof(line)) Serial.write(reinterpret_cast<const uint8_t*>(line),size_t(n));
    }
    n=snprintf(line,sizeof(line),"PHQEND,%u\n",unsigned(first));
    if (n>0 && size_t(n)<sizeof(line)) Serial.write(reinterpret_cast<const uint8_t*>(line),size_t(n));
    return;
  }
}

/* ================= Original validated module: VoltageClamp_commands.h ================= */
/* SPDX-License-Identifier: GPL-3.0-or-later */
// Included after SCmd and General_settings.h. Commands are short enough for the
// existing 32-byte SerialCommand buffer; no unsolicited text enters binary mode.
#include <cstdlib>

inline bool vcReadFloat(float& value) {
  char* token = SCmd.next();
  if (!token) return false;
  errno = 0;                                           // Clear numeric overflow status before conversion.
  char* end = nullptr;                                 // Detect invalid suffixes and incomplete numbers.
  const float candidate = strtof(token, &end);          // Parse the candidate without changing the caller's state.
  if (errno == ERANGE || end == token || *end != '\0' || !std::isfinite(candidate)) return false;
  value = candidate;                                   // Commit only a complete finite value.
  return true;
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
  vc::diagnosticUsbMode(clampMode == ClampMode::VoltageClamp && voltageClamp.diagnostic);
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
  vc::diagnosticUsbMode(clampMode == ClampMode::VoltageClamp && voltageClamp.diagnostic);
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


/* Override a pot-controlled floating parameter only after validating its complete command.
   Input: override flag, destination variable and legacy GUI scaling; leaves both unchanged on errors. */
static inline void setFloatParam(bool &usePotFlag, float &param, float scale = 1.0f) {
  float val;                                           // Hold the candidate until every argument is checked.
  if (!readNextFloat(val) || SCmd.next() != nullptr || !isfinite(val * scale)) return; // Reject malformed, extra or overflowing values.
  param = val * scale;                                 // Apply the existing GUI-to-firmware unit conversion.
  usePotFlag = false;                                 // Disable the hardware potentiometer only after acceptance.
}

/* Override a pot-controlled integer without inadvertently disabling the hardware knob. */
static inline void setIntParam(bool &usePotFlag, int &param) {
  int val;                                             // Keep a temporary until command parsing succeeds.
  if (!readNextInt(val) || SCmd.next() != nullptr) return; // Missing/extra/invalid arguments change nothing.
  param = val;                                         // Apply the accepted legacy integer value.
  usePotFlag = false;                                 // GUI acquires control only after acceptance.
}



inline void SetRefreshRate(){
  int val_us;
  if (readNextInt(val_us) && SCmd.next() == nullptr && val_us >= 1000 && val_us <= 1000000) {
    timing.step_us  = (uint32_t)(val_us);               // Guard against zero/negative periods and scheduler overflow.
  }
}


inline void applyNeuronParameters(float a, float b, float c, float d, float v_rest) {
  neuron.a = a;
  neuron.b = b;
  neuron.c = c;
  neuron.d = d;
  neuron.v_rest = v_rest;

  // Reset dynamic state cleanly
  neuron.v = neuron.v_rest;
  neuron.u = neuron.b * neuron.v;
  neuron.v_out = neuron.v;
  neuron.total_current = 0.0f;
  neuron.spike = false;
  pharmResetIntrinsic(neuron.v);

  // Reset clamp-related state as well, otherwise an old V-clamp / current state
  // can make it look as if the model immediately reverted or became unstable.
  patch.e_int = 0.0f;
  patch.I_clamp = 0.0f;

  if (clampMode == ClampMode::VoltageClamp) {
    patch.v_hold = constrain(neuron.v_rest, vc::command_min, vc::command_max);
    voltageClamp.reset(neuron.v);
    voltageClamp.source = vc::Source::Hardware;
    patch.v_cmd  = patch.v_hold;
    patch.v_step = 0.0f;
  }
}

inline void NeuronPreset() {
  int idx;
  // Read preset index from command:
  if (!readNextInt(idx)) {
    return;
  }
  // Safety check before indexing izhikevich[]
  if (idx < 0 || idx >= (int)IzhikevichModelCount || SCmd.next() != nullptr) {
    return;
  }

  const IzhikevichParams &p =
    getIzhikevichParams(static_cast<IzhikevichModel>(idx));

  applyNeuronParameters(p.a, p.b, p.c, p.d, p.v_rest);

  neuron.selected_model = idx;
  neuron.custom_model = false;
}

inline void NeuronCustom() {
  float a, b, c, d; 
  // Read required parameters
  if (!readNextFloat(a)) return;
  if (!readNextFloat(b)) return;
  if (!readNextFloat(c)) return;
  if (!readNextFloat(d) || SCmd.next() != nullptr) return;  // Reject partial and trailing parameters atomically.
  // Imported/custom neurons currently provide only a,b,c,d.
  // Keep the existing v_rest unless you later add v_rest to the CSV.
  applyNeuronParameters(a, b, c, d, neuron.v_rest);

  neuron.selected_model = -1;
  neuron.custom_model = true;

  // // Reset neuron state to a consistent initial condition
  // neuron.v = neuron.v_rest;
  // neuron.u = neuron.b * neuron.v;              
}



inline void StimFre_on(){
  setIntParam(pot.use_stimfrequency_pot, stim.freq);
}
inline void StimFre_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  pot.use_stimfrequency_pot = true;
}



inline void StimStr_on(){
  int val;                                             // Parse before taking control from the hardware knob.
  if (readNextInt(val) && SCmd.next() == nullptr) {
    stim.str_digital = val;                           // Preserve original digital stimulus command semantics.
    stim.str_analog = val;                            // Match the original analogue command value.
    pot.use_stimstrength_pot = false;                // Rejecting malformed commands preserves the knob.
  }
}
inline void StimStr_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  pot.use_stimstrength_pot = true;
}



inline void StimCus_on(){
  setIntParam(stim.custom_disable, stim.value_custom);
}
inline void StimCus_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  stim.custom_disable = true; // Exit custom mode -> return to pot/square mode
}



inline void Serial_Trigger(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  stim.serialTrigger_enable = true;
}



inline void PDGain_on(){
  setFloatParam(pot.use_photodiode_pot, PD.gain, 0.1f);
}
inline void PDGain_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  pot.use_photodiode_pot = true;
}



inline void PDDecay_on(){
  setFloatParam(PD.decay_enable, PD.decay);
}
inline void PDDecay_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  PD.decay_enable = true;
}



inline void PDRecovery_on(){
  setFloatParam(PD.recovery_enable, PD.recovery);
}
inline void PDRecovery_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  PD.recovery_enable = true;
}



inline void patch_on() {
  float val;
  if (clampMode == ClampMode::VoltageClamp) {
    voltageClamp.command_ok = vcReadFloat(val) && vcNoMoreArguments() &&
                              vcSetHolding(val, vc::Source::Hardware);
    return;
  }
  // Preserve the original current-clamp command and parsing behaviour.
  if (!readNextFloat(val) || SCmd.next() != nullptr) return; // Reject missing/extra arguments without touching the override.
  pot.use_patch_pot = false;
  patch.current_clamp = val;
}
inline void patch_off() {
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  pot.use_patch_pot = true;
  if (clampMode == ClampMode::VoltageClamp) voltageClamp.source = vc::Source::Hardware;
}
inline void VClampMode() {
  float value;
  voltageClamp.command_ok = vcReadFloat(value) && (value == 0 || value == 1) && vcNoMoreArguments();
  if (voltageClamp.command_ok)
    setClampMode(value ? ClampMode::VoltageClamp : ClampMode::CurrentClamp);
}
inline void VPID_set() {
  // The passive equivalent circuit has no PI gains. Flag the obsolete command.
  voltageClamp.command_ok = false;
}
inline void VILIM_set() { VCLimits(); }  // VC current limits now have explicit nA units.
inline void VSpan_set() {
  float value;
  voltageClamp.command_ok = vcReadFloat(value) && value > 0 && value <= 190 && vcNoMoreArguments();
  if (voltageClamp.command_ok) patch.v_cmd_span = value;
}
inline void VClampReset() {
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  patch.e_int = 0;
  patch.I_clamp = 0;
  voltageClamp.reset(neuron.v);
  voltageClamp.source = vc::Source::Hardware;
  voltageClamp.command_ok = true;
}

inline void Noise_on(){
  setFloatParam(pot.use_noise_pot, noise.current);
}
inline void Noise_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  pot.use_noise_pot = true;
}



inline void Syn1Gain_on(){
  setFloatParam(syn1.use_syn_pot, syn1.gain, 0.25f);
}
inline void Syn1Gain_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  syn1.use_syn_pot = true;
}



inline void Syn1Decay_on(){
  setFloatParam(syn1.decay_enable, syn1.decay, 1.0f / 1000.0f);
}
inline void Syn1Decay_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  syn1.decay_enable = true;
}



inline void Syn2Gain_on(){
  setFloatParam(syn2.use_syn_pot, syn2.gain, 0.25f);
}
inline void Syn2Gain_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  syn2.use_syn_pot = true;
}



inline void Syn2Decay_on(){
  setFloatParam(syn2.decay_enable, syn2.decay, 1.0f / 1000.0f);
}
inline void Syn2Decay_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  syn2.decay_enable = true;
}



// // // // // // // // // // // // // // // // // // // // // // // //
//                      Short-term plasticity                       //
// Each command changes ONLY its selected synapse and clears that synapse's
// transient facilitation/depletion state. The existing current tail is retained.
// STP and pharmacology now share a single presynaptic event gain; the mode
// remains independent of PH E and the receiving clamp mode.
inline void SetSTPMode(Synapse &syn) {
  int mode;                                                                                     // 0 Off; 1 Facilitation; 2 Depression; 3 Combined
  if (!readNextInt(mode) || SCmd.next() != nullptr) return;                                    // Missing/extra mode leaves state unchanged
  if (mode < 0 || mode > 3) return;                                                             // Reject undefined classroom presets
  STP_setMode(syn.stp, static_cast<uint8_t>(mode));                                              // Preserve raw synaptic-current tail across mode changes
}

inline void Syn1STPMode() {
  SetSTPMode(syn1);                                                                             // Configure independently of clamp mode
}
inline void Syn2STPMode() {
  SetSTPMode(syn2);                                                                             // Configure independently of clamp mode
}


inline void Buzzer_on(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  spike.Buzzer_enable = true;
}
inline void Buzzer_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  spike.Buzzer_enable = false;
  digitalWrite(pins.gpio.spike, LOW);
}



inline void LED_on(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  spike.LED_enable = true;
}
inline void LED_off(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  spike.LED_enable = false;
  ledcWrite(pins.gpio.led_r, 0);
  ledcWrite(pins.gpio.led_g, 0);
  ledcWrite(pins.gpio.led_b, 0);
  ledcWrite(pins.gpio.led_stim_r, 0);                                         
  ledcWrite(pins.gpio.led_stim_g, 0);                                          
  ledcWrite(pins.gpio.led_stim_b, 0);                                          
}



inline void Connected(){
  if (SCmd.next() != nullptr) return;                  // No-argument command: reject unexpected data without changing state.
  digitalWrite(pins.gpio.led_r,HIGH);delay(5);
  digitalWrite(pins.gpio.led_g,HIGH);digitalWrite(pins.gpio.led_r,LOW);delay(5);
  digitalWrite(pins.gpio.led_b,HIGH);digitalWrite(pins.gpio.led_g,LOW);delay(5);
  digitalWrite(pins.gpio.led_b,LOW);delay(5);
}



inline void Unrecognized(const char *cmd) {
  (void)cmd;                                     // Unknown commands are ignored: never interleave ASCII with binary data.
}



inline void SerialFunctions(){
  SCmd.addCommand("DT",SetRefreshRate);
  SCmd.addCommand("NEU", NeuronPreset); 
  SCmd.addCommand("NE", NeuronCustom); 
  SCmd.addCommand("FR1",StimFre_on);
  SCmd.addCommand("FR0",StimFre_off);
  SCmd.addCommand("ST1",StimStr_on);
  SCmd.addCommand("ST0",StimStr_off);
  SCmd.addCommand("SC1",StimCus_on);
  SCmd.addCommand("SC0",StimCus_off);
  SCmd.addCommand("TR",Serial_Trigger);
  SCmd.addCommand("PG1",PDGain_on);
  SCmd.addCommand("PG0",PDGain_off);
  SCmd.addCommand("PD1",PDDecay_on);
  SCmd.addCommand("PD0",PDDecay_off);
  SCmd.addCommand("PR1",PDRecovery_on);
  SCmd.addCommand("PR0",PDRecovery_off);
  SCmd.addCommand("PC1",patch_on);
  SCmd.addCommand("PC0",patch_off);
  SCmd.addCommand("VCMD",VCommand);        // Absolute Vcmd; ignores Current-In voltage steps.
  SCmd.addCommand("VCA",VCActive);
  SCmd.addCommand("VCINFO",VCInfo);        // Explicit prototype/version/units query.
  SCmd.addCommand("VCPR",VCProfile);       // Opt-in timing trace; explicit frozen query only.
  SCmd.addCommand("VCP",VCParameters);     // Cm[pF] Rm[MOhm] Rs[MOhm] EL[mV]
  SCmd.addCommand("VCL",VCLimits);         // Imin[nA] Imax[nA]
  SCmd.addCommand("VCI",VCIdeal);          // 0=finite access (default), 1=ideal
  SCmd.addCommand("VCT",VCDiagnostics);    // 1=CSV diagnostic stream, 0=legacy frames
  SCmd.addCommand("VSTEP",VCStep);        // absolute target[mV] delay[ms] duration[ms]
  SCmd.addCommand("VCM",VClampMode);        // 0=current clamp, 1=voltage clamp
  SCmd.addCommand("PH",PharmSerialCommand);
  SCmd.addCommand("PHS",PharmStatusSerialCommand); // Read-only 11-byte framed receptor/gain status query for GUI target availability.
  SCmd.addCommand("PHQ",PharmAuditSerialCommand); // Optional frozen incoming-spike/vesicle audit; disabled by default.
  SCmd.addCommand("VPID",VPID_set);         
  SCmd.addCommand("VIL",VILIM_set);        
  SCmd.addCommand("VSP",VSpan_set);         
  SCmd.addCommand("VRS",VClampReset);       
  SCmd.addCommand("NO1",Noise_on);
  SCmd.addCommand("NO0",Noise_off);
  SCmd.addCommand("STP1",Syn1STPMode);                                                       // Per-channel STP mode, valid in CC and VC
  SCmd.addCommand("STP2",Syn2STPMode);                                                       // Mode selection resets only the targeted transient state
  SCmd.addCommand("SG11",Syn1Gain_on);
  SCmd.addCommand("SG10",Syn1Gain_off);
  SCmd.addCommand("SD11",Syn1Decay_on);
  SCmd.addCommand("SD10",Syn1Decay_off);
  SCmd.addCommand("SG21",Syn2Gain_on);
  SCmd.addCommand("SG20",Syn2Gain_off);
  SCmd.addCommand("SD21",Syn2Decay_on);
  SCmd.addCommand("SD20",Syn2Decay_off);
  SCmd.addCommand("BZ1",Buzzer_on);
  SCmd.addCommand("BZ0",Buzzer_off);
  SCmd.addCommand("LED1",LED_on);
  SCmd.addCommand("LED0",LED_off);
  SCmd.addCommand("CON",Connected);
  SCmd.setDefaultHandler(Unrecognized);
}



