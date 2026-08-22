// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  DEFAULT_OSCILLOSCOPE_THEME,
  DESKTOP_CURRENT_RANGE,
  DESKTOP_TRACE_WIDTH_PX,
  DESKTOP_VISIBLE_WINDOW_MS,
  DESKTOP_VOLTAGE_RANGE,
  OSCILLOSCOPE_TRACES,
  OscilloscopeCanvasRenderer,
  OscilloscopeRenderLoop,
  SPIKELING_PALETTE,
  SpikelingModel,
  buildAxisTicks,
  calculatePlotLayout,
  decimateTrace,
  defaultVisibleTraces,
  formatAxisValue,
  getOscilloscopeTrace,
  projectX,
  projectY,
} from "../src/index.ts";
import type { SimulationSample, TraceField } from "../src/index.ts";
import { createDevelopmentServer, readDevelopmentAsset } from "../tools/serve.mjs";
import {
  ManualAnimationFrames,
  ManualPageVisibility,
  RecordingCanvas,
} from "./helpers/fake-canvas.ts";

function samplesWithVoltages(values: readonly number[]): SimulationSample[] {
  const baseline = new SpikelingModel().run(values.length);
  return baseline.map((sample, index) => ({
    ...sample,
    timeMs: index,
    mainVm: values[index],
  }));
}

test("desktop trace registry preserves all seven exact colours, order and axis assignments", () => {
  assert.deepEqual(
    OSCILLOSCOPE_TRACES.map((trace) => [trace.id, trace.colour, trace.axis]),
    [
      ["mainVm", "#DC322F", "voltage"],
      ["stimulus", "#268BD2", "current"],
      ["totalCurrent", "#859900", "current"],
      ["synapse1Vm", "#CB4B16", "voltage"],
      ["synapse1Current", "#2AA198", "current"],
      ["synapse2Vm", "#B58900", "voltage"],
      ["synapse2Current", "#D33682", "current"],
    ],
  );
  assert.deepEqual([...defaultVisibleTraces()], ["mainVm", "stimulus", "totalCurrent"]);
  assert.equal(getOscilloscopeTrace("synapse1Current").label, "Synapse 1 input");
  assert.throws(() => getOscilloscopeTrace("invalid" as TraceField), RangeError);
  assert.equal(SPIKELING_PALETTE.backgroundDeep, "#001E26");
  assert.equal(DEFAULT_OSCILLOSCOPE_THEME.grid, "#073642");
});

test("desktop scientific axes use the audited 500 ms window and independent ranges", () => {
  assert.equal(DESKTOP_VISIBLE_WINDOW_MS, 500);
  assert.equal(DESKTOP_TRACE_WIDTH_PX, 1);
  assert.deepEqual(DESKTOP_VOLTAGE_RANGE, { minimum: -90, maximum: 30 });
  assert.deepEqual(DESKTOP_CURRENT_RANGE, { minimum: -100, maximum: 100 });
  assert.deepEqual(buildAxisTicks({ minimum: -500, maximum: 0 }, 100), [
    -500, -400, -300, -200, -100, 0,
  ]);
  assert.deepEqual(buildAxisTicks(DESKTOP_VOLTAGE_RANGE, 30), [-90, -60, -30, 0, 30]);
  assert.deepEqual(buildAxisTicks(DESKTOP_CURRENT_RANGE, 50), [-100, -50, 0, 50, 100]);
  assert.deepEqual(buildAxisTicks({ minimum: -0.3, maximum: 0.3 }, 0.1), [
    -0.2, -0.1, 0, 0.1, 0.2, 0.3,
  ]);
  assert.equal(formatAxisValue(-90), "−90");
  assert.equal(formatAxisValue(-0), "0");
  assert.throws(() => buildAxisTicks({ minimum: 1, maximum: 1 }, 1), RangeError);
  assert.throws(() => buildAxisTicks({ minimum: 0, maximum: 1 }, 0), RangeError);
});

test("responsive plotting geometry stays usable and switches to compact mobile margins", () => {
  const desktop = calculatePlotLayout(900, 420);
  assert.equal(desktop.compact, false);
  assert.equal(desktop.plotWidth, 752);
  assert.equal(desktop.plotHeight, 340);

  const mobile = calculatePlotLayout(360, 300);
  assert.equal(mobile.compact, true);
  assert.equal(mobile.plotWidth, 252);
  assert.equal(mobile.plotHeight, 236);

  const tiny = calculatePlotLayout(10, 10);
  assert.equal(tiny.plotWidth, 1);
  assert.equal(tiny.plotHeight, 1);
  assert.throws(() => calculatePlotLayout(0, 100), RangeError);
  assert.throws(() => calculatePlotLayout(100, Number.NaN), RangeError);
});

test("time and dual-axis projections align desktop limits with plot boundaries", () => {
  const layout = calculatePlotLayout(900, 420);
  assert.equal(projectX(-500, 500, layout), layout.left);
  assert.equal(projectX(0, 500, layout), layout.left + layout.plotWidth);
  assert.equal(projectY(30, DESKTOP_VOLTAGE_RANGE, layout), layout.top);
  assert.equal(projectY(-90, DESKTOP_VOLTAGE_RANGE, layout), layout.top + layout.plotHeight);
  assert.equal(projectY(100, DESKTOP_CURRENT_RANGE, layout), layout.top);
  assert.equal(projectY(-100, DESKTOP_CURRENT_RANGE, layout), layout.top + layout.plotHeight);
  assert.equal(projectY(0, DESKTOP_CURRENT_RANGE, layout), layout.top + layout.plotHeight / 2);
});

test("display decimation retains sparse genuine samples without inventing interpolation", () => {
  const samples = samplesWithVoltages([-70, -64, 30, -65, -60]);
  const result = decimateTrace(samples, {
    field: "mainVm",
    pixelWidth: 100,
    windowMs: 10,
  });

  assert.deepEqual(result.map((point) => point.value), [-70, -64, 30, -65, -60]);
  assert.deepEqual(result.map((point) => point.relativeTimeMs), [-4, -3, -2, -1, 0]);
  assert.deepEqual(result.map((point) => point.sampleIndex), [0, 1, 2, 3, 4]);
});

test("pixel-bucket min/max decimation never loses a narrow action-potential peak", () => {
  const values = Array.from({ length: 500 }, () => -68);
  values[124] = 30;
  values[125] = -90;
  values[376] = 30;
  const original = samplesWithVoltages(values);
  const result = decimateTrace(original, {
    field: "mainVm",
    pixelWidth: 18,
    windowMs: 500,
  });

  assert.ok(result.some((point) => point.sampleIndex === 124 && point.value === 30));
  assert.ok(result.some((point) => point.sampleIndex === 125 && point.value === -90));
  assert.ok(result.some((point) => point.sampleIndex === 376 && point.value === 30));
  assert.ok(result.length <= 18 * 4);
  assert.ok(result.every((point, index) => index === 0 || point.timeMs > result[index - 1].timeMs));
  assert.equal(original[124].mainVm, 30);
  assert.equal(original[125].mainVm, -90);
  assert.equal(original.length, 500);
});

test("bucket extrema preserve chronological order even when maximum precedes minimum", () => {
  const samples = samplesWithVoltages([-65, 30, -90, -64]);
  const result = decimateTrace(samples, {
    field: "mainVm",
    pixelWidth: 1,
    windowMs: 10,
  });
  assert.deepEqual(result.map((point) => point.value), [-65, 30, -90, -64]);
});

test("rolling windows exclude old and future samples while preserving a selected anchor", () => {
  const samples = samplesWithVoltages([-70, -69, -68, -67, -66, -65]);
  const result = decimateTrace(samples, {
    field: "mainVm",
    pixelWidth: 20,
    windowMs: 2,
    anchorTimeMs: 4,
  });
  assert.deepEqual(result.map((point) => point.timeMs), [2, 3, 4]);
  assert.deepEqual(result.map((point) => point.relativeTimeMs), [-2, -1, 0]);
  assert.deepEqual(
    decimateTrace([], { field: "mainVm", pixelWidth: 10, windowMs: 5 }),
    [],
  );
});

test("decimation rejects malformed time-window, width and anchor inputs", () => {
  const samples = samplesWithVoltages([-65]);
  assert.throws(
    () => decimateTrace(samples, { field: "mainVm", pixelWidth: 0, windowMs: 1 }),
    RangeError,
  );
  assert.throws(
    () => decimateTrace(samples, { field: "mainVm", pixelWidth: 1, windowMs: 0 }),
    RangeError,
  );
  assert.throws(
    () =>
      decimateTrace(samples, {
        field: "mainVm",
        pixelWidth: 1,
        windowMs: 1,
        anchorTimeMs: Number.NaN,
      }),
    RangeError,
  );
});

test("oscilloscope trace values agree with pinned Python desktop-reference fixtures", () => {
  const fixture = JSON.parse(
    readFileSync(new URL("./fixtures/golden/desktop-reference.json", import.meta.url), "utf8"),
  );
  const scenarios = [
    "tonic-spiking",
    "internal-square-and-trigger",
    "synaptic-excitation",
    "synapse-2-corrected-decay",
  ];
  const columnByField = new Map<string, number>(
    fixture.metadata.sampleColumns.map((field: string, index: number) => [field, index]),
  );

  for (const name of scenarios) {
    const scenario = fixture.scenarios.find((entry: { name: string }) => entry.name === name);
    assert.ok(scenario, "Missing source-pinned scenario " + name);
    const model = new SpikelingModel({
      seed: scenario.seed,
      controls: scenario.controls,
      initialisation: scenario.initialisation,
      compatibility: scenario.compatibility,
    });
    const generated = model.run(scenario.steps);

    for (const trace of OSCILLOSCOPE_TRACES) {
      const points = decimateTrace(generated, {
        field: trace.id,
        pixelWidth: 48,
        windowMs: 500,
      });
      for (const point of points) {
        const expected = scenario.samples[point.sampleIndex][columnByField.get(trace.id)!];
        assert.ok(
          Math.abs(point.value - expected) <= fixture.metadata.absoluteTolerance,
          name + " / " + trace.id + " / sample " + point.sampleIndex,
        );
      }
    }
  }
});

test("Canvas renderer draws scientific labels, separate axes and desktop-matched traces", () => {
  const canvas = new RecordingCanvas(900, 420);
  const renderer = new OscilloscopeCanvasRenderer(canvas, { devicePixelRatio: () => 1 });
  const samples = new SpikelingModel({
    controls: {
      main: { patchCurrent: 18, directCurrentEnabled: true },
      stimulus: { strength: 25 },
    },
  }).run(150);
  const stats = renderer.render(samples, defaultVisibleTraces());

  assert.equal(stats.sourceSamples, 150);
  assert.equal(stats.enabledTraces, 3);
  assert.ok(stats.displayedPoints > 0);
  assert.ok(canvas.context.labels.some((label) => label.text === "Membrane potential (mV)"));
  assert.ok(canvas.context.labels.some((label) => label.text === "Current input (a.u.)"));
  assert.ok(canvas.context.labels.some((label) => label.text === "Time (ms)"));
  assert.ok(canvas.context.labels.some((label) => label.text === "−500"));
  assert.ok(canvas.context.labels.some((label) => label.text === "−90"));
  assert.ok(canvas.context.labels.some((label) => label.text === "100"));
  assert.ok(canvas.context.strokes.some((stroke) => stroke.colour === "#DC322F"));
  assert.ok(canvas.context.strokes.some((stroke) => stroke.colour === "#268BD2"));
  assert.ok(canvas.context.strokes.some((stroke) => stroke.colour === "#859900"));
  assert.ok(canvas.context.strokes.every((stroke) => stroke.width === 1));
  assert.equal(canvas.context.clips.length, 1);
  assert.equal(renderer.traceColour("synapse2Current"), "#D33682");
});

test("renderer omits disabled traces and never uses interpolation or smoothing", () => {
  const canvas = new RecordingCanvas();
  const renderer = new OscilloscopeCanvasRenderer(canvas);
  const samples = samplesWithVoltages([-70, 30, -65]);
  const stats = renderer.render(samples, new Set(["mainVm"]));

  assert.equal(stats.enabledTraces, 1);
  const trace = canvas.context.strokes.find((stroke) => stroke.colour === "#DC322F");
  assert.ok(trace);
  assert.equal(trace.points.length, 3);
  assert.equal(trace.points[1].y, renderer.getLayout().top);
  assert.ok(!canvas.context.strokes.some((stroke) => stroke.colour === "#268BD2"));
  assert.equal("bezierCurveTo" in canvas.context, false);
  assert.equal("quadraticCurveTo" in canvas.context, false);
});

test("renderer adapts to mobile dimensions and device pixel ratios without altering axes", () => {
  const canvas = new RecordingCanvas(360, 300);
  const renderer = new OscilloscopeCanvasRenderer(canvas, { devicePixelRatio: () => 2 });
  assert.equal(canvas.width, 720);
  assert.equal(canvas.height, 600);
  assert.deepEqual(canvas.context.transforms.at(-1), [2, 0, 0, 2, 0, 0]);
  assert.equal(renderer.getLayout().compact, true);

  renderer.render([], defaultVisibleTraces());
  assert.ok(canvas.context.labels.some((label) => label.text === "Vm (mV)"));
  assert.ok(canvas.context.labels.some((label) => label.text === "I (a.u.)"));

  canvas.cssWidth = 900;
  canvas.cssHeight = 420;
  const resized = renderer.resize();
  assert.equal(resized.compact, false);
  assert.equal(canvas.width, 1_800);
  assert.equal(canvas.height, 840);
  assert.deepEqual(renderer.voltageRange, DESKTOP_VOLTAGE_RANGE);
});

test("renderer validates contexts, windows and independent scientific ranges", () => {
  const broken = {
    width: 0,
    height: 0,
    getBoundingClientRect: () => ({ width: 100, height: 100 }),
    getContext: () => null,
  };
  assert.throws(() => new OscilloscopeCanvasRenderer(broken), /2D Canvas/);
  assert.throws(() => new OscilloscopeCanvasRenderer(new RecordingCanvas(), { windowMs: 0 }), RangeError);
  assert.throws(
    () =>
      new OscilloscopeCanvasRenderer(new RecordingCanvas(), {
        voltageRange: { minimum: 30, maximum: -90 },
      }),
    RangeError,
  );
  assert.throws(
    () =>
      new OscilloscopeCanvasRenderer(new RecordingCanvas(), {
        currentRange: { minimum: 0, maximum: Number.NaN },
      }),
    RangeError,
  );

  const fallback = new RecordingCanvas(200, 100);
  new OscilloscopeCanvasRenderer(fallback, { devicePixelRatio: () => Number.NaN });
  assert.equal(fallback.width, 200);
});

test("animation-frame loop coalesces worker batches without changing simulation timing", () => {
  const scheduler = new ManualAnimationFrames();
  const timestamps: number[] = [];
  const loop = new OscilloscopeRenderLoop((timestamp) => timestamps.push(timestamp), {
    scheduler,
  });

  loop.invalidate();
  assert.equal(scheduler.pending, 0);
  loop.start();
  loop.start();
  loop.invalidate();
  loop.invalidate();
  assert.equal(loop.running, true);
  assert.equal(loop.scheduled, true);
  assert.equal(scheduler.pending, 1);
  scheduler.advance(16.7);
  assert.deepEqual(timestamps, [16.7]);
  assert.equal(scheduler.pending, 0);

  loop.invalidate();
  scheduler.advance(33.3);
  assert.deepEqual(timestamps, [16.7, 33.3]);
  loop.stop();
  assert.equal(loop.running, false);
});

test("background-tab visibility cancels rendering and resumes with one clean frame", () => {
  const scheduler = new ManualAnimationFrames();
  const visibility = new ManualPageVisibility();
  let frames = 0;
  const loop = new OscilloscopeRenderLoop(() => {
    frames += 1;
  }, { scheduler, visibility });

  loop.start();
  assert.equal(scheduler.pending, 1);
  visibility.setHidden(true);
  assert.equal(scheduler.pending, 0);
  loop.invalidate();
  assert.equal(scheduler.pending, 0);
  visibility.setHidden(false);
  assert.equal(scheduler.pending, 1);
  scheduler.advance();
  assert.equal(frames, 1);

  loop.invalidate();
  loop.stop();
  assert.equal(scheduler.pending, 0);
  loop.dispose();
  assert.equal(visibility.listeners.size, 0);
});

test("a frame invalidated during rendering schedules exactly one follow-up paint", () => {
  const scheduler = new ManualAnimationFrames();
  let frames = 0;
  let loop: OscilloscopeRenderLoop;
  loop = new OscilloscopeRenderLoop(() => {
    frames += 1;
    if (frames === 1) {
      loop.invalidate();
    }
  }, { scheduler });

  loop.start();
  scheduler.advance();
  assert.equal(frames, 1);
  assert.equal(scheduler.pending, 1);
  scheduler.advance();
  assert.equal(frames, 2);
  assert.equal(scheduler.pending, 0);
});

test("local preview serves scoped styles and strips erasable TypeScript without npm", async () => {
  const html = await readDevelopmentAsset("/");
  assert.equal(html.status, 200);
  assert.match(html.contentType, /text\/html/);
  assert.match(html.content, /Spikeling neuronal oscilloscope/);
  assert.match(html.content, /\/demo\/main\.ts/);

  const module = await readDevelopmentAsset("/demo/main.ts");
  assert.equal(module.status, 200);
  assert.match(module.contentType, /text\/javascript/);
  assert.match(module.content, /new EmulatorSource/);
  assert.doesNotMatch(module.content, /<HTMLButtonElement>/);

  const stylesheet = await readDevelopmentAsset("/src/styles/oscilloscope.css");
  assert.equal(stylesheet.status, 200);
  assert.match(stylesheet.content, /--spk-membrane:/);
  assert.match(stylesheet.content, /prefers-reduced-motion/);

  assert.equal((await readDevelopmentAsset("/missing.ts")).status, 404);
  assert.equal((await readDevelopmentAsset("/README.md")).status, 404);
  assert.equal((await readDevelopmentAsset("/%2e%2e/%2e%2e/secret.ts")).status, 403);
  assert.equal((await readDevelopmentAsset("/%E0%A4%A")).status, 400);
});

test("development server provides browser modules and worker scripts with correct MIME types", async (context) => {
  const server = createDevelopmentServer();
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve());
  });
  context.after(
    () =>
      new Promise<void>((resolve, reject) => {
        server.close((error) => (error ? reject(error) : resolve()));
      }),
  );

  const address = server.address();
  assert.ok(address && typeof address !== "string");
  const base = "http://127.0.0.1:" + address.port;

  for (const path of ["/", "/demo/main.ts", "/src/worker/emulator.worker.ts", "/src/styles/oscilloscope.css"]) {
    const response = await fetch(base + path);
    assert.equal(response.status, 200, path);
    assert.equal(response.headers.get("cache-control"), "no-store");
    if (path.endsWith(".ts")) {
      assert.match(response.headers.get("content-type") ?? "", /text\/javascript/);
    }
    await response.text();
  }

  const missing = await fetch(base + "/not-there.ts");
  assert.equal(missing.status, 404);
});
