#pragma once
struct MCP4922 {
  unsigned output[2]{};
  void begin(int){}
  void write(unsigned value,unsigned channel){output[channel]=value;}
};
