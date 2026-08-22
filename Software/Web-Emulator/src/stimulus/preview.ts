// SPDX-License-Identifier: GPL-3.0-or-later

import { SPIKELING_PALETTE } from "../visualisation/theme.ts";

export interface StimulusPreviewSurface {
  width: number;
  height: number;
  getBoundingClientRect(): { readonly width: number; readonly height: number };
  getContext(context: "2d"): CanvasRenderingContext2D | null;
}

export interface StimulusPreviewStatistics {
  readonly samples: number;
  readonly displayedPoints: number;
  readonly minimum: number;
  readonly maximum: number;
}

/** Compact local-file waveform preview, keeping per-pixel minima and maxima. */
export function renderStimulusPreview(
  canvas: StimulusPreviewSurface,
  samples: readonly number[],
  pixelRatio = globalThis.devicePixelRatio ?? 1,
): StimulusPreviewStatistics {
  const context = canvas.getContext("2d");
  if (context === null) {
    throw new Error("The stimulus preview requires a 2D Canvas rendering context.");
  }
  if (!Number.isFinite(pixelRatio) || pixelRatio <= 0) {
    throw new RangeError("The stimulus-preview device pixel ratio must be positive.");
  }

  const bounds = canvas.getBoundingClientRect();
  const width = Math.max(1, Math.round(bounds.width));
  const height = Math.max(1, Math.round(bounds.height));
  canvas.width = Math.round(width * pixelRatio);
  canvas.height = Math.round(height * pixelRatio);
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  context.fillStyle = SPIKELING_PALETTE.backgroundDeep;
  context.fillRect(0, 0, width, height);

  if (samples.length === 0) {
    return { samples: 0, displayedPoints: 0, minimum: 0, maximum: 0 };
  }

  let minimum = Number.POSITIVE_INFINITY;
  let maximum = Number.NEGATIVE_INFINITY;
  for (const sample of samples) {
    if (!Number.isFinite(sample)) {
      throw new RangeError("Stimulus-preview samples must be finite.");
    }
    minimum = Math.min(minimum, sample);
    maximum = Math.max(maximum, sample);
  }

  const low = Math.min(minimum, 0);
  const high = Math.max(maximum, 0);
  const span = high - low || 1;
  const verticalPadding = 6;
  const availableHeight = Math.max(1, height - verticalPadding * 2);
  const projectY = (value: number) =>
    verticalPadding + ((high - value) / span) * availableHeight;

  context.strokeStyle = SPIKELING_PALETTE.panel;
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(0, projectY(0));
  context.lineTo(width, projectY(0));
  context.stroke();

  context.strokeStyle = SPIKELING_PALETTE.stimulus;
  context.beginPath();
  let displayedPoints = 0;
  let first = true;

  const columns = Math.min(width, samples.length);
  for (let pixel = 0; pixel < columns; pixel += 1) {
    const start = Math.floor((pixel / columns) * samples.length);
    const end = Math.min(
      samples.length,
      Math.max(start + 1, Math.floor(((pixel + 1) / columns) * samples.length)),
    );
    let lowIndex = start;
    let highIndex = start;
    for (let index = start + 1; index < end; index += 1) {
      if (samples[index] < samples[lowIndex]) {
        lowIndex = index;
      }
      if (samples[index] > samples[highIndex]) {
        highIndex = index;
      }
    }
    const indices = Array.from(new Set([start, lowIndex, highIndex, end - 1])).sort(
      (left, right) => left - right,
    );
    for (const index of indices) {
      const x = samples.length === 1 ? 0 : (index / (samples.length - 1)) * width;
      const y = projectY(samples[index]);
      if (first) {
        context.moveTo(x, y);
        first = false;
      } else {
        context.lineTo(x, y);
      }
      displayedPoints += 1;
    }
  }
  context.stroke();

  return { samples: samples.length, displayedPoints, minimum, maximum };
}
