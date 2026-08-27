/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Non-blocking, dual-core NeoPixel visualisation for Big Spiky.
 * Visual timing is deliberately separate from the biological model.
 * Copyright (c) 2025-2026 Maxime Zimmermann and contributors.
 */
#pragma once

#include <Adafruit_NeoPixel.h>
#include "BigSpiky_Model.h"

namespace bigspiky::leds {

struct VisualSnapshot {
  float vm = -70.0f;
  float vmMin = VM_MIN;
  float vmRest = -70.0f;
  float vmSpike = VM_SPIKE;
  float vmPeak = VM_PEAK;
  float gains[SYNAPSE_COUNT]{};
  float flashes[SYNAPSE_COUNT]{};
  uint8_t brightnessPercent = LED_DEFAULT_BRIGHTNESS_PERCENT;
  bool quiet = false;
};

inline Adafruit_NeoPixel branch0(BRANCH_PIXELS, kPins.ledData[0], NEO_GRB + NEO_KHZ800);
inline Adafruit_NeoPixel branch1(BRANCH_PIXELS, kPins.ledData[1], NEO_GRB + NEO_KHZ800);
inline Adafruit_NeoPixel branch2(BRANCH_PIXELS, kPins.ledData[2], NEO_GRB + NEO_KHZ800);
inline Adafruit_NeoPixel branch3(BRANCH_PIXELS, kPins.ledData[3], NEO_GRB + NEO_KHZ800);
inline Adafruit_NeoPixel somaStrip(SOMA_PIXELS, kPins.ledData[4], NEO_GRB + NEO_KHZ800);
inline Adafruit_NeoPixel axonStrip(AXON_PIXELS, kPins.ledData[5], NEO_GRB + NEO_KHZ800);

inline Rgb8 branchPixels[4][BRANCH_PIXELS];
inline Rgb8 somaPixels[SOMA_PIXELS];
inline Rgb8 axonPixels[AXON_PIXELS];
inline VisualSnapshot snapshot;
inline portMUX_TYPE ledMux = portMUX_INITIALIZER_UNLOCKED;
inline AxonQueueState axonQueue{0U, AXON_VISUAL_QUEUE_DEPTH, false, 0U, 0U, 0U};
inline SelfTestState selfTest;
inline uint32_t somaFlashUntilMs = 0U;
inline uint32_t connectionPulseUntilMs = 0U;
inline volatile uint32_t lastEstimatedCurrentMa = 0U;
inline volatile uint8_t lastCurrentLimitScale255 = 255U;
inline TaskHandle_t ledTaskHandle = nullptr;
inline volatile bool softwareEnabled = true;

inline Adafruit_NeoPixel &branchStrip(uint8_t branch) {
  switch (branch) {
    case 0U: return branch0;
    case 1U: return branch1;
    case 2U: return branch2;
    default: return branch3;
  }
}

inline void clearBuffers() {
  for (auto &branch : branchPixels) for (auto &pixel : branch) pixel = Rgb8{};
  for (auto &pixel : somaPixels) pixel = Rgb8{};
  for (auto &pixel : axonPixels) pixel = Rgb8{};
}

inline Rgb8 scaleRgb(Rgb8 colour, uint8_t scale) {
  colour.r = static_cast<uint8_t>((static_cast<uint16_t>(colour.r) * scale + 127U) / 255U);
  colour.g = static_cast<uint8_t>((static_cast<uint16_t>(colour.g) * scale + 127U) / 255U);
  colour.b = static_cast<uint8_t>((static_cast<uint16_t>(colour.b) * scale + 127U) / 255U);
  return colour;
}

inline void renderSynapseRings(const VisualSnapshot &state) {
  if (state.quiet) return;
  for (std::size_t index = 0U; index < SYNAPSE_COUNT; ++index) {
    const float gain = state.gains[index];
    const float magnitude = clampValue(fabsf(gain) / SYNAPSE_GAIN_MAX, 0.0f, 1.0f);
    if (magnitude < 0.001f && state.flashes[index] < 0.001f) continue;
    uint8_t arc = magnitude > 0.0f
        ? static_cast<uint8_t>(ceilf(magnitude * static_cast<float>(RING_PIXELS))) : 0U;
    const uint8_t baseIntensity = static_cast<uint8_t>(20.0f + 100.0f * magnitude);
    const uint8_t flashIntensity = static_cast<uint8_t>(235.0f * clampValue(state.flashes[index], 0.0f, 1.0f));
    const uint8_t intensity = static_cast<uint8_t>(clampValue<uint16_t>(
        static_cast<uint16_t>(baseIntensity) + flashIntensity, 0U, 255U));
    const Rgb8 colour = gain > 0.0f ? Rgb8{intensity, 0U, 0U}
                                    : (gain < 0.0f ? Rgb8{0U, 0U, intensity}
                                                   : Rgb8{static_cast<uint8_t>(intensity / 8U),
                                                          static_cast<uint8_t>(intensity / 8U),
                                                          static_cast<uint8_t>(intensity / 8U)});
    const uint8_t branch = kSynapseBranch[index];
    const uint8_t offset = static_cast<uint8_t>(kSynapseRingInBranch[index] * RING_PIXELS);
    if (state.flashes[index] > 0.02f && arc == 0U) arc = RING_PIXELS;
    for (uint8_t pixel = 0U; pixel < arc; ++pixel) branchPixels[branch][offset + pixel] = colour;
  }
}

inline void renderSoma(const VisualSnapshot &state, uint32_t nowMs, bool spikeFlash) {
  const float normal = normaliseVm(state.vm, state.vmMin, state.vmPeak);
  uint16_t arc = static_cast<uint16_t>(ceilf(normal * static_cast<float>(SOMA_PIXELS)));
  if (arc == 0U) arc = 1U;
  Rgb8 colour;
  if (spikeFlash) {
    colour = {255U, 255U, 255U};
    arc = SOMA_PIXELS;
  } else if (state.vm < state.vmRest) {
    const float cool = clampValue((state.vm - state.vmMin) / fmaxf(1.0f, state.vmRest - state.vmMin), 0.0f, 1.0f);
    const uint8_t intensity = static_cast<uint8_t>(8.0f + 42.0f * cool);
    colour = {0U, static_cast<uint8_t>(intensity / 4U), intensity};
  } else {
    const float depolarised = clampValue((state.vm - state.vmRest) /
        fmaxf(1.0f, state.vmSpike - state.vmRest), 0.0f, 1.0f);
    colour = {
      static_cast<uint8_t>(12.0f + 190.0f * depolarised),
      static_cast<uint8_t>(42.0f + 80.0f * depolarised),
      static_cast<uint8_t>(50.0f * (1.0f - depolarised))
    };
  }
  if (state.quiet && !spikeFlash) colour = {0U, 10U, 12U};
  for (uint16_t pixel = 0U; pixel < arc; ++pixel) somaPixels[pixel] = colour;
  (void)nowMs;
}

inline void renderAxon(uint32_t nowMs) {
  axonQueue.service(nowMs, AXON_TRAVEL_MS);
  if (!axonQueue.active) return;
  const float progress = axonQueue.progress(nowMs, AXON_TRAVEL_MS);
  const int head = static_cast<int>(lroundf(progress * static_cast<float>(AXON_PIXELS - 1U)));
  for (int tail = 0; tail < 6; ++tail) {
    const int pixel = head - tail;
    if (pixel < 0 || pixel >= static_cast<int>(AXON_PIXELS)) continue;
    const uint8_t intensity = static_cast<uint8_t>(255U / static_cast<uint8_t>(tail + 1));
    axonPixels[pixel] = {intensity, intensity, intensity};
  }
}

inline void renderSelfTest(const SelfTestState &test) {
  if (test.stage < 12U) {
    const uint8_t branch = kSynapseBranch[test.stage];
    const uint8_t offset = static_cast<uint8_t>(kSynapseRingInBranch[test.stage] * RING_PIXELS);
    for (uint8_t pixel = 0U; pixel < RING_PIXELS; ++pixel)
      branchPixels[branch][offset + pixel] = {20U, 80U, 80U};
  } else if (test.stage < 16U) {
    const uint8_t branch = static_cast<uint8_t>(test.stage - 12U);
    for (uint16_t pixel = 0U; pixel < BRANCH_PIXELS; ++pixel)
      branchPixels[branch][pixel] = {20U, 60U, 70U};
  } else if (test.stage == 16U) {
    for (uint16_t pixel = 0U; pixel < SOMA_PIXELS; ++pixel) somaPixels[pixel] = {20U, 70U, 70U};
  } else {
    for (uint16_t pixel = 0U; pixel < AXON_PIXELS; ++pixel) axonPixels[pixel] = {20U, 70U, 70U};
  }
}

inline void applyBrightnessAndCurrentLimit(uint8_t brightnessPercent) {
  const uint8_t cappedPercent = clampValue<uint8_t>(brightnessPercent, 0U, LED_MAX_BRIGHTNESS_PERCENT);
  const uint8_t brightnessScale = static_cast<uint8_t>((static_cast<uint16_t>(cappedPercent) * 255U) / 100U);
  for (auto &branch : branchPixels) for (auto &pixel : branch) pixel = scaleRgb(pixel, brightnessScale);
  for (auto &pixel : somaPixels) pixel = scaleRgb(pixel, brightnessScale);
  for (auto &pixel : axonPixels) pixel = scaleRgb(pixel, brightnessScale);
  uint32_t estimate = 0U;
  for (uint8_t branch = 0U; branch < 4U; ++branch)
    estimate += estimateWs2812CurrentMa(branchPixels[branch], BRANCH_PIXELS);
  estimate += estimateWs2812CurrentMa(somaPixels, SOMA_PIXELS);
  estimate += estimateWs2812CurrentMa(axonPixels, AXON_PIXELS);
  const uint8_t currentScale = currentLimitScale255(estimate, LED_HARD_CURRENT_MA);
  if (currentScale < 255U) {
    for (auto &branch : branchPixels) for (auto &pixel : branch) pixel = scaleRgb(pixel, currentScale);
    for (auto &pixel : somaPixels) pixel = scaleRgb(pixel, currentScale);
    for (auto &pixel : axonPixels) pixel = scaleRgb(pixel, currentScale);
  }
  lastEstimatedCurrentMa = estimate;
  lastCurrentLimitScale255 = currentScale;
}

inline void transmitBuffers() {
  for (uint8_t branch = 0U; branch < 4U; ++branch) {
    Adafruit_NeoPixel &strip = branchStrip(branch);
    for (uint16_t pixel = 0U; pixel < BRANCH_PIXELS; ++pixel) {
      const Rgb8 colour = branchPixels[branch][pixel];
      strip.setPixelColor(pixel, colour.r, colour.g, colour.b);
    }
    strip.show();
  }
  for (uint16_t pixel = 0U; pixel < SOMA_PIXELS; ++pixel) {
    const Rgb8 colour = somaPixels[pixel];
    somaStrip.setPixelColor(pixel, colour.r, colour.g, colour.b);
  }
  somaStrip.show();
  for (uint16_t pixel = 0U; pixel < AXON_PIXELS; ++pixel) {
    const Rgb8 colour = axonPixels[pixel];
    axonStrip.setPixelColor(pixel, colour.r, colour.g, colour.b);
  }
  axonStrip.show();
}

inline void renderFrame() {
  const uint32_t nowMs = millis();
  const bool physicalDisable = digitalRead(kPins.ledDisableSwitch) == HIGH || !softwareEnabled;
  VisualSnapshot local;
  SelfTestState localTest;
  bool spikeFlash = false;
  bool connectionPulse = false;
  portENTER_CRITICAL(&ledMux);
  selfTest.service(nowMs, SELF_TEST_STAGE_MS);
  local = snapshot;
  localTest = selfTest;
  spikeFlash = static_cast<int32_t>(somaFlashUntilMs - nowMs) > 0;
  connectionPulse = static_cast<int32_t>(connectionPulseUntilMs - nowMs) > 0;
  portEXIT_CRITICAL(&ledMux);

  setStatusFlag(STATUS_SELF_TEST, localTest.active);
  setStatusFlag(STATUS_LEDS_DISABLED, physicalDisable);
  setStatusFlag(STATUS_ACTIVITY_QUIET, local.quiet);
  clearBuffers();
  if (!physicalDisable) {
    if (localTest.active) renderSelfTest(localTest);
    else {
      renderSynapseRings(local);
      renderSoma(local, nowMs, spikeFlash);
      renderAxon(nowMs);
      if (connectionPulse) {
        for (auto &pixel : somaPixels) pixel = {0U, 80U, 90U};
      }
    }
    applyBrightnessAndCurrentLimit(localTest.active ? 10U : local.brightnessPercent);
  }
  transmitBuffers();
}

inline void ledTask(void *) {
  TickType_t lastWake = xTaskGetTickCount();
  while (true) {
    renderFrame();
    vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(LED_FRAME_MS));
  }
}

inline void begin() {
  branch0.begin(); branch1.begin(); branch2.begin(); branch3.begin();
  somaStrip.begin(); axonStrip.begin();
  branch0.clear(); branch1.clear(); branch2.clear(); branch3.clear();
  somaStrip.clear(); axonStrip.clear();
  branch0.show(); branch1.show(); branch2.show(); branch3.show();
  somaStrip.show(); axonStrip.show();
  axonQueue.capacity = AXON_VISUAL_QUEUE_DEPTH;
  xTaskCreatePinnedToCore(ledTask, "BigSpikyLED", 8192U, nullptr, 1U, &ledTaskHandle, 0);
}

inline void publishModelState(bool spikeEvent) {
  const uint32_t nowMs = millis();
  portENTER_CRITICAL(&ledMux);
  snapshot.vm = neuron.vOut;
  snapshot.vmMin = neuron.vmMin;
  snapshot.vmRest = neuron.vRest;
  snapshot.vmSpike = neuron.vmSpike;
  snapshot.vmPeak = neuron.vmPeak;
  snapshot.brightnessPercent = ledBrightnessPercent;
  snapshot.quiet = ENABLE_ACTIVITY_TIMEOUT &&
      static_cast<uint32_t>(nowMs - lastActivityMs) >= ACTIVITY_TIMEOUT_MS;
  for (std::size_t index = 0U; index < SYNAPSE_COUNT; ++index) {
    snapshot.gains[index] = synapses[index].gain;
    snapshot.flashes[index] = synapses[index].ledFlash;
  }
  if (spikeEvent && !selfTest.active) {
    somaFlashUntilMs = nowMs + 80U;
    if (!axonQueue.enqueue(true)) {
      ++diagnostics.visualQueueDrops;
      diagnostics.statusFlags |= STATUS_LED_QUEUE_OVERFLOW;
    }
  }
  portEXIT_CRITICAL(&ledMux);
}

inline void startSelfTest() {
  portENTER_CRITICAL(&ledMux);
  axonQueue.queued = 0U;
  axonQueue.active = false;
  somaFlashUntilMs = 0U;
  selfTest.start(millis(), SELF_TEST_STAGE_COUNT);
  portEXIT_CRITICAL(&ledMux);
  lastActivityMs = millis();
}

inline void showConnectedPulse() {
  portENTER_CRITICAL(&ledMux);
  connectionPulseUntilMs = millis() + 250U;
  portEXIT_CRITICAL(&ledMux);
}

}  // namespace bigspiky::leds
