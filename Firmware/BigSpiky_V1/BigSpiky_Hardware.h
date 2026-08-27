/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Big Spiky ESP32-S3 hardware access.
 * Derived from Open Source Neuro Spikeling V3.
 * Copyright (c) 2025-2026 Maxime Zimmermann and contributors.
 */
#pragma once

#include <Arduino.h>
#include <SPI.h>
#include "BigSpiky_Config.h"
#include "BigSpiky_Logic.h"

namespace bigspiky {

enum StatusFlag : uint32_t {
  STATUS_ADC0_FAULT          = 1UL << 0,
  STATUS_ADC1_FAULT          = 1UL << 1,
  STATUS_ADC2_FAULT          = 1UL << 2,
  STATUS_ADC3_FAULT          = 1UL << 3,
  STATUS_ADC_CHANNEL_FAULT   = 1UL << 4,
  STATUS_MODEL_OVERRUN       = 1UL << 5,
  STATUS_SERIAL_OVERFLOW     = 1UL << 6,
  STATUS_EVENT_SATURATION    = 1UL << 7,
  STATUS_LED_QUEUE_OVERFLOW  = 1UL << 8,
  STATUS_SELF_TEST           = 1UL << 9,
  STATUS_LEDS_DISABLED       = 1UL << 10,
  STATUS_ACTIVITY_QUIET      = 1UL << 11,
  STATUS_VOLTAGE_CLAMP       = 1UL << 12
};

struct Diagnostics {
  volatile uint32_t statusFlags = 0U;
  volatile uint32_t modelOverruns = 0U;
  volatile uint32_t maximumModelExecutionUs = 0U;
  volatile uint32_t serialOverflowErrors = 0U;
  volatile uint32_t serialCommandErrors = 0U;
  volatile uint32_t adcFaultEvents = 0U;
  volatile uint32_t eventSaturations = 0U;
  volatile uint32_t visualQueueDrops = 0U;
};

inline Diagnostics diagnostics;
inline portMUX_TYPE diagnosticsMux = portMUX_INITIALIZER_UNLOCKED;

inline void setStatusFlag(StatusFlag flag, bool set) {
  portENTER_CRITICAL(&diagnosticsMux);
  if (set) diagnostics.statusFlags |= static_cast<uint32_t>(flag);
  else diagnostics.statusFlags &= ~static_cast<uint32_t>(flag);
  portEXIT_CRITICAL(&diagnosticsMux);
}

inline uint32_t statusFlagsSnapshot() {
  portENTER_CRITICAL(&diagnosticsMux);
  const uint32_t flags = diagnostics.statusFlags;
  portEXIT_CRITICAL(&diagnosticsMux);
  return flags;
}

namespace hardware {

inline SPISettings adcSpiSettings(MCP3208_SPI_HZ, MSBFIRST, SPI_MODE0);
inline SPISettings dacSpiSettings(MCP4922_SPI_HZ, MSBFIRST, SPI_MODE0);
inline bool spiReady = false;

inline void beginSafePins() {
  pinMode(kPins.axonDigital, OUTPUT);
  digitalWrite(kPins.axonDigital, LOW);

  for (uint8_t i = 0U; i < 4U; ++i) {
    pinMode(kPins.adcCs[i], OUTPUT);
    digitalWrite(kPins.adcCs[i], HIGH);
  }
  pinMode(kPins.dacCs, OUTPUT);
  digitalWrite(kPins.dacCs, HIGH);

  for (uint8_t i = 0U; i < 6U; ++i) {
    pinMode(kPins.ledData[i], OUTPUT);
    digitalWrite(kPins.ledData[i], LOW);
  }
  pinMode(kPins.ledDisableSwitch, INPUT_PULLDOWN);
  pinMode(kPins.selfTestButton, INPUT_PULLDOWN);
}

inline void beginSpi() {
  SPI.begin(kPins.spiSck, kPins.spiMiso, kPins.spiMosi, -1);
  spiReady = true;
}

inline uint16_t readMcp3208Raw(uint8_t device, uint8_t channel) {
  if (!spiReady || device >= ADC_DEVICE_COUNT || channel >= 8U) return 0U;
  const uint8_t cs = kPins.adcCs[device];
  SPI.beginTransaction(adcSpiSettings);
  digitalWrite(cs, LOW);
  SPI.transfer(static_cast<uint8_t>(0x06U | (channel >> 2U)));
  const uint8_t high = SPI.transfer(static_cast<uint8_t>(channel << 6U));
  const uint8_t low = SPI.transfer(0x00U);
  digitalWrite(cs, HIGH);
  SPI.endTransaction();
  return static_cast<uint16_t>(((high & 0x0FU) << 8U) | low);
}

inline void writeMcp4922(uint8_t channel, uint16_t value) {
  if (!spiReady) return;
  const uint16_t control = channel == 0U ? 0x3000U : 0xB000U;
  const uint16_t frame = static_cast<uint16_t>(control | (value & 0x0FFFU));
  SPI.beginTransaction(dacSpiSettings);
  digitalWrite(kPins.dacCs, LOW);
  SPI.transfer16(frame);
  digitalWrite(kPins.dacCs, HIGH);
  SPI.endTransaction();
}

inline void writeAxonVm(float vm, float vmMin, float vmMax) {
  const float normal = (vmMax > vmMin) ? clampValue((vm - vmMin) / (vmMax - vmMin), 0.0f, 1.0f) : 0.0f;
  const uint16_t code = static_cast<uint16_t>(normal * 4095.0f + 0.5f);
  writeMcp4922(MCP4922_AXON_CHANNEL, code);
}

}  // namespace hardware
}  // namespace bigspiky

