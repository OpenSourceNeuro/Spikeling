/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Big Spiky real-time Izhikevich model and central inputs.
 * Derived from Open Source Neuro Spikeling V3.
 * Copyright (c) 2025-2026 Maxime Zimmermann and contributors.
 */
#pragma once

#include <esp_system.h>
#include "BigSpiky_Synapses.h"

namespace bigspiky {

enum class ClampMode : uint8_t { CurrentClamp = 0U, VoltageClamp = 1U };

struct NeuronState {
  float v = -70.0f;
  float u = -14.0f;
  float a = 0.02f;
  float b = 0.20f;
  float c = -65.0f;
  float d = 6.0f;
  float vRest = -70.0f;
  float vmMin = VM_MIN;
  float vmMax = VM_MAX;
  float vmSpike = VM_SPIKE;
  float vmPeak = VM_PEAK;
  float vOut = -70.0f;
  float totalCurrent = 0.0f;
  bool spike = false;
  int16_t selectedModel = static_cast<int16_t>(DEFAULT_MODEL);
  bool customModel = false;
};

struct PatchState {
  PotFilter potFilter{};
  PotFilter externalFilter{};
  bool usePot = true;
  bool potValid = false;
  uint16_t potRaw = POT_CENTRE;
  float currentCommand = 0.0f;
  bool externalValid = false;
  float externalFiltered = static_cast<float>(POT_CENTRE);
  float externalCurrent = 0.0f;
  float vHold = -70.0f;
  float vCommand = -70.0f;
  float vCommandSpan = 70.0f;
  float kp = 7.5f;
  float ki = 0.10f;
  float integral = 0.0f;
  float clampCurrent = 0.0f;
  float currentMinimum = -200.0f;
  float currentMaximum = 300.0f;
};

struct NoiseState {
  PotFilter potFilter{};
  bool usePot = true;
  bool potValid = false;
  uint16_t potRaw = 0U;
  float sigma = 0.0f;
  float current = 0.0f;
  bool spareReady = false;
  float spare = 0.0f;
};

struct PhotodiodeState {
  PotFilter gainFilter{};
  bool useGainPot = true;
  bool gainPotValid = false;
  float gain = 0.0f;
  uint16_t raw = 0U;
  float filtered = 0.0f;
  float darkCounts = 0.0f;
  uint32_t darkAccumulator = 0U;
  uint16_t calibrationSamples = 0U;
  bool calibrated = false;
  float fullCounts = 400.0f;
  float fullCurrent = 10.0f;
  float adaptation = 1.0f;
  float decayPerCurrent = 0.001f;
  float recovery = 0.025f;
  float current = 0.0f;
};

inline NeuronState neuron;
inline PatchState patch;
inline NoiseState noise;
inline PhotodiodeState photodiode;
inline ClampMode clampMode = ClampMode::CurrentClamp;
inline uint8_t ledBrightnessPercent = LED_DEFAULT_BRIGHTNESS_PERCENT;
inline bool brightnessFromPot = USE_BRIGHTNESS_POT;
inline uint8_t triggerState = 0U;
inline int16_t stimulusState = 0;
inline uint32_t lastActivityMs = 0U;
inline uint32_t nextControlScanUs = 0U;
inline uint8_t controlScanIndex = 0U;

inline float bipolarControl(uint16_t raw, float maximum, uint16_t deadZone = POT_DEAD_ZONE) {
  return mapBipolarGain(raw, POT_CENTRE, deadZone, maximum, false);
}

inline float gaussianSample(float sigma) {
  if (sigma <= 0.0f || !std::isfinite(sigma)) return 0.0f;
  if (noise.spareReady) {
    noise.spareReady = false;
    return noise.spare * sigma;
  }
  const float denominator = 4294967297.0f;
  const float u1 = (static_cast<float>(esp_random()) + 1.0f) / denominator;
  const float u2 = (static_cast<float>(esp_random()) + 1.0f) / denominator;
  const float radius = sqrtf(-2.0f * logf(u1));
  const float angle = 6.28318530718f * u2;
  noise.spare = radius * sinf(angle);
  noise.spareReady = true;
  return radius * cosf(angle) * sigma;
}

inline void resetNeuronDynamicState() {
  neuron.v = neuron.vRest;
  neuron.u = neuron.b * neuron.v;
  neuron.vOut = neuron.v;
  neuron.totalCurrent = 0.0f;
  neuron.spike = false;
  patch.integral = 0.0f;
  patch.clampCurrent = 0.0f;
  patch.vHold = clampValue(neuron.vRest, neuron.vmMin, neuron.vmPeak);
  patch.vCommand = patch.vHold;
  resetSynapticState();
  digitalWrite(kPins.axonDigital, LOW);
}

inline bool applyNeuronParameters(float a, float b, float c, float d, float vRest,
                                  int16_t selected, bool custom) {
  if (!std::isfinite(a) || !std::isfinite(b) || !std::isfinite(c) || !std::isfinite(d) || !std::isfinite(vRest) ||
      a < 0.0f || a > 2.0f || b < -2.0f || b > 2.0f || c < VM_MIN || c > VM_PEAK ||
      d < -100.0f || d > 100.0f || vRest < VM_MIN || vRest > VM_PEAK) return false;
  neuron.a = a; neuron.b = b; neuron.c = c; neuron.d = d; neuron.vRest = vRest;
  neuron.selectedModel = selected;
  neuron.customModel = custom;
  resetNeuronDynamicState();
  return true;
}

inline bool selectNeuronPreset(uint8_t index) {
  if (index >= kIzhikevichModelCount) return false;
  const IzhikevichParams &preset = getIzhikevichParams(static_cast<IzhikevichModel>(index));
  return applyNeuronParameters(preset.a, preset.b, preset.c, preset.d, preset.v_rest,
                               static_cast<int16_t>(index), false);
}

inline void setClampMode(ClampMode mode) {
  if (clampMode == mode) return;
  clampMode = mode;
  patch.integral = 0.0f;
  patch.clampCurrent = 0.0f;
  patch.vHold = clampValue(neuron.v, neuron.vmMin, neuron.vmPeak);
  patch.vCommand = patch.vHold;
  setStatusFlag(STATUS_VOLTAGE_CLAMP, clampMode == ClampMode::VoltageClamp);
}

inline void beginModel() {
  const IzhikevichParams &preset = getIzhikevichParams(DEFAULT_MODEL);
  neuron.a = preset.a; neuron.b = preset.b; neuron.c = preset.c; neuron.d = preset.d;
  neuron.vRest = preset.v_rest;
  patch.potFilter.alpha = 0.20f;
  patch.potFilter.deadband = 6U;
  patch.externalFilter.alpha = 0.25f;
  patch.externalFilter.deadband = 4U;
  noise.potFilter.alpha = 0.20f;
  noise.potFilter.deadband = 2U;
  photodiode.gainFilter.alpha = 0.20f;
  photodiode.gainFilter.deadband = 6U;
  resetNeuronDynamicState();
  lastActivityMs = millis();
  nextControlScanUs = micros();
  hardware::writeAxonVm(neuron.vOut, neuron.vmMin, neuron.vmMax);
}

inline void scanCentralControl(uint8_t index) {
  bool valid = false;
  if (index == 12U && patch.usePot) {
    patch.potRaw = adc::read(kPatchPotChannel, &valid);
    patch.potValid = valid;
    if (!valid) patch.currentCommand = 0.0f;
    else {
      const uint16_t filtered = patch.potFilter.update(patch.potRaw);
      if (clampMode == ClampMode::CurrentClamp) patch.currentCommand = bipolarControl(filtered, 80.0f);
      else {
        patch.vHold = clampValue(neuron.vRest + bipolarControl(filtered, patch.vCommandSpan),
                                 neuron.vmMin, neuron.vmPeak);
        patch.vCommand = patch.vHold;
      }
    }
  } else if (index == 13U && noise.usePot) {
    noise.potRaw = adc::read(kNoisePotChannel, &valid);
    noise.potValid = valid;
    if (!valid) noise.sigma = 0.0f;
    else {
      const uint16_t filtered = noise.potFilter.update(noise.potRaw);
      noise.sigma = filtered <= 20U ? 0.0f : 15.0f * static_cast<float>(filtered - 20U) / 4075.0f;
    }
  } else if (index == 14U && ENABLE_PHOTODIODE && photodiode.useGainPot) {
    const uint16_t raw = adc::read(kPhotodiodeGainPotChannel, &valid);
    photodiode.gainPotValid = valid;
    photodiode.gain = valid ? bipolarControl(photodiode.gainFilter.update(raw), 2.0f) : 0.0f;
  } else if (index == 15U && brightnessFromPot) {
    const uint16_t raw = adc::read(kBrightnessPotChannel, &valid);
    if (valid) ledBrightnessPercent = static_cast<uint8_t>(
        (static_cast<uint32_t>(raw) * LED_MAX_BRIGHTNESS_PERCENT) / ADC_MAX);
  }
}

inline void serviceControlScanning(uint32_t nowUs) {
  if (static_cast<int32_t>(nowUs - nextControlScanUs) < 0) return;
  nextControlScanUs += CONTROL_SCAN_SLOT_US;
  if (controlScanIndex < SYNAPSE_COUNT) scanSynapseGainPot(controlScanIndex);
  else scanCentralControl(controlScanIndex);
  controlScanIndex = static_cast<uint8_t>((controlScanIndex + 1U) % 16U);
}

inline void updateExternalCurrent() {
  bool valid = false;
  const uint16_t raw = adc::read(kExternalCurrentChannel, &valid);
  patch.externalValid = valid;
  if (!valid || clampMode == ClampMode::VoltageClamp) {
    patch.externalCurrent = 0.0f;
    return;
  }
  const uint16_t filtered = patch.externalFilter.update(raw);
  patch.externalCurrent = bipolarControl(filtered, 50.0f, 80U);
}

inline void updatePhotodiode() {
  if (!ENABLE_PHOTODIODE) { photodiode.current = 0.0f; return; }
  bool valid = false;
  photodiode.raw = adc::read(kPhotodiodeChannel, &valid);
  if (!valid) { photodiode.current = 0.0f; return; }
  if (!photodiode.calibrated) {
    photodiode.darkAccumulator += photodiode.raw;
    ++photodiode.calibrationSamples;
    photodiode.current = 0.0f;
    if (photodiode.calibrationSamples >= 128U) {
      photodiode.darkCounts = static_cast<float>(photodiode.darkAccumulator) /
                              static_cast<float>(photodiode.calibrationSamples);
      photodiode.filtered = photodiode.darkCounts;
      photodiode.calibrated = true;
    }
    return;
  }
  photodiode.filtered += 0.10f * (static_cast<float>(photodiode.raw) - photodiode.filtered);
  const float effective = fmaxf(0.0f, photodiode.filtered - photodiode.darkCounts);
  const float normal = clampValue(effective / fmaxf(1.0f, photodiode.fullCounts), 0.0f, 1.0f);
  photodiode.current = normal * photodiode.fullCurrent * photodiode.gain * photodiode.adaptation;
  photodiode.adaptation -= photodiode.decayPerCurrent * fabsf(photodiode.current);
  photodiode.adaptation += photodiode.recovery * (1.0f - photodiode.adaptation);
  photodiode.adaptation = clampValue(photodiode.adaptation, 0.0f, 1.0f);
}

inline void updateVoltageClamp() {
  if (clampMode != ClampMode::VoltageClamp) {
    patch.integral = 0.0f;
    patch.clampCurrent = 0.0f;
    return;
  }
  const float error = patch.vCommand - neuron.v;
  const float proportional = patch.kp * error;
  const float unsaturated = proportional + patch.ki * patch.integral;
  const bool saturatedHigh = unsaturated > patch.currentMaximum;
  const bool saturatedLow = unsaturated < patch.currentMinimum;
  if ((!saturatedHigh && !saturatedLow) || (saturatedHigh && error < 0.0f) ||
      (saturatedLow && error > 0.0f)) patch.integral += error * MODEL_DT_MS;
  patch.clampCurrent = clampValue(proportional + patch.ki * patch.integral,
                                  patch.currentMinimum, patch.currentMaximum);
}

inline bool modelStep() {
  updateExternalCurrent();
  updatePhotodiode();
  const float synapticCurrent = updateAllSynapses();
  updateSynapseAnalogVm();
  noise.current = gaussianSample(noise.sigma);
  updateVoltageClamp();

  const float primaryCurrent = clampMode == ClampMode::VoltageClamp
      ? patch.clampCurrent : patch.currentCommand + patch.externalCurrent;
  neuron.totalCurrent = clampValue(primaryCurrent + photodiode.current +
                                   synapticCurrent + noise.current,
                                   TOTAL_CURRENT_MIN, TOTAL_CURRENT_MAX);
  stimulusState = static_cast<int16_t>(clampValue(lroundf(primaryCurrent), -32768L, 32767L));

  neuron.spike = false;
  neuron.v += MODEL_DT_MS * (0.04f * neuron.v * neuron.v + 5.0f * neuron.v +
                             140.0f - neuron.u + neuron.totalCurrent);
  neuron.u += MODEL_DT_MS * (neuron.a * (neuron.b * neuron.v - neuron.u));

  if (clampMode == ClampMode::CurrentClamp && neuron.v >= neuron.vmPeak) {
    neuron.vOut = neuron.vmPeak;
    neuron.v = neuron.c;
    neuron.u += neuron.d;
    neuron.spike = true;
  } else {
    if (!std::isfinite(neuron.v) || !std::isfinite(neuron.u)) resetNeuronDynamicState();
    neuron.v = clampValue(neuron.v, neuron.vmMin, neuron.vmPeak);
    neuron.vOut = neuron.v;
  }

  digitalWrite(kPins.axonDigital, neuron.spike ? HIGH : LOW);
  hardware::writeAxonVm(neuron.vOut, neuron.vmMin, neuron.vmMax);
  if (incomingMaskThisStep != 0U || neuron.spike) lastActivityMs = millis();
  return neuron.spike;
}

inline void recordModelExecution(uint32_t elapsedUs, uint32_t latenessUs) {
  if (elapsedUs > diagnostics.maximumModelExecutionUs) diagnostics.maximumModelExecutionUs = elapsedUs;
  if (latenessUs >= MODEL_STEP_US || elapsedUs >= MODEL_STEP_US) {
    ++diagnostics.modelOverruns;
    setStatusFlag(STATUS_MODEL_OVERRUN, true);
  }
}

}  // namespace bigspiky
