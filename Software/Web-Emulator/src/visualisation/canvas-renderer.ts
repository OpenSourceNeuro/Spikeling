// SPDX-License-Identifier: GPL-3.0-or-later

import type { SimulationSample } from "../model/types.ts";
import {
  DESKTOP_CURRENT_RANGE,
  DESKTOP_TRACE_WIDTH_PX,
  DESKTOP_VISIBLE_WINDOW_MS,
  DESKTOP_VOLTAGE_RANGE,
  buildAxisTicks,
  calculatePlotLayout,
  formatAxisValue,
  projectX,
  projectY,
} from "./axes.ts";
import type { AxisRange, PlotLayout } from "./axes.ts";
import { decimateTrace } from "./decimation.ts";
import { DEFAULT_OSCILLOSCOPE_THEME } from "./theme.ts";
import type { OscilloscopeTheme } from "./theme.ts";
import { OSCILLOSCOPE_TRACES, getOscilloscopeTrace } from "./traces.ts";
import type { OscilloscopeTrace, TraceField } from "./traces.ts";

export interface CanvasRenderingSurface {
  width: number;
  height: number;
  getBoundingClientRect(): { readonly width: number; readonly height: number };
  getContext(context: "2d"): CanvasRenderingContext2D | null;
}

export interface OscilloscopeRendererOptions {
  readonly windowMs?: number;
  readonly voltageRange?: AxisRange;
  readonly currentRange?: AxisRange;
  readonly theme?: OscilloscopeTheme;
  readonly devicePixelRatio?: () => number;
}

export interface RenderStatistics {
  readonly sourceSamples: number;
  readonly displayedPoints: number;
  readonly enabledTraces: number;
  readonly width: number;
  readonly height: number;
}

function validateRange(range: AxisRange, label: string): AxisRange {
  if (
    !Number.isFinite(range.minimum) ||
    !Number.isFinite(range.maximum) ||
    range.minimum >= range.maximum
  ) {
    throw new RangeError(label + " must have finite, increasing limits.");
  }
  return range;
}

/** Dual-axis, straight-segment Canvas oscilloscope; no spline interpolation. */
export class OscilloscopeCanvasRenderer {
  readonly windowMs: number;
  readonly voltageRange: AxisRange;
  readonly currentRange: AxisRange;

  private readonly canvas: CanvasRenderingSurface;
  private readonly context: CanvasRenderingContext2D;
  private readonly theme: OscilloscopeTheme;
  private readonly getPixelRatio: () => number;
  private layout: PlotLayout;

  constructor(canvas: CanvasRenderingSurface, options: OscilloscopeRendererOptions = {}) {
    const context = canvas.getContext("2d");
    if (context === null) {
      throw new Error("The oscilloscope requires a 2D Canvas rendering context.");
    }

    this.windowMs = options.windowMs ?? DESKTOP_VISIBLE_WINDOW_MS;
    if (!Number.isFinite(this.windowMs) || this.windowMs <= 0) {
      throw new RangeError("The oscilloscope time window must be finite and positive.");
    }

    this.voltageRange = validateRange(
      options.voltageRange ?? DESKTOP_VOLTAGE_RANGE,
      "The voltage axis",
    );
    this.currentRange = validateRange(
      options.currentRange ?? DESKTOP_CURRENT_RANGE,
      "The current axis",
    );
    this.canvas = canvas;
    this.context = context;
    this.theme = options.theme ?? DEFAULT_OSCILLOSCOPE_THEME;
    this.getPixelRatio =
      options.devicePixelRatio ?? (() => globalThis.devicePixelRatio ?? 1);
    this.layout = calculatePlotLayout(1, 1);
    this.resize();
  }

  getLayout(): PlotLayout {
    return this.layout;
  }

  resize(): PlotLayout {
    const bounds = this.canvas.getBoundingClientRect();
    const width = Math.max(1, Math.round(bounds.width));
    const height = Math.max(1, Math.round(bounds.height));
    const suppliedRatio = this.getPixelRatio();
    const ratio = Number.isFinite(suppliedRatio) && suppliedRatio > 0 ? suppliedRatio : 1;
    this.canvas.width = Math.max(1, Math.round(width * ratio));
    this.canvas.height = Math.max(1, Math.round(height * ratio));
    this.context.setTransform(ratio, 0, 0, ratio, 0, 0);
    this.layout = calculatePlotLayout(width, height);
    return this.layout;
  }

  render(
    samples: readonly SimulationSample[],
    enabledTraces: ReadonlySet<TraceField>,
  ): RenderStatistics {
    const context = this.context;
    const layout = this.layout;
    context.clearRect(0, 0, layout.width, layout.height);
    context.fillStyle = this.theme.background;
    context.fillRect(0, 0, layout.width, layout.height);
    this.drawAxes();

    let displayedPoints = 0;
    let enabled = 0;

    context.save();
    context.beginPath();
    context.rect(layout.left, layout.top, layout.plotWidth, layout.plotHeight);
    context.clip();

    for (const trace of OSCILLOSCOPE_TRACES) {
      if (!enabledTraces.has(trace.id)) {
        continue;
      }
      enabled += 1;
      displayedPoints += this.drawTrace(samples, trace);
    }

    context.restore();

    return {
      sourceSamples: samples.length,
      displayedPoints,
      enabledTraces: enabled,
      width: layout.width,
      height: layout.height,
    };
  }

  traceColour(field: TraceField): string {
    return getOscilloscopeTrace(field).colour;
  }

  private drawAxes(): void {
    const context = this.context;
    const layout = this.layout;
    const xTicks = buildAxisTicks({ minimum: -this.windowMs, maximum: 0 }, this.windowMs / 5);
    const voltageTicks = buildAxisTicks(this.voltageRange, 30);
    const currentTicks = buildAxisTicks(this.currentRange, 50);

    context.lineWidth = 1;
    context.strokeStyle = this.theme.grid;
    context.fillStyle = this.theme.muted;
    context.font = layout.compact
      ? "11px system-ui, sans-serif"
      : "12px system-ui, sans-serif";

    for (const tick of xTicks) {
      const x = projectX(tick, this.windowMs, layout);
      context.beginPath();
      context.moveTo(x, layout.top);
      context.lineTo(x, layout.top + layout.plotHeight);
      context.stroke();
      context.textAlign = "center";
      context.textBaseline = "top";
      context.fillText(formatAxisValue(tick), x, layout.top + layout.plotHeight + 8);
    }

    for (const tick of voltageTicks) {
      const y = projectY(tick, this.voltageRange, layout);
      context.beginPath();
      context.moveTo(layout.left, y);
      context.lineTo(layout.left + layout.plotWidth, y);
      context.stroke();
      context.textAlign = "right";
      context.textBaseline = "middle";
      context.fillText(formatAxisValue(tick), layout.left - 8, y);
    }

    for (const tick of currentTicks) {
      const y = projectY(tick, this.currentRange, layout);
      context.textAlign = "left";
      context.textBaseline = "middle";
      context.fillText(formatAxisValue(tick), layout.left + layout.plotWidth + 8, y);
    }

    context.fillStyle = this.theme.text;
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(
      "Time (ms)",
      layout.left + layout.plotWidth / 2,
      layout.height - (layout.compact ? 10 : 14),
    );

    context.save();
    context.translate(layout.compact ? 12 : 16, layout.top + layout.plotHeight / 2);
    context.rotate(-Math.PI / 2);
    context.fillText(layout.compact ? "Vm (mV)" : "Membrane potential (mV)", 0, 0);
    context.restore();

    context.save();
    context.translate(
      layout.width - (layout.compact ? 10 : 14),
      layout.top + layout.plotHeight / 2,
    );
    context.rotate(Math.PI / 2);
    context.fillText(layout.compact ? "I (a.u.)" : "Current input (a.u.)", 0, 0);
    context.restore();
  }

  private drawTrace(samples: readonly SimulationSample[], trace: OscilloscopeTrace): number {
    const points = decimateTrace(samples, {
      field: trace.id,
      pixelWidth: this.layout.plotWidth,
      windowMs: this.windowMs,
    });

    if (points.length === 0) {
      return 0;
    }

    const range = trace.axis === "voltage" ? this.voltageRange : this.currentRange;
    const context = this.context;
    context.strokeStyle = trace.colour;
    context.lineWidth = DESKTOP_TRACE_WIDTH_PX;
    context.beginPath();

    for (let index = 0; index < points.length; index += 1) {
      const point = points[index];
      const x = projectX(point.relativeTimeMs, this.windowMs, this.layout);
      const y = projectY(point.value, range, this.layout);
      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    }

    context.stroke();
    return points.length;
  }
}
