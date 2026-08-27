/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Big Spiky firmware - pure, host-testable logic.
 * Derived from Open Source Neuro Spikeling V3.
 * Copyright (c) 2025-2026 Maxime Zimmermann and contributors.
 */
#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cerrno>
#include <climits>

namespace bigspiky {

template <typename T>
constexpr T clampValue(T value, T low, T high) {
  return value < low ? low : (value > high ? high : value);
}

constexpr uint16_t median3(uint16_t a, uint16_t b, uint16_t c) {
  if (a > b) { const uint16_t t = a; a = b; b = t; }
  if (b > c) { const uint16_t t = b; b = c; c = t; }
  if (a > b) { const uint16_t t = a; a = b; b = t; }
  return b;
}

inline float mapBipolarGain(uint16_t raw, uint16_t centre,
                            uint16_t deadZone, float maximum,
                            bool reverse) {
  int32_t centred = static_cast<int32_t>(raw) - static_cast<int32_t>(centre);
  if (reverse) centred = -centred;
  if (std::abs(centred) <= static_cast<int32_t>(deadZone)) return 0.0f;
  const int32_t adjusted = centred > 0 ? centred - deadZone : centred + deadZone;
  const float positiveSpan = static_cast<float>(4095U - centre - deadZone);
  const float negativeSpan = static_cast<float>(centre - deadZone);
  const float span = adjusted >= 0 ? positiveSpan : negativeSpan;
  if (span <= 1.0f || !std::isfinite(maximum)) return 0.0f;
  return clampValue((static_cast<float>(adjusted) / span) * maximum,
                    -maximum, maximum);
}

inline float applySynapticEvents(float current, float gain,
                                 uint16_t eventCount, float decay,
                                 float minimum, float maximum,
                                 bool enabled = true) {
  if (!enabled || !std::isfinite(current) || !std::isfinite(gain) ||
      !std::isfinite(decay)) {
    return 0.0f;
  }
  const float accumulated = current + gain * static_cast<float>(eventCount);
  return clampValue(accumulated, minimum, maximum) * clampValue(decay, 0.0f, 1.0f);
}

inline float normaliseVm(float vm, float vmMin, float vmPeak) {
  const float span = vmPeak - vmMin;
  if (!std::isfinite(vm) || span <= 0.0f) return 0.0f;
  return clampValue((vm - vmMin) / span, 0.0f, 1.0f);
}

inline uint16_t crc16CcittFalse(const uint8_t *data, std::size_t length,
                                uint16_t initial = 0xFFFFU) {
  uint16_t crc = initial;
  for (std::size_t i = 0; i < length; ++i) {
    crc ^= static_cast<uint16_t>(data[i]) << 8U;
    for (uint8_t bit = 0; bit < 8U; ++bit) {
      crc = (crc & 0x8000U) ? static_cast<uint16_t>((crc << 1U) ^ 0x1021U)
                            : static_cast<uint16_t>(crc << 1U);
    }
  }
  return crc;
}

inline bool parseLongStrict(const char *text, long minimum, long maximum, long &out) {
  if (text == nullptr || *text == '\0') return false;
  char *end = nullptr;
  errno = 0;
  const long parsed = std::strtol(text, &end, 10);
  if (errno == ERANGE || end == text || *end != '\0' || parsed < minimum || parsed > maximum) {
    return false;
  }
  out = parsed;
  return true;
}

inline bool parseFloatStrict(const char *text, float minimum, float maximum, float &out) {
  if (text == nullptr || *text == '\0') return false;
  char *end = nullptr;
  errno = 0;
  const float parsed = std::strtof(text, &end);
  if (errno == ERANGE || end == text || *end != '\0' || !std::isfinite(parsed) ||
      parsed < minimum || parsed > maximum) {
    return false;
  }
  out = parsed;
  return true;
}

struct Rgb8 {
  uint8_t r = 0;
  uint8_t g = 0;
  uint8_t b = 0;
};

inline uint32_t estimateWs2812CurrentMa(const Rgb8 *pixels, std::size_t count) {
  uint64_t channelSum = 0;
  for (std::size_t i = 0; i < count; ++i) {
    channelSum += pixels[i].r;
    channelSum += pixels[i].g;
    channelSum += pixels[i].b;
  }
  return static_cast<uint32_t>((channelSum * 20ULL + 254ULL) / 255ULL);
}

inline uint8_t currentLimitScale255(uint32_t estimatedMa, uint32_t limitMa) {
  if (limitMa == 0U) return 0U;
  if (estimatedMa <= limitMa) return 255U;
  return static_cast<uint8_t>(clampValue<uint32_t>((limitMa * 255U) / estimatedMa, 1U, 255U));
}

struct AxonQueueState {
  uint8_t queued = 0;
  uint8_t capacity = 4;
  bool active = false;
  uint32_t startedMs = 0;
  uint32_t dropped = 0;
  uint32_t launched = 0;

  bool enqueue(bool oneShotSpike) {
    if (!oneShotSpike) return false;
    if (queued >= capacity) { ++dropped; return false; }
    ++queued;
    return true;
  }

  void service(uint32_t nowMs, uint32_t durationMs) {
    if (active && static_cast<uint32_t>(nowMs - startedMs) >= durationMs) active = false;
    if (!active && queued > 0U) {
      --queued;
      active = true;
      startedMs = nowMs;
      ++launched;
    }
  }

  float progress(uint32_t nowMs, uint32_t durationMs) const {
    if (!active || durationMs == 0U) return 0.0f;
    return clampValue(static_cast<float>(static_cast<uint32_t>(nowMs - startedMs)) /
                      static_cast<float>(durationMs), 0.0f, 1.0f);
  }
};

struct SelfTestState {
  bool active = false;
  uint8_t stage = 0;
  uint8_t stageCount = 0;
  uint32_t stageStartedMs = 0;

  void start(uint32_t nowMs, uint8_t count) {
    active = count > 0U;
    stage = 0U;
    stageCount = count;
    stageStartedMs = nowMs;
  }

  void service(uint32_t nowMs, uint32_t stageDurationMs) {
    if (!active || stageDurationMs == 0U) return;
    while (active && static_cast<uint32_t>(nowMs - stageStartedMs) >= stageDurationMs) {
      stageStartedMs += stageDurationMs;
      ++stage;
      if (stage >= stageCount) active = false;
    }
  }
};

}  // namespace bigspiky

