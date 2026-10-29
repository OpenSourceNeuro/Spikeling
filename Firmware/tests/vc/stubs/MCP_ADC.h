#pragma once
#include <cstdint>
struct MCP3208 {
  unsigned channels[8]={2048,2048,2048,2048,2048,2048,2048,2048};
  void begin(int){}
  uint16_t read(unsigned channel){return channels[channel];}
};
