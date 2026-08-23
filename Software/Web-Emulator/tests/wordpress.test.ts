// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  DEFAULT_WORDPRESS_SEED,
  MAX_WORDPRESS_RECORDING_SAMPLES,
  WORDPRESS_EMULATOR_SELECTOR,
  SimulationEngine,
  initialiseWordPressEmulators,
  mountWordPressEmulator,
  parseWordPressConfiguration,
} from "../src/index.ts";
import type {
  ControlsPatch,
  DataSource,
  ErrorListener,
  RecordingSnapshot,
  SampleListener,
  SimulationSample,
  StateListener,
  Unsubscribe,
  WordPressConfiguration,
  WordPressIntegrationOptions,
  WordPressObserver,
} from "../src/index.ts";
import { ManualAnimationFrames } from "./helpers/fake-canvas.ts";
import { FakeDocument, FakeElement } from "./helpers/fake-dom.ts";
import { ManualScheduler } from "./helpers/manual-scheduler.ts";

class WordPressSource implements DataSource {
  readonly kind = "emulator";
  readonly scheduler = new ManualScheduler();
  readonly sampleListeners = new Set<SampleListener>();
  readonly stateListeners = new Set<StateListener>();
  readonly errorListeners = new Set<ErrorListener>();
  readonly engine: SimulationEngine;
  connects = 0;
  disconnects = 0;
  failure: Error | undefined;

  constructor(configuration: WordPressConfiguration = { speedIndex: 2, seed: 123456, maxSamples: 200 }) {
    this.engine = new SimulationEngine({
      modelOptions: { seed: configuration.seed },
      speedIndex: configuration.speedIndex,
      scheduler: this.scheduler,
      onSamples: (samples) => { for (const listener of this.sampleListeners) listener(samples); },
      onState: (snapshot) => { for (const listener of this.stateListeners) listener(snapshot); },
    });
  }

  async connect(): Promise<void> {
    this.connects += 1;
    if (this.failure !== undefined) throw this.failure;
    for (const listener of this.stateListeners) listener(this.engine.getSnapshot());
  }

  async disconnect(): Promise<void> { this.disconnects += 1; this.engine.dispose(); }
  start(): void { this.engine.start(); }
  pause(): void { this.engine.pause(); }
  stop(): void { this.engine.stop(); }
  reset(): void { this.engine.reset(); }
  setSpeed(index: number): void { this.engine.setSpeed(index); }
  updateControls(patch: ControlsPatch): void { this.engine.updateControls(patch); }
  requestSnapshot(): void { for (const listener of this.stateListeners) listener(this.engine.getSnapshot()); }
  latest(count?: number): SimulationSample[] { return this.engine.history.latest(count); }
  subscribe(listener: SampleListener): Unsubscribe { this.sampleListeners.add(listener); return () => this.sampleListeners.delete(listener); }
  subscribeState(listener: StateListener): Unsubscribe { this.stateListeners.add(listener); return () => this.stateListeners.delete(listener); }
  subscribeErrors(listener: ErrorListener): Unsubscribe { this.errorListeners.add(listener); return () => this.errorListeners.delete(listener); }
}

class WordPressDocument extends FakeDocument {
  readyState = "complete";
  readonly body = this.createHost();
  readonly roots: FakeElement[] = [];
  readonly events = new Map<string, Set<() => void>>();

  createRoot(values: Record<string, string> = {}): FakeElement {
    const root = this.createHost();
    root.dataset.spikelingEmulator = "1";
    Object.assign(root.dataset, values);
    this.roots.push(root);
    this.body.append(root);
    return root;
  }

  querySelectorAll(selector: string): HTMLElement[] {
    assert.equal(selector, WORDPRESS_EMULATOR_SELECTOR);
    return this.roots as unknown as HTMLElement[];
  }

  override addEventListener(type: "visibilitychange", listener: () => void): void {
    if (type === "visibilitychange") {
      super.addEventListener(type, listener);
      return;
    }
    const listeners = this.events.get(type) ?? new Set<() => void>();
    listeners.add(listener);
    this.events.set(type, listeners);
  }

  override removeEventListener(type: "visibilitychange", listener: () => void): void {
    if (type === "visibilitychange") {
      super.removeEventListener(type, listener);
      return;
    }
    this.events.get(type)?.delete(listener);
  }

  dispatch(type: string): void {
    for (const listener of this.events.get(type) ?? []) listener();
  }
}

class FakeEventTarget {
  readonly events = new Map<string, Set<() => void>>();
  addEventListener(type: string, listener: () => void): void {
    const listeners = this.events.get(type) ?? new Set<() => void>();
    listeners.add(listener);
    this.events.set(type, listeners);
  }
  removeEventListener(type: string, listener: () => void): void { this.events.get(type)?.delete(listener); }
  dispatch(type: string): void { for (const listener of this.events.get(type) ?? []) listener(); }
}

class FakeObserver implements WordPressObserver {
  readonly callback: () => void;
  target: Node | undefined;
  options: MutationObserverInit | undefined;
  disconnected = false;
  constructor(callback: () => void) { this.callback = callback; }
  observe(target: Node, options: MutationObserverInit): void { this.target = target; this.options = options; }
  disconnect(): void { this.disconnected = true; }
  trigger(): void { this.callback(); }
}

function documentAndRoot(values: Record<string, string> = {}): { owner: WordPressDocument; root: FakeElement } {
  const owner = new WordPressDocument();
  return { owner, root: owner.createRoot(values) };
}

function optionsFor(source: WordPressSource): WordPressIntegrationOptions {
  return {
    sourceFactory: () => source,
    interfaceOptions: { oscilloscope: { frameScheduler: new ManualAnimationFrames() } },
  };
}

async function flush(): Promise<void> {
  await new Promise<void>((resolve) => setTimeout(resolve, 0));
}

test("WordPress mount selector and safe scientific defaults are source-pinned", () => {
  const { root } = documentAndRoot();
  assert.equal(WORDPRESS_EMULATOR_SELECTOR, "[data-spikeling-emulator]");
  assert.equal(DEFAULT_WORDPRESS_SEED, 123_456);
  assert.equal(MAX_WORDPRESS_RECORDING_SAMPLES, 1_000_000);
  assert.deepEqual(parseWordPressConfiguration(root as unknown as HTMLElement), {
    speedIndex: 2,
    seed: 123_456,
    maxSamples: 250_000,
  });
});

test("shortcode data attributes preserve explicit speed, random seed and recording capacity", () => {
  const { root } = documentAndRoot({ spikelingSpeed: "5", spikelingSeed: "4294967295", spikelingMaxSamples: "1000000" });
  assert.deepEqual(parseWordPressConfiguration(root as unknown as HTMLElement), {
    speedIndex: 5,
    seed: 4_294_967_295,
    maxSamples: 1_000_000,
  });
  root.dataset.spikelingSpeed = "";
  assert.equal(parseWordPressConfiguration(root as unknown as HTMLElement).speedIndex, 2);
});

test("unsafe shortcode configuration cannot bypass model or browser-memory bounds", () => {
  const checks: Array<[string, string, RegExp]> = [
    ["spikelingSpeed", "-1", /positive integer/],
    ["spikelingSpeed", "6", /between 0 and 5/],
    ["spikelingSpeed", "2.5", /positive integer/],
    ["spikelingSeed", "0", /between 1 and 4294967295/],
    ["spikelingSeed", "4294967296", /between 1 and 4294967295/],
    ["spikelingMaxSamples", "0", /between 1 and 1000000/],
    ["spikelingMaxSamples", "1000001", /between 1 and 1000000/],
    ["spikelingMaxSamples", "9007199254740992", /between 1 and 1000000/],
    ["spikelingSeed", "NaN", /positive integer/],
    ["spikelingSeed", "0x20", /positive integer/],
  ];
  for (const [key, value, expected] of checks) {
    const { root } = documentAndRoot({ [key]: value });
    assert.throws(() => parseWordPressConfiguration(root as unknown as HTMLElement), expected);
  }
});

test("a shortcode root mounts once and preserves bounded worker and recording configuration", async () => {
  const { root } = documentAndRoot({ spikelingSpeed: "1", spikelingSeed: "800", spikelingMaxSamples: "50" });
  let captured: WordPressConfiguration | undefined;
  let created: WordPressSource | undefined;
  const options: WordPressIntegrationOptions = {
    sourceFactory: (configuration) => { captured = configuration; created = new WordPressSource(configuration); return created; },
    interfaceOptions: { oscilloscope: { frameScheduler: new ManualAnimationFrames() } },
  };
  const first = mountWordPressEmulator(root as unknown as HTMLElement, options);
  const duplicate = mountWordPressEmulator(root as unknown as HTMLElement, options);
  assert.equal(first, duplicate);
  assert.equal(root.dataset.spikelingState, "mounting");
  const mounted = await first;
  assert.deepEqual(captured, { speedIndex: 1, seed: 800, maxSamples: 50 });
  assert.equal(created?.connects, 1);
  assert.equal(mounted.emulator.recorder.getSnapshot().maxSamples, 50);
  assert.equal(root.dataset.spikelingState, "ready");
  await mounted.dispose();
  await mounted.dispose();
  assert.equal(created?.disconnects, 1);
  assert.equal(root.dataset.spikelingState, "disposed");
});

test("configuration failures appear as accessible root-local errors before a worker is created", async () => {
  const { root } = documentAndRoot({ spikelingSpeed: "99" });
  let created = false;
  await assert.rejects(mountWordPressEmulator(root as unknown as HTMLElement, {
    sourceFactory: () => { created = true; return new WordPressSource(); },
  }), /between 0 and 5/);
  assert.equal(created, false);
  assert.equal(root.dataset.spikelingState, "error");
  const alert = root.findAll((element) => element.attributes.get("role") === "alert").at(-1);
  assert.match(alert?.textContent ?? "", /Simulation speed/);
});

test("source-construction failures never initialise unrelated Elementor content", async () => {
  const { root } = documentAndRoot();
  await assert.rejects(mountWordPressEmulator(root as unknown as HTMLElement, {
    sourceFactory: () => { throw new Error("Unsupported worker environment"); },
  }), /Unsupported worker environment/);
  assert.equal(root.dataset.spikelingState, "error");
  assert.match(root.children.at(-1)?.textContent ?? "", /Unsupported worker environment/);
});

test("the default production worker source fails locally without leaking its mounted interface", async () => {
  const { root } = documentAndRoot({ spikelingSpeed: "3", spikelingSeed: "42" });
  await assert.rejects(mountWordPressEmulator(root as unknown as HTMLElement, {
    interfaceOptions: { oscilloscope: { frameScheduler: new ManualAnimationFrames() } },
  }), /Worker is not defined/);
  assert.equal(root.dataset.spikelingState, "error");
  assert.equal(root.findAll((node) => node.className === "spk-emulator").length, 0);
});

test("worker connection failures clean up the mounted shell and permit a later retry", async () => {
  const { root } = documentAndRoot({ spikelingMaxSamples: "5" });
  const source = new WordPressSource();
  source.failure = new Error("Worker initialisation failed");
  await assert.rejects(mountWordPressEmulator(root as unknown as HTMLElement, optionsFor(source)), /Worker initialisation failed/);
  assert.equal(root.dataset.spikelingState, "error");
  assert.equal(source.disconnects, 1);
  assert.equal(root.findAll((node) => node.className === "spk-emulator").length, 0);
  const replacement = new WordPressSource();
  const mounted = await mountWordPressEmulator(root as unknown as HTMLElement, optionsFor(replacement));
  assert.equal(root.dataset.spikelingState, "ready");
  await mounted.dispose();
  assert.equal(replacement.disconnects, 1);
});

test("cleanup errors never replace the original worker initialisation failure", async () => {
  const { root } = documentAndRoot();
  const source = new WordPressSource();
  source.failure = new Error("Original worker failure");
  source.disconnect = async () => {
    source.disconnects += 1;
    throw new Error("Secondary cleanup failure");
  };
  await assert.rejects(mountWordPressEmulator(root as unknown as HTMLElement, optionsFor(source)), /Original worker failure/);
  assert.equal(source.disconnects, 1);
  assert.equal(root.dataset.spikelingState, "error");
  assert.match(root.children.at(-1)?.textContent ?? "", /Original worker failure/);
});

test("unknown host failures remain accessible without leaking unsanitised exception values", async () => {
  const { root } = documentAndRoot();
  await assert.rejects(mountWordPressEmulator(root as unknown as HTMLElement, {
    sourceFactory: () => { throw "non-error host failure"; },
  }), (failure: unknown) => failure === "non-error host failure");
  assert.match(root.children.at(-1)?.textContent ?? "", /Unable to initialise the neuronal emulator/);
});

test("document controller stays idle on unrelated pages without shortcode roots", async () => {
  const owner = new WordPressDocument();
  let sources = 0;
  const controller = initialiseWordPressEmulators(owner as unknown as Document, {
    sourceFactory: () => { sources += 1; return new WordPressSource(); },
  });
  await flush();
  assert.equal(sources, 0);
  await controller.dispose();
});

test("repeated Elementor bootstrap returns exactly one controller per document", async () => {
  const { owner, root } = documentAndRoot({ spikelingMaxSamples: "10" });
  const source = new WordPressSource();
  const first = initialiseWordPressEmulators(owner as unknown as Document, optionsFor(source));
  const second = initialiseWordPressEmulators(owner as unknown as Document, optionsFor(source));
  assert.equal(first, second);
  first.scan();
  second.scan();
  await flush();
  assert.equal(source.connects, 1);
  assert.equal(root.findAll((node) => node.className === "spk-emulator").length, 1);
  await first.dispose();
});

test("loading documents defer scientific initialisation until DOMContentLoaded", async () => {
  const { owner, root } = documentAndRoot({ spikelingMaxSamples: "10" });
  owner.readyState = "loading";
  const source = new WordPressSource();
  const controller = initialiseWordPressEmulators(owner as unknown as Document, optionsFor(source));
  assert.equal(source.connects, 0);
  assert.equal(root.children.length, 0);
  owner.readyState = "complete";
  owner.dispatch("DOMContentLoaded");
  await flush();
  assert.equal(source.connects, 1);
  await controller.dispose();
});

test("DOM mutation discovery mounts newly inserted Elementor shortcode roots only once", async () => {
  const owner = new WordPressDocument();
  const sources: WordPressSource[] = [];
  let observer: FakeObserver | undefined;
  const controller = initialiseWordPressEmulators(owner as unknown as Document, {
    sourceFactory: () => { const source = new WordPressSource(); sources.push(source); return source; },
    interfaceOptions: { oscilloscope: { frameScheduler: new ManualAnimationFrames() } },
    observerFactory: (callback) => { observer = new FakeObserver(callback); return observer; },
  });
  assert.ok(observer);
  assert.equal(observer.options?.subtree, true);
  const root = owner.createRoot({ spikelingMaxSamples: "12" });
  observer.trigger();
  observer.trigger();
  await flush();
  assert.equal(sources.length, 1);
  assert.equal(root.dataset.spikelingState, "ready");
  await controller.dispose();
  assert.equal(observer.disconnected, true);
});

test("Elementor frontend-init events reuse existing roots and discover newly rendered widgets", async () => {
  const { owner } = documentAndRoot({ spikelingMaxSamples: "10" });
  const target = new FakeEventTarget();
  const sources: WordPressSource[] = [];
  const controller = initialiseWordPressEmulators(owner as unknown as Document, {
    eventTarget: target as unknown as Pick<Window, "addEventListener" | "removeEventListener">,
    sourceFactory: () => { const source = new WordPressSource(); sources.push(source); return source; },
    interfaceOptions: { oscilloscope: { frameScheduler: new ManualAnimationFrames() } },
  });
  await flush();
  owner.createRoot({ spikelingMaxSamples: "11" });
  target.dispatch("elementor/frontend/init");
  target.dispatch("elementor/frontend/init");
  await flush();
  assert.equal(sources.length, 2);
  assert.equal(sources[0].connects, 1);
  assert.equal(sources[1].connects, 1);
  await controller.dispose();
});

test("native MutationObserver integrates with ordinary WordPress without a custom adapter", async () => {
  const { owner, root } = documentAndRoot();
  const source = new WordPressSource();
  let observed: FakeObserver | undefined;
  const globals = globalThis as unknown as { MutationObserver?: typeof MutationObserver };
  const previous = globals.MutationObserver;
  globals.MutationObserver = class {
    constructor(callback: () => void) {
      observed = new FakeObserver(callback);
      return observed;
    }
  } as unknown as typeof MutationObserver;

  try {
    const controller = initialiseWordPressEmulators(owner as unknown as Document, optionsFor(source));
    await flush();
    assert.equal(root.dataset.spikelingState, "ready");
    assert.equal(observed?.target, owner.body);
    observed?.trigger();
    assert.equal(source.connects, 1);
    await controller.dispose();
    assert.equal(observed?.disconnected, true);
  } finally {
    if (previous === undefined) delete globals.MutationObserver;
    else globals.MutationObserver = previous;
  }
});

test("pagehide disposes all workers, render loops and Elementor listeners without touching siblings", async () => {
  const { owner, root } = documentAndRoot({ spikelingMaxSamples: "10" });
  const target = new FakeEventTarget();
  const source = new WordPressSource();
  const controller = initialiseWordPressEmulators(owner as unknown as Document, {
    ...optionsFor(source),
    eventTarget: target as unknown as Pick<Window, "addEventListener" | "removeEventListener">,
  });
  await flush();
  source.start();
  source.scheduler.advance(50);
  target.dispatch("pagehide");
  await flush();
  assert.equal(source.disconnects, 1);
  assert.equal(root.dataset.spikelingState, "disposed");
  assert.equal(target.events.get("pagehide")?.size, 0);
  assert.equal(target.events.get("elementor/frontend/init")?.size, 0);
  await controller.dispose();
});

test("controller disposal before DOM readiness cancels pending mount and remains idempotent", async () => {
  const { owner } = documentAndRoot();
  owner.readyState = "loading";
  const source = new WordPressSource();
  const controller = initialiseWordPressEmulators(owner as unknown as Document, optionsFor(source));
  await controller.dispose();
  await controller.dispose();
  owner.dispatch("DOMContentLoaded");
  controller.scan();
  assert.equal(source.connects, 0);
});

test("a disposed document can be initialised again without retaining old listeners", async () => {
  const { owner } = documentAndRoot({ spikelingMaxSamples: "10" });
  const first = new WordPressSource();
  const one = initialiseWordPressEmulators(owner as unknown as Document, optionsFor(first));
  await flush();
  await one.dispose();
  const second = new WordPressSource();
  const two = initialiseWordPressEmulators(owner as unknown as Document, optionsFor(second));
  await flush();
  assert.notEqual(one, two);
  assert.equal(first.disconnects, 1);
  assert.equal(second.connects, 1);
  await two.dispose();
});

test("WordPress-mounted instrument retains full fixed-timestep scientific recording", async () => {
  const { root } = documentAndRoot({ spikelingSpeed: "1", spikelingSeed: "909", spikelingMaxSamples: "50" });
  const configuration = parseWordPressConfiguration(root as unknown as HTMLElement);
  const source = new WordPressSource(configuration);
  const mounted = await mountWordPressEmulator(root as unknown as HTMLElement, optionsFor(source));
  mounted.emulator.recorder.start();
  source.start();
  source.scheduler.advance(100);
  const state: RecordingSnapshot = mounted.emulator.recorder.getSnapshot();
  assert.equal(state.sampleCount, 50);
  assert.equal(state.recordingSampleRateHz, 10_000);
  assert.equal(state.wallClockStepsPerSecond, 500);
  await mounted.dispose();
});

test("WordPress PHP plugin guards direct execution and registers one narrow shortcode", async () => {
  const php = await readFile(new URL("../wordpress/spikeling-emulator/spikeling-emulator.php", import.meta.url), "utf8");
  assert.match(php, /defined\( 'ABSPATH' \) \|\| exit/);
  assert.match(php, /add_shortcode\( self::SHORTCODE/);
  assert.match(php, /private const SHORTCODE\s*=\s*'osn_spikeling_emulator'/);
  assert.match(php, /OSN_Spikeling_Emulator::boot\(\)/);
  assert.match(php, /License:\s*GPL-3\.0-or-later/);
});

test("PHP assets load only for singular pages containing a real block or Elementor shortcode", async () => {
  const php = await readFile(new URL("../wordpress/spikeling-emulator/spikeling-emulator.php", import.meta.url), "utf8");
  assert.match(php, /if \( ! is_singular\(\) \)/);
  assert.match(php, /has_shortcode\( \(string\) \$post->post_content, self::SHORTCODE \)/);
  assert.match(php, /get_post_meta\( \$post->ID, '_elementor_data', true \)/);
  assert.match(php, /wp_enqueue_style\( self::STYLE_HANDLE/);
  assert.match(php, /wp_enqueue_script\( self::SCRIPT_HANDLE/);
  assert.doesNotMatch(php, /wp_head|admin_enqueue_scripts|wp_add_inline_style|wp_add_inline_script/);
});

test("PHP validates manifest paths, version hashes, shortcode bounds and HTML escaping", async () => {
  const php = await readFile(new URL("../wordpress/spikeling-emulator/spikeling-emulator.php", import.meta.url), "utf8");
  assert.match(php, /manifest\.json/);
  assert.match(php, /\[a-f0-9\]\{16\}/);
  assert.match(php, /\[a-f0-9\]\{12\}/);
  assert.match(php, /is_file\( \$root \. \$worker \)/);
  assert.match(php, /esc_attr\( \(string\) \$speed \)/);
  assert.match(php, /esc_attr\( \(string\) \$seed \)/);
  assert.match(php, /esc_attr\( \(string\) \$limit \)/);
  assert.match(php, /esc_url\( \$source \)/);
  assert.match(php, /filter_var\( \$value, FILTER_VALIDATE_INT \)/);
  assert.match(php, /private const MAX_SAMPLES\s*=\s*1000000/);
});

test("WordPress integration adds no database options, global CSS, telemetry or serial access", async () => {
  const php = await readFile(new URL("../wordpress/spikeling-emulator/spikeling-emulator.php", import.meta.url), "utf8");
  const integration = await readFile(new URL("../src/integration/wordpress.ts", import.meta.url), "utf8");
  assert.doesNotMatch(php, /update_option|add_option|register_setting|register_rest_route|wp_remote_post|wp_mail|register_activation_hook/);
  assert.doesNotMatch(integration, /\bfetch\s*\(|XMLHttpRequest|sendBeacon|navigator\.serial/);
  assert.match(php, /if \( self::SCRIPT_HANDLE !== \$handle \)/);
  assert.match(php, /return \$tag/);
});

test("unpublished draft template contains one OSN-aligned H1 and exactly one shortcode", async () => {
  const draft = await readFile(new URL("../wordpress/draft-page.html", import.meta.url), "utf8");
  assert.equal([...draft.matchAll(/<h1\b/g)].length, 1);
  assert.equal([...draft.matchAll(/\[osn_spikeling_emulator\b/g)].length, 1);
  assert.match(draft, /Open-source neuroscience education/);
  assert.match(draft, /Turn spiking-neuron theory into an experiment\./);
  assert.match(draft, /not a biological preparation/);
  assert.match(draft, /remain local to your browser/);
  assert.match(draft, /contentSize":"1240px"/);
  assert.doesNotMatch(draft, /<img\b|<iframe\b|<script\b|\bpublish\b/i);
});

test("outer WordPress styles follow the OSN palette without leaking global selectors", async () => {
  const css = await readFile(new URL("../src/styles/wordpress.css", import.meta.url), "utf8");
  assert.match(css, /#073642/i);
  assert.match(css, /#f7f7f2/i);
  assert.match(css, /#586e75/i);
  assert.match(css, /1240px/);
  assert.doesNotMatch(css, /(?:^|\n)\s*(?:html|body|button|input|canvas|\*)\s*\{/);
});
