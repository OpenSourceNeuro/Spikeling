/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
/* ========================================================================================================
  Spikeling V3 - Optional synaptic currents, receptor conductances and NMDA/APV dynamics
  ---------------------------------------------------------------------------------------------------------
  Called AFTER original update_Synapse(), BEFORE original update_AllCurrent(). The existing
  Synapse.current, gain, edge detection and analogue Vm monitoring are never overwritten.
  The per-channel effective_current replaces its raw current only in the optional simulation path.
  (c) 2026 Open Source Neuro contributors. GPL-3.0-or-later.
  ====================================================================================================== */
#include "Pharmacology_release.h"

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

/* Reset both synaptic receptor activations, preserving the user-defined configuration and RNG.
   Called on explicit PH RESET, not on every exposure change (which would erase ongoing PSCs). */
inline void pharmResetSynapses() {
  pharmResetSynapse(0);
  pharmResetSynapse(1);
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
   Inputs: signed potentiometer gain, explicit receptor classification.
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
   Synapses are strictly current-based by default; no STP/LTP is implemented here. */
inline void pharmStepSynapse(uint8_t i, bool rising_edge, float gain, float decay, float vm, float dt_ms) {
  if (i > 1) return;
  PharmSynapseState &s = pharmacology.syn[i];
  const PharmReceptor receptor = s.receptor;
  const bool conductance_mode = pharmacology.mode == PharmSynapseMode::Conductance;
  const bool ampa = receptor == PharmReceptor::AMPA;
  const bool gabaa = receptor == PharmReceptor::GABAA;
  const bool valid_gain = receptor == PharmReceptor::Legacy ||
                           (ampa && gain >= 0.0f) || (gabaa && gain <= 0.0f);
  if (rising_edge) {                                               // Do not consume RNG on ordinary simulation ticks.
    const float gv = pharmGVRelease(s);                             // Applied to newly released transmitter only.
    const float release_multiplier = pharmReleaseEvent(s, gv);      // Deterministic or K/(N*p0), never multiplied by gv again.
    if (valid_gain) {
      s.released_current += gain * release_multiplier;              // Signed amplitude in current-based receptor model.
      const float conductance_event = pharmEventConductance(gain, receptor) * release_multiplier;
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
