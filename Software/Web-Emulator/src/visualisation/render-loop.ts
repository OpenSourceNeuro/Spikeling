// SPDX-License-Identifier: GPL-3.0-or-later

export interface AnimationFrameScheduler {
  request(callback: (timestamp: number) => void): number;
  cancel(handle: number): void;
}

export interface PageVisibilitySource {
  readonly hidden: boolean;
  addEventListener(type: "visibilitychange", listener: () => void): void;
  removeEventListener(type: "visibilitychange", listener: () => void): void;
}

export interface OscilloscopeRenderLoopOptions {
  readonly scheduler?: AnimationFrameScheduler;
  readonly visibility?: PageVisibilitySource;
}

const browserScheduler: AnimationFrameScheduler = {
  request: (callback) => requestAnimationFrame(callback),
  cancel: (handle) => cancelAnimationFrame(handle),
};

/** Coalesces any number of worker batches into at most one browser paint. */
export class OscilloscopeRenderLoop {
  private readonly render: (timestamp: number) => void;
  private readonly scheduler: AnimationFrameScheduler;
  private readonly visibility: PageVisibilitySource | undefined;
  private active = false;
  private dirty = false;
  private frameHandle: number | undefined;

  constructor(
    render: (timestamp: number) => void,
    options: OscilloscopeRenderLoopOptions = {},
  ) {
    this.render = render;
    this.scheduler = options.scheduler ?? browserScheduler;
    this.visibility = options.visibility;
    this.visibility?.addEventListener("visibilitychange", this.handleVisibility);
  }

  get running(): boolean {
    return this.active;
  }

  get scheduled(): boolean {
    return this.frameHandle !== undefined;
  }

  start(): void {
    if (this.active) {
      return;
    }
    this.active = true;
    this.invalidate();
  }

  stop(): void {
    this.active = false;
    this.dirty = false;
    this.cancelFrame();
  }

  invalidate(): void {
    this.dirty = true;
    if (this.active && !this.visibility?.hidden && this.frameHandle === undefined) {
      this.frameHandle = this.scheduler.request(this.handleFrame);
    }
  }

  dispose(): void {
    this.stop();
    this.visibility?.removeEventListener("visibilitychange", this.handleVisibility);
  }

  private cancelFrame(): void {
    if (this.frameHandle !== undefined) {
      this.scheduler.cancel(this.frameHandle);
      this.frameHandle = undefined;
    }
  }

  private readonly handleFrame = (timestamp: number): void => {
    this.frameHandle = undefined;
    if (!this.active || this.visibility?.hidden || !this.dirty) {
      return;
    }

    this.dirty = false;
    this.render(timestamp);
    if (this.dirty) {
      this.invalidate();
    }
  };

  private readonly handleVisibility = (): void => {
    if (this.visibility?.hidden) {
      this.cancelFrame();
    } else if (this.active) {
      this.invalidate();
    }
  };
}
