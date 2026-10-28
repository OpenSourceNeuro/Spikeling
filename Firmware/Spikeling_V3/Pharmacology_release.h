/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
/* ========================================================================================================
   Spikeling V3 - Presynaptic CaV2.2/GVIA and optional probabilistic neurotransmitter release
   --------------------------------------------------------------------------------------------------------
   One binomial sample per incoming DIGITAL presynaptic AP; analogue Vm is monitoring-only.
   xorshift32 is a reproducible, non-cryptographic generator (not NumPy PCG64).
   No STP, LTP/LTD, vesicle depletion or explicit Ca currents are represented.
   (c) 2026 Open Source Neuro contributors. GPL-3.0-or-later.
   ====================================================================================================== */
#include "Pharmacology_settings.h"

/* Mix a global seed and stream index into a nonzero independent RNG state.
   Inputs: unsigned base seed and index 0/1; output: valid xorshift32 state.
   Called on boot or an explicit PH SEED update. */
inline uint32_t pharmMixSeed(uint32_t seed,uint32_t channel) {
  uint32_t x=seed^(0x9E3779B9UL*(channel+1UL));       // Split neighbouring channel seeds.
  x^=x>>16; x*=0x7FEB352DUL;                       // Avalanche initial seed bits.
  x^=x>>15; x*=0x846CA68BUL; x^=x>>16;
  return x?x:0xA341316CUL;                          // Zero state would permanently stop xorshift32.
}
/* Restart BOTH per-channel RNG streams without clearing receptor activation.
   Input: unsigned seed. Next event in each stream begins a new reproducible sequence. */
inline void pharmSeed(uint32_t seed) {
  pharmacology.seed=seed;
  for(uint8_t i=0;i<2;++i) pharmacology.syn[i].rng=pharmMixSeed(seed,i);
}
/* Generate one pseudorandom 32-bit value; N draws are made for each incoming AP.
   Input/output: mutable channel RNG state; called only on stochastic release events. */
inline uint32_t pharmRandom(PharmSynapse &s) {
  uint32_t x=s.rng;
  x^=x<<13; x^=x>>17; x^=x<<5;
  return s.rng=x;
}
/* Compute (1-f_N*B_GVIA)^3, illustrating CaV2.2-dependent transmitter release efficiency.
   Input: per-synapse N-type fraction; output: event-specific factor in [0,1].
   Toxin affects NEW presynaptic events, never previously activated receptor states. */
inline float pharmGVFactor(const PharmSynapse &s) {
  if(!pharmacology.presyn_enabled) return 1.0f;
  const float a=1.0f-s.ntype_fraction*pharmacology.block[7];
  return a*a*a;                                      // Accepted illustrative cooperativity exponent: 3.
}
/* Sample Binomial(N, p0*R_GVIA) and normalise event amplitude as K/(N*p0).
   Inputs: channel, event-specific calcium factor; output: signed-gain multiplier.
   Every site consumes one draw, even for p=0 or 1; fixed seeds permit reproducibility.
   E[M]=R_GVIA. Do NOT multiply by GVIA again after this result.
   Future STP may alter effective p but must NOT redefine baseline normalisation N*p0. */
inline float pharmReleaseEvent(PharmSynapse &s,float gvia) {
  if(s.release_mode==PharmReleaseMode::Deterministic) {
    s.last_quanta=0;
    return s.last_multiplier=gvia;                   // Deterministic limit applies event efficacy once.
  }
  const float p=pharmClip01(s.p0*gvia);              // Binomial probability after GVIA, [0,1].
  const double threshold=double(p)*4294967296.0;   // Exclusive uint32 acceptance threshold.
  uint8_t released=0;
  for(uint8_t j=0;j<s.sites;++j)
    if(double(pharmRandom(s))<threshold) ++released;
  s.last_quanta=released;                           // Failed event: zero quantal increment, old PSC decays.
  return s.last_multiplier=float(released)/(float(s.sites)*s.p0);
}
