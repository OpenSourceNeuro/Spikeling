#pragma once
#include <cstdint>
#define NEO_GRB 1
#define NEO_KHZ800 2
class Adafruit_NeoPixel {
 public:
  Adafruit_NeoPixel(uint16_t, uint8_t, int) {}
  void begin() {}
  void clear() {}
  void show() {}
  void setPixelColor(uint16_t, uint8_t, uint8_t, uint8_t) {}
};

