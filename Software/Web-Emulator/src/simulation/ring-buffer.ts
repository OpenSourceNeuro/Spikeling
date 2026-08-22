// SPDX-License-Identifier: GPL-3.0-or-later

import type { SimulationSample } from "../model/types.ts";

export const DEFAULT_HISTORY_CAPACITY = 50_000;
export const DEFAULT_VISIBLE_SAMPLES = 5_000;

/** Stable row order for transferable, full-precision worker batches. */
export const SAMPLE_COLUMNS = [
  "timeMs",
  "mainVm",
  "mainRecovery",
  "stimulus",
  "totalCurrent",
  "synapse1Vm",
  "synapse1Recovery",
  "synapse1Current",
  "synapse2Vm",
  "synapse2Recovery",
  "synapse2Current",
  "trigger",
] as const satisfies ReadonlyArray<keyof SimulationSample>;

export const SAMPLE_WIDTH = SAMPLE_COLUMNS.length;

export function packSamples(samples: readonly SimulationSample[]): Float64Array {
  const packed = new Float64Array(samples.length * SAMPLE_WIDTH);

  for (let row = 0; row < samples.length; row += 1) {
    const sample = samples[row];
    for (let column = 0; column < SAMPLE_WIDTH; column += 1) {
      packed[row * SAMPLE_WIDTH + column] = sample[SAMPLE_COLUMNS[column]];
    }
  }

  return packed;
}

export function unpackSamples(packed: Float64Array): SimulationSample[] {
  if (packed.length % SAMPLE_WIDTH !== 0) {
    throw new RangeError("A packed sample batch must contain complete sample rows.");
  }

  const samples: SimulationSample[] = [];
  for (let offset = 0; offset < packed.length; offset += SAMPLE_WIDTH) {
    const trigger = packed[offset + 11];
    if (trigger !== 0 && trigger !== 1) {
      throw new RangeError("A packed sample trigger must be zero or one.");
    }

    samples.push({
      timeMs: packed[offset],
      mainVm: packed[offset + 1],
      mainRecovery: packed[offset + 2],
      stimulus: packed[offset + 3],
      totalCurrent: packed[offset + 4],
      synapse1Vm: packed[offset + 5],
      synapse1Recovery: packed[offset + 6],
      synapse1Current: packed[offset + 7],
      synapse2Vm: packed[offset + 8],
      synapse2Recovery: packed[offset + 9],
      synapse2Current: packed[offset + 10],
      trigger,
    });
  }

  return samples;
}

/**
 * Preallocated, column-oriented Float64 history. No scientific value is
 * downsampled, rounded to Float32 or retained in an ever-growing array.
 */
export class SampleRingBuffer {
  readonly capacity: number;

  private readonly columns: Float64Array[];
  private writeIndex = 0;
  private sampleCount = 0;
  private writtenCount = 0;

  constructor(capacity = DEFAULT_HISTORY_CAPACITY) {
    if (!Number.isSafeInteger(capacity) || capacity < 1) {
      throw new RangeError("History capacity must be a positive safe integer.");
    }

    this.capacity = capacity;
    this.columns = SAMPLE_COLUMNS.map(() => new Float64Array(capacity));
  }

  get length(): number {
    return this.sampleCount;
  }

  get totalWritten(): number {
    return this.writtenCount;
  }

  get allocatedBytes(): number {
    return this.capacity * SAMPLE_WIDTH * Float64Array.BYTES_PER_ELEMENT;
  }

  push(sample: SimulationSample): void {
    for (let column = 0; column < SAMPLE_WIDTH; column += 1) {
      this.columns[column][this.writeIndex] = sample[SAMPLE_COLUMNS[column]];
    }

    this.writeIndex = (this.writeIndex + 1) % this.capacity;
    this.sampleCount = Math.min(this.sampleCount + 1, this.capacity);
    this.writtenCount += 1;
  }

  pushBatch(samples: readonly SimulationSample[]): void {
    for (const sample of samples) {
      this.push(sample);
    }
  }

  at(index: number): SimulationSample | undefined {
    if (!Number.isInteger(index)) {
      throw new RangeError("A history index must be an integer.");
    }

    const normalised = index < 0 ? this.sampleCount + index : index;
    if (normalised < 0 || normalised >= this.sampleCount) {
      return undefined;
    }

    const oldest =
      (this.writeIndex - this.sampleCount + this.capacity) % this.capacity;
    const physical = (oldest + normalised) % this.capacity;

    return {
      timeMs: this.columns[0][physical],
      mainVm: this.columns[1][physical],
      mainRecovery: this.columns[2][physical],
      stimulus: this.columns[3][physical],
      totalCurrent: this.columns[4][physical],
      synapse1Vm: this.columns[5][physical],
      synapse1Recovery: this.columns[6][physical],
      synapse1Current: this.columns[7][physical],
      synapse2Vm: this.columns[8][physical],
      synapse2Recovery: this.columns[9][physical],
      synapse2Current: this.columns[10][physical],
      trigger: this.columns[11][physical] as 0 | 1,
    };
  }

  latest(count = this.sampleCount): SimulationSample[] {
    if (!Number.isSafeInteger(count) || count < 0) {
      throw new RangeError("Requested history length must be a non-negative integer.");
    }

    const retained = Math.min(count, this.sampleCount);
    const samples: SimulationSample[] = [];
    for (let index = this.sampleCount - retained; index < this.sampleCount; index += 1) {
      samples.push(this.at(index)!);
    }
    return samples;
  }

  clear(): void {
    this.writeIndex = 0;
    this.sampleCount = 0;
    this.writtenCount = 0;
  }
}
