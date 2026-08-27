/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Big Spiky MCP3208 access, filtering, and fault containment.
 * Derived from Open Source Neuro Spikeling V3.
 * Copyright (c) 2025-2026 Maxime Zimmermann and contributors.
 */
#pragma once

#include "BigSpiky_Hardware.h"

namespace bigspiky {

struct PotFilter {
  float alpha = 0.20f;
  uint16_t deadband = 6U;
  bool initialized = false;
  uint16_t raw1 = 0U;
  uint16_t raw2 = 0U;
  float filteredFloat = 0.0f;
  uint16_t stable = 0U;

  void reset(uint16_t raw) {
    initialized = true;
    raw1 = raw2 = stable = raw;
    filteredFloat = static_cast<float>(raw);
  }

  uint16_t update(uint16_t raw) {
    if (!initialized) { reset(raw); return stable; }
    const uint16_t middle = median3(raw, raw1, raw2);
    raw2 = raw1;
    raw1 = raw;
    filteredFloat += alpha * (static_cast<float>(middle) - filteredFloat);
    const uint16_t rounded = static_cast<uint16_t>(lroundf(filteredFloat));
    const int32_t difference = static_cast<int32_t>(rounded) - static_cast<int32_t>(stable);
    if (difference >= static_cast<int32_t>(deadband) ||
        difference <= -static_cast<int32_t>(deadband)) stable = rounded;
    return stable;
  }
};

namespace adc {

struct ChannelHealth {
  uint16_t railSamples = 0U;
  bool trusted = false;
  bool fault = false;
  uint32_t reads = 0U;
};

inline ChannelHealth health[4][8];
inline uint32_t faultMask = 0U;

inline StatusFlag deviceFaultFlag(uint8_t device) {
  return static_cast<StatusFlag>(STATUS_ADC0_FAULT << device);
}

inline void refreshDeviceFault(uint8_t device) {
  bool allUsedFault = true;
  bool anyObserved = false;
  for (uint8_t channel = 0U; channel < 8U; ++channel) {
    const ChannelHealth &h = health[device][channel];
    if (h.reads > 0U) {
      anyObserved = true;
      if (!h.fault) allUsedFault = false;
    }
  }
  setStatusFlag(deviceFaultFlag(device), anyObserved && allUsedFault);
}

inline uint16_t read(AdcChannel mapping, bool *valid = nullptr) {
  if (!mapping.valid()) {
    if (valid) *valid = false;
    return 0U;
  }
  const uint16_t raw = hardware::readMcp3208Raw(mapping.device, mapping.channel);
  ChannelHealth &h = health[mapping.device][mapping.channel];
  ++h.reads;
  const bool nearRail = raw <= ADC_RAIL_MARGIN || raw >= static_cast<uint16_t>(ADC_MAX - ADC_RAIL_MARGIN);
  if (!nearRail) {
    h.trusted = true;
    h.railSamples = 0U;
    if (h.fault) {
      h.fault = false;
      faultMask &= ~(1UL << (mapping.device * 8U + mapping.channel));
    }
  } else if (!h.trusted && h.railSamples < UINT16_MAX) {
    ++h.railSamples;
    if (h.railSamples >= ADC_RAIL_FAULT_SAMPLES && !h.fault) {
      h.fault = true;
      faultMask |= 1UL << (mapping.device * 8U + mapping.channel);
      diagnostics.adcFaultEvents = diagnostics.adcFaultEvents + 1U;
    }
  }
  setStatusFlag(STATUS_ADC_CHANNEL_FAULT, faultMask != 0U);
  refreshDeviceFault(mapping.device);
  if (valid) *valid = h.trusted && !h.fault;
  return raw;
}

inline void begin() {
  faultMask = 0U;
  for (uint8_t device = 0U; device < ADC_DEVICE_COUNT; ++device) {
    for (uint8_t channel = 0U; channel < 8U; ++channel) health[device][channel] = ChannelHealth{};
    (void)hardware::readMcp3208Raw(device, 0U);
  }
}

}  // namespace adc
}  // namespace bigspiky
