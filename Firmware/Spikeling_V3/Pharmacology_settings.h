/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
/* ========================================================================================================
  Spikeling V3 - Optional pharmacology: configurations, concentrations and dynamic states
  ---------------------------------------------------------------------------------------------------------
  Independent of hardware pin definitions. All parameters are phenomenological Izhikevich-model units.
  Concentrations use the units encoded in their variable names, never SI base units implicitly.
  This educational model is not a preparation-specific pharmacokinetic or ion-channel model.
  Include from the main sketch AFTER General_settings.h, and before the pharmacology function headers.
  (c) 2026 Open Source Neuro contributors. GPL-3.0-or-later.
  ====================================================================================================== */
#include <stdint.h>
#include <math.h>

// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // //
/*                                          Enumerations                                                  */
enum class PharmReceptor : uint8_t { Legacy = 0, AMPA = 1, GABAA = 2 };
enum class PharmSynapseMode : uint8_t { Current = 0, Conductance = 1 };
enum class PharmReleaseMode : uint8_t { Deterministic = 0, Probabilistic = 1 };
enum class PharmDrug : uint8_t { TTX = 0, TEA = 1, Apamin = 2, AP4 = 3, NBQX = 4, Gabazine = 5, APV = 6, GVIA = 7 };

// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // //
/*                                   Pharmacological configuration                                      */
struct PharmSynapseState {
  PharmReceptor receptor = PharmReceptor::Legacy;                       // Default: original current synapse, with unspecified receptor.
  PharmReleaseMode release_mode = PharmReleaseMode::Deterministic;      // Default: deterministic release; no stochastic draws.
  uint8_t sites = 4;                                                    // Binomial release sites, valid 1..128.
  float p0 = 0.35f;                                                     // Baseline release probability/site, 0 < p0 <= 1.
  float ntype_fraction = 0.35f;                                         // Illustrative CaV2.2 contribution, in [0,1].
  uint32_t rng_state = 1;                                               // Independent xorshift32 stream; must not be zero.
  float released_current = 0.0f;                                        // Delivered signed current state, Izhikevich units.
  float conductance = 0.0f;                                             // Released nonnegative AMPA or GABA conductance.
  float nmda_rise = 0.0f;                                               // NMDA rise state (pre-normalisation).
  float nmda_decay = 0.0f;                                              // NMDA decay state (pre-normalisation).
  float effective_current = 0.0f;                                       // Total current consumed by the neuron THIS step.
  float last_release_multiplier = 1.0f;                                 // Last incoming AP's quantal event scale.
  uint8_t last_quanta = 0;                                              // Number of release quanta at last incoming AP.
};

struct PharmIntrinsicState {
  float h_na = 0.0f;                                                     // Shared phenomenological Na availability [0,1].
  float h_a = 0.0f;                                                      // Voltage-dependent A-type availability [0,1].
  float s_sk = 0.0f;                                                     // SK-like accumulated spike activity [0,1].
  bool committed = false;                                               // TTX upstroke passed accepted onset detector.
  bool armed = true;                                                    // Eligible to detect a new -30 mV upstroke.
  bool failed_passive = false;                                          // Aborted upstroke temporarily follows passive branch.
  bool verified_event = false;                                          // True for one integration step on verified AP.
  uint32_t rejected_attempts = 0;                                       // Failed / aborted action-potential attempts.
};

struct PharmacologySettings {
  bool enabled = false;                                                 // Master switch OFF by default (bitwise legacy path).
  PharmSynapseMode mode = PharmSynapseMode::Current;                     // Original current-based input model.
  bool nmda_enabled = false;                                            // Optional only in glutamatergic conductance mode.
  bool presyn_enabled = false;                                          // Optional event-time CaV2.2/GVIA model.
  float concentration[8] = {0.0f,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f};  // In drug-specific units; all OFF initially.
  float block[8] = {0.0f,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f};          // Precomputed Hill blockade [0,1].
  float e_ampa = 0.0f;                                                   // AMPA reversal, mV.
  float e_gaba = -80.0f;                                                 // GABA-A reversal, mV (advanced user setting).
  float e_nmda = 0.0f;                                                   // NMDA reversal, mV.
  float extracellular_mg_mM = 1.0f;                                     // Physiological illustration; Mg blocker in mM.
  float nmda_peak_ratio = 2.0f;                                         // Peak NMDA/AMPA conductance ratio.
  float nmda_rise_ms = 4.0f;                                            // Numerical model milliseconds.
  float nmda_decay_ms = 100.0f;                                         // Numerical model milliseconds.
  float e_reference = -70.0f;                                           // Conductance calibrated at this model voltage.
  float gvia_cooperativity = 3.0f;                                      // Illustrative release cooperativity exponent.
  uint32_t seed = 20261028UL;                                          // Reproducible base seed, independent streams.
  PharmIntrinsicState intrinsic;                                        // Mutable neuron pharmacology state.
  PharmSynapseState syn[2];                                             // Independent presynaptic/postsynaptic states.
};

inline PharmacologySettings pharmacology;                               // Single shared firmware configuration/state.

/*                                Accepted half-block values                                            */
static constexpr float pharm_ic50[8] = {9.2f, 0.5f, 2.3f, 0.88f, 0.30f, 0.90f, 3.7f, 10.0f};
// Units respectively: nM, mM, nM, mM, uM, uM, uM, nM. These values are illustrative/preparation-specific.

// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // //
/*                                       Numeric helpers                                                */
/* Clamp floating-point state to [0,1]; only call with finite values (serial parser rejects NaN/Inf).
   Input: finite x; output: unit interval; called in auxiliary state and release dynamics. */
inline float pharmClip01(float x) { return x <= 0.0f ? 0.0f : (x >= 1.0f ? 1.0f : x); }

/* Compute Hill inhibition C/(C+IC50), exactly zero when concentration is zero.
   Input: nonnegative finite C in the unit of its drug, positive IC50 in matching unit.
   Output: [0,1]. Called on concentration changes, never unnecessarily per simulation tick. */
inline float pharmHill(float concentration, float ic50) {
  if (concentration == 0.0f) return 0.0f;                     // Preserve the original drug-free branch exactly.
  return concentration / (concentration + ic50);              // Hill exponent one; no additional receptor mechanism.
}

/* Validate and apply one drug concentration, atomically after validation.
   Inputs: accepted drug index 0..7, concentration in the corresponding documented unit.
   Output: success flag. Receptor/intrinsic parameters take effect on subsequent updates;
   stored synaptic activations remain intact (a postsynaptic blocker acts immediately). */
inline bool pharmSetDrug(uint8_t drug, float concentration) {
  if (drug >= 8 || !isfinite(concentration) || concentration < 0.0f || concentration > 1000000.0f) return false;
  pharmacology.concentration[drug] = concentration;           // Commit only after validating the entire argument.
  pharmacology.block[drug] = pharmHill(concentration, pharm_ic50[drug]);
  return true;
}

/* Return effective Hill fraction, zero when pharmacology or presynaptic CaV2.2 mode is disabled.
   Called at incoming spike handling, never used for retroactive attenuation of synaptic states. */
inline float pharmGVBlock() {
  return pharmacology.enabled && pharmacology.presyn_enabled ? pharmacology.block[7] : 0.0f;
}
