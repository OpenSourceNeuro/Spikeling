/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
/* ========================================================================================================
   Spikeling V3 - Optional illustrative pharmacology: parameters and state
   --------------------------------------------------------------------------------------------------------
   Include from the main sketch after General_settings.h. Concentrations are drug-specific units.
   These phenomenological equations are teaching tools, not biophysical ion-channel predictions.
   (c) 2026 Open Source Neuro contributors. GPL-3.0-or-later.
   ====================================================================================================== */
#include <stdint.h>
#include <math.h>

enum class PharmReceptor : uint8_t { Legacy=0, AMPA=1, GABAA=2 };
enum class PharmSynMode : uint8_t { Current=0, Conductance=1 };
enum class PharmReleaseMode : uint8_t { Deterministic=0, Probabilistic=1 };
// Drug indices: TTX[nM], TEA[mM], apamin[nM], 4-AP[mM],
// NBQX[uM], gabazine[uM], APV[uM], omega-conotoxin GVIA[nM].
static constexpr float pharm_ic50[8]={9.2f,0.5f,2.3f,0.88f,0.30f,0.90f,3.7f,10.0f};

struct PharmIntrinsic {
  float h_na=0.0f;                // Phenomenological sodium availability, 0..1.
  float h_a=0.0f;                 // A-type potassium availability, 0..1.
  float s_sk=0.0f;                // SK-like spike activity, 0..1.
  bool committed=false;          // TTX-dependent upstroke verified at onset, pending peak.
  bool armed=true;               // Arm a new attempt only after Vm recovers sufficiently.
  bool failed_passive=false;     // Failed upstroke temporarily follows passive branch.
  bool verified_event=false;     // Authoritative one-step AP event used for all outputs.
  uint32_t rejected_attempts=0; // Educational diagnostic; never put into binary packet.
};
struct PharmSynapse {
  PharmReceptor receptor=PharmReceptor::Legacy;                   // Legacy raw current by default.
  PharmReleaseMode release_mode=PharmReleaseMode::Deterministic;  // No RNG sampling at boot.
  uint8_t sites=4;                                               // N=4, acceptable 1..128.
  float p0=0.35f;                                                // Baseline release-site probability, (0,1].
  float ntype_fraction=0.35f;                                    // N-type CaV2.2 fraction, [0,1].
  uint32_t rng=1;                                                // Independent deterministic xorshift32 RNG stream.
  float released=0.0f;                                           // Signed released synaptic current state.
  float g_fast=0.0f;                                             // Positive AMPA/GABA-A conductance state.
  float nmda_r=0.0f;                                             // Biexponential fast rise variable.
  float nmda_d=0.0f;                                             // Biexponential slow decay variable.
  float effective=0.0f;                                          // Output current consumed once by neuron.
  float last_multiplier=1.0f;                                    // Event amplitude, separate from synaptic weight.
  uint8_t last_quanta=0;                                         // Last number of successful release sites.
};
struct PharmSettings {
  bool enabled=false;                                            // OFF: original firmware execution preserved.
  PharmSynMode mode=PharmSynMode::Current;                        // Original current-mode default.
  bool nmda_enabled=false;                                       // Requires conductance mode and AMPA receptor.
  bool presyn_enabled=false;                                     // GVIA/Calcium model opt-in.
  float dose[8]={0,0,0,0,0,0,0,0};                               // Validated nonnegative drug concentrations.
  float block[8]={0,0,0,0,0,0,0,0};                              // Cached Hill occupancy fractions.
  float e_ampa=0.0f;                                             // mV, AMPA reversal.
  float e_gaba=-80.0f;                                           // mV, GABA-A reversal (advanced).
  float e_nmda=0.0f;                                             // mV, NMDA reversal.
  float magnesium_mM=1.0f;                                      // Extracellular Mg, mM.
  float nmda_ratio=2.0f;                                        // Peak NMDA/AMPA conductance.
  float tau_rise_ms=4.0f;                                       // NMDA rise in MODEL milliseconds.
  float tau_decay_ms=100.0f;                                    // NMDA decay in MODEL milliseconds.
  float v_reference=-70.0f;                                     // Calibration voltage in model mV.
  uint32_t seed=20261028UL;                                     // Independent streams derive from this global seed.
  PharmIntrinsic intrinsic;                                     // Auxiliary neuron state.
  PharmSynapse syn[2];                                          // Independent synaptic/release states.
};
inline PharmSettings pharmacology;                              // Single shared state; no heap allocation.

/* Clamp a finite value to the unit interval; inputs are finite following command validation.
   Called when updating auxiliary state variables and probabilistic release. */
inline float pharmClip01(float x) { return x<0.0f?0.0f:(x>1.0f?1.0f:x); }

/* Hill occupancy C/(IC50+C), with exact zero occupancy at zero drug concentration.
   Called only when a serial command changes a dose, not once per numerical tick. */
inline float pharmHill(float c,float ic50) { return c==0.0f?0.0f:c/(ic50+c); }

/* Atomic dose validation and blockade precomputation. Drug 0..7 units are listed above.
   Reject NaN, infinities, negatives and pathologically large values WITHOUT state changes. */
inline bool pharmSetDose(uint8_t drug,float dose) {
  if(drug>=8 || !isfinite(dose) || dose<0.0f || dose>1000000.0f) return false;
  pharmacology.dose[drug]=dose;
  pharmacology.block[drug]=pharmHill(dose,pharm_ic50[drug]);
  return true;
}
