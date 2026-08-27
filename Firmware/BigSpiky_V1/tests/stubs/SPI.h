#pragma once
#include <cstdint>
#define MSBFIRST 1
#define SPI_MODE0 0
class SPISettings { public: SPISettings(uint32_t, int, int) {} };
class SPIClass {
 public:
  void begin(uint8_t,uint8_t,uint8_t,int) {}
  void beginTransaction(const SPISettings &) {}
  void endTransaction() {}
  uint8_t transfer(uint8_t value) { return value; }
  uint16_t transfer16(uint16_t value) { return value; }
};
inline SPIClass SPI;

