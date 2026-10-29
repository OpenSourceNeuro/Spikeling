/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
/* ========================================================================================================
  Spikeling V3 - Optional phenomenological intrinsic pharmacology (frozen Python integrated v2)
  ---------------------------------------------------------------------------------------------------------
  Depends on Pharmacology_settings.h. Euler state order follows the frozen Python numerical reference.
  This is a demonstration of excitability and drug interactions, not explicit Na/K membrane currents.
  (c) 2026 Open Source Neuro contributors. GPL-3.0-or-later.
  ====================================================================================================== */
#include "Pharmacology_settings.h"

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
