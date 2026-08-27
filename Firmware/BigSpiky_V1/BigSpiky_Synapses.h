/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Twelve interrupt-captured synapses for Big Spiky.
 * Derived from Open Source Neuro Spikeling V3.
 * Copyright (c) 2025-2026 Maxime Zimmermann and contributors.
 */
#pragma once

#include "BigSpiky_Adc.h"

namespace bigspiky {

struct Synapse {
  uint8_t digitalGpio = 0U;
  AdcChannel analogVmAdc = kNoAdcChannel;
  AdcChannel gainPotAdc = kNoAdcChannel;
  PotFilter gainFilter{};
  uint16_t rawPot = 0U;
  uint16_t filteredPot = POT_CENTRE;
  float gain = 0.0f;
  float decay = SYNAPSE_DEFAULT_DECAY;
  float current = 0.0f;
  bool enabled = true;
  bool usePot = true;
  bool reversePot = false;
  bool potValid = false;
  bool analogVmEnabled = false;
  uint8_t branch = 0U;
  uint8_t ring = 0U;
  uint16_t analogVmRaw = 0U;
  float analogVm = 0.0f;
  uint16_t eventsThisStep = 0U;
  float ledFlash = 0.0f;

  volatile uint8_t pendingEvents = 0U;
  volatile uint32_t incomingEventCount = 0U;
  volatile uint32_t lastEventUs = 0U;
  volatile uint32_t lastAcceptedUs = 0U;
  volatile uint32_t rejectedEventCount = 0U;
  volatile uint32_t lostEventCount = 0U;
};

inline Synapse synapses[SYNAPSE_COUNT];
inline portMUX_TYPE synapseMux = portMUX_INITIALIZER_UNLOCKED;
inline uint16_t incomingMaskThisStep = 0U;

inline void IRAM_ATTR synapseRisingIsr(void *argument) {
  Synapse *synapse = static_cast<Synapse *>(argument);
  const uint32_t nowUs = micros();
  portENTER_CRITICAL_ISR(&synapseMux);
  const uint32_t interval = nowUs - synapse->lastAcceptedUs;
  if (synapse->lastAcceptedUs != 0U && interval < DIGITAL_REFRACTORY_US) {
    ++synapse->rejectedEventCount;
    portEXIT_CRITICAL_ISR(&synapseMux);
    return;
  }
  synapse->lastAcceptedUs = nowUs;
  synapse->lastEventUs = nowUs;
  ++synapse->incomingEventCount;
  if (synapse->pendingEvents < MAX_PENDING_EVENTS) {
    ++synapse->pendingEvents;
  } else {
    ++synapse->lostEventCount;
    ++diagnostics.eventSaturations;
    diagnostics.statusFlags |= STATUS_EVENT_SATURATION;
  }
  portEXIT_CRITICAL_ISR(&synapseMux);
}

inline void beginSynapses() {
  for (std::size_t index = 0U; index < SYNAPSE_COUNT; ++index) {
    Synapse &synapse = synapses[index];
    synapse.digitalGpio = kPins.synapseDigital[index];
    synapse.analogVmAdc = kSynapseAnalogChannels[index];
    synapse.gainPotAdc = kSynapseGainChannels[index];
    synapse.gainFilter.alpha = 0.20f;
    synapse.gainFilter.deadband = 6U;
    synapse.gain = 0.0f;
    synapse.decay = SYNAPSE_DEFAULT_DECAY;
    synapse.current = 0.0f;
    synapse.enabled = true;
    synapse.usePot = true;
    synapse.reversePot = kReverseGainPot[index];
    synapse.potValid = false;
    synapse.analogVmEnabled = ENABLE_ANALOG_SYNAPSE_VM && synapse.analogVmAdc.valid();
    synapse.branch = kSynapseBranch[index];
    synapse.ring = kSynapseRingInBranch[index];
    pinMode(synapse.digitalGpio, INPUT_PULLDOWN);
    attachInterruptArg(digitalPinToInterrupt(synapse.digitalGpio), synapseRisingIsr,
                       &synapse, RISING);
  }
}

inline void scanSynapseGainPot(std::size_t index) {
  if (index >= SYNAPSE_COUNT) return;
  Synapse &synapse = synapses[index];
  if (!synapse.usePot) return;
  bool valid = false;
  const uint16_t raw = adc::read(synapse.gainPotAdc, &valid);
  synapse.rawPot = raw;
  if (!valid) {
    synapse.potValid = false;
    synapse.gain = 0.0f;
    return;
  }
  if (!synapse.gainFilter.initialized) synapse.gainFilter.reset(raw);
  synapse.filteredPot = synapse.gainFilter.update(raw);
  synapse.potValid = true;
  synapse.gain = mapBipolarGain(synapse.filteredPot, POT_CENTRE, POT_DEAD_ZONE,
                                SYNAPSE_GAIN_MAX, synapse.reversePot);
}

inline uint16_t snapshotPendingEvents() {
  uint16_t mask = 0U;
  portENTER_CRITICAL(&synapseMux);
  for (std::size_t index = 0U; index < SYNAPSE_COUNT; ++index) {
    synapses[index].eventsThisStep = synapses[index].pendingEvents;
    synapses[index].pendingEvents = 0U;
    if (synapses[index].eventsThisStep > 0U) mask |= static_cast<uint16_t>(1U << index);
  }
  portEXIT_CRITICAL(&synapseMux);
  incomingMaskThisStep = mask;
  return mask;
}

inline float updateAllSynapses() {
  snapshotPendingEvents();
  float sum = 0.0f;
  const float visualDecay = expf(-static_cast<float>(MODEL_STEP_US) /
                                  (1000.0f * static_cast<float>(SYNAPSE_FLASH_TAU_MS)));
  for (std::size_t index = 0U; index < SYNAPSE_COUNT; ++index) {
    Synapse &synapse = synapses[index];
    synapse.current = applySynapticEvents(synapse.current, synapse.gain,
                                          synapse.eventsThisStep, synapse.decay,
                                          SYNAPSE_CURRENT_MIN, SYNAPSE_CURRENT_MAX,
                                          synapse.enabled);
    if (synapse.eventsThisStep > 0U) synapse.ledFlash = 1.0f;
    else synapse.ledFlash *= visualDecay;
    if (synapse.ledFlash < 0.002f) synapse.ledFlash = 0.0f;
    sum += synapse.current;
  }
  return clampValue(sum * SYNAPTIC_GLOBAL_SCALE,
                    TOTAL_CURRENT_MIN, TOTAL_CURRENT_MAX);
}

inline void updateSynapseAnalogVm() {
  for (std::size_t index = 0U; index < SYNAPSE_COUNT; ++index) {
    Synapse &synapse = synapses[index];
    if (!synapse.analogVmEnabled) { synapse.analogVm = 0.0f; continue; }
    bool valid = false;
    synapse.analogVmRaw = adc::read(synapse.analogVmAdc, &valid);
    synapse.analogVm = valid
      ? VM_MIN + (static_cast<float>(synapse.analogVmRaw) / static_cast<float>(ADC_MAX)) * (VM_MAX - VM_MIN)
      : 0.0f;
  }
}

inline void setSynapseEnabled(std::size_t index, bool enabled) {
  if (index >= SYNAPSE_COUNT) return;
  synapses[index].enabled = enabled;
  if (!enabled) synapses[index].current = 0.0f;
}

inline void resetSynapticState() {
  portENTER_CRITICAL(&synapseMux);
  for (std::size_t index = 0U; index < SYNAPSE_COUNT; ++index) {
    synapses[index].pendingEvents = 0U;
    synapses[index].current = 0.0f;
    synapses[index].eventsThisStep = 0U;
    synapses[index].ledFlash = 0.0f;
  }
  portEXIT_CRITICAL(&synapseMux);
}

}  // namespace bigspiky

