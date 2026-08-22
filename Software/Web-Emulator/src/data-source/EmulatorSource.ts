// SPDX-License-Identifier: GPL-3.0-or-later

import type { ControlsPatch, InitialisationMode, SimulationSample } from "../model/types.ts";
import type {
  EngineSnapshot,
  MainToWorkerMessage,
  TransferableSimulationOptions,
  WorkerToMainMessage,
} from "../simulation/protocol.ts";
import {
  DEFAULT_HISTORY_CAPACITY,
  SAMPLE_WIDTH,
  SampleRingBuffer,
  unpackSamples,
} from "../simulation/ring-buffer.ts";
import type {
  DataSource,
  ErrorListener,
  SampleListener,
  StateListener,
  Unsubscribe,
} from "./DataSource.ts";

export interface EmulatorSourceWorker {
  postMessage(message: MainToWorkerMessage): void;
  addEventListener(
    type: "message",
    listener: (event: { readonly data: WorkerToMainMessage }) => void,
  ): void;
  removeEventListener(
    type: "message",
    listener: (event: { readonly data: WorkerToMainMessage }) => void,
  ): void;
  terminate(): unknown;
}

export interface EmulatorSourceOptions {
  readonly simulation?: TransferableSimulationOptions;
  readonly historyCapacity?: number;
  readonly speedIndex?: number;
  readonly maxStepsPerSlice?: number;
  readonly maxCatchUpTicks?: number;
  readonly workerFactory?: () => EmulatorSourceWorker;
}

/**
 * Browser-side worker adapter. Rendering code consumes DataSource batches and
 * bounded history without knowing whether a future source is physical hardware.
 */
export class EmulatorSource implements DataSource {
  readonly kind = "emulator";
  readonly history: SampleRingBuffer;

  private readonly options: EmulatorSourceOptions;
  private readonly sampleListeners = new Set<SampleListener>();
  private readonly stateListeners = new Set<StateListener>();
  private readonly errorListeners = new Set<ErrorListener>();
  private worker: EmulatorSourceWorker | undefined;
  private connection: Promise<void> | undefined;
  private resolveConnection: (() => void) | undefined;
  private rejectConnection: ((error: Error) => void) | undefined;
  private snapshot: EngineSnapshot | undefined;

  constructor(options: EmulatorSourceOptions = {}) {
    this.options = options;
    this.history = new SampleRingBuffer(
      options.historyCapacity ?? DEFAULT_HISTORY_CAPACITY,
    );
  }

  connect(): Promise<void> {
    if (this.connection !== undefined) {
      return this.connection;
    }

    const factory =
      this.options.workerFactory ??
      (() =>
        new Worker(new URL("../worker/emulator.worker.ts", import.meta.url), {
          type: "module",
        }) as unknown as EmulatorSourceWorker);

    this.worker = factory();
    this.worker.addEventListener("message", this.handleMessage);
    this.connection = new Promise<void>((resolve, reject) => {
      this.resolveConnection = resolve;
      this.rejectConnection = reject;
    });
    this.worker.postMessage({
      type: "initialise",
      options: this.options.simulation,
      historyCapacity: this.options.historyCapacity,
      speedIndex: this.options.speedIndex,
      maxStepsPerSlice: this.options.maxStepsPerSlice,
      maxCatchUpTicks: this.options.maxCatchUpTicks,
    });

    return this.connection;
  }

  async disconnect(): Promise<void> {
    if (this.worker === undefined) {
      return;
    }

    this.worker.postMessage({ type: "dispose" });
    this.worker.removeEventListener("message", this.handleMessage);
    await this.worker.terminate();
    this.rejectConnection?.(new Error("The emulator worker was disconnected."));
    this.resolveConnection = undefined;
    this.rejectConnection = undefined;
    this.connection = undefined;
    this.worker = undefined;
    this.snapshot = undefined;
    this.history.clear();
  }

  start(): void {
    this.send({ type: "start" });
  }

  pause(): void {
    this.send({ type: "pause" });
  }

  stop(): void {
    this.send({ type: "stop" });
  }

  reset(
    options?: { readonly seed?: number; readonly initialisation?: InitialisationMode },
  ): void {
    this.send({ type: "reset", options });
  }

  setSpeed(index: number): void {
    this.send({ type: "set-speed", index });
  }

  updateControls(patch: ControlsPatch): void {
    this.send({ type: "update-controls", patch });
  }

  requestSnapshot(): void {
    this.send({ type: "snapshot" });
  }

  getSnapshot(): EngineSnapshot | undefined {
    return this.snapshot;
  }

  latest(count?: number): SimulationSample[] {
    return this.history.latest(count);
  }

  subscribe(listener: SampleListener): Unsubscribe {
    this.sampleListeners.add(listener);
    return () => this.sampleListeners.delete(listener);
  }

  subscribeState(listener: StateListener): Unsubscribe {
    this.stateListeners.add(listener);
    if (this.snapshot !== undefined) {
      listener(this.snapshot);
    }
    return () => this.stateListeners.delete(listener);
  }

  subscribeErrors(listener: ErrorListener): Unsubscribe {
    this.errorListeners.add(listener);
    return () => this.errorListeners.delete(listener);
  }

  private send(message: MainToWorkerMessage): void {
    if (this.worker === undefined) {
      throw new Error("Connect the emulator source before sending commands.");
    }
    this.worker.postMessage(message);
  }

  private readonly handleMessage = (event: {
    readonly data: WorkerToMainMessage;
  }): void => {
    const message = event.data;

    switch (message.type) {
      case "ready":
        this.publishState(message.snapshot);
        this.resolveConnection?.();
        this.resolveConnection = undefined;
        this.rejectConnection = undefined;
        break;

      case "state":
      case "snapshot":
        if (message.snapshot.stepIndex === 0 && this.history.length > 0) {
          this.history.clear();
        }
        this.publishState(message.snapshot);
        break;

      case "samples": {
        const packed = new Float64Array(message.buffer);
        if (packed.length !== message.count * SAMPLE_WIDTH) {
          this.publishError(new Error("The worker sent a malformed sample batch."));
          return;
        }

        const samples = unpackSamples(packed);
        this.history.pushBatch(samples);
        for (const listener of this.sampleListeners) {
          listener(samples);
        }
        break;
      }

      case "error":
        this.publishError(new Error(message.message));
        break;
    }
  };

  private publishState(snapshot: EngineSnapshot): void {
    this.snapshot = snapshot;
    for (const listener of this.stateListeners) {
      listener(snapshot);
    }
  }

  private publishError(error: Error): void {
    this.rejectConnection?.(error);
    this.resolveConnection = undefined;
    this.rejectConnection = undefined;
    for (const listener of this.errorListeners) {
      listener(error);
    }
  }
}
