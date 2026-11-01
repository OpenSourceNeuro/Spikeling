// Host-compiled regression checks for the firmware-only STP header.
// Build: g++ -std=c++17 -Wall -Wextra -pedantic -o /tmp/stp_smoke stp_model_smoke.cpp

#include "../STP_functions.h"
#include <cassert>
#include <cmath>

static float secondResponse(uint8_t mode, uint32_t interval_steps) {
  STPState state;                                              // Start with an independent untrained synapse
  STP_setMode(state, mode);                                    // Select a mode and reset transient history
  assert(std::fabs(STP_spikeMultiplier(state, 0, 0.1f) - 1.0f) < 1e-6f); // First event has baseline strength
  return STP_spikeMultiplier(state, interval_steps, 0.1f);     // Return the second event's normalized amplitude
}

int main() {
  assert(secondResponse(0, 1000) == 1.0f);                    // Off exactly preserves the original static synapse
  assert(secondResponse(1, 1000) > 1.0f);                     // A 100 ms paired pulse shows facilitation
  assert(secondResponse(2, 1000) < 1.0f);                     // A 100 ms paired pulse shows depression
  assert(secondResponse(3, 500) > 1.0f);                      // Combined mode initially facilitates at 50 ms
  assert(std::fabs(secondResponse(1, 200000) - 1.0f) < 1e-4f); // Facilitation recovers after a long interval
  assert(std::fabs(secondResponse(2, 300000) - 1.0f) < 1e-4f); // Depression recovers after a long interval

  STPState syn1;                                              // Synapse 1 is independent of Synapse 2
  STPState syn2;                                              // Create a separate state for Synapse 2
  STP_setMode(syn1, 2);                                       // Synapse 1: depression
  STP_setMode(syn2, 1);                                       // Synapse 2: facilitation
  STP_spikeMultiplier(syn1, 0, 0.1f);                         // Deliver a baseline spike to Synapse 1
  STP_spikeMultiplier(syn1, 1000, 0.1f);                      // Deplete Synapse 1 resources
  assert(std::fabs(STP_spikeMultiplier(syn2, 1000, 0.1f) - 1.0f) < 1e-6f); // Synapse 2 stays at baseline
  STP_setMode(syn1, 2);                                       // Re-selecting the mode is an explicit transient reset
  assert(std::fabs(STP_spikeMultiplier(syn1, 1001, 0.1f) - 1.0f) < 1e-6f); // Response is restored
  return 0;
}
