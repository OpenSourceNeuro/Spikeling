// SPDX-License-Identifier: GPL-3.0-or-later

import type { SimulationScheduler } from "../../src/index.ts";

interface ScheduledTask {
  readonly id: number;
  readonly dueAt: number;
  readonly callback: () => void;
}

/** Explicit monotonic clock; tests never wait for real desktop tick intervals. */
export class ManualScheduler implements SimulationScheduler {
  private currentTime = 0;
  private nextId = 1;
  private readonly tasks = new Map<number, ScheduledTask>();

  now(): number {
    return this.currentTime;
  }

  get pending(): number {
    return this.tasks.size;
  }

  setTimeout(callback: () => void, delayMs: number): number {
    const id = this.nextId;
    this.nextId += 1;
    this.tasks.set(id, {
      id,
      dueAt: this.currentTime + delayMs,
      callback,
    });
    return id;
  }

  clearTimeout(handle: unknown): void {
    this.tasks.delete(handle as number);
  }

  elapse(milliseconds: number): void {
    if (!Number.isFinite(milliseconds) || milliseconds < 0) {
      throw new RangeError("Manual elapsed time must be finite and non-negative.");
    }
    this.currentTime += milliseconds;
  }

  runNext(): boolean {
    const due = Array.from(this.tasks.values())
      .filter((task) => task.dueAt <= this.currentTime)
      .sort((left, right) => left.dueAt - right.dueAt || left.id - right.id)[0];

    if (due === undefined) {
      return false;
    }

    this.tasks.delete(due.id);
    due.callback();
    return true;
  }

  flush(limit = 100_000): number {
    let completed = 0;
    while (completed < limit && this.runNext()) {
      completed += 1;
    }
    if (completed === limit && this.runNext()) {
      throw new Error("Manual scheduler exceeded its callback safety limit.");
    }
    return completed;
  }

  advance(milliseconds: number): number {
    this.elapse(milliseconds);
    return this.flush();
  }
}
