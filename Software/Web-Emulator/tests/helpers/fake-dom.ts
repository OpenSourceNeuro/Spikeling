// SPDX-License-Identifier: GPL-3.0-or-later

import { RecordingCanvasContext } from "./fake-canvas.ts";

type FakeListener = () => void;

class FakeStyle {
  readonly values = new Map<string, string>();

  setProperty(name: string, value: string): void {
    this.values.set(name, value);
  }
}

export class FakeElement {
  className = "";
  textContent = "";
  readonly style = new FakeStyle();
  readonly dataset: Record<string, string> = {};
  readonly attributes = new Map<string, string>();
  readonly children: FakeElement[] = [];
  readonly listeners = new Map<string, Set<FakeListener>>();
  parent: FakeElement | undefined;
  id = "";
  type = "";
  value = "";
  min = "";
  max = "";
  step = "";
  accept = "";
  htmlFor = "";
  disabled = false;
  checked = false;
  files: Array<{ name: string; size: number; text(): Promise<string> }> | undefined;
  readonly ownerDocument: FakeDocument;
  readonly tagName: string;

  constructor(ownerDocument: FakeDocument, tagName: string) {
    this.ownerDocument = ownerDocument;
    this.tagName = tagName;
  }

  setAttribute(name: string, value: string): void {
    this.attributes.set(name, value);
  }

  append(...elements: FakeElement[]): void {
    for (const element of elements) {
      element.parent = this;
      this.children.push(element);
    }
  }

  replaceChildren(...elements: FakeElement[]): void {
    for (const child of this.children) {
      child.parent = undefined;
    }
    this.children.length = 0;
    this.append(...elements);
  }

  remove(): void {
    if (this.parent !== undefined) {
      const index = this.parent.children.indexOf(this);
      if (index >= 0) {
        this.parent.children.splice(index, 1);
      }
      this.parent = undefined;
    }
  }

  addEventListener(type: string, listener: FakeListener): void {
    const listeners = this.listeners.get(type) ?? new Set<FakeListener>();
    listeners.add(listener);
    this.listeners.set(type, listeners);
  }

  dispatch(type: string): void {
    for (const listener of this.listeners.get(type) ?? []) {
      listener();
    }
  }

  findAll(predicate: (element: FakeElement) => boolean): FakeElement[] {
    const matches = predicate(this) ? [this] : [];
    for (const child of this.children) {
      matches.push(...child.findAll(predicate));
    }
    return matches;
  }
}

export class FakeCanvasElement extends FakeElement {
  width = 0;
  height = 0;
  cssWidth = 800;
  cssHeight = 400;
  readonly context = new RecordingCanvasContext();

  constructor(owner: FakeDocument) {
    super(owner, "canvas");
  }

  getBoundingClientRect(): { width: number; height: number } {
    return { width: this.cssWidth, height: this.cssHeight };
  }

  getContext(_type: "2d"): CanvasRenderingContext2D {
    return this.context as unknown as CanvasRenderingContext2D;
  }
}

export class FakeDocument {
  hidden = false;
  readonly visibilityListeners = new Set<() => void>();
  readonly canvases: FakeCanvasElement[] = [];

  createElement(tagName: string): FakeElement {
    if (tagName === "canvas") {
      const canvas = new FakeCanvasElement(this);
      this.canvases.push(canvas);
      return canvas;
    }
    return new FakeElement(this, tagName);
  }

  createHost(): FakeElement {
    return new FakeElement(this, "div");
  }

  addEventListener(_type: "visibilitychange", listener: () => void): void {
    this.visibilityListeners.add(listener);
  }

  removeEventListener(_type: "visibilitychange", listener: () => void): void {
    this.visibilityListeners.delete(listener);
  }

  setHidden(value: boolean): void {
    this.hidden = value;
    for (const listener of this.visibilityListeners) {
      listener();
    }
  }
}
