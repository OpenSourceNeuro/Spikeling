// SPDX-License-Identifier: GPL-3.0-or-later

import type { RandomSource } from "./types.ts";

export const DEFAULT_RANDOM_SEED = 0x5350494b;

/**
 * Portable xorshift32 + Box-Muller generator.
 *
 * The reference Python generator implements the same unsigned operations so
 * stochastic fixtures can be reproduced without depending on NumPy internals.
 */
export class SeededRandomSource implements RandomSource {
  private state: number;
  private spare: number | undefined;

  constructor(seed: number = DEFAULT_RANDOM_SEED) {
    if (!Number.isInteger(seed) || seed < 1 || seed > 0xffffffff) {
      throw new RangeError("A random seed must be an integer from 1 to 4294967295.");
    }

    this.state = seed >>> 0;
    this.spare = undefined;
  }

  nextGaussian(): number {
    if (this.spare !== undefined) {
      const value = this.spare;
      this.spare = undefined;
      return value;
    }

    const u1 = this.nextUniform();
    const u2 = this.nextUniform();
    const radius = Math.sqrt(-2 * Math.log(u1));
    const angle = 2 * Math.PI * u2;

    this.spare = radius * Math.sin(angle);
    return radius * Math.cos(angle);
  }

  private nextUniform(): number {
    let value = this.state;
    value ^= value << 13;
    value ^= value >>> 17;
    value ^= value << 5;
    this.state = value >>> 0;

    // Keep both endpoints open so Box-Muller never takes log(0).
    return (this.state + 1) / 4294967297;
  }
}

export class SequenceRandomSource implements RandomSource {
  private readonly values: readonly number[];
  private position = 0;

  constructor(values: readonly number[]) {
    if (values.length === 0 || values.some((value) => !Number.isFinite(value))) {
      throw new TypeError("A Gaussian sequence must contain finite numeric values.");
    }
    this.values = [...values];
  }

  nextGaussian(): number {
    const value = this.values[this.position % this.values.length];
    this.position += 1;
    return value;
  }
}
