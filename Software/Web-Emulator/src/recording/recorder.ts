// SPDX-License-Identifier: GPL-3.0-or-later

import type { DataSource, Unsubscribe } from "../data-source/DataSource.ts";
import { TIMESTEP_MS } from "../model/izhikevich.ts";
import type { SimulationSample } from "../model/types.ts";
import type { EngineSnapshot, SimulationLifecycle } from "../simulation/protocol.ts";
import {
  DEFAULT_RECORDING_MAX_SAMPLES,
  DESKTOP_RECORDING_COLUMNS,
  MAX_RECORDING_FILE_BYTES,
  RECORDING_SAMPLE_RATE_HZ,
  parseRecordingCsv,
  parseRecordingFile,
  recordingLimit,
  serialiseRecordingCsv,
} from "./csv.ts";
import type { LocalRecordingFile, RecordingSample } from "./csv.ts";

export const RECORDING_CHUNK_SAMPLES = 1_024;
export type RecordingLifecycle = "idle" | "recording" | "stopped" | "full";
export type RecordingOrigin = "live" | "imported";

export interface RecordingSnapshot {
  readonly lifecycle: RecordingLifecycle;
  readonly origin: RecordingOrigin;
  readonly sampleCount: number;
  readonly maxSamples: number;
  readonly allocatedBytes: number;
  readonly maximumBytes: number;
  readonly durationMs: number;
  readonly sampleIntervalMs: number;
  readonly scientificSampleRateHz: number;
  readonly recordingSampleRateHz: number;
  readonly wallClockStepsPerSecond: number | undefined;
  readonly simulationLifecycle: SimulationLifecycle | undefined;
  readonly filename: string | undefined;
  readonly error: string | undefined;
}

export interface RecordingOptions {
  readonly maxSamples?: number;
  readonly maxBytes?: number;
  readonly chunkSamples?: number;
}

export type RecordingListener = (snapshot: RecordingSnapshot) => void;
const WIDTH = DESKTOP_RECORDING_COLUMNS.length;

/** Lazily allocated Float64 chunks; a full recording stops instead of overwriting. */
export class RecordingBuffer {
  readonly capacity: number;
  readonly chunkSamples: number;
  private readonly chunks: Float64Array[] = [];
  private count = 0;

  constructor(capacity = DEFAULT_RECORDING_MAX_SAMPLES, chunkSamples = RECORDING_CHUNK_SAMPLES) {
    this.capacity = recordingLimit(capacity, DEFAULT_RECORDING_MAX_SAMPLES, "Recording capacity");
    this.chunkSamples = recordingLimit(chunkSamples, RECORDING_CHUNK_SAMPLES, "Recording chunk size");
  }

  get length(): number { return this.count; }
  get allocatedBytes(): number { return this.chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0); }
  get maximumBytes(): number { return this.capacity * WIDTH * Float64Array.BYTES_PER_ELEMENT; }

  push(sample: RecordingSample): boolean {
    if (this.count === this.capacity) return false;
    for (const column of DESKTOP_RECORDING_COLUMNS) {
      if (!Number.isFinite(sample[column.field])) {
        throw new RangeError("Recorded scientific values must be finite.");
      }
    }
    if (sample.trigger !== 0 && sample.trigger !== 1) {
      throw new RangeError("Recorded trigger values must be zero or one.");
    }
    const chunkIndex = Math.floor(this.count / this.chunkSamples);
    let chunk = this.chunks[chunkIndex];
    if (chunk === undefined) {
      const size = Math.min(this.chunkSamples, this.capacity - chunkIndex * this.chunkSamples);
      chunk = new Float64Array(size * WIDTH);
      this.chunks.push(chunk);
    }
    const offset = (this.count % this.chunkSamples) * WIDTH;
    for (let index = 0; index < WIDTH; index += 1) {
      chunk[offset + index] = sample[DESKTOP_RECORDING_COLUMNS[index].field];
    }
    this.count += 1;
    return true;
  }

  at(index: number): RecordingSample | undefined {
    if (!Number.isInteger(index)) throw new RangeError("A recording index must be an integer.");
    const actual = index < 0 ? this.count + index : index;
    if (actual < 0 || actual >= this.count) return undefined;
    const chunk = this.chunks[Math.floor(actual / this.chunkSamples)];
    const offset = (actual % this.chunkSamples) * WIDTH;
    return {
      timeMs: chunk[offset],
      mainVm: chunk[offset + 1],
      stimulus: chunk[offset + 2],
      totalCurrent: chunk[offset + 3],
      synapse1Vm: chunk[offset + 4],
      synapse1Current: chunk[offset + 5],
      synapse2Vm: chunk[offset + 6],
      synapse2Current: chunk[offset + 7],
      trigger: chunk[offset + 8] as 0 | 1,
    };
  }

  samples(): RecordingSample[] {
    return Array.from({ length: this.count }, (_, index) => this.at(index)!);
  }

  clear(): void {
    this.chunks.length = 0;
    this.count = 0;
  }
}

/** A display-independent scientific consumer of the existing DataSource seam. */
export class SpikelingRecorder {
  readonly buffer: RecordingBuffer;
  private readonly maxBytes: number;
  private readonly listeners = new Set<RecordingListener>();
  private readonly subscriptions: Unsubscribe[] = [];
  private lifecycle: RecordingLifecycle = "idle";
  private origin: RecordingOrigin = "live";
  private filename: string | undefined;
  private error: string | undefined;
  private sourceSnapshot: EngineSnapshot | undefined;
  private lastSourceTime: number | undefined;
  private disposed = false;

  constructor(source: DataSource, options: RecordingOptions = {}) {
    this.buffer = new RecordingBuffer(options.maxSamples, options.chunkSamples);
    this.maxBytes = recordingLimit(options.maxBytes, MAX_RECORDING_FILE_BYTES, "Recording file-size limit");
    this.subscriptions.push(
      source.subscribe((samples) => this.handleSamples(samples)),
      source.subscribeState((snapshot) => this.handleSourceState(snapshot)),
      source.subscribeErrors((error) => this.handleSourceError(error)),
    );
  }

  getSnapshot(): RecordingSnapshot {
    return {
      lifecycle: this.lifecycle,
      origin: this.origin,
      sampleCount: this.buffer.length,
      maxSamples: this.buffer.capacity,
      allocatedBytes: this.buffer.allocatedBytes,
      maximumBytes: this.buffer.maximumBytes,
      durationMs: this.buffer.length * TIMESTEP_MS,
      sampleIntervalMs: TIMESTEP_MS,
      scientificSampleRateHz: RECORDING_SAMPLE_RATE_HZ,
      recordingSampleRateHz: RECORDING_SAMPLE_RATE_HZ,
      wallClockStepsPerSecond: this.sourceSnapshot?.speed.stepsPerSecond,
      simulationLifecycle: this.sourceSnapshot?.lifecycle,
      filename: this.filename,
      error: this.error,
    };
  }

  subscribe(listener: RecordingListener): Unsubscribe {
    this.requireActive();
    this.listeners.add(listener);
    listener(this.getSnapshot());
    return () => this.listeners.delete(listener);
  }

  start(): void {
    this.requireActive();
    if (this.lifecycle === "recording") return;
    this.buffer.clear();
    this.origin = "live";
    this.filename = undefined;
    this.error = undefined;
    this.lastSourceTime = undefined;
    this.lifecycle = "recording";
    this.publish();
  }

  stop(): void {
    this.requireActive();
    if (this.lifecycle !== "recording") return;
    this.lifecycle = "stopped";
    this.publish();
  }

  clear(): void {
    this.requireActive();
    this.buffer.clear();
    this.lifecycle = "idle";
    this.origin = "live";
    this.filename = undefined;
    this.error = undefined;
    this.lastSourceTime = undefined;
    this.publish();
  }

  samples(): RecordingSample[] { return this.buffer.samples(); }

  exportCsv(): string {
    this.requireActive();
    if (this.lifecycle === "recording") {
      throw new Error("Stop recording before exporting the scientific samples.");
    }
    return serialiseRecordingCsv(this.buffer.samples());
  }

  importCsv(content: string, filename?: string): void {
    this.requireActive();
    if (this.lifecycle === "recording") {
      throw new Error("Stop recording before importing another recording.");
    }
    const parsed = parseRecordingCsv(content, { maxSamples: this.buffer.capacity, maxBytes: this.maxBytes });
    this.replaceImported(parsed.samples, filename);
  }

  async importFile(file: LocalRecordingFile): Promise<void> {
    this.requireActive();
    if (this.lifecycle === "recording") {
      throw new Error("Stop recording before importing another recording.");
    }
    const parsed = await parseRecordingFile(file, { maxSamples: this.buffer.capacity, maxBytes: this.maxBytes });
    this.requireActive();
    if (this.lifecycle === "recording") {
      throw new Error("Stop recording before importing another recording.");
    }
    this.replaceImported(parsed.samples, file.name);
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    for (const unsubscribe of this.subscriptions) unsubscribe();
    this.listeners.clear();
    this.buffer.clear();
  }

  private replaceImported(samples: readonly RecordingSample[], filename?: string): void {
    this.buffer.clear();
    for (const sample of samples) this.buffer.push(sample);
    this.lifecycle = "stopped";
    this.origin = "imported";
    this.filename = filename;
    this.error = undefined;
    this.lastSourceTime = undefined;
    this.publish();
  }

  private handleSamples(samples: readonly SimulationSample[]): void {
    if (this.lifecycle !== "recording" || samples.length === 0) return;
    for (const sample of samples) {
      if (this.lastSourceTime !== undefined && Math.abs(sample.timeMs - this.lastSourceTime - TIMESTEP_MS) > 1e-8) {
        this.error = "The simulation sample stream was discontinuous; recording stopped without inventing samples.";
        this.lifecycle = "stopped";
        break;
      }
      const recorded: RecordingSample = {
        timeMs: this.buffer.length * TIMESTEP_MS,
        mainVm: sample.mainVm,
        stimulus: sample.stimulus,
        totalCurrent: sample.totalCurrent,
        synapse1Vm: sample.synapse1Vm,
        synapse1Current: sample.synapse1Current,
        synapse2Vm: sample.synapse2Vm,
        synapse2Current: sample.synapse2Current,
        trigger: sample.trigger,
      };
      this.buffer.push(recorded);
      this.lastSourceTime = sample.timeMs;
      if (this.buffer.length === this.buffer.capacity) {
        this.lifecycle = "full";
        break;
      }
    }
    this.publish();
  }

  private handleSourceState(snapshot: EngineSnapshot): void {
    const reset = this.sourceSnapshot !== undefined && snapshot.stepIndex === 0 && this.buffer.length > 0;
    this.sourceSnapshot = snapshot;
    if (this.lifecycle === "recording" && (snapshot.lifecycle === "stopped" || reset)) {
      this.lifecycle = "stopped";
    }
    this.publish();
  }

  private handleSourceError(error: Error): void {
    this.error = error.message;
    if (this.lifecycle === "recording") this.lifecycle = "stopped";
    this.publish();
  }

  private publish(): void {
    const snapshot = this.getSnapshot();
    for (const listener of this.listeners) listener(snapshot);
  }

  private requireActive(): void {
    if (this.disposed) throw new Error("The scientific recorder has been disposed.");
  }
}
