/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Big Spiky compile-time configuration and audited reference pin map.
 * Derived from Open Source Neuro Spikeling V3.
 * Copyright (c) 2025-2026 Maxime Zimmermann and contributors.
 */
#pragma once

#include <cstddef>
#include <cstdint>
#include "Izhikevich_parameters.h"

#ifndef BIGSPIKY_ADC_PROFILE
#define BIGSPIKY_ADC_PROFILE 3
#endif

namespace bigspiky {

inline constexpr std::size_t SYNAPSE_COUNT = 12U;
inline constexpr uint8_t ADC_DEVICE_COUNT = BIGSPIKY_ADC_PROFILE;
static_assert(ADC_DEVICE_COUNT == 3U || ADC_DEVICE_COUNT == 4U,
              "BIGSPIKY_ADC_PROFILE must be 3 or 4");

struct AdcChannel {
  uint8_t device;
  uint8_t channel;
  constexpr bool valid() const { return device < ADC_DEVICE_COUNT && channel < 8U; }
};
inline constexpr AdcChannel kNoAdcChannel{0xFFU, 0xFFU};

struct PinMap {
  uint8_t spiSck;
  uint8_t spiMosi;
  uint8_t spiMiso;
  uint8_t adcCs[4];
  uint8_t dacCs;
  uint8_t synapseDigital[SYNAPSE_COUNT];
  uint8_t axonDigital;
  uint8_t ledData[6];
  uint8_t ledDisableSwitch;
  uint8_t selfTestButton;
};

inline constexpr PinMap kPins{
  12U, 11U, 13U,
  {21U, 38U, 39U, 40U},
  41U,
  {1U, 2U, 4U, 5U, 6U, 7U, 8U, 9U, 14U, 15U, 16U, 17U},
  18U,
  {33U, 34U, 35U, 36U, 37U, 42U},
  43U,
  44U
};

inline constexpr AdcChannel kSynapseGainChannels[SYNAPSE_COUNT] = {
  {0U,0U},{0U,1U},{0U,2U},{0U,3U},{0U,4U},{0U,5U},{0U,6U},{0U,7U},
  {1U,0U},{1U,1U},{1U,2U},{1U,3U}
};

#if BIGSPIKY_ADC_PROFILE == 3
inline constexpr AdcChannel kSynapseAnalogChannels[SYNAPSE_COUNT] = {
  {2U,0U},{2U,1U},kNoAdcChannel,kNoAdcChannel,kNoAdcChannel,kNoAdcChannel,
  kNoAdcChannel,kNoAdcChannel,kNoAdcChannel,kNoAdcChannel,kNoAdcChannel,kNoAdcChannel
};
inline constexpr AdcChannel kExternalCurrentChannel{2U,2U};
inline constexpr AdcChannel kPhotodiodeChannel{2U,3U};
#else
inline constexpr AdcChannel kSynapseAnalogChannels[SYNAPSE_COUNT] = {
  {2U,0U},{2U,1U},{2U,2U},{2U,3U},{2U,4U},{2U,5U},{2U,6U},{2U,7U},
  {3U,0U},{3U,1U},{3U,2U},{3U,3U}
};
inline constexpr AdcChannel kExternalCurrentChannel{3U,4U};
inline constexpr AdcChannel kPhotodiodeChannel{3U,5U};
#endif
inline constexpr AdcChannel kPatchPotChannel{1U,4U};
inline constexpr AdcChannel kNoisePotChannel{1U,5U};
inline constexpr AdcChannel kPhotodiodeGainPotChannel{1U,6U};
inline constexpr AdcChannel kBrightnessPotChannel{1U,7U};

inline constexpr bool kReverseGainPot[SYNAPSE_COUNT] = {
  false,false,false,false,false,false,false,false,false,false,false,false
};
inline constexpr uint8_t kSynapseBranch[SYNAPSE_COUNT] = {
  0U,0U,0U,1U,1U,1U,2U,2U,2U,3U,3U,3U
};
inline constexpr uint8_t kSynapseRingInBranch[SYNAPSE_COUNT] = {
  0U,1U,2U,0U,1U,2U,0U,1U,2U,0U,1U,2U
};

inline constexpr uint32_t SERIAL_BAUD = 500000UL;
inline constexpr uint32_t MODEL_STEP_US = 2000UL;
inline constexpr float MODEL_DT_MS = 0.1f;
inline constexpr uint32_t CONTROL_SCAN_SLOT_US = 500UL;
inline constexpr uint32_t DIGITAL_REFRACTORY_US = 1500UL;
inline constexpr uint8_t MAX_PENDING_EVENTS = 255U;
inline constexpr float SYNAPSE_GAIN_MAX = 20.0f;
inline constexpr float SYNAPSE_CURRENT_MIN = -80.0f;
inline constexpr float SYNAPSE_CURRENT_MAX = 80.0f;
inline constexpr float SYNAPSE_DEFAULT_DECAY = 0.995f;
inline constexpr float SYNAPTIC_GLOBAL_SCALE = 0.75f;
inline constexpr float TOTAL_CURRENT_MIN = -300.0f;
inline constexpr float TOTAL_CURRENT_MAX = 300.0f;
inline constexpr uint16_t ADC_MAX = 4095U;
inline constexpr uint16_t POT_CENTRE = 2048U;
inline constexpr uint16_t POT_DEAD_ZONE = 260U;
inline constexpr uint16_t ADC_RAIL_MARGIN = 8U;
inline constexpr uint16_t ADC_RAIL_FAULT_SAMPLES = 32U;
inline constexpr uint32_t MCP3208_SPI_HZ = 1800000UL;
inline constexpr uint32_t MCP4922_SPI_HZ = 10000000UL;
inline constexpr uint8_t MCP4922_AXON_CHANNEL = 0U;

inline constexpr uint16_t RING_PIXELS = 8U;
inline constexpr uint16_t RINGS_PER_BRANCH = 3U;
inline constexpr uint16_t BRANCH_PIXELS = RING_PIXELS * RINGS_PER_BRANCH;
inline constexpr uint16_t SOMA_PIXELS = 24U;
inline constexpr uint16_t AXON_PIXELS = 60U;
inline constexpr uint16_t TOTAL_PIXELS = 4U * BRANCH_PIXELS + SOMA_PIXELS + AXON_PIXELS;
inline constexpr uint8_t LED_DEFAULT_BRIGHTNESS_PERCENT = 25U;
inline constexpr uint8_t LED_MAX_BRIGHTNESS_PERCENT = 30U;
inline constexpr uint32_t LED_HARD_CURRENT_MA = 3000UL;
inline constexpr uint32_t LED_FRAME_MS = 25UL;
inline constexpr uint32_t SYNAPSE_FLASH_TAU_MS = 150UL;
inline constexpr uint32_t AXON_TRAVEL_MS = 350UL;
inline constexpr uint8_t AXON_VISUAL_QUEUE_DEPTH = 4U;
inline constexpr uint32_t SELF_TEST_STAGE_MS = 500UL;
inline constexpr uint8_t SELF_TEST_STAGE_COUNT = 18U;  // 12 rings + 4 branches + soma + axon
inline constexpr uint32_t ACTIVITY_TIMEOUT_MS = 300000UL;

inline constexpr bool ENABLE_PHOTODIODE = true;
inline constexpr bool ENABLE_ANALOG_SYNAPSE_VM = true;
inline constexpr bool ENABLE_ACTIVITY_TIMEOUT = true;
inline constexpr bool USE_BRIGHTNESS_POT = false;

inline constexpr IzhikevichModel DEFAULT_MODEL = IzhikevichModel::TonicSpiking;
inline constexpr float VM_MIN = -110.0f;
inline constexpr float VM_MAX = 100.0f;
inline constexpr float VM_SPIKE = -30.0f;
inline constexpr float VM_PEAK = 30.0f;

static_assert(SYNAPSE_COUNT == 12U, "Protocol and hardware assume twelve synapses");
static_assert(RING_PIXELS == 8U, "Reference ring map assumes eight pixels");
static_assert(TOTAL_PIXELS == 180U, "Update power budget when pixel count changes");

}  // namespace bigspiky

