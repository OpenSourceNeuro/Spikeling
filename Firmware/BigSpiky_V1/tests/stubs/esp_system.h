#pragma once
#include <cstdint>
inline uint32_t esp_random() { static uint32_t x=0x12345678U; x=x*1664525U+1013904223U; return x; }

