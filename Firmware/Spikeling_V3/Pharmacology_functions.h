#pragma once
/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Spikeling V3 - single optional pharmacology model module.
   Concentration-response, intrinsic excitability, synaptic kinetics and
   probabilistic release are retained from the tested PR19 implementation.
   Serial handlers are centralised in Serial_functions.h; physical TTL/LED/DAC
   driving remains in Core_functions.h, as for the original hardware. */

/* ================= Original validated module: Pharmacology_settings.h ================= */
/* SPDX-License-Identifier: GPL-3.0-or-later */
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
  PharmReceptor receptor = PharmReceptor::Legacy;                       // Resolved receptor: Legacy until an effective nonzero gain is available.
  bool auto_receptor = true;                                           // Default: derive receptor identity from the effective signed synaptic gain.
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

/*                              Optional presynaptic event audit                                       */
/* A bounded observational record is filled only on received TTL rising edges while armed.
   It never consumes random numbers, changes release probability, or enters the VC2 stream.
   Each record is for one incoming AP, including K=0 (a failed vesicle release). */
struct PharmReleaseAuditEvent {
  uint32_t tick = 0;                                               // VC2 sequence in voltage clamp; shared STP model-step sequence in current clamp.
  float stp_multiplier = 1.0f;                                     // Normalised presynaptic STP weight before quantal sampling.
  float release_multiplier = 1.0f;                                 // Quantal amplitude multiplier K / (N*p0).
  float calcium_efficiency = 1.0f;                                 // GVIA-dependent release efficacy before Bernoulli sampling.
  uint8_t synapse = 0;                                             // Synapse number 1 or 2.
  uint8_t quanta = 0;                                              // Actual released quanta, including zero.
  uint8_t sites = 0;                                               // Site count when this AP arrived.
  uint8_t reserved = 0;                                            // Explicit padding for stable fixed-size records.
};
struct PharmReleaseAudit {
  static constexpr uint16_t capacity = 256;                       // Maximum stored incoming spikes per capture (both synapses total).
  bool armed = false;                                              // Default disabled: original firmware behaviour is unchanged.
  uint16_t count = 0;                                              // Number of complete stored event records.
  uint32_t overflow = 0;                                           // Incoming spikes not stored when the fixed array fills.
  uint32_t received[2] = {0,0};                                   // Observed TTL edges, independent of release success.
  uint32_t failures[2] = {0,0};                                   // TTL edges with K=0 in probabilistic mode.
  PharmReleaseAuditEvent events[capacity];                         // No heap, allocation, queue or per-tick transport.
};
inline PharmReleaseAudit pharmReleaseAudit;                         // One inactive audit shared by both synapses.

/* Reset and arm or disarm the optional audit; configuration and RNG are untouched. */
inline void pharmAuditSet(bool active) {
  pharmReleaseAudit.armed = false;                                 // Never collect half-reset records.
  if (active) {
    pharmReleaseAudit.count = 0;                                   // Discard records from previous experimental conditions.
    pharmReleaseAudit.overflow = 0;                                // Clear loss counter for this complete capture.
    for (unsigned i=0;i<2;++i) {
      pharmReleaseAudit.received[i] = 0;                            // Clear incoming edge count for each channel.
      pharmReleaseAudit.failures[i] = 0;                            // Clear failed-release count for each channel.
    }
  }
  pharmReleaseAudit.armed = active;                                // Enable audit only after reset is complete.
}

/* Log one *actual* TTL edge, after the existing pharmacology function samples K.
   'tick' is a VC2 sample sequence in VC or a model-step sequence in CC.
   The call is observational; it does not alter the sampled quanta or RNG. */
inline void pharmAuditEvent(uint8_t channel, uint32_t tick, float stp_multiplier, float calcium_efficiency, const PharmSynapseState &state) {
  if (!pharmReleaseAudit.armed || channel > 1) return;               // Disabled fast path costs only one check per incoming AP.
  ++pharmReleaseAudit.received[channel];                           // Count even zero-quanta presynaptic events.
  if (state.release_mode == PharmReleaseMode::Probabilistic && state.last_quanta == 0) ++pharmReleaseAudit.failures[channel];
  if (pharmReleaseAudit.count >= PharmReleaseAudit::capacity) {
    ++pharmReleaseAudit.overflow;                                  // Explicitly refuse to overwrite or silently lose events.
    return;
  }
  auto &event = pharmReleaseAudit.events[pharmReleaseAudit.count++]; // Reserve one fixed, preallocated event slot.
  event.tick = tick;                                               // Correlate this edge with VC2 samples using tick identity.
  event.stp_multiplier = stp_multiplier;                           // Preserve pre-release plasticity state per spike.
  event.release_multiplier = state.last_release_multiplier;        // Record scale applied to synaptic transmission.
  event.calcium_efficiency = calcium_efficiency;                    // Record GVIA attenuation at the time of this spike.
  event.synapse = uint8_t(channel+1);                              // Present serial channel as 1 or 2.
  event.quanta = state.last_quanta;                                 // Zero quanta is a meaningful observed outcome.
  event.sites = state.sites;                                       // Retain sampling site count to check statistics.
}

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


/* ================= Original validated module: Pharmacology_release.h ================= */
/* SPDX-License-Identifier: GPL-3.0-or-later */
/* ========================================================================================================
  Spikeling V3 - Presynaptic release and deterministic event-driven binomial sampler
  ---------------------------------------------------------------------------------------------------------
  This header depends on Pharmacology_settings.h. Called ONLY on digital rising edges.
  The presynaptic analogue membrane potential is deliberately not a calcium input.
  xorshift32 streams are reproducible, not cryptographic, and need not match NumPy PCG64 samples.
  (c) 2026 Open Source Neuro contributors. GPL-3.0-or-later.
  ====================================================================================================== */
/* Mix a seed with a per-synapse stream identifier so identical seeds cannot couple both synapses.
   Inputs: global seed and stream index; output: nonzero xorshift32 state.
   Called at boot, explicit reseeding, or a complete pharmacology default/reset. */
inline uint32_t pharmMixSeed(uint32_t seed, uint32_t stream) {
  uint32_t x = seed ^ (0x9E3779B9UL * (stream + 1UL));       // Distinct per-channel source words.
  x ^= x >> 16; x *= 0x7FEB352DUL;                         // Avalanche input bits to avoid correlated nearby seeds.
  x ^= x >> 15; x *= 0x846CA68BUL;                         // Second reversible integer mixing round.
  x ^= x >> 16;
  return x ? x : 0xA341316CUL;                            // xorshift32 would lock at zero indefinitely.
}

/* Restart both independent deterministic streams without changing any receptor state.
   Input: integer base seed; called only by initialisation or explicit PH SEED command.
   The next event on each synapse will consume the first draw from the newly seeded stream. */
inline void pharmSeed(uint32_t seed) {
  pharmacology.seed = seed;
  pharmacology.syn[0].rng_state = pharmMixSeed(seed, 0);
  pharmacology.syn[1].rng_state = pharmMixSeed(seed, 1);
}

/* Generate one pseudorandom word for one release site (one draw per site per event).
   Input/output: mutable per-synapse nonzero state; output uniform pseudorandom uint32.
   Called only for probabilistic events; no allocation and no state sharing between synapses. */
inline uint32_t pharmNextRandom(PharmSynapseState &state) {
  uint32_t x = state.rng_state;
  x ^= x << 13; x ^= x >> 17; x ^= x << 5;
  state.rng_state = x;
  return x;
}

/* Compute CaV2.2 release efficacy (1-f_N B_GVIA)^3, not an explicit calcium current.
   Input: synapse state, precomputed toxin blockade; output: release multiplier [0,1].
   Called on incoming events only so changing the toxin does NOT erase existing EPSCs/IPSCs. */
inline float pharmGVRelease(const PharmSynapseState &state) {
  const float available = 1.0f - state.ntype_fraction * pharmGVBlock();
  return available * available * available;                   // Fixed accepted illustrative cooperativity eta = 3.
}

/* Sample a binomial release event and return its NORMALISED response scale.
   Inputs: synapse channel state and CaV2.2 efficiency; output: K/(N*p0), where K~Bin(N,p0*R).
   One incoming action potential invokes this once. Each of N sites consumes exactly one draw,
   including p=0 or 1, preserving reproducible counterfactuals across drug concentrations.
   Mean multiplier is R (not R squared). Never apply toxin scaling a second time. */
inline float pharmReleaseEvent(PharmSynapseState &state, float calcium_efficiency) {
  if (state.release_mode == PharmReleaseMode::Deterministic) {
    state.last_quanta = 0;                                  // No stochastic vesicle count in deterministic mode.
    state.last_release_multiplier = calcium_efficiency;
    return calcium_efficiency;                              // Toxin multiplies the new event only.
  }
  const float p_effective = pharmClip01(state.p0 * calcium_efficiency);
  const double threshold = double(p_effective) * 4294967296.0; // Exclusive uniform threshold on [0,2^32).
  uint8_t released = 0;
  for (uint8_t site = 0; site < state.sites; ++site) {  // Sites valid 1..128; loop only on incoming APs.
    if (double(pharmNextRandom(state)) < threshold) ++released;
  }
  state.last_quanta = released;
  state.last_release_multiplier = float(released) / (float(state.sites) * state.p0);
  return state.last_release_multiplier;                      // Baseline p0 stays fixed; upstream STP scales amplitude, not Bernoulli probabilities.
}


/* ================= Original validated module: Pharmacology_synapses.h ================= */
/* SPDX-License-Identifier: GPL-3.0-or-later */
/* ========================================================================================================
  Spikeling V3 - Optional synaptic currents, receptor conductances and NMDA/APV dynamics
  ---------------------------------------------------------------------------------------------------------
  Called AFTER original update_Synapse(), BEFORE original update_AllCurrent(). The existing
  Synapse.current, gain, edge detection and analogue Vm monitoring are never overwritten.
  The per-channel effective_current replaces its raw current only in the optional simulation path.
  (c) 2026 Open Source Neuro contributors. GPL-3.0-or-later.
  ====================================================================================================== */
/* Reset one receptor's numerical states without changing the physical input, gain or RNG.
   Input: index 0/1; called on receptor or global synaptic mode switching.
   A mode transition deliberately clears receptor activation to avoid reinterpreting a stale state. */
inline void pharmResetSynapse(uint8_t i) {
  if (i > 1) return;
  PharmSynapseState &s = pharmacology.syn[i];
  s.released_current = 0.0f; s.conductance = 0.0f;
  s.nmda_rise = 0.0f; s.nmda_decay = 0.0f;
  s.effective_current = 0.0f; s.last_release_multiplier = 1.0f; s.last_quanta = 0;
}

/* Convert one finite, nonzero effective synaptic gain to its automatic receptor class.
   Input: signed gain AFTER physical potentiometer or GUI override selection.
   Output: AMPA for excitation, GABA-A for inhibition, Legacy for zero or invalid gain.
   The AMPA identity also carries an NMDA component when PH M 1 and PH N 1 are active. */
inline PharmReceptor pharmReceptorFromGain(float gain) {
  if (!isfinite(gain) || gain == 0.0f) return PharmReceptor::Legacy;  // A centred or invalid gain creates no new receptor identity.
  if (gain > 0.0f) return PharmReceptor::AMPA;                     // Positive effective gain denotes an excitatory synapse.
  return PharmReceptor::GABAA;                                     // Negative effective gain denotes an inhibitory synapse.
}

/* Synchronise one automatically managed receptor with the effective gain.
   Input: zero-based synapse index and its effective physical/GUI gain.
   Output: true only when receptor identity changes; existing receptor tails are then cleared.
   Zero gain retains the previous identity while producing no NEW synaptic activation.
   Manual PH R 0/1/2 overrides bypass this function; PH R synapse 3 re-enables it.
   This function never modifies STP, RNG, drugs, the other synapse or the membrane state. */
inline bool pharmSyncReceptorFromGain(uint8_t i, float gain) {
  if (i > 1 || !pharmacology.syn[i].auto_receptor) return false;   // Respect manual overrides and reject invalid channel indices.
  const PharmReceptor candidate = pharmReceptorFromGain(gain);    // Inspect the already-selected effective synaptic gain.
  if (candidate == PharmReceptor::Legacy) return false;          // Retain identity at the centre to avoid repeated tail resets.
  PharmSynapseState &s = pharmacology.syn[i];                     // Reference only the targeted pharmacological synapse.
  if (s.receptor == candidate) return false;                      // Do not touch states if the polarity has not changed.
  s.receptor = candidate;                                        // Commit the polarity-defined receptor identity.
  pharmResetSynapse(i);                                          // Clear incompatible legacy/AMPA/GABA/NMDA tails on a real transition.
  return true;                                                   // Report the identity transition for native tests and diagnostics.
}

/* Reset both synaptic receptor activations, preserving the user-defined configuration and RNG.
   Called on explicit PH RESET, not on every exposure change (which would erase ongoing PSCs). */
inline void pharmResetSynapses() {
  pharmResetSynapse(0);
  pharmResetSynapse(1);
}

/* Return one finite signed gain rounded to centi-model-units and clamped to int16 range.
   Input: physical-potentiometer or GUI-resolved effective gain.
   Output: signed integer for the stable PHS v1 binary format; NaN becomes zero. */
inline int16_t pharmGainStatusQ(float gain) {
  if (!isfinite(gain)) return 0;                                // Guard against an invalid diagnostic source without changing neuron state.
  const float scaled = gain * 100.0f;                          // Preserve hundredth-unit resolution in the short diagnostic.
  if (scaled > 32767.0f) return 32767;                        // Saturate the positive wire range.
  if (scaled < -32768.0f) return -32768;                      // Saturate the negative wire range.
  return static_cast<int16_t>(lroundf(scaled));              // Match the normal sample stream's round-to-nearest convention.
}

/* Construct an 11-byte read-only receptor status response; no ASCII is mixed into binary telemetry.
   Format: AA 56 | version | receptor1 | receptor2 | flags | gain1_le_i16 | gain2_le_i16 | XOR.
   Flags: bit0 PH enabled, bit1 conductance, bit2 NMDA, bit3 CaV, bits4/5 auto receptor,
          bit6 Syn1 pot-owned, bit7 Syn2 pot-owned; gains have model units times 100.
   Input: complete fixed-size output buffer, two effective gains and physical ownership flags; returns no value and never writes to Serial. */
inline void pharmEncodeReceptorStatus(uint8_t (&frame)[11], float gain1, float gain2, bool syn1_pot, bool syn2_pot) {
  frame[0] = 0xAA;                                          // Unique first framing byte shared with regular binary samples.
  frame[1] = 0x56;                                          // Distinct second framing byte (regular samples use 0x55).
  frame[2] = 1;                                             // Fixed receptor-status protocol version.
  frame[3] = static_cast<uint8_t>(pharmacology.syn[0].receptor); // Synapse 1 resolved receptor identity.
  frame[4] = static_cast<uint8_t>(pharmacology.syn[1].receptor); // Synapse 2 resolved receptor identity.
  frame[5] = (pharmacology.enabled ? 0x01 : 0x00)           // Indicate whether optional pharmacology is active.
           | (pharmacology.mode == PharmSynapseMode::Conductance ? 0x02 : 0x00) // Modelled conductance-mode flag.
           | (pharmacology.nmda_enabled ? 0x04 : 0x00)      // Global NMDA activation flag.
           | (pharmacology.presyn_enabled ? 0x08 : 0x00)    // CaV2.2 release-path enable flag.
           | (pharmacology.syn[0].auto_receptor ? 0x10 : 0x00) // Synapse 1 automatic receptor control.
           | (pharmacology.syn[1].auto_receptor ? 0x20 : 0x00) // Synapse 2 automatic receptor control.
           | (syn1_pot ? 0x40 : 0x00)               // Synapse 1 effective gain follows its physical potentiometer.
           | (syn2_pot ? 0x80 : 0x00);              // Synapse 2 effective gain follows its physical potentiometer.
  const uint16_t q1 = static_cast<uint16_t>(pharmGainStatusQ(gain1)); // Preserve signed wire bits without undefined shifts.
  const uint16_t q2 = static_cast<uint16_t>(pharmGainStatusQ(gain2)); // Preserve signed wire bits for the second channel.
  frame[6] = static_cast<uint8_t>(q1 & 0xFFU);             // Synapse 1 little-endian gain low byte.
  frame[7] = static_cast<uint8_t>(q1 >> 8);                // Synapse 1 little-endian gain high byte.
  frame[8] = static_cast<uint8_t>(q2 & 0xFFU);             // Synapse 2 little-endian gain low byte.
  frame[9] = static_cast<uint8_t>(q2 >> 8);                // Synapse 2 little-endian gain high byte.
  uint8_t checksum = 0;                                   // Initialise eight-byte XOR checksum.
  for (uint8_t i = 2; i < 10; ++i) checksum ^= frame[i];   // Cover version, receptor IDs, flags and both signed gains.
  frame[10] = checksum;                                   // Terminate the fixed-length diagnostic packet.
}

/* Seed a newly enabled current-mode simulation with the existing legacy synaptic tail.
   Inputs: signed legacy current states BEFORE the next event; called on enabling pharmacology.
   Used only in current mode to prevent a discontinuity in already-active current-based inputs.
   Conductance mode instead starts from zero because raw current cannot be converted unambiguously. */
inline void pharmAdoptLegacyCurrents(float syn1_current, float syn2_current) {
  pharmResetSynapses();
  if (pharmacology.mode == PharmSynapseMode::Current) {
    pharmacology.syn[0].released_current = syn1_current;
    pharmacology.syn[1].released_current = syn2_current;
  }
}

/* Cached coefficients: recompute only when numerical dt or NMDA parameters change.
   Unlike the membrane-voltage-dependent Mg factor, these terms are constants per configuration. */
inline float pharmNMDA_R = 0.0f;
inline float pharmNMDA_D = 0.0f;
inline float pharmNMDA_Norm = 1.0f;
inline float pharmNMDA_Dt = -1.0f;

/* Return a finite nonnegative conductance increment calibrated at -70 model mV.
   Inputs: signed event gain after one STP update, explicit receptor classification.
   AMPA requires a positive gain; GABA-A requires a negative gain. Opposite-sign hardware
   inputs produce zero NEW receptor activation, not an invented negative conductance.
   Reference E_GABA=-80 remains FIXED when a user changes actual E_GABA for shunting studies. */
inline float pharmEventConductance(float gain, PharmReceptor receptor) {
  if (receptor == PharmReceptor::AMPA) {
    return gain > 0.0f ? gain / (pharmacology.e_ampa - pharmacology.e_reference) : 0.0f;
  }
  if (receptor == PharmReceptor::GABAA) {
    return gain < 0.0f ? gain / (-80.0f - pharmacology.e_reference) : 0.0f;
  }
  return 0.0f;
}

/* Compute normalisation so a 4/100 ms NMDA biexponential has unit peak.
   Input: strictly positive rise < decay in model ms; output: normalisation factor.
   Called when NMDA is active; accepted reference peak NMDA/AMPA conductance ratio is 2. */
inline float pharmNMDANormalisation() {
  const float tr = pharmacology.nmda_rise_ms;
  const float td = pharmacology.nmda_decay_ms;
  const float tp = tr*td/(td-tr) * logf(td/tr);
  return 1.0f / (expf(-tp/td) - expf(-tp/tr));
}

/* Update cached NMDA coefficients once per changed dt or explicit parameter reset.
   Input: model dt; called each step but normally returns immediately. */
inline void pharmPrepareNMDA(float dt_ms) {
  if (dt_ms == pharmNMDA_Dt) return;
  pharmNMDA_Dt = dt_ms;
  pharmNMDA_R = expf(-dt_ms / pharmacology.nmda_rise_ms);
  pharmNMDA_D = expf(-dt_ms / pharmacology.nmda_decay_ms);
  pharmNMDA_Norm = pharmNMDANormalisation();
}

/* Mg-dependent NMDA unblocking: 1/[1+([Mg]/3.57)*exp(-0.062*v)].
   Inputs: postsynaptic model Vm in mV and configured extracellular Mg in mM.
   Called once per simulation step when NMDA is enabled. It is not an ion-flux model. */
inline float pharmNMDAUnblocked(float v) {
  return 1.0f / (1.0f + (pharmacology.extracellular_mg_mM / 3.57f) * expf(-0.062f*v));
}

/* Advance ONE synapse with the original digital edge/gain/decay and optional receptor states.
   Inputs: channel index 0/1, rising-edge flag read by hardware code, signed gain from knob/GUI,
   original per-update decay factor, current postsynaptic Vm and model dt in ms.
   Output: syn[i].effective_current, subsequently replacing raw syn.current in update_AllCurrent.
   A new presynaptic AP samples release ONCE, then receptor states decay in the Python order.
   NBQX, gabazine and APV apply to current outputs, not stored activations. GVIA applies at events.
   STP is advanced ONCE upstream by update_Synapse() and arrives here as event_gain.
   Its normalised multiplier scales the signed event amplitude; it does not modify
   the release probability p0, vesicle count K, receptor blockers, or stored tails.
   For classroom use this is phenomenological amplitude STP: resource depletion
   advances on each presynaptic AP even if probabilistic release fails. */
inline void pharmStepSynapse(uint8_t i, bool rising_edge, float event_gain, float decay, float vm, float dt_ms, uint32_t audit_tick=0, float audit_stp_multiplier=1.0f) {
  if (i > 1) return;
  PharmSynapseState &s = pharmacology.syn[i];
  const PharmReceptor receptor = s.receptor;
  const bool conductance_mode = pharmacology.mode == PharmSynapseMode::Conductance;
  const bool ampa = receptor == PharmReceptor::AMPA;
  const bool gabaa = receptor == PharmReceptor::GABAA;
  const bool valid_gain = receptor == PharmReceptor::Legacy ||
                           (ampa && event_gain >= 0.0f) || (gabaa && event_gain <= 0.0f);
  if (rising_edge) {                                               // Do not consume RNG on ordinary simulation ticks.
    const float gv = pharmGVRelease(s);                             // Applied to newly released transmitter only.
    const float release_multiplier = pharmReleaseEvent(s, gv);      // Deterministic or K/(N*p0), never multiplied by gv again.
    pharmAuditEvent(i, audit_tick, audit_stp_multiplier, gv, s);       // Log the incoming AP even when no vesicles were released.
    if (valid_gain) {
      s.released_current += event_gain * release_multiplier;        // One STP multiplier times one release multiplier; never apply either twice.
      const float conductance_event = pharmEventConductance(event_gain, receptor) * release_multiplier;
      s.conductance += conductance_event;                           // Positive receptor conductance, in model units.
      if (ampa && conductance_mode && pharmacology.nmda_enabled) {
        const float nmda_event = conductance_event * pharmacology.nmda_peak_ratio;
        s.nmda_rise += nmda_event;                                  // Same release event activates both AMPA and NMDA.
        s.nmda_decay += nmda_event;
      }
    }
  }
  s.released_current *= decay;                                      // Exactly the firmware's per-update current decay.
  s.conductance *= decay;                                          // Same decay for fast AMPA/GABA conductance states.
  float nmda_current = 0.0f;
  pharmPrepareNMDA(dt_ms);
  if (conductance_mode && pharmacology.nmda_enabled && ampa) {
    s.nmda_rise *= pharmNMDA_R;         // Accepted NMDA rise time, model ms.
    s.nmda_decay *= pharmNMDA_D;       // Accepted NMDA decay time, model ms.
    const float g_nmda = pharmNMDA_Norm * fmaxf(0.0f,s.nmda_decay-s.nmda_rise);
    nmda_current = (1.0f-pharmacology.block[6]) * g_nmda * pharmNMDAUnblocked(vm) * (pharmacology.e_nmda-vm);
  } else {
    // Keep any old NMDA state decaying when mode is current-based; it is never injected there.
    s.nmda_rise *= pharmNMDA_R;
    s.nmda_decay *= pharmNMDA_D;
  }
  float fast_current = 0.0f;
  if (conductance_mode && ampa) {
    fast_current = (1.0f-pharmacology.block[4])*s.conductance*(pharmacology.e_ampa-vm);
  } else if (conductance_mode && gabaa) {
    fast_current = (1.0f-pharmacology.block[5])*s.conductance*(pharmacology.e_gaba-vm);
  } else if (conductance_mode) {
    fast_current = 0.0f;                                         // Legacy receptor is undefined in conductance mode.
  } else if (ampa) {
    fast_current = (1.0f-pharmacology.block[4])*s.released_current;
  } else if (gabaa) {
    fast_current = (1.0f-pharmacology.block[5])*s.released_current;
  } else {
    fast_current = s.released_current;                            // Unclassified original current has no receptor blockers.
  }
  s.effective_current = fast_current + nmda_current;             // Single source consumed by neuron, no double-counting.
}


/* ================= Original validated module: Pharmacology_intrinsic.h ================= */
/* SPDX-License-Identifier: GPL-3.0-or-later */
/* ========================================================================================================
  Spikeling V3 - Optional phenomenological intrinsic pharmacology (frozen Python integrated v2)
  ---------------------------------------------------------------------------------------------------------
  Depends on Pharmacology_settings.h. Euler state order follows the frozen Python numerical reference.
  This is a demonstration of excitability and drug interactions, not explicit Na/K membrane currents.
  (c) 2026 Open Source Neuro contributors. GPL-3.0-or-later.
  ====================================================================================================== */
/* Numerically stable logistic sigmoid 1/(1+exp(-x)); avoids exp overflow at large |x|.
   Input: finite dimensionless x. Output: activation in (0,1). Called for voltage-dependent states. */
inline float pharmSigmoid(float x) {
  if (x >= 0.0f) return 1.0f / (1.0f + expf(-x));
  const float e = expf(x); return e / (1.0f + e);
}

/* Smoothly blend passive and active fields for TTX reserve R_T in [0.10,0.21].
   Input: reserve; output 0..1. Called during intrinsic updates when TTX is present. */
inline float pharmSmoothTTX(float reserve) {
  const float q = pharmClip01((reserve - 0.10f) / 0.11f);
  return q * q * (3.0f - 2.0f * q);
}

/* Stable soft minimum: (r1^-3+r2^-3-1)^(-1/3) for two reserves in [0,1].
   Input: TTX reserve and potassium-coupled reserve; output combined Na reserve [0,1].
   Algebra removes divisions by vanishing constituent reserves, preserving the accepted equation. */
inline float pharmSoftmin(float r1, float r2) {
  if (r1 <= 0.0f || r2 <= 0.0f) return 0.0f;
  const float product = r1 * r2;
  const float denominator = r1*r1*r1 + r2*r2*r2 - product*product*product;
  return product / cbrtf(denominator);
}

/* Initialise Na/A availability and SK state at the model's initial voltage.
   Input: resting Vm in model mV. Called on boot, neuron preset change, and explicit state reset.
   Concentration settings and synaptic states are NOT modified here. */
inline void pharmResetIntrinsic(float v_rest) {
  PharmIntrinsicState &s = pharmacology.intrinsic;
  s = PharmIntrinsicState();
  s.h_na = pharmSigmoid(-(v_rest + 55.0f) / 6.0f);
  s.h_a = pharmSigmoid(-(v_rest + 78.0f) / 6.0f);
}

/* Advance the optional intrinsic model by ONE model tick; report a verified spike separately.
   Inputs: v and u updated by reference; a,b,c,d original preset; dt in MODEL milliseconds;
   total input current in Izhikevich units; voltage_clamp disables all verified AP reset.
   Operation order matches frozen Python: decay SK, update h_A if drug active, update h_Na,
   calculate fields and Euler v, update Euler u using UPDATED v, detect/verify AP, apply reset.
   The original a,b,c,d remain untouched. On zero intrinsic blockade, use the original
   Izhikevich voltage expression (same operation order), even if receptor drugs are enabled.
   The VC PI controller and numeric voltage bounds remain in the original sketch. */
inline void pharmStepIntrinsic(float &v, float &u, float a, float b, float c, float d,
                              float dt, float total_current, bool voltage_clamp,
                              float v_peak = 30.0f) {
  PharmIntrinsicState &s = pharmacology.intrinsic;
  s.verified_event = false;                                        // Reset one-tick event before each update.
  const float bt = pharmacology.block[0];                          // TTX blockade, IC50 9.2 nM.
  const float btea = pharmacology.block[1];                        // TEA blockade, IC50 0.5 mM.
  const float bap = pharmacology.block[2];                         // Apamin blockade, IC50 2.3 nM.
  const float b4 = pharmacology.block[3];                          // 4-AP blockade, IC50 0.88 mM.
  const float v_before = v;                                       // Needed for one-time crossing detection.
  s.s_sk *= expf(-dt / 120.0f);                                   // SK-like spike activity decays over 120 model ms.
  const float correction_ap = bap * 0.25f * s.s_sk * (v + 90.0f); // Removal of implicit outward SK restraint (not inward channel).
  float correction_4ap = 0.0f;
  if (b4 > 0.0f) {
    const float tau_a = v >= -78.0f ? 35.0f : 80.0f;             // A availability inactivation/recovery in model ms.
    const float h_a_inf = pharmSigmoid(-(v + 78.0f) / 6.0f);
    s.h_a = pharmClip01(s.h_a + (h_a_inf - s.h_a) * (-expm1f(-dt / tau_a)));
    correction_4ap = b4 * 2.5f * pharmSigmoid((v + 55.0f) / 7.0f) * s.h_a * (v + 90.0f);
  }
  const float tau_na = v <= -62.0f ? 2.0f : 9.0f;                // Na recovery in model ms.
  const float h_na_inf = pharmSigmoid(-(v + 55.0f) / 6.0f);
  s.h_na = pharmClip01(s.h_na + (h_na_inf - s.h_na) * (-expm1f(-dt / tau_na)));
  const float rho_k = pharmClip01(1.25f*btea + 0.25f*bap + 0.17f*b4);
  const float q_k = pharmClip01(1.10f*rho_k*(1.0f-s.h_na));
  const float q_t = pharmClip01(0.15f*bt*(1.0f-s.h_na));
  const float r_t = pharmClip01((1.0f - bt - 0.14f) / 0.86f);
  const float r_na = pharmSoftmin(r_t * (1.0f-q_t), 1.0f-q_k);
  float weight = bt <= 0.0f ? 1.0f : pharmSmoothTTX(r_t);
  if (s.failed_passive) weight = 0.0f;                         // Aborted TTX upstroke follows passive turnaround.
  const float depolarised = fmaxf(0.0f,v+70.0f);
  const float izhi = 0.04f*v*v + 5.0f*v + 140.0f-u;
  const float active = izhi - 0.04f*(1.0f-r_na)*depolarised*depolarised;
  const float upper = fmaxf(0.0f,v+45.0f);
  const float passive = -0.8f*(v+70.0f) - 0.12f*upper*upper;
  const float dv_dt = weight*active + (1.0f-weight)*passive + total_current + correction_ap + correction_4ap;
  if (bt == 0.0f && btea == 0.0f && bap == 0.0f && b4 == 0.0f && !s.failed_passive) {
    v = v + dt*(0.04f*v*v + 5.0f*v + 140.0f-u + total_current); // Original drug-free Euler path.
  } else {
    v = v + dt*dv_dt;                                         // Pharmacology-corrected active/passive field.
  }
  u = u + dt*(a*(b*v-u));                                    // ORIGINAL update order: recovery uses new voltage.
  if (voltage_clamp) {                                       // Controller remains in original code; never generate VC events.
    s.committed = false; s.armed = true; s.failed_passive = false;
    return;
  }
  bool verified = false;
  if (bt <= 0.0f) {
    verified = v >= v_peak;                                  // Frozen Python's drug-free peak check.
  } else {
    if (s.armed && !s.committed && v_before < -30.0f && v >= -30.0f) {
      if (r_t > 0.12f) { s.committed = true; s.armed = false; } // Accepted onset threshold; NO timeout/onset gate.
      else { ++s.rejected_attempts; s.armed = false; s.failed_passive = true; }
    }
    if (s.committed) {
      if (v >= v_peak) verified = true;
      else if (dv_dt <= 0.0f || v < -35.0f) {
        s.committed = false; ++s.rejected_attempts; s.failed_passive = true;
      }
    }
    if (!s.committed && v < -40.0f) {
      s.failed_passive = false; s.armed = true;              // Re-arm only after sufficiently returning below upstroke threshold.
    }
  }
  if (verified) {
    s.verified_event = true;                                 // One verified spike controls output TTL/LED/buzzer/DAC.
    v = c;                                                   // Keep original Izhikevich post-spike reset.
    u = u + d;                                               // Keep original recovery increment d (NOT changed by TEA).
    s.h_na *= expf(-(0.30f+0.85f*btea+0.12f*bap));         // Accepted post-AP Na availability depletion.
    s.s_sk += 0.4f*(1.0f-s.s_sk);                           // Spike-dependent SK-like activity increment.
    s.committed = false; s.armed = true; s.failed_passive = false;
  }
}

