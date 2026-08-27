/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Big Spiky serial packet definitions.
 * Copyright (c) 2025-2026 Maxime Zimmermann and contributors.
 */
#pragma once

#include <cstddef>
#include <cstdint>

namespace bigspiky {

inline constexpr uint8_t kLegacyHeader[2] = {0xAAU, 0x55U};
inline constexpr uint8_t kExtendedHeader[4] = {0x42U, 0x53U, 0x50U, 0x4BU};  // BSPK
inline constexpr uint8_t kExtendedProtocolVersion = 2U;

struct __attribute__((packed)) LegacySamplePacket {
  int16_t v_q;
  int16_t stim_state;
  int16_t Itot_q;
  int16_t syn1_vm_q;
  int16_t Isyn1_q;
  int16_t syn2_vm_q;
  int16_t Isyn2_q;
  int16_t trigger_q;
};
static_assert(sizeof(LegacySamplePacket) == 16U, "Legacy payload must remain exactly 16 bytes");

struct __attribute__((packed)) ExtendedPacketV2 {
  uint8_t sync[4];
  uint8_t version;
  uint8_t flags;
  uint16_t payload_length;
  uint32_t sequence;
  uint32_t timestamp_us;
  int16_t vm_q;
  int16_t total_current_q;
  uint8_t output_spike;
  uint16_t incoming_spike_mask;
  int16_t gains_q[12];
  int16_t synaptic_currents_q[12];
  int16_t current_control_q;
  int16_t noise_control_q;
  uint8_t trigger_state;
  uint32_t status_flags;
  uint16_t crc16;
};
static_assert(sizeof(ExtendedPacketV2) == 82U, "Extended V2 packet layout changed");
inline constexpr uint16_t kExtendedPayloadLength = sizeof(ExtendedPacketV2) - 8U;
inline constexpr std::size_t kExtendedCrcOffset = offsetof(ExtendedPacketV2, version);
inline constexpr std::size_t kExtendedCrcLength =
    offsetof(ExtendedPacketV2, crc16) - kExtendedCrcOffset;

}  // namespace bigspiky

