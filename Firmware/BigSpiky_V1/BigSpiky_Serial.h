/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Backward-aware serial commands and binary protocols for Big Spiky.
 * Derived from Open Source Neuro Spikeling V3.
 * Copyright (c) 2025-2026 Maxime Zimmermann and contributors.
 */
#pragma once

#include <cstring>
#include "BigSpiky_Leds.h"
#include "BigSpiky_Protocol.h"

namespace bigspiky::serial {

enum class ProtocolMode : uint8_t { Legacy = 1U, Extended = 2U };
inline ProtocolMode protocolMode = ProtocolMode::Legacy;
inline uint32_t packetSequence = 0U;
inline uint8_t extendedDecimationCounter = 0U;
inline constexpr uint8_t EXTENDED_DECIMATION = 5U;
inline char lineBuffer[160];
inline uint16_t lineLength = 0U;
inline bool discardingLine = false;

inline int16_t quantise(float value, float scale = 100.0f) {
  if (!std::isfinite(value)) return 0;
  const float scaled = value * scale;
  if (scaled > 32767.0f) return 32767;
  if (scaled < -32768.0f) return -32768;
  return static_cast<int16_t>(scaled >= 0.0f ? scaled + 0.5f : scaled - 0.5f);
}

inline void sendLegacyPacket() {
  LegacySamplePacket packet{};
  packet.v_q = quantise(neuron.vOut);
  packet.stim_state = stimulusState;
  packet.Itot_q = quantise(clampMode == ClampMode::VoltageClamp
                           ? patch.clampCurrent : neuron.totalCurrent);
  packet.syn1_vm_q = quantise(synapses[0].analogVm);
  packet.Isyn1_q = quantise(synapses[0].current);
  packet.syn2_vm_q = quantise(synapses[1].analogVm);
  packet.Isyn2_q = quantise(synapses[1].current);
  packet.trigger_q = triggerState;
  Serial.write(kLegacyHeader, sizeof(kLegacyHeader));
  Serial.write(reinterpret_cast<const uint8_t *>(&packet), sizeof(packet));
}

inline void sendExtendedPacket(uint32_t timestampUs) {
  ExtendedPacketV2 packet{};
  memcpy(packet.sync, kExtendedHeader, sizeof(packet.sync));
  packet.version = kExtendedProtocolVersion;
  packet.flags = 0U;
  packet.payload_length = kExtendedPayloadLength;
  packet.sequence = packetSequence++;
  packet.timestamp_us = timestampUs;
  packet.vm_q = quantise(neuron.vOut);
  packet.total_current_q = quantise(neuron.totalCurrent);
  packet.output_spike = neuron.spike ? 1U : 0U;
  packet.incoming_spike_mask = incomingMaskThisStep;
  for (std::size_t index = 0U; index < SYNAPSE_COUNT; ++index) {
    packet.gains_q[index] = quantise(synapses[index].gain);
    packet.synaptic_currents_q[index] = quantise(synapses[index].current);
  }
  packet.current_control_q = quantise(patch.currentCommand + patch.externalCurrent);
  packet.noise_control_q = quantise(noise.sigma);
  packet.trigger_state = triggerState;
  packet.status_flags = statusFlagsSnapshot();
  const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&packet);
  packet.crc16 = crc16CcittFalse(bytes + kExtendedCrcOffset, kExtendedCrcLength);
  Serial.write(bytes, sizeof(packet));
}

inline void sendTelemetry(uint32_t timestampUs) {
  if (protocolMode == ProtocolMode::Legacy) sendLegacyPacket();
  else if (++extendedDecimationCounter >= EXTENDED_DECIMATION) {
    extendedDecimationCounter = 0U;
    sendExtendedPacket(timestampUs);
  }
  triggerState = 0U;
}

inline void error(const char *message) {
  diagnostics.serialCommandErrors = diagnostics.serialCommandErrors + 1U;
  Serial.print("#BSERR ");
  Serial.println(message);
}

inline void ok(const char *command) {
  Serial.print("#BSOK ");
  Serial.println(command);
}

inline bool exactCount(uint8_t count, uint8_t expected) {
  if (count == expected) return true;
  error("incomplete-or-extra-arguments");
  return false;
}

inline bool parseIndex(const char *token, std::size_t &index) {
  long parsed = 0;
  if (!parseLongStrict(token, 1L, static_cast<long>(SYNAPSE_COUNT), parsed)) {
    error("index-must-be-1..12");
    return false;
  }
  index = static_cast<std::size_t>(parsed - 1L);
  return true;
}

inline void printStatus() {
  Serial.print("#BSSTATUS proto="); Serial.print(static_cast<uint8_t>(protocolMode));
  Serial.print(" model="); Serial.print(neuron.selectedModel);
  Serial.print(" clamp="); Serial.print(static_cast<uint8_t>(clampMode));
  Serial.print(" flags=0x"); Serial.print(statusFlagsSnapshot(), HEX);
  Serial.print(" overruns="); Serial.print(diagnostics.modelOverruns);
  Serial.print(" max_us="); Serial.print(diagnostics.maximumModelExecutionUs);
  Serial.print(" serial_errors="); Serial.print(diagnostics.serialCommandErrors);
  Serial.print(" serial_overflows="); Serial.print(diagnostics.serialOverflowErrors);
  Serial.print(" adc_fault_mask=0x"); Serial.print(adc::faultMask, HEX);
  Serial.print(" event_saturations="); Serial.print(diagnostics.eventSaturations);
  Serial.print(" visual_drops="); Serial.print(diagnostics.visualQueueDrops);
  Serial.print(" led_est_ma="); Serial.print(leds::lastEstimatedCurrentMa);
  Serial.print(" brightness="); Serial.print(ledBrightnessPercent);
  Serial.println();
}

inline bool handleBigSpikyCommand(char **tokens, uint8_t count) {
  const char *command = tokens[0];
  if (strcmp(command, "BSG") == 0) {
    if (!exactCount(count, 3U)) return true;
    std::size_t index = 0U; float gain;
    if (!parseIndex(tokens[1], index)) return true;
    if (!parseFloatStrict(tokens[2], -SYNAPSE_GAIN_MAX, SYNAPSE_GAIN_MAX, gain)) {
      error("gain-out-of-range-or-non-finite"); return true;
    }
    synapses[index].gain = gain;
    synapses[index].usePot = false;
    lastActivityMs = millis();
    ok("BSG"); return true;
  }
  if (strcmp(command, "BSD") == 0) {
    if (!exactCount(count, 3U)) return true;
    std::size_t index; float decay;
    if (!parseIndex(tokens[1], index)) return true;
    if (!parseFloatStrict(tokens[2], 0.0f, 1.0f, decay)) { error("decay-must-be-0..1"); return true; }
    synapses[index].decay = decay;
    ok("BSD"); return true;
  }
  if (strcmp(command, "BSPOT") == 0 || strcmp(command, "BSEN") == 0) {
    if (!exactCount(count, 3U)) return true;
    std::size_t index; long enabled;
    if (!parseIndex(tokens[1], index)) return true;
    if (!parseLongStrict(tokens[2], 0L, 1L, enabled)) { error("state-must-be-0-or-1"); return true; }
    if (strcmp(command, "BSPOT") == 0) synapses[index].usePot = enabled != 0L;
    else setSynapseEnabled(index, enabled != 0L);
    ok(command); return true;
  }
  if (strcmp(command, "BSBRI") == 0) {
    if (!exactCount(count, 2U)) return true;
    long percent;
    if (!parseLongStrict(tokens[1], 0L, 100L, percent)) { error("brightness-must-be-0..100"); return true; }
    ledBrightnessPercent = static_cast<uint8_t>(clampValue<long>(percent, 0L, LED_MAX_BRIGHTNESS_PERCENT));
    brightnessFromPot = false;
    ok("BSBRI"); return true;
  }
  if (strcmp(command, "BSPROTO") == 0) {
    if (!exactCount(count, 2U)) return true;
    long protocol;
    if (!parseLongStrict(tokens[1], 1L, 2L, protocol)) { error("protocol-must-be-1-or-2"); return true; }
    protocolMode = static_cast<ProtocolMode>(protocol);
    packetSequence = 0U;
    extendedDecimationCounter = 0U;
    ok("BSPROTO"); return true;
  }
  if (strcmp(command, "BSSTATUS") == 0) {
    if (!exactCount(count, 1U)) return true;
    printStatus(); return true;
  }
  if (strcmp(command, "BSSELFTEST") == 0) {
    if (!exactCount(count, 1U)) return true;
    leds::startSelfTest();
    ok("BSSELFTEST"); return true;
  }
  return false;
}

inline bool floatArgument(char **tokens, uint8_t count, float minimum, float maximum, float &value) {
  return exactCount(count, 2U) && parseFloatStrict(tokens[1], minimum, maximum, value);
}

inline bool handleLegacyCommand(char **tokens, uint8_t count) {
  const char *command = tokens[0];
  if (strcmp(command, "DT") == 0) {
    long period;
    if (!exactCount(count, 2U) || !parseLongStrict(tokens[1], MODEL_STEP_US, MODEL_STEP_US, period))
      error("exhibition-profile-DT-is-fixed-at-2000");
    return true;
  }
  if (strcmp(command, "NEU") == 0) {
    long index;
    if (!exactCount(count, 2U) || !parseLongStrict(tokens[1], 0L,
        static_cast<long>(kIzhikevichModelCount - 1U), index) ||
        !selectNeuronPreset(static_cast<uint8_t>(index))) error("invalid-neuron-preset");
    return true;
  }
  if (strcmp(command, "NE") == 0) {
    if (!exactCount(count, 5U)) return true;
    float a,b,c,d;
    if (!parseFloatStrict(tokens[1],0.0f,2.0f,a) || !parseFloatStrict(tokens[2],-2.0f,2.0f,b) ||
        !parseFloatStrict(tokens[3],VM_MIN,VM_PEAK,c) || !parseFloatStrict(tokens[4],-100.0f,100.0f,d) ||
        !applyNeuronParameters(a,b,c,d,neuron.vRest,-1,true)) error("invalid-custom-neuron");
    return true;
  }
  float value = 0.0f;
  if (strcmp(command, "PC1") == 0) {
    if (floatArgument(tokens,count,-300.0f,300.0f,value)) {
      patch.usePot = false;
      if (clampMode == ClampMode::VoltageClamp) { patch.vHold = value; patch.vCommand = value; patch.integral = 0.0f; }
      else patch.currentCommand = value;
    } else error("invalid-PC1");
    return true;
  }
  if (strcmp(command, "PC0") == 0) { if (exactCount(count,1U)) patch.usePot = true; return true; }
  if (strcmp(command, "NO1") == 0) {
    if (floatArgument(tokens,count,0.0f,50.0f,value)) { noise.usePot = false; noise.sigma = value; }
    else error("invalid-NO1");
    return true;
  }
  if (strcmp(command, "NO0") == 0) { if (exactCount(count,1U)) noise.usePot = true; return true; }
  if (strcmp(command, "PG1") == 0) {
    if (floatArgument(tokens,count,-100.0f,100.0f,value)) { photodiode.useGainPot = false; photodiode.gain = value * 0.1f; }
    else error("invalid-PG1");
    return true;
  }
  if (strcmp(command, "PG0") == 0) { if (exactCount(count,1U)) photodiode.useGainPot = true; return true; }
  if (strcmp(command, "PD1") == 0) {
    if (floatArgument(tokens,count,0.0f,1.0f,value)) photodiode.decayPerCurrent=value;
    else error("invalid-PD1");
    return true;
  }
  if (strcmp(command, "PD0") == 0) {
    if (exactCount(count,1U)) photodiode.decayPerCurrent=0.001f;
    return true;
  }
  if (strcmp(command, "PR1") == 0) {
    if (floatArgument(tokens,count,0.0f,1.0f,value)) photodiode.recovery=value;
    else error("invalid-PR1");
    return true;
  }
  if (strcmp(command, "PR0") == 0) {
    if (exactCount(count,1U)) photodiode.recovery=0.025f;
    return true;
  }
  if (strcmp(command, "VCM") == 0) {
    long mode;
    if (exactCount(count,2U) && parseLongStrict(tokens[1],0L,1L,mode)) setClampMode(mode ? ClampMode::VoltageClamp : ClampMode::CurrentClamp);
    else error("invalid-VCM");
    return true;
  }
  if (strcmp(command, "VPID") == 0) {
    float kp,ki;
    if (exactCount(count,3U) && parseFloatStrict(tokens[1],0.0f,100.0f,kp) &&
        parseFloatStrict(tokens[2],0.0f,10.0f,ki)) { patch.kp=kp; patch.ki=ki; }
    else error("invalid-VPID");
    return true;
  }
  if (strcmp(command, "VIL") == 0) {
    float minimum,maximum;
    if (exactCount(count,3U) && parseFloatStrict(tokens[1],-500.0f,500.0f,minimum) &&
        parseFloatStrict(tokens[2],-500.0f,500.0f,maximum) && minimum < maximum) {
      patch.currentMinimum=minimum; patch.currentMaximum=maximum;
    } else error("invalid-VIL");
    return true;
  }
  if (strcmp(command, "VSP") == 0) {
    if (floatArgument(tokens,count,0.0f,140.0f,value)) patch.vCommandSpan=value;
    else error("invalid-VSP");
    return true;
  }
  if (strcmp(command, "VRS") == 0) { if (exactCount(count,1U)) { patch.integral=0.0f; patch.clampCurrent=0.0f; } return true; }
  if (strcmp(command, "SG11") == 0 || strcmp(command, "SG21") == 0) {
    const std::size_t index = command[2] == '1' ? 0U : 1U;
    if (floatArgument(tokens,count,-80.0f,80.0f,value)) { synapses[index].usePot=false; synapses[index].gain=value*0.25f; }
    else error("invalid-legacy-synaptic-gain");
    return true;
  }
  if (strcmp(command, "SG10") == 0 || strcmp(command, "SG20") == 0) {
    if (exactCount(count,1U)) synapses[command[2]=='1'?0U:1U].usePot=true;
    return true;
  }
  if (strcmp(command, "SD11") == 0 || strcmp(command, "SD21") == 0) {
    const std::size_t index = command[2] == '1' ? 0U : 1U;
    if (floatArgument(tokens,count,0.0f,1000.0f,value)) synapses[index].decay=value*0.001f;
    else error("invalid-legacy-synaptic-decay");
    return true;
  }
  if (strcmp(command, "SD10") == 0 || strcmp(command, "SD20") == 0) {
    if (exactCount(count,1U)) synapses[command[2]=='1'?0U:1U].decay=SYNAPSE_DEFAULT_DECAY;
    return true;
  }
  if (strcmp(command, "TR") == 0) { if (exactCount(count,1U)) triggerState=1U; return true; }
  if (strcmp(command, "FR1") == 0 || strcmp(command, "ST1") == 0 || strcmp(command, "SC1") == 0) {
    if (floatArgument(tokens,count,-32768.0f,32767.0f,value)) stimulusState=static_cast<int16_t>(lroundf(value));
    else error("invalid-legacy-stimulus-command");
    return true;
  }
  if (strcmp(command, "FR0") == 0 || strcmp(command, "ST0") == 0 || strcmp(command, "SC0") == 0) {
    if (exactCount(count,1U)) stimulusState=0;
    return true;
  }
  if (strcmp(command, "LED1") == 0 || strcmp(command, "LED0") == 0) {
    if (exactCount(count,1U)) leds::softwareEnabled = command[3] == '1';
    return true;
  }
  if (strcmp(command, "BZ1") == 0 || strcmp(command, "BZ0") == 0) return exactCount(count,1U);
  if (strcmp(command, "CON") == 0) { if (exactCount(count,1U)) leds::showConnectedPulse(); return true; }
  return false;
}

inline void processLine(char *line) {
  char *tokens[8]{};
  uint8_t count = 0U;
  char *save = nullptr;
  for (char *token = strtok_r(line, " \t", &save); token != nullptr && count < 8U;
       token = strtok_r(nullptr, " \t", &save)) tokens[count++] = token;
  if (count == 0U) return;
  if (handleBigSpikyCommand(tokens, count)) return;
  if (handleLegacyCommand(tokens, count)) return;
  error("unknown-command");
}

inline void serviceInput() {
  while (Serial.available() > 0) {
    const char character = static_cast<char>(Serial.read());
    if (character == '\r') continue;
    if (character == '\n') {
      if (discardingLine) {
        discardingLine = false;
        lineLength = 0U;
        error("line-too-long");
      } else if (lineLength > 0U) {
        lineBuffer[lineLength] = '\0';
        processLine(lineBuffer);
        lineLength = 0U;
      }
      continue;
    }
    if (discardingLine) continue;
    if (lineLength + 1U >= sizeof(lineBuffer)) {
      discardingLine = true;
      diagnostics.serialOverflowErrors = diagnostics.serialOverflowErrors + 1U;
      setStatusFlag(STATUS_SERIAL_OVERFLOW, true);
      continue;
    }
    lineBuffer[lineLength++] = character;
  }
}

}  // namespace bigspiky::serial
