#pragma once

// // // // // // // // // // // // // // // // // // // // // // // //
/*                 Short-term synaptic plasticity                 */

// Event-driven, simplified Tsodyks-Markram model for classroom use.
// The baseline synaptic gain and exponential current decay are unchanged.
// Mode 0: Off; 1: Facilitation; 2: Depression; 3: Combined STP.
// The first spike after a mode reset has multiplier 1.0 in every mode.

#include <stdint.h>
#include <math.h>

struct STPState {
  uint8_t  mode = 0;                                      // Plasticity mode; zero keeps the original static synapse
  float    u = 0.0f;                                      // Transient synaptic utilisation at the most recent event
  float    x = 1.0f;                                      // Fraction of synaptic resources available at the most recent event
  uint32_t lastEventStep = 0;                             // Simulated integration-step index of the previous presynaptic event
  bool     hasEvent = false;                              // Distinguishes the first event from subsequent events
};

struct STPPreset {
  float U;                                                // Resting utilisation (dimensionless)
  float tauFac_ms;                                        // Facilitation recovery time constant, 0 disables facilitation
  float tauRec_ms;                                        // Resource recovery time constant, 0 disables depletion
};

inline STPPreset STP_preset(uint8_t mode) {
  if (mode == 1) return {0.15f, 500.0f, 0.0f};           // Facilitation: increasing utilisation, no resource depletion
  if (mode == 2) return {0.40f, 0.0f, 800.0f};           // Depression: resource depletion, fixed utilisation
  if (mode == 3) return {0.25f, 500.0f, 600.0f};         // Combined: facilitation and depression compete
  return {1.0f, 0.0f, 0.0f};                             // Off: original gain, no additional plasticity
}

inline void STP_setMode(STPState &state, uint8_t mode) {
  if (mode > 3) return;                                   // Reject undefined modes instead of changing synaptic behaviour
  state.mode          = mode;                             // Store the newly selected classroom preset
  state.u             = STP_preset(mode).U;               // Restore resting utilisation
  state.x             = 1.0f;                             // Replenish synaptic resources
  state.lastEventStep = 0;                                // Clear the previous event's time
  state.hasEvent      = false;                            // The next spike is the baseline response
}

inline float STP_spikeMultiplier(STPState &state, uint32_t step, float dt_ms) {
  if (state.mode == 0) return 1.0f;                       // Disabled mode is exactly equivalent to the original firmware

  const STPPreset preset = STP_preset(state.mode);         // Select the fixed educational parameter set
  if (state.hasEvent) {                                   // Recover transient state only between distinct spike events
    const uint32_t elapsedSteps = step - state.lastEventStep; // Unsigned subtraction also handles counter rollover
    const float elapsed_ms = (float)elapsedSteps * dt_ms;  // Use simulated model time, not the adjustable real-time loop delay
    if (preset.tauFac_ms > 0.0f) {                         // When facilitation is enabled:
      state.u = preset.U + (state.u - preset.U) * expf(-elapsed_ms / preset.tauFac_ms); // Utilisation relaxes to its resting level
    } else {
      state.u = preset.U;                                  // Without facilitation, the release fraction stays at baseline
    }
    if (preset.tauRec_ms > 0.0f) {                         // When resource depletion is enabled:
      state.x = 1.0f - (1.0f - state.x) * expf(-elapsed_ms / preset.tauRec_ms); // Available resources recover towards one
    } else {
      state.x = 1.0f;                                     // Without depression, available resources remain full
    }
  }

  const float multiplier = (state.u / preset.U) * state.x; // Normalise so the fully recovered first response equals the original gain
  if (preset.tauRec_ms > 0.0f) {                           // After this spike, release consumes a fraction of the resources
    state.x *= (1.0f - state.u);                          // The next spike has fewer resources unless enough time elapses
  }
  if (preset.tauFac_ms > 0.0f) {                           // After this spike, facilitation increases subsequent utilisation
    state.u += preset.U * (1.0f - state.u);               // Utilisation remains bounded by one
  }

  state.lastEventStep = step;                              // Remember when the event occurred in simulated time
  state.hasEvent      = true;                              // Later events will first recover the transient state
  return multiplier;                                       // This scales the next synaptic-current increment, not its decay
}

inline uint32_t stpStepCount = 0;                          // Shared integration-step clock for both independent synapses
