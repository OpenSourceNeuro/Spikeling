// SPDX-License-Identifier: GPL-3.0-or-later

import { SpikelingModel } from "../model/simulation.ts";
import type {
  ControlsPatch,
  InitialisationMode,
  SimulationOptions,
  SimulationSample,
} from "../model/types.ts";
import type { EngineSnapshot, SimulationLifecycle } from "./protocol.ts";
import {
  DEFAULT_HISTORY_CAPACITY,
  SampleRingBuffer,
} from "./ring-buffer.ts";
import {
  DEFAULT_SPEED_INDEX,
  DESKTOP_UPDATE_INTERVAL_MS,
  getSimulationSpeed,
} from "./speed.ts";

export interface SimulationScheduler {
  now(): number;
  setTimeout(callback: () => void, delayMs: number): unknown;
  clearTimeout(handle: unknown): void;
}

export interface SimulationEngineOptions {
  readonly model?: SpikelingModel;
  readonly modelOptions?: SimulationOptions;
  readonly historyCapacity?: number;
  readonly speedIndex?: number;
  readonly maxStepsPerSlice?: number;
  readonly maxCatchUpTicks?: number;
  readonly scheduler?: SimulationScheduler;
  readonly onSamples?: (samples: readonly SimulationSample[]) => void;
  readonly onState?: (snapshot: EngineSnapshot) => void;
  readonly onError?: (error: Error) => void;
}

const defaultScheduler: SimulationScheduler = {
  now: () => performance.now(),
  setTimeout: (callback, delayMs) => setTimeout(callback, delayMs),
  clearTimeout: (handle) => clearTimeout(handle as ReturnType<typeof setTimeout>),
};

function positiveInteger(value: number, label: string): number {
  if (!Number.isSafeInteger(value) || value < 1) {
    throw new RangeError(label + " must be a positive safe integer.");
  }
  return value;
}

/**
 * Fixed-step model scheduler. Numerical time never depends on paint frequency;
 * large desktop-equivalent updates yield between bounded worker slices.
 */
export class SimulationEngine {
  readonly history: SampleRingBuffer;
  readonly model: SpikelingModel;
  readonly maxStepsPerSlice: number;
  readonly maxCatchUpTicks: number;

  private readonly scheduler: SimulationScheduler;
  private readonly onSamples: ((samples: readonly SimulationSample[]) => void) | undefined;
  private readonly onState: ((snapshot: EngineSnapshot) => void) | undefined;
  private readonly onError: ((error: Error) => void) | undefined;
  private lifecycle: SimulationLifecycle = "idle";
  private speedIndex: number;
  private timeoutHandle: unknown;
  private timeoutScheduled = false;
  private nextTickAt = 0;
  private pendingSteps = 0;
  private droppedSteps = 0;

  constructor(options: SimulationEngineOptions = {}) {
    if (options.model !== undefined && options.modelOptions !== undefined) {
      throw new TypeError("Supply either an existing model or model options, not both.");
    }

    this.model = options.model ?? new SpikelingModel(options.modelOptions);
    this.history = new SampleRingBuffer(
      options.historyCapacity ?? DEFAULT_HISTORY_CAPACITY,
    );
    this.speedIndex = options.speedIndex ?? DEFAULT_SPEED_INDEX;
    getSimulationSpeed(this.speedIndex);
    this.maxStepsPerSlice = positiveInteger(
      options.maxStepsPerSlice ?? 250,
      "Maximum steps per slice",
    );
    this.maxCatchUpTicks = positiveInteger(
      options.maxCatchUpTicks ?? 4,
      "Maximum catch-up ticks",
    );
    this.scheduler = options.scheduler ?? defaultScheduler;
    this.onSamples = options.onSamples;
    this.onState = options.onState;
    this.onError = options.onError;
  }

  getSnapshot(): EngineSnapshot {
    return {
      lifecycle: this.lifecycle,
      speed: getSimulationSpeed(this.speedIndex),
      stepIndex: this.model.getState().stepIndex,
      retainedSamples: this.history.length,
      historyCapacity: this.history.capacity,
      historyBytes: this.history.allocatedBytes,
      pendingSteps: this.pendingSteps,
      droppedSteps: this.droppedSteps,
      controls: this.model.getControls(),
    };
  }

  start(): void {
    if (this.lifecycle === "running") {
      return;
    }

    this.lifecycle = "running";
    this.nextTickAt = this.scheduler.now() + DESKTOP_UPDATE_INTERVAL_MS;
    this.publishState();
    this.schedule(DESKTOP_UPDATE_INTERVAL_MS);
  }

  pause(): void {
    if (this.lifecycle !== "running") {
      return;
    }

    this.cancelScheduledWork();
    this.pendingSteps = 0;
    this.lifecycle = "paused";
    this.publishState();
  }

  stop(): void {
    this.cancelScheduledWork();
    this.pendingSteps = 0;
    this.droppedSteps = 0;
    this.model.reset();
    this.history.clear();
    this.lifecycle = "stopped";
    this.publishState();
  }

  reset(
    options: { readonly seed?: number; readonly initialisation?: InitialisationMode } = {},
  ): void {
    const wasRunning = this.lifecycle === "running";
    this.cancelScheduledWork();
    this.pendingSteps = 0;
    this.droppedSteps = 0;
    this.model.reset(options);
    this.history.clear();
    this.lifecycle = wasRunning ? "running" : "idle";

    if (wasRunning) {
      this.nextTickAt = this.scheduler.now() + DESKTOP_UPDATE_INTERVAL_MS;
      this.schedule(DESKTOP_UPDATE_INTERVAL_MS);
    }

    this.publishState();
  }

  setSpeed(index: number): void {
    getSimulationSpeed(index);
    this.speedIndex = index;
    this.publishState();
  }

  updateControls(patch: ControlsPatch): void {
    this.model.updateControls(patch);
    this.publishState();
  }

  dispose(): void {
    this.cancelScheduledWork();
    this.pendingSteps = 0;
    this.lifecycle = "stopped";
  }

  private publishState(): void {
    this.onState?.(this.getSnapshot());
  }

  private cancelScheduledWork(): void {
    if (this.timeoutScheduled) {
      this.scheduler.clearTimeout(this.timeoutHandle);
      this.timeoutScheduled = false;
      this.timeoutHandle = undefined;
    }
  }

  private schedule(delayMs: number): void {
    this.cancelScheduledWork();
    this.timeoutScheduled = true;
    this.timeoutHandle = this.scheduler.setTimeout(() => {
      this.timeoutScheduled = false;
      this.timeoutHandle = undefined;
      this.runSlice();
    }, Math.max(0, delayMs));
  }

  private runSlice(): void {
    if (this.lifecycle !== "running") {
      return;
    }

    try {
      const now = this.scheduler.now();
      if (now >= this.nextTickAt) {
        const elapsedTicks =
          Math.floor((now - this.nextTickAt) / DESKTOP_UPDATE_INTERVAL_MS) + 1;
        const retainedTicks = Math.min(elapsedTicks, this.maxCatchUpTicks);
        const stepsPerUpdate = getSimulationSpeed(this.speedIndex).stepsPerUpdate;
        this.pendingSteps += retainedTicks * stepsPerUpdate;
        this.droppedSteps += (elapsedTicks - retainedTicks) * stepsPerUpdate;
        this.nextTickAt += elapsedTicks * DESKTOP_UPDATE_INTERVAL_MS;
      }

      const sliceLength = Math.min(this.pendingSteps, this.maxStepsPerSlice);
      if (sliceLength > 0) {
        const samples: SimulationSample[] = [];
        for (let index = 0; index < sliceLength; index += 1) {
          const sample = this.model.step();
          this.history.push(sample);
          samples.push(sample);
        }
        this.pendingSteps -= sliceLength;
        this.onSamples?.(samples);
      }

      if (this.lifecycle === "running") {
        const delay =
          this.pendingSteps > 0 ? 0 : this.nextTickAt - this.scheduler.now();
        this.schedule(delay);
      }
    } catch (caught) {
      this.cancelScheduledWork();
      this.pendingSteps = 0;
      this.lifecycle = "paused";
      this.publishState();
      const error = caught instanceof Error ? caught : new Error(String(caught));
      this.onError?.(error);
    }
  }
}
