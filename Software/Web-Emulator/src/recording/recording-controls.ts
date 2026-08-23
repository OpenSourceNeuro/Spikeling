// SPDX-License-Identifier: GPL-3.0-or-later

import type { Unsubscribe } from "../data-source/DataSource.ts";
import type { LocalRecordingFile } from "./csv.ts";
import type { RecordingSnapshot } from "./recorder.ts";
import { SpikelingRecorder } from "./recorder.ts";

export interface RecordingDownload {
  readonly filename: string;
  readonly content: string;
  readonly mimeType: string;
}

export interface RecordingControlsOptions {
  readonly download?: (recording: RecordingDownload) => void;
  readonly now?: () => Date;
}

function create<K extends keyof HTMLElementTagNameMap>(
  owner: Document,
  tag: K,
  className: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = owner.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function count(value: number): string {
  return value.toLocaleString("en-GB");
}

/** Accessible, entirely local recording transport alongside the scientific scope. */
export class SpikelingRecordingControls {
  readonly element: HTMLElement;
  private readonly recorder: SpikelingRecorder;
  private readonly owner: Document;
  private readonly options: RecordingControlsOptions;
  private readonly startButton: HTMLButtonElement;
  private readonly stopButton: HTMLButtonElement;
  private readonly downloadButton: HTMLButtonElement;
  private readonly clearButton: HTMLButtonElement;
  private readonly input: HTMLInputElement;
  private readonly status: HTMLElement;
  private readonly statistics: HTMLElement;
  private readonly rates: HTMLElement;
  private readonly progress: HTMLProgressElement;
  private readonly error: HTMLElement;
  private unsubscribe: Unsubscribe | undefined;
  private disposed = false;

  constructor(host: HTMLElement, recorder: SpikelingRecorder, options: RecordingControlsOptions = {}) {
    this.owner = host.ownerDocument;
    this.recorder = recorder;
    this.options = options;
    this.element = create(this.owner, "section", "spk-controls spk-recording");
    this.element.setAttribute("aria-label", "Scientific recording and local CSV files");

    const heading = create(this.owner, "h2", "spk-recording__heading", "Scientific recording");
    this.status = create(this.owner, "p", "spk-recording__status");
    this.status.setAttribute("role", "status");
    this.status.setAttribute("aria-live", "polite");
    this.element.append(heading, this.status);

    const transport = create(this.owner, "div", "spk-recording__transport");
    transport.setAttribute("aria-label", "Recording transport controls");
    this.startButton = this.button("Start recording", "start");
    this.stopButton = this.button("Stop recording", "stop");
    this.downloadButton = this.button("Download CSV", "download");
    this.clearButton = this.button("Clear recording", "clear");
    transport.append(this.startButton, this.stopButton, this.downloadButton, this.clearButton);
    this.element.append(transport);

    const importLabel = create(this.owner, "label", "spk-recording__import", "Import desktop-compatible recording CSV");
    this.input = create(this.owner, "input", "spk-recording__file");
    this.input.type = "file";
    this.input.accept = ".csv,text/csv";
    this.input.setAttribute("aria-label", "Import recording CSV");
    importLabel.append(this.input);
    this.element.append(importLabel);

    this.progress = create(this.owner, "progress", "spk-recording__progress");
    this.progress.setAttribute("aria-label", "Recording capacity used");
    this.statistics = create(this.owner, "p", "spk-recording__statistics");
    this.statistics.setAttribute("aria-live", "off");
    this.rates = create(this.owner, "p", "spk-recording__rates");
    this.rates.setAttribute("aria-live", "off");
    this.error = create(this.owner, "p", "spk-recording__error");
    this.error.setAttribute("role", "alert");
    this.element.append(this.progress, this.statistics, this.rates, this.error);
    host.append(this.element);

    this.startButton.addEventListener("click", () => this.run(() => this.recorder.start()));
    this.stopButton.addEventListener("click", () => this.run(() => this.recorder.stop()));
    this.clearButton.addEventListener("click", () => this.run(() => this.recorder.clear()));
    this.downloadButton.addEventListener("click", () => this.run(() => this.download()));
    this.input.addEventListener("change", () => {
      const file = this.input.files?.[0];
      if (file !== undefined) void this.importFile(file);
    });
    this.unsubscribe = this.recorder.subscribe((snapshot) => this.synchronise(snapshot));
  }

  async importFile(file: LocalRecordingFile): Promise<void> {
    this.error.textContent = "";
    try {
      await this.recorder.importFile(file);
    } catch (failure) {
      this.showError(failure);
    }
  }

  download(): RecordingDownload {
    const content = this.recorder.exportCsv();
    const now = (this.options.now ?? (() => new Date()))();
    const stamp = now.toISOString().replace(/[:.]/g, "-");
    const recording = {
      filename: "spikeling-recording-" + stamp + ".csv",
      content,
      mimeType: "text/csv;charset=utf-8",
    };
    if (this.options.download !== undefined) {
      this.options.download(recording);
    } else {
      const object = URL.createObjectURL(new Blob([content], { type: recording.mimeType }));
      const link = this.owner.createElement("a");
      link.href = object;
      link.download = recording.filename;
      link.click();
      setTimeout(() => URL.revokeObjectURL(object), 0);
    }
    return recording;
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.unsubscribe?.();
    this.element.remove();
  }

  private button(label: string, action: string): HTMLButtonElement {
    const button = create(this.owner, "button", "spk-recording__button", label);
    button.type = "button";
    button.dataset.action = action;
    button.setAttribute("aria-label", label);
    return button;
  }

  private synchronise(snapshot: RecordingSnapshot): void {
    const active = snapshot.lifecycle === "recording";
    this.startButton.disabled = active;
    this.stopButton.disabled = !active;
    this.downloadButton.disabled = active || snapshot.sampleCount === 0;
    this.clearButton.disabled = !active && snapshot.lifecycle === "idle";
    this.input.disabled = active;
    this.progress.max = snapshot.maxSamples;
    this.progress.value = snapshot.sampleCount;

    if (snapshot.lifecycle === "full") {
      this.status.textContent = "Recording complete: capacity reached without overwriting samples.";
    } else if (active && snapshot.simulationLifecycle === "paused") {
      this.status.textContent = "Recording armed; simulation paused.";
    } else if (active) {
      this.status.textContent = "Recording every scientific simulation sample.";
    } else if (snapshot.origin === "imported") {
      this.status.textContent = "Imported " + (snapshot.filename ?? "desktop-compatible recording") + ".";
    } else if (snapshot.lifecycle === "stopped") {
      this.status.textContent = "Recording stopped; samples remain available locally.";
    } else {
      this.status.textContent = "Ready to record locally; no files are uploaded.";
    }

    this.statistics.textContent = count(snapshot.sampleCount) + " / " + count(snapshot.maxSamples)
      + " samples · " + count(snapshot.durationMs) + " ms of simulation time";
    const wallClock = snapshot.wallClockStepsPerSecond === undefined
      ? "waiting for simulation"
      : count(snapshot.wallClockStepsPerSecond) + " samples/s wall-clock target";
    this.rates.textContent = "Timestep " + snapshot.sampleIntervalMs + " ms · capture "
      + count(snapshot.recordingSampleRateHz) + " samples/s of simulation time · "
      + wallClock + " · display refresh independent";
    if (snapshot.error !== undefined) this.error.textContent = snapshot.error;
  }

  private run(action: () => void): void {
    this.error.textContent = "";
    try {
      action();
    } catch (failure) {
      this.showError(failure);
    }
  }

  private showError(failure: unknown): void {
    this.error.textContent = failure instanceof Error ? failure.message : "Unable to process the scientific recording.";
  }
}
