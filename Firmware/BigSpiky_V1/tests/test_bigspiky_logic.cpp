/* SPDX-License-Identifier: GPL-3.0-or-later */
#include <cmath>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

#include "../BigSpiky_Config.h"
#include "../BigSpiky_Logic.h"
#include "../BigSpiky_Protocol.h"

using namespace bigspiky;

namespace {
void require(bool condition, const std::string &name) {
  if (!condition) throw std::runtime_error(name);
  std::cout << "PASS " << name << '\n';
}
bool close(float a, float b, float tolerance = 1.0e-4f) {
  return std::fabs(a - b) <= tolerance;
}
}

int main() {
  for (std::size_t channel = 0; channel < SYNAPSE_COUNT; ++channel) {
    const bool reverse = kReverseGainPot[channel];
    const float minimum = mapBipolarGain(0U, POT_CENTRE, POT_DEAD_ZONE, SYNAPSE_GAIN_MAX, reverse);
    const float centre = mapBipolarGain(POT_CENTRE, POT_CENTRE, POT_DEAD_ZONE, SYNAPSE_GAIN_MAX, reverse);
    const float maximum = mapBipolarGain(ADC_MAX, POT_CENTRE, POT_DEAD_ZONE, SYNAPSE_GAIN_MAX, reverse);
    require(close(centre, 0.0f), "pot-centre-zero-ch" + std::to_string(channel + 1));
    require(reverse ? minimum > 0.0f : minimum < 0.0f,
            "pot-minimum-sign-ch" + std::to_string(channel + 1));
    require(reverse ? maximum < 0.0f : maximum > 0.0f,
            "pot-maximum-sign-ch" + std::to_string(channel + 1));
  }

  require(close(applySynapticEvents(0.0f, 10.0f, 1U, 0.9f, -80.0f, 80.0f), 9.0f),
          "single-excitatory-spike");
  require(close(applySynapticEvents(0.0f, -10.0f, 1U, 0.9f, -80.0f, 80.0f), -9.0f),
          "single-inhibitory-spike");
  require(close(applySynapticEvents(0.0f, 2.0f, 4U, 1.0f, -80.0f, 80.0f), 8.0f),
          "multiple-events-between-model-steps");

  float simultaneous = 0.0f;
  for (std::size_t i = 0; i < SYNAPSE_COUNT; ++i)
    simultaneous += applySynapticEvents(0.0f, 1.0f, 1U, 1.0f, -80.0f, 80.0f);
  require(close(simultaneous, 12.0f), "simultaneous-events-all-twelve");

  const float fast = applySynapticEvents(10.0f, 0.0f, 0U, 0.5f, -80.0f, 80.0f);
  const float slow = applySynapticEvents(10.0f, 0.0f, 0U, 0.9f, -80.0f, 80.0f);
  require(close(fast, 5.0f) && close(slow, 9.0f), "independent-decay");

  const float mixed = applySynapticEvents(0.0f, 8.0f, 1U, 1.0f, -80.0f, 80.0f) +
                      applySynapticEvents(0.0f, -3.0f, 2U, 1.0f, -80.0f, 80.0f);
  require(close(mixed, 2.0f), "mixed-excitation-inhibition");
  require(close(applySynapticEvents(79.0f, 20.0f, 20U, 1.0f, -80.0f, 80.0f), 80.0f),
          "synaptic-current-upper-bound");
  require(close(applySynapticEvents(10.0f, 5.0f, 1U, 0.9f, -80.0f, 80.0f, false), 0.0f),
          "disabled-input-clears-current");
  require(close(applySynapticEvents(std::numeric_limits<float>::quiet_NaN(), 5.0f, 1U, 0.9f,
                                    -80.0f, 80.0f), 0.0f),
          "non-finite-current-contained");

  require(sizeof(LegacySamplePacket) == 16U, "legacy-payload-size-16");
  require(offsetof(LegacySamplePacket, trigger_q) == 14U, "legacy-field-order");
  require(sizeof(ExtendedPacketV2) == 82U && kExtendedPayloadLength == 74U,
          "extended-framing-layout");
  const char *crcVector = "123456789";
  require(crc16CcittFalse(reinterpret_cast<const uint8_t *>(crcVector), std::strlen(crcVector)) == 0x29B1U,
          "crc16-ccitt-false-known-vector");

  long integer = 0;
  float number = 0.0f;
  require(!parseLongStrict("13", 1, 12, integer) && !parseLongStrict("1x", 1, 12, integer) &&
          !parseFloatStrict("nan", -20.0f, 20.0f, number) &&
          !parseFloatStrict("21", -20.0f, 20.0f, number),
          "invalid-command-arguments-rejected");
  require(parseLongStrict("12", 1, 12, integer) && integer == 12 &&
          parseFloatStrict("-12.5", -20.0f, 20.0f, number) && close(number, -12.5f),
          "valid-command-arguments-accepted");

  require(close(normaliseVm(VM_MIN, VM_MIN, VM_PEAK), 0.0f) &&
          close(normaliseVm(VM_PEAK, VM_MIN, VM_PEAK), 1.0f) &&
          normaliseVm(-40.0f, VM_MIN, VM_PEAK) > normaliseVm(-70.0f, VM_MIN, VM_PEAK),
          "soma-vm-mapping-monotonic");

  AxonQueueState axon;
  axon.capacity = 4U;
  require(axon.enqueue(true) && !axon.enqueue(false), "axon-launch-only-on-one-shot-event");
  axon.service(100U, 350U);
  for (int i = 0; i < 100; ++i) axon.enqueue(false);
  axon.service(451U, 350U);
  require(axon.launched == 1U && !axon.active && axon.queued == 0U,
          "one-axon-animation-per-model-spike");

  Rgb8 pixels[TOTAL_PIXELS];
  for (Rgb8 &pixel : pixels) pixel = {255U, 255U, 255U};
  const uint32_t worstCase = estimateWs2812CurrentMa(pixels, TOTAL_PIXELS);
  const uint8_t limitScale = currentLimitScale255(worstCase, LED_HARD_CURRENT_MA);
  require(worstCase == 10800U && limitScale < 255U && limitScale > 0U,
          "led-current-limiter");

  SelfTestState test;
  test.start(0U, SELF_TEST_STAGE_COUNT);
  for (uint8_t stage = 0U; stage < SELF_TEST_STAGE_COUNT; ++stage)
    test.service(static_cast<uint32_t>(stage + 1U) * SELF_TEST_STAGE_MS, SELF_TEST_STAGE_MS);
  require(!test.active && test.stage == SELF_TEST_STAGE_COUNT,
          "self-test-completes-without-model-blocking");

  std::cout << "ALL FUNCTIONAL TESTS PASSED\n";
  return 0;
}

