/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <cstdint>

namespace vc {
// Optional, fixed-size instrumentation. No allocation, serial IO or model state.
enum class TraceStage : unsigned { Command, Input, Release, Stimulus, Membrane,
                                  Output, Format, Write, Count };
constexpr unsigned trace_stage_count = unsigned(TraceStage::Count);
struct TraceRecord {
  uint32_t sequence = 0, elapsed_us = 0, total_us = 0;
  uint32_t stage_us[trace_stage_count]{};
  uint32_t expected_bytes = 0, written_bytes = 0, solve_us = 0, reason = 0;
};
struct TimingTrace {
  static constexpr unsigned capacity = 16;
  bool enabled = false, capturing = false;
  uint32_t ticks = 0, overruns = 0, late_starts = 0, short_writes = 0;
  uint32_t format_errors = 0, overflow = 0, capacity_skips = 0;
  unsigned count = 0;
  uint32_t maximum_stage_us[trace_stage_count]{};
  TraceRecord records[capacity]{};
  TraceRecord current;
  uint32_t started_us = 0, marked_us = 0;
  void start() { *this = TimingTrace{}; enabled = true; }
  void stop() { enabled = capturing = false; }
  void begin(uint32_t now, uint32_t elapsed) {
    capturing = enabled;
    if (!capturing) return;
    current = TraceRecord{};
    current.elapsed_us = elapsed;
    started_us = marked_us = now;
  }
  void mark(TraceStage stage, uint32_t now) {
    if (!capturing) return;
    current.stage_us[unsigned(stage)] += now - marked_us;
    marked_us = now;
  }
  void transmitted(uint32_t expected, uint32_t written, bool format_error = false) {
    if (!capturing) return;
    current.expected_bytes = expected;
    current.written_bytes = written;
    if (format_error) current.reason |= 8;
    else if (written != expected) current.reason |= 4;
  }
  void capacitySkipped(uint32_t expected) {
    if (!capturing) return;
    current.expected_bytes = expected;
    current.written_bytes = 0;
    current.reason |= 16;  // No Serial.write call was made; whole record skipped.
  }
  void finish(uint32_t sequence, uint32_t solve, uint32_t now, uint32_t period) {
    if (!capturing) return;
    capturing = false;
    current.sequence = sequence;
    current.solve_us = solve;
    current.total_us = now - started_us;
    ++ticks;
    if (current.total_us >= period) { ++overruns; current.reason |= 1; }
    if (uint64_t(current.elapsed_us) >= 2ULL * period) {
      ++late_starts; current.reason |= 2;
    }
    if (current.reason & 4) ++short_writes;
    if (current.reason & 8) ++format_errors;
    if (current.reason & 16) ++capacity_skips;
    for (unsigned i = 0; i < trace_stage_count; ++i)
      if (current.stage_us[i] > maximum_stage_us[i])
        maximum_stage_us[i] = current.stage_us[i];
    if (current.reason) {
      if (count < capacity) records[count++] = current;
      else ++overflow;
    }
  }
};
} // namespace vc
