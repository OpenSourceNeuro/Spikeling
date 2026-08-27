#pragma once
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT_PULLDOWN 2
#define RISING 3
#define HEX 16
#define IRAM_ATTR
using TaskHandle_t = void *;
using TickType_t = uint32_t;
using portMUX_TYPE = int;
#define portMUX_INITIALIZER_UNLOCKED 0
#define portENTER_CRITICAL(x) ((void)(x))
#define portEXIT_CRITICAL(x) ((void)(x))
#define portENTER_CRITICAL_ISR(x) ((void)(x))
#define portEXIT_CRITICAL_ISR(x) ((void)(x))
#define pdMS_TO_TICKS(x) (x)
inline uint32_t millis() { static uint32_t t=0; return ++t; }
inline uint32_t micros() { static uint32_t t=0; t+=10; return t; }
inline void pinMode(uint8_t, int) {}
inline void digitalWrite(uint8_t, int) {}
inline int digitalRead(uint8_t) { return LOW; }
inline uint8_t digitalPinToInterrupt(uint8_t pin) { return pin; }
inline void attachInterruptArg(uint8_t, void (*)(void *), void *, int) {}
inline void yield() {}
inline TickType_t xTaskGetTickCount() { return 0; }
inline void vTaskDelayUntil(TickType_t *, TickType_t) {}
inline int xTaskCreatePinnedToCore(void (*)(void *), const char *, uint32_t, void *, uint32_t,
                                   TaskHandle_t *, int) { return 1; }
class HardwareSerial {
 public:
  void begin(uint32_t) {}
  int available() { return 0; }
  int read() { return -1; }
  std::size_t write(const uint8_t *, std::size_t n) { return n; }
  void print(const char *) {}
  void print(uint8_t) {}
  void print(int16_t) {}
  void print(uint32_t) {}
  void print(uint32_t, int) {}
  void println() {}
  void println(const char *) {}
};
inline HardwareSerial Serial;

