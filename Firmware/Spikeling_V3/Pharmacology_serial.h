/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
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
#include "Pharmacology_synapses.h"
#include "Pharmacology_intrinsic.h"

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
   PH M 0|1: current/conductance. PH R syn 0|1|2: receptor legacy/AMPA/GABA-A.
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
      if (a < 1 || a > 2 || b < 0 || b > 2) return;
      if (pharmacology.syn[a-1].receptor != PharmReceptor(b)) {
        pharmacology.syn[a-1].receptor = PharmReceptor(b);
        pharmResetSynapse(uint8_t(a-1));                       // Identity changes reset only that receptor's activation.
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
