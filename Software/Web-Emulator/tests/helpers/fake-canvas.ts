// SPDX-License-Identifier: GPL-3.0-or-later

import type {
  AnimationFrameScheduler,
  CanvasRenderingSurface,
  PageVisibilitySource,
} from "../../src/index.ts";

export interface RecordedStroke {
  readonly colour: string;
  readonly width: number;
  readonly points: ReadonlyArray<{ readonly x: number; readonly y: number }>;
}

export interface RecordedLabel {
  readonly text: string;
  readonly x: number;
  readonly y: number;
}

/** Tiny recording Canvas context; it intentionally offers no smoothing APIs. */
export class RecordingCanvasContext {
  fillStyle = "";
  strokeStyle = "";
  lineWidth = 1;
  font = "";
  textAlign = "start";
  textBaseline = "alphabetic";
  readonly strokes: RecordedStroke[] = [];
  readonly labels: RecordedLabel[] = [];
  readonly transforms: number[][] = [];
  readonly fills: Array<{ x: number; y: number; width: number; height: number }> = [];
  readonly clips: Array<{ x: number; y: number; width: number; height: number }> = [];

  private currentPath: Array<{ x: number; y: number }> = [];
  private clippingRectangle:
    | { x: number; y: number; width: number; height: number }
    | undefined;

  setTransform(...values: number[]): void {
    this.transforms.push(values);
  }

  clearRect(_x: number, _y: number, _width: number, _height: number): void {}

  fillRect(x: number, y: number, width: number, height: number): void {
    this.fills.push({ x, y, width, height });
  }

  beginPath(): void {
    this.currentPath = [];
    this.clippingRectangle = undefined;
  }

  moveTo(x: number, y: number): void {
    this.currentPath.push({ x, y });
  }

  lineTo(x: number, y: number): void {
    this.currentPath.push({ x, y });
  }

  stroke(): void {
    this.strokes.push({
      colour: this.strokeStyle,
      width: this.lineWidth,
      points: [...this.currentPath],
    });
  }

  fillText(text: string, x: number, y: number): void {
    this.labels.push({ text, x, y });
  }

  rect(x: number, y: number, width: number, height: number): void {
    this.clippingRectangle = { x, y, width, height };
  }

  clip(): void {
    if (this.clippingRectangle !== undefined) {
      this.clips.push(this.clippingRectangle);
    }
  }

  save(): void {}
  restore(): void {}
  translate(_x: number, _y: number): void {}
  rotate(_radians: number): void {}
}

export class RecordingCanvas implements CanvasRenderingSurface {
  width = 0;
  height = 0;
  readonly context = new RecordingCanvasContext();
  cssWidth: number;
  cssHeight: number;

  constructor(cssWidth = 800, cssHeight = 400) {
    this.cssWidth = cssWidth;
    this.cssHeight = cssHeight;
  }

  getBoundingClientRect(): { width: number; height: number } {
    return { width: this.cssWidth, height: this.cssHeight };
  }

  getContext(_kind: "2d"): CanvasRenderingContext2D {
    return this.context as unknown as CanvasRenderingContext2D;
  }
}

export class ManualAnimationFrames implements AnimationFrameScheduler {
  private nextHandle = 1;
  private readonly callbacks = new Map<number, (timestamp: number) => void>();

  get pending(): number {
    return this.callbacks.size;
  }

  request(callback: (timestamp: number) => void): number {
    const handle = this.nextHandle;
    this.nextHandle += 1;
    this.callbacks.set(handle, callback);
    return handle;
  }

  cancel(handle: number): void {
    this.callbacks.delete(handle);
  }

  advance(timestamp = 16): number {
    const callbacks = Array.from(this.callbacks.entries());
    for (const [handle, callback] of callbacks) {
      this.callbacks.delete(handle);
      callback(timestamp);
    }
    return callbacks.length;
  }
}

export class ManualPageVisibility implements PageVisibilitySource {
  hidden = false;
  readonly listeners = new Set<() => void>();

  addEventListener(_type: "visibilitychange", listener: () => void): void {
    this.listeners.add(listener);
  }

  removeEventListener(_type: "visibilitychange", listener: () => void): void {
    this.listeners.delete(listener);
  }

  setHidden(hidden: boolean): void {
    this.hidden = hidden;
    for (const listener of this.listeners) {
      listener();
    }
  }
}
