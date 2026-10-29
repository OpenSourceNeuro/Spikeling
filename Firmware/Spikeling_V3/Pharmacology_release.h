/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
/* ========================================================================================================
  Spikeling V3 - Presynaptic release and deterministic event-driven binomial sampler
  ---------------------------------------------------------------------------------------------------------
  This header depends on Pharmacology_settings.h. Called ONLY on digital rising edges.
  The presynaptic analogue membrane potential is deliberately not a calcium input.
  xorshift32 streams are reproducible, not cryptographic, and need not match NumPy PCG64 samples.
  (c) 2026 Open Source Neuro contributors. GPL-3.0-or-later.
  ====================================================================================================== */
#include "Pharmacology_settings.h"

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
  return state.last_release_multiplier;                      // Baseline p0 remains fixed for future STP/LTP support.
}
