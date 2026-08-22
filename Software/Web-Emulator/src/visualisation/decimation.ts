// SPDX-License-Identifier: GPL-3.0-or-later

import type { SimulationSample } from "../model/types.ts";
import type { TraceField } from "./traces.ts";

export interface TracePoint {
  readonly sampleIndex: number;
  readonly timeMs: number;
  readonly relativeTimeMs: number;
  readonly value: number;
}

export interface TraceDecimationOptions {
  readonly field: TraceField;
  readonly pixelWidth: number;
  readonly windowMs: number;
  readonly anchorTimeMs?: number;
}

/**
 * Retain each pixel bucket's first, minimum, maximum and last actual samples.
 * Narrow +30 mV action-potential peaks therefore survive display decimation;
 * scientific history and worker batches are never modified.
 */
export function decimateTrace(
  samples: readonly SimulationSample[],
  options: TraceDecimationOptions,
): TracePoint[] {
  if (
    !Number.isFinite(options.pixelWidth) ||
    options.pixelWidth < 1 ||
    !Number.isFinite(options.windowMs) ||
    options.windowMs <= 0
  ) {
    throw new RangeError("Display decimation requires a positive width and time window.");
  }

  if (samples.length === 0) {
    return [];
  }

  const anchor = options.anchorTimeMs ?? samples[samples.length - 1].timeMs;
  if (!Number.isFinite(anchor)) {
    throw new RangeError("The display anchor must be a finite timestamp.");
  }

  const width = Math.max(1, Math.floor(options.pixelWidth));
  const result: TracePoint[] = [];
  let bucket = -1;
  let first = -1;
  let minimum = -1;
  let maximum = -1;
  let last = -1;

  function append(index: number): void {
    const sample = samples[index];
    result.push({
      sampleIndex: index,
      timeMs: sample.timeMs,
      relativeTimeMs: sample.timeMs - anchor,
      value: sample[options.field],
    });
  }

  function flush(): void {
    if (first < 0) {
      return;
    }

    const indices = Array.from(new Set([first, minimum, maximum, last])).sort(
      (left, right) => left - right,
    );
    for (const index of indices) {
      append(index);
    }
  }

  for (let index = 0; index < samples.length; index += 1) {
    const sample = samples[index];
    const relativeTimeMs = sample.timeMs - anchor;
    if (relativeTimeMs < -options.windowMs || relativeTimeMs > 0) {
      continue;
    }

    const position = Math.min(
      width - 1,
      Math.max(0, Math.floor(((relativeTimeMs + options.windowMs) / options.windowMs) * width)),
    );

    if (position !== bucket) {
      flush();
      bucket = position;
      first = index;
      minimum = index;
      maximum = index;
      last = index;
      continue;
    }

    if (sample[options.field] < samples[minimum][options.field]) {
      minimum = index;
    }
    if (sample[options.field] > samples[maximum][options.field]) {
      maximum = index;
    }
    last = index;
  }

  flush();
  return result;
}
