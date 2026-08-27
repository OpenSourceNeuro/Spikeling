/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Presets retained from Open Source Neuro Spikeling V3.
 * Copyright (c) 2025-2026 Maxime Zimmermann and contributors.
 */
#pragma once

#include <cstddef>
#include <cstdint>

namespace bigspiky {

enum class IzhikevichModel : uint8_t {
  TonicSpiking = 0, PhasicSpiking, TonicBursting, PhasicBursting,
  MixedMode, SpikeFrequencyAdaptation, Class1, Class2, SpikeLatency,
  SubThresholdOscillations, Resonator, Integrator, ReboundSpike,
  ReboundBurst, ThresholdVariability, Bistability, DAP, Accommodation,
  InhibitionInducedSpiking, InhibitionInducedBursting, Count
};

struct IzhikevichParams { float a; float b; float c; float d; float v_rest; };

inline constexpr IzhikevichParams kIzhikevichPresets[] = {
  {0.02f,  0.20f, -65.0f,   6.0f, -70.0f},
  {0.02f,  0.25f, -65.0f,   6.0f, -64.0f},
  {0.02f,  0.20f, -50.0f,   2.0f, -70.0f},
  {0.02f,  0.25f, -55.0f,   0.05f,-64.0f},
  {0.02f,  0.20f, -55.0f,   4.0f, -70.0f},
  {0.01f,  0.20f, -65.0f,   8.0f, -70.0f},
  {0.02f, -0.10f, -55.0f,   6.0f, -60.0f},
  {0.20f,  0.26f, -65.0f,   0.0f, -64.0f},
  {0.02f,  0.20f, -65.0f,   6.0f, -70.0f},
  {0.05f,  0.26f, -60.0f,   0.0f, -62.0f},
  {0.10f,  0.26f, -60.0f,  -1.0f, -62.0f},
  {0.02f, -0.10f, -55.0f,   6.0f, -60.0f},
  {0.03f,  0.25f, -60.0f,   4.0f, -64.0f},
  {0.03f,  0.25f, -52.0f,   0.0f, -64.0f},
  {0.03f,  0.25f, -60.0f,   4.0f, -64.0f},
  {0.10f,  0.26f, -60.0f,   0.0f, -61.0f},
  {1.00f,  0.20f, -60.0f, -21.0f, -70.0f},
  {0.02f,  1.00f, -55.0f,   4.0f, -65.0f},
  {0.02f,  1.00f, -60.0f,   8.0f, -63.8f},
  {0.026f,-1.00f, -45.0f,  -2.0f, -63.8f}
};

inline constexpr std::size_t kIzhikevichModelCount =
    static_cast<std::size_t>(IzhikevichModel::Count);
static_assert(kIzhikevichModelCount == sizeof(kIzhikevichPresets) / sizeof(kIzhikevichPresets[0]),
              "Izhikevich preset table mismatch");
inline constexpr const IzhikevichParams &getIzhikevichParams(IzhikevichModel model) {
  return kIzhikevichPresets[static_cast<std::size_t>(model)];
}

}  // namespace bigspiky

