// SPDX-License-Identifier: GPL-3.0-or-later

import type { DataSource, Unsubscribe } from "../data-source/DataSource.ts";
import { TIMESTEP_MS } from "../model/izhikevich.ts";
import type { SimulationSample } from "../model/types.ts";
import type { EngineSnapshot } from "../simulation/protocol.ts";
import {
  OscilloscopeCanvasRenderer,
} from "./canvas-renderer.ts";
import type { RenderStatistics } from "./canvas-renderer.ts";
import {
  OscilloscopeRenderLoop,
} from "./render-loop.ts";
import type {
  AnimationFrameScheduler,
  PageVisibilitySource,
} from "./render-loop.ts";
import {
  defaultVisibleTraces,
  getOscilloscopeTrace,
} from "./traces.ts";
import type { TraceField } from "./traces.ts";

export interface ResizeObserverAdapter {
  observe(element: Element): void;
  disconnect(): void;
}

export interface OscilloscopeOptions {
  readonly windowMs?: number;
  readonly frameScheduler?: AnimationFrameScheduler;
  readonly visibility?: PageVisibilitySource;
  readonly devicePixelRatio?: () => number;
  readonly resizeObserverFactory?: (callback: () => void) => ResizeObserverAdapter;
}

function createElement<K extends keyof HTMLElementTagNameMap>(
  owner: Document,
  tag: K,
  className: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const element = owner.createElement(tag);
  element.className = className;
  if (text !== undefined) {
    element.textContent = text;
  }
  return element;
}

function formatReading(value: number | undefined): string {
  if (value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  return value.toFixed(1).replace("-", "−");
}

function lifecycleLabel(snapshot: EngineSnapshot | undefined): string {
  const lifecycle = snapshot?.lifecycle ?? "idle";
  switch (lifecycle) {
    case "running":
      return "Running";
    case "paused":
      return "Paused";
    case "stopped":
      return "Stopped";
    default:
      return "Ready";
  }
}

/** Accessible desktop-matched instrument component backed only by DataSource. */
export class SpikelingOscilloscope {
  readonly element: HTMLElement;
  readonly canvas: HTMLCanvasElement;
  readonly renderer: OscilloscopeCanvasRenderer;
  readonly renderLoop: OscilloscopeRenderLoop;

  private readonly source: DataSource;
  private readonly status: HTMLElement;
  private readonly readings: HTMLElement;
  private readonly traceInputs = new Map<TraceField, HTMLInputElement>();
  private readonly visible = defaultVisibleTraces();
  private readonly subscriptions: Unsubscribe[] = [];
  private readonly resizeObserver: ResizeObserverAdapter | undefined;
  private latestSample: SimulationSample | undefined;
  private currentSnapshot: EngineSnapshot | undefined;
  private statistics: RenderStatistics | undefined;
  private disposed = false;

  constructor(host: HTMLElement, source: DataSource, options: OscilloscopeOptions = {}) {
    const owner = host.ownerDocument;
    this.source = source;
    this.element = createElement(owner, "section", "spk-oscilloscope");
    this.element.setAttribute("aria-label", "Spikeling neuronal oscilloscope");

    const header = createElement(owner, "div", "spk-oscilloscope__header");
    const title = createElement(owner, "h2", "spk-oscilloscope__title", "Neuronal oscilloscope");
    this.status = createElement(owner, "span", "spk-oscilloscope__status", "Ready");
    this.status.setAttribute("role", "status");
    this.status.setAttribute("aria-live", "polite");
    header.append(title, this.status);

    this.canvas = createElement(owner, "canvas", "spk-oscilloscope__canvas");
    this.canvas.setAttribute("role", "img");
    this.canvas.setAttribute(
      "aria-label",
      "Rolling membrane potential and input current plotted against time.",
    );

    this.readings = createElement(owner, "p", "spk-oscilloscope__readings");
    this.readings.setAttribute("aria-live", "off");
    this.readings.setAttribute("aria-atomic", "true");

    const controls = createElement(owner, "fieldset", "spk-oscilloscope__traces");
    const legend = createElement(owner, "legend", "spk-oscilloscope__legend", "Visible traces");
    controls.append(legend);

    const traceGroups: ReadonlyArray<{
      readonly id: "main" | "synapses";
      readonly label: string;
      readonly traces: readonly TraceField[];
    }> = [
      { id: "main", label: "Main-neuron traces", traces: ["mainVm", "totalCurrent", "stimulus"] },
      {
        id: "synapses",
        label: "Synapse traces",
        traces: ["synapse1Vm", "synapse1Current", "synapse2Vm", "synapse2Current"],
      },
    ];

    for (const group of traceGroups) {
      const row = createElement(owner, "div", "spk-oscilloscope__trace-row");
      row.dataset.traceGroup = group.id;
      row.setAttribute("role", "group");
      row.setAttribute("aria-label", group.label);

      for (const id of group.traces) {
        const trace = getOscilloscopeTrace(id);
        const label = createElement(owner, "label", "spk-oscilloscope__trace");
        label.style.setProperty("--spk-trace-colour", "var(" + trace.colourVariable + ")");
        const input = createElement(owner, "input", "spk-oscilloscope__trace-input");
        input.type = "checkbox";
        input.checked = this.visible.has(trace.id);
        input.setAttribute("aria-label", "Show " + trace.label.toLowerCase());
        input.addEventListener("change", () => {
          this.setTraceVisible(trace.id, input.checked);
        });
        const name = createElement(owner, "span", "spk-oscilloscope__trace-label", trace.label);
        label.append(input, name);
        row.append(label);
        this.traceInputs.set(trace.id, input);
      }

      controls.append(row);
    }

    this.element.append(header, this.canvas, this.readings, controls);
    host.append(this.element);

    this.renderer = new OscilloscopeCanvasRenderer(this.canvas, {
      windowMs: options.windowMs,
      devicePixelRatio: options.devicePixelRatio,
    });
    this.renderLoop = new OscilloscopeRenderLoop(() => this.render(), {
      scheduler: options.frameScheduler,
      visibility:
        options.visibility ??
        (typeof owner.hidden === "boolean" ? (owner as PageVisibilitySource) : undefined),
    });

    const observerFactory =
      options.resizeObserverFactory ??
      (typeof ResizeObserver === "undefined"
        ? undefined
        : (callback: () => void) => new ResizeObserver(callback));
    this.resizeObserver = observerFactory?.(() => this.resize());
    this.resizeObserver?.observe(this.canvas);

    this.subscriptions.push(
      source.subscribe((samples) => this.handleSamples(samples)),
      source.subscribeState((snapshot) => this.handleState(snapshot)),
    );
    this.updateReadings();
    this.render();
  }

  setTraceVisible(field: TraceField, visible: boolean): void {
    getOscilloscopeTrace(field);
    if (visible) {
      this.visible.add(field);
    } else {
      this.visible.delete(field);
    }

    const input = this.traceInputs.get(field);
    if (input !== undefined) {
      input.checked = visible;
    }
    this.invalidate();
  }

  isTraceVisible(field: TraceField): boolean {
    getOscilloscopeTrace(field);
    return this.visible.has(field);
  }

  getStatistics(): RenderStatistics | undefined {
    return this.statistics;
  }

  resize(): void {
    if (this.disposed) {
      return;
    }
    this.renderer.resize();
    this.invalidate();
  }

  dispose(): void {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    this.renderLoop.dispose();
    this.resizeObserver?.disconnect();
    for (const unsubscribe of this.subscriptions) {
      unsubscribe();
    }
    this.element.remove();
  }

  private handleSamples(samples: readonly SimulationSample[]): void {
    if (samples.length > 0) {
      this.latestSample = samples[samples.length - 1];
      this.updateReadings();
      this.renderLoop.invalidate();
    }
  }

  private handleState(snapshot: EngineSnapshot): void {
    this.currentSnapshot = snapshot;
    this.status.textContent = lifecycleLabel(snapshot);
    this.status.dataset.state = snapshot.lifecycle;

    if (snapshot.stepIndex === 0) {
      this.latestSample = undefined;
      this.updateReadings();
    }

    if (snapshot.lifecycle === "running") {
      this.renderLoop.start();
    } else {
      this.renderLoop.stop();
      this.render();
    }
  }

  private updateReadings(): void {
    this.readings.textContent =
      lifecycleLabel(this.currentSnapshot) +
      " · Vm " +
      formatReading(this.latestSample?.mainVm) +
      " mV · Input " +
      formatReading(this.latestSample?.totalCurrent) +
      " a.u. · Stimulus " +
      formatReading(this.latestSample?.stimulus) +
      " a.u.";
  }

  private invalidate(): void {
    if (this.renderLoop.running) {
      this.renderLoop.invalidate();
    } else {
      this.render();
    }
  }

  private render(): void {
    const visibleSamples = Math.ceil(this.renderer.windowMs / TIMESTEP_MS) + 1;
    this.statistics = this.renderer.render(this.source.latest(visibleSamples), this.visible);
  }
}
