/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
// Included after Arduino.h. Only active diagnostic VC2 uses guarded writes.
// HWCDC 3.3.12 bounds its zero-timeout retry loop; older implementations may
// spin indefinitely with timeout=0. Pin the audited core for this experiment.
#if defined(ARDUINO_USB_MODE) && ARDUINO_USB_MODE && ARDUINO_USB_CDC_ON_BOOT
#include <esp_arduino_version.h>
#if ESP_ARDUINO_VERSION != ESP_ARDUINO_VERSION_VAL(3,3,12)
#error "Guarded VC USB prototype requires ESP32 Arduino core 3.3.12"
#endif
#define VC_GUARDED_HWCDC 1
#elif defined(VC_PROTOTYPE_TEST)
#define VC_GUARDED_HWCDC 1
#else
#define VC_GUARDED_HWCDC 0
#endif

namespace vc {
constexpr unsigned diagnostic_tx_buffer_bytes = 4096;
inline bool usb_tx_ready = false, usb_tx_guarded = false, usb_tx_fault = false;

inline void prepareDiagnosticUsb() {
#if VC_GUARDED_HWCDC
  // Hardware CDC is not auto-begun by core main.cpp. Allocate once BEFORE
  // Serial.begin(), never resize a live ISR-owned ring buffer.
  usb_tx_ready = Serial.setTxBufferSize(diagnostic_tx_buffer_bytes) == diagnostic_tx_buffer_bytes;
  Serial.setTxTimeoutMs(100);  // Audited core default, retained outside VC2.
#endif
}

inline void diagnosticUsbMode(bool enabled) {
  const bool guarded = enabled && usb_tx_ready;
  if (guarded && !usb_tx_guarded) usb_tx_fault = false;
  usb_tx_guarded = guarded;
#if VC_GUARDED_HWCDC
  Serial.setTxTimeoutMs(guarded ? 0 : 100);
#endif
}

inline size_t writeDiagnosticUsb(const uint8_t* bytes, size_t count, bool& capacity_skip) {
  capacity_skip = true;
#if VC_GUARDED_HWCDC
  // Single sketch-side producer. The ISR only frees ring space. No wait for
  // room, retry in the model loop or hidden partial-frame retry is permitted.
  if (usb_tx_guarded && Serial.availableForWrite() >= int(count)) {
    capacity_skip = false;
    const size_t accepted = Serial.write(bytes,count);
    if (accepted != count) usb_tx_fault = true;
    return accepted;
  }
#endif
  usb_tx_fault = true;
  return 0;
}
} // namespace vc
