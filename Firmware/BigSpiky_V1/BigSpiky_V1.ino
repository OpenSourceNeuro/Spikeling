/* SPDX-License-Identifier: GPL-3.0-or-later */
/* =====================================================================================================
 * Big Spiky V1 - Maker Faire Rome 2026 interactive neuron firmware
 *
 * Target: ESP32-S3-WROOM-1 N4 / ESP32S3 Dev Module
 * Scientific baseline: Open Source Neuro Spikeling V3, source commit recorded in SOURCE_AUDIT.md
 * Author: Maxime Zimmermann and Open Source Neuro contributors
 * License: GPL-3.0-or-later
 *
 * This is an educational real-time computational neuron. It is not a biological preparation and it is not
 * a research-grade electrophysiology recorder. LED animations never modify the model equations or timing.
 * =================================================================================================== */

#include "BigSpiky_Serial.h"

using namespace bigspiky;

namespace {
uint32_t nextModelDeadlineUs = 0U;
bool selfTestRaw = false;
bool selfTestStable = false;
uint32_t selfTestChangedMs = 0U;

void serviceSelfTestButton() {
  const bool raw = digitalRead(kPins.selfTestButton) == HIGH;
  const uint32_t nowMs = millis();
  if (raw != selfTestRaw) {
    selfTestRaw = raw;
    selfTestChangedMs = nowMs;
  }
  if (raw != selfTestStable && static_cast<uint32_t>(nowMs - selfTestChangedMs) >= 30U) {
    selfTestStable = raw;
    if (selfTestStable) leds::startSelfTest();
  }
}

void serviceModel(uint32_t nowUs) {
  if (static_cast<int32_t>(nowUs - nextModelDeadlineUs) < 0) return;
  const uint32_t latenessUs = nowUs - nextModelDeadlineUs;
  const uint32_t missedDeadlines = latenessUs / MODEL_STEP_US;
  if (missedDeadlines > 0U) {
    diagnostics.modelOverruns += missedDeadlines;
    setStatusFlag(STATUS_MODEL_OVERRUN, true);
  }
  nextModelDeadlineUs += (missedDeadlines + 1U) * MODEL_STEP_US;

  const uint32_t startedUs = micros();
  const bool spikeEvent = modelStep();
  leds::publishModelState(spikeEvent);
  serial::sendTelemetry(startedUs);
  const uint32_t elapsedUs = micros() - startedUs;
  recordModelExecution(elapsedUs, latenessUs % MODEL_STEP_US);
}
}  // namespace

void setup() {
  hardware::beginSafePins();
  Serial.begin(SERIAL_BAUD);
  hardware::beginSpi();
  adc::begin();
  beginSynapses();
  beginModel();
  leds::begin();
  nextModelDeadlineUs = micros() + MODEL_STEP_US;
}

void loop() {
  const uint32_t nowUs = micros();
  serial::serviceInput();
  serviceControlScanning(nowUs);
  serviceSelfTestButton();
  serviceModel(nowUs);
  yield();
}

