// SPDX-License-Identifier: GPL-3.0-or-later

import { SpikelingMainControls } from "../controls/main-controls.ts";
import type { MainNeuronControlsOptions } from "../controls/main-controls.ts";
import { SpikelingSynapseControls } from "../controls/synapse-controls.ts";
import type { SynapseControlsOptions } from "../controls/synapse-controls.ts";
import type { DataSource, Unsubscribe } from "../data-source/DataSource.ts";
import { SpikelingRecorder } from "../recording/recorder.ts";
import type { RecordingOptions } from "../recording/recorder.ts";
import { SpikelingRecordingControls } from "../recording/recording-controls.ts";
import type { RecordingControlsOptions } from "../recording/recording-controls.ts";
import type { EngineSnapshot } from "../simulation/protocol.ts";
import { DESKTOP_STEPS_PER_UPDATE, getSimulationSpeed } from "../simulation/speed.ts";
import { SpikelingOscilloscope } from "../visualisation/oscilloscope.ts";
import type { OscilloscopeOptions } from "../visualisation/oscilloscope.ts";
import {
  MOBILE_MEDIA_QUERY,
  REDUCED_MOTION_MEDIA_QUERY,
  TABLET_MEDIA_QUERY,
} from "./accessibility.ts";
import type { EmulatorLayout } from "./accessibility.ts";

export interface MediaQueryAdapter {
  readonly matches: boolean;
  addEventListener(type: "change", listener: () => void): void;
  removeEventListener(type: "change", listener: () => void): void;
}

export interface EmulatorInterfaceOptions {
  readonly oscilloscope?: OscilloscopeOptions;
  readonly controls?: MainNeuronControlsOptions;
  readonly synapses?: Omit<SynapseControlsOptions, "oscilloscope">;
  readonly recorder?: RecordingOptions;
  readonly recording?: RecordingControlsOptions;
  readonly mediaQueryFactory?: (query: string) => MediaQueryAdapter;
  readonly sourceUrl?: string;
}

export type EmulatorPanel = "main" | "stimulus" | "synapses";

interface PanelElements {
  readonly details: HTMLDetailsElement;
  readonly summary: HTMLElement;
  readonly content: HTMLElement;
}

let instanceCount = 0;

function node<K extends keyof HTMLElementTagNameMap>(
  owner: Document,
  tag: K,
  className: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const created = owner.createElement(tag);
  created.className = className;
  if (text !== undefined) created.textContent = text;
  return created;
}

/** Reusable standalone and isolated WordPress-embeddable instrument. */
export class SpikelingEmulator {
  readonly element: HTMLElement;
  readonly oscilloscope: SpikelingOscilloscope;
  readonly controls: SpikelingMainControls;
  readonly synapses: SpikelingSynapseControls;
  readonly recorder: SpikelingRecorder;
  readonly recording: SpikelingRecordingControls;

  private readonly source: DataSource;
  private readonly owner: Document;
  private readonly prefix: string;
  private readonly panels = new Map<EmulatorPanel, PanelElements>();
  private readonly subscriptions: Unsubscribe[] = [];
  private readonly mediaQueries: MediaQueryAdapter[] = [];
  private readonly startButton: HTMLButtonElement;
  private readonly pauseButton: HTMLButtonElement;
  private readonly stopButton: HTMLButtonElement;
  private readonly resetButton: HTMLButtonElement;
  private readonly speed: HTMLSelectElement;
  private readonly status: HTMLElement;
  private readonly error: HTMLElement;
  private layout: EmulatorLayout = "desktop";
  private disposed = false;

  constructor(host: HTMLElement, source: DataSource, options: EmulatorInterfaceOptions = {}) {
    this.owner = host.ownerDocument;
    this.source = source;
    instanceCount += 1;
    this.prefix = "spk-emulator-" + instanceCount + "-";
    this.element = node(this.owner, "section", "spk-emulator");
    this.element.setAttribute("aria-label", "Interactive Spikeling neuronal emulator");
    this.element.dataset.layout = this.layout;
    this.element.dataset.motion = "standard";

  
    const transport = node(this.owner, "div", "spk-emulator__transport");
    transport.setAttribute("role", "group");
    transport.setAttribute("aria-label", "Simulation transport and speed");
    const transportTitle = node(this.owner, "h3", "spk-emulator__transport-title", "Simulation speed");
    this.startButton = this.transportButton("Start simulation", "start");
    this.pauseButton = this.transportButton("Pause simulation", "pause");
    this.stopButton = this.transportButton("Stop simulation", "stop");
    this.resetButton = this.transportButton("Reset simulation", "reset");
    const speedLabel = node(this.owner, "label", "spk-emulator__speed-label");
    this.speed = node(this.owner, "select", "spk-emulator__speed");
    this.speed.id = this.prefix + "speed";
    speedLabel.htmlFor = this.speed.id;
    this.speed.setAttribute("aria-label", "Simulation speed");
    this.speed.setAttribute("aria-describedby", scope.id);
    for (const [index] of DESKTOP_STEPS_PER_UPDATE.entries()) {
      const setting = getSimulationSpeed(index);
      const option = node(this.owner, "option", "", setting.realtimeMultiplier + "× real time · "
        + setting.stepsPerSecond.toLocaleString("en-GB") + " samples/s");
      option.value = String(index);
      this.speed.append(option);
    }
    speedLabel.append(this.speed);
    this.status = node(this.owner, "p", "spk-emulator__status", "Waiting for the simulation to connect.");
    this.status.setAttribute("role", "status");
    this.status.setAttribute("aria-live", "polite");
    this.status.setAttribute("aria-atomic", "true");
    transport.append(transportTitle, this.startButton, this.pauseButton, this.stopButton, this.resetButton, speedLabel, this.status);

    const workspace = node(this.owner, "div", "spk-emulator__workspace");
    const instrument = node(this.owner, "div", "spk-emulator__instrument");
    const scopeHost = node(this.owner, "div", "spk-emulator__oscilloscope");
    instrument.append(transport, scopeHost);
    workspace.append(instrument);
    const main = this.addPanel(workspace, "main", "Neuron Parameters");
    const stimulus = this.addPanel(workspace, "stimulus", "Stimulus Parameters");
    const synapses = this.addPanel(workspace, "synapses", "Synapses");
    this.element.append(workspace);

    this.error = node(this.owner, "p", "spk-emulator__error");
    this.error.setAttribute("role", "alert");
    this.element.append(this.error);

    const footer = node(this.owner, "footer", "spk-emulator__footer");
    const sourceLink = node(this.owner, "a", "spk-emulator__source", "View open-source project");
    sourceLink.href = options.sourceUrl ?? "https://github.com/OpenSourceNeuro/Spikeling";
    footer.append(sourceLink);
    this.element.append(footer);
    host.append(this.element);

    this.oscilloscope = new SpikelingOscilloscope(scopeHost, source, options.oscilloscope);
    this.controls = new SpikelingMainControls(main.content, source, {
      ...options.controls,
      compact: true,
      stimulusHost: stimulus.content,
    });
    this.recorder = new SpikelingRecorder(source, options.recorder);
    const recordingHost = node(this.owner, "div", "spk-emulator__background-recording");
    this.recording = new SpikelingRecordingControls(recordingHost, this.recorder, options.recording);
    this.synapses = new SpikelingSynapseControls(synapses.content, source, {
      ...options.synapses,
      compact: true,
      oscilloscope: this.oscilloscope,
    });

    this.disableTransport();
    this.startButton.addEventListener("click", () => this.command(() => source.start()));
    this.pauseButton.addEventListener("click", () => this.command(() => source.pause()));
    this.stopButton.addEventListener("click", () => this.command(() => source.stop()));
    this.resetButton.addEventListener("click", () => this.command(() => source.reset()));
    this.speed.addEventListener("change", () => this.command(() => source.setSpeed(Number(this.speed.value))));
    this.subscriptions.push(
      source.subscribeState((snapshot) => this.synchronise(snapshot)),
      source.subscribeErrors((failure) => this.showError(failure)),
    );
    this.initialiseMedia(options.mediaQueryFactory);
  }

  getLayout(): EmulatorLayout { return this.layout; }

  isPanelOpen(panel: EmulatorPanel): boolean {
    return this.panel(panel).details.open;
  }

  setPanelOpen(panel: EmulatorPanel, open: boolean): void {
    const selected = this.panel(panel);
    selected.details.open = open;
    selected.summary.setAttribute("aria-expanded", String(open));
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    for (const unsubscribe of this.subscriptions) unsubscribe();
    for (const query of this.mediaQueries) query.removeEventListener("change", this.handleMedia);
    this.recording.dispose();
    this.recorder.dispose();
    this.synapses.dispose();
    this.controls.dispose();
    this.oscilloscope.dispose();
    this.element.remove();
  }

  private transportButton(label: string, action: string): HTMLButtonElement {
    const button = node(this.owner, "button", "spk-emulator__button", label);
    button.type = "button";
    button.dataset.action = action;
    button.setAttribute("aria-label", label);
    return button;
  }

  private addPanel(parent: HTMLElement, panel: EmulatorPanel, label: string): PanelElements {
    const details = node(this.owner, "details", "spk-emulator__panel");
    details.dataset.panel = panel;
    details.open = true;
    const summary = node(this.owner, "summary", "spk-emulator__panel-summary", label);
    summary.id = this.prefix + panel + "-label";
    summary.setAttribute("aria-expanded", "true");
    const content = node(this.owner, "div", "spk-emulator__panel-content");
    content.id = this.prefix + panel + "-content";
    content.setAttribute("role", "region");
    content.setAttribute("aria-labelledby", summary.id);
    summary.setAttribute("aria-controls", content.id);
    details.append(summary, content);
    details.addEventListener("toggle", () => summary.setAttribute("aria-expanded", String(details.open)));
    parent.append(details);
    const elements = { details, summary, content };
    this.panels.set(panel, elements);
    return elements;
  }

  private panel(identifier: EmulatorPanel): PanelElements {
    const selected = this.panels.get(identifier);
    if (selected === undefined) throw new RangeError("Unknown emulator control panel.");
    return selected;
  }

  private disableTransport(): void {
    this.startButton.disabled = true;
    this.pauseButton.disabled = true;
    this.stopButton.disabled = true;
    this.resetButton.disabled = true;
    this.speed.disabled = true;
  }

  private synchronise(snapshot: EngineSnapshot): void {
    const running = snapshot.lifecycle === "running";
    this.startButton.disabled = running;
    this.pauseButton.disabled = !running;
    this.stopButton.disabled = snapshot.lifecycle === "idle" || snapshot.lifecycle === "stopped";
    this.resetButton.disabled = false;
    this.speed.disabled = false;
    this.speed.value = String(snapshot.speed.index);
    const label = snapshot.lifecycle === "idle" ? "Ready" : snapshot.lifecycle[0].toUpperCase() + snapshot.lifecycle.slice(1);
    this.status.textContent = label + " · " + snapshot.speed.realtimeMultiplier + "× real time · "
      + snapshot.speed.stepsPerSecond.toLocaleString("en-GB") + " samples/s wall-clock target.";
    this.status.dataset.state = snapshot.lifecycle;
  }

  private initialiseMedia(factory?: (query: string) => MediaQueryAdapter): void {
    const view = this.owner.defaultView;
    const match = factory ?? (typeof view?.matchMedia === "function" ? view.matchMedia.bind(view) : undefined);
    if (match === undefined) return;
    for (const query of [TABLET_MEDIA_QUERY, MOBILE_MEDIA_QUERY, REDUCED_MOTION_MEDIA_QUERY]) {
      const media = match(query);
      this.mediaQueries.push(media);
      media.addEventListener("change", this.handleMedia);
    }
    this.handleMedia();
  }

  private readonly handleMedia = (): void => {
    const [tablet, mobile, reduced] = this.mediaQueries;
    const next: EmulatorLayout = mobile.matches ? "mobile" : tablet.matches ? "tablet" : "desktop";
    if (next !== this.layout) {
      this.layout = next;
      this.element.dataset.layout = next;
      for (const panel of this.panels.keys()) this.setPanelOpen(panel, next !== "mobile");
      this.oscilloscope.resize();
    }
    this.element.dataset.motion = reduced.matches ? "reduced" : "standard";
  };

  private command(action: () => void): void {
    this.error.textContent = "";
    try {
      action();
    } catch (failure) {
      this.showError(failure instanceof Error ? failure : new Error("Unable to update the emulator."));
    }
  }

  private showError(error: Error): void {
    this.error.textContent = error.message;
  }
}
