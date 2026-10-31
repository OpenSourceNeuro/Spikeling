/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
/* ========================================================================================================
  Spikeling V3 - Verified-spike hardware outputs in optional pharmacology mode
  ---------------------------------------------------------------------------------------------------------
  Requires General_settings.h and Pharmacology_intrinsic.h. The unmodified legacy output path
  remains active when pharmacology is OFF. In the optional path ONLY verified APs activate outputs.
  (c) 2026 Open Source Neuro contributors. GPL-3.0-or-later.
  ====================================================================================================== */
#include "General_settings.h"
#include "Pharmacology_intrinsic.h"

/* Show a verified AP through the unchanged output pins, PWM calibration and 12-bit DAC mapping.
   Input: one-tick verified_event from the intrinsic model; called instead of update_Spike()
   only when pharmacology is enabled and current-clamp is active. Failed TTX upstrokes
   cannot activate TTL, spike LED or buzzer, nor generate the analogue +30 mV spike marker. */
inline void pharmUpdateVerifiedSpikeOutput() {
  const bool verified = pharmacology.intrinsic.verified_event;                      // Authoritative AP gate for every output.
  neuron.spike = verified;                                                          // Record event for optional consumers.
  if (verified) {
    neuron.v_out = neuron.Vm_peak;                                                   // Display the last verified +30 mV model peak.
    digitalWrite(axon.pin_digital, HIGH);                                            // Axonal TTL pulse lasts one hardware loop step.
    if (spike.LED_enable) setSpikeRgbLedWhite();                                      // No white output for failed upstroke.
    digitalWrite(pins.gpio.spike, spike.Buzzer_enable ? HIGH : LOW);                  // Existing buzzer enable respected.
  } else {
    neuron.v_out = neuron.v;                                                         // Preserve the actual non-spike Vm.
    digitalWrite(axon.pin_digital, LOW);                                             // Suppress false AP TTL.
    digitalWrite(pins.gpio.spike, LOW);                                              // Suppress false buzzer pulse.
    if (spike.LED_enable) {
      spike.led_Vm_pwmf = (neuron.v_out - neuron.Vm_min) * spike.led_Vm;             // Original Vm brightness calculation.
      spike.led_Vm_pwm = int(constrain(spike.led_Vm_pwmf, 0.0f, float(spike.ledc_Max)));
      setVmRgbLed((uint16_t)spike.led_Vm_pwm);                                        // Preserve the selected non-spike RGB colour.
    }
  }
  axon.norm = (neuron.v_out - neuron.Vm_min) * axon.Vm_range;                       // Original analogue Vm calibration.
  axon.norm = constrain(axon.norm, 0.0f, 1.0f);
  axon.dacVal = axon.norm * dac_max + 0.5f;
  DAC.write(axon.dacVal, axon.pin_analog);
}
