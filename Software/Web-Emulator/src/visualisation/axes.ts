// SPDX-License-Identifier: GPL-3.0-or-later

export const DESKTOP_VISIBLE_WINDOW_MS = 500;
export const DESKTOP_VOLTAGE_MIN_MV = -90;
export const DESKTOP_VOLTAGE_MAX_MV = 30;
export const DESKTOP_CURRENT_MIN = -100;
export const DESKTOP_CURRENT_MAX = 100;
export const DESKTOP_TRACE_WIDTH_PX = 1;

export interface AxisRange {
  readonly minimum: number;
  readonly maximum: number;
}

export interface PlotLayout {
  readonly width: number;
  readonly height: number;
  readonly left: number;
  readonly right: number;
  readonly top: number;
  readonly bottom: number;
  readonly plotWidth: number;
  readonly plotHeight: number;
  readonly compact: boolean;
}

export const DESKTOP_VOLTAGE_RANGE: AxisRange = Object.freeze({
  minimum: DESKTOP_VOLTAGE_MIN_MV,
  maximum: DESKTOP_VOLTAGE_MAX_MV,
});

export const DESKTOP_CURRENT_RANGE: AxisRange = Object.freeze({
  minimum: DESKTOP_CURRENT_MIN,
  maximum: DESKTOP_CURRENT_MAX,
});

export function calculatePlotLayout(width: number, height: number): PlotLayout {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    throw new RangeError("Oscilloscope dimensions must be finite positive numbers.");
  }

  const compact = width < 540;
  const left = compact ? 56 : 76;
  const right = compact ? 52 : 72;
  const top = compact ? 18 : 24;
  const bottom = compact ? 46 : 56;

  return {
    width,
    height,
    left,
    right,
    top,
    bottom,
    plotWidth: Math.max(1, width - left - right),
    plotHeight: Math.max(1, height - top - bottom),
    compact,
  };
}

export function buildAxisTicks(range: AxisRange, interval: number): number[] {
  if (
    !Number.isFinite(range.minimum) ||
    !Number.isFinite(range.maximum) ||
    range.minimum >= range.maximum ||
    !Number.isFinite(interval) ||
    interval <= 0
  ) {
    throw new RangeError("Axis ticks require an increasing range and positive interval.");
  }

  const ticks: number[] = [];
  const first = Math.ceil(range.minimum / interval) * interval;
  for (let value = first; value <= range.maximum + interval * 1e-9; value += interval) {
    ticks.push(Object.is(value, -0) ? 0 : Number(value.toPrecision(12)));
  }
  return ticks;
}

export function projectX(relativeTimeMs: number, windowMs: number, layout: PlotLayout): number {
  return layout.left + ((relativeTimeMs + windowMs) / windowMs) * layout.plotWidth;
}

export function projectY(value: number, range: AxisRange, layout: PlotLayout): number {
  return (
    layout.top +
    ((range.maximum - value) / (range.maximum - range.minimum)) * layout.plotHeight
  );
}

export function formatAxisValue(value: number): string {
  const normalised = Math.abs(value) < 1e-10 ? 0 : value;
  return String(normalised).replace("-", "−");
}
