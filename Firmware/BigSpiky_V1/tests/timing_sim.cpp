/* SPDX-License-Identifier: GPL-3.0-or-later */
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>

#include "../BigSpiky_Config.h"
#include "../BigSpiky_Logic.h"
#include "../BigSpiky_Protocol.h"

using namespace bigspiky;

int main() {
  constexpr std::size_t iterations = 200000U;
  float currents[SYNAPSE_COUNT]{};
  float v = -70.0f;
  float u = -14.0f;
  uint64_t maximumNs = 0U;
  const auto allStarted = std::chrono::steady_clock::now();
  for (std::size_t step = 0U; step < iterations; ++step) {
    const auto started = std::chrono::steady_clock::now();
    float sum = 0.0f;
    const uint16_t events = (step % 97U == 0U) ? 3U : 0U;
    for (std::size_t index = 0U; index < SYNAPSE_COUNT; ++index) {
      const float gain = (index & 1U) ? -3.0f : 4.0f;
      currents[index] = applySynapticEvents(currents[index], gain, events,
                                            0.995f - 0.0001f * static_cast<float>(index),
                                            SYNAPSE_CURRENT_MIN, SYNAPSE_CURRENT_MAX);
      sum += currents[index];
    }
    const float total = clampValue(sum * SYNAPTIC_GLOBAL_SCALE, TOTAL_CURRENT_MIN, TOTAL_CURRENT_MAX);
    v += MODEL_DT_MS * (0.04f * v * v + 5.0f * v + 140.0f - u + total);
    u += MODEL_DT_MS * (0.02f * (0.2f * v - u));
    if (v >= VM_PEAK) { v = -65.0f; u += 6.0f; }
    v = clampValue(v, VM_MIN, VM_PEAK);
    ExtendedPacketV2 packet{};
    packet.vm_q = static_cast<int16_t>(v * 100.0f);
    const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&packet);
    packet.crc16 = crc16CcittFalse(bytes + kExtendedCrcOffset, kExtendedCrcLength);
    const auto elapsed = std::chrono::steady_clock::now() - started;
    maximumNs = std::max<uint64_t>(maximumNs,
        static_cast<uint64_t>(std::chrono::duration_cast<std::chrono::nanoseconds>(elapsed).count()));
  }
  const auto totalElapsed = std::chrono::steady_clock::now() - allStarted;
  const double totalUs = static_cast<double>(
      std::chrono::duration_cast<std::chrono::nanoseconds>(totalElapsed).count()) / 1000.0;
  const double averageUs = totalUs / static_cast<double>(iterations);
  std::cout << "HOST_TIMING iterations=" << iterations
            << " average_us=" << averageUs
            << " maximum_us=" << static_cast<double>(maximumNs) / 1000.0
            << " deadline_us=" << MODEL_STEP_US << '\n';
  if (!std::isfinite(v) || !std::isfinite(u) || averageUs >= MODEL_STEP_US) return 1;
  std::cout << "HOST TIMING SIMULATION PASSED\n";
  return 0;
}

