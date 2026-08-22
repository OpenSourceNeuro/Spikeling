// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  CustomStimulusError,
  MAX_CUSTOM_STIMULUS_BYTES,
  MAX_CUSTOM_STIMULUS_SAMPLES,
  REQUIRED_STIMULUS_COLUMN,
  SpikelingModel,
  parseCustomStimulusCsv,
  parseCustomStimulusFile,
  renderStimulusPreview,
} from "../src/index.ts";
import type { CustomStimulusErrorCode, LocalStimulusFile } from "../src/index.ts";
import { RecordingCanvas } from "./helpers/fake-canvas.ts";

function rejectsCsv(content: string, code: CustomStimulusErrorCode, line?: number): void {
  assert.throws(
    () => parseCustomStimulusCsv(content),
    (error: unknown) => {
      assert.ok(error instanceof CustomStimulusError);
      assert.equal(error.name, "CustomStimulusError");
      assert.equal(error.code, code);
      if (line !== undefined) {
        assert.equal(error.line, line);
      }
      return true;
    },
  );
}

function localFile(name: string, content: string, size = new TextEncoder().encode(content).length): LocalStimulusFile {
  return { name, size, text: async () => content };
}

test("desktop Stim,Trigger CSV files retain signed, full-precision 0.1 ms samples", () => {
  const parsed = parseCustomStimulusCsv("Stim,Trigger\n-12.5,1\n0,0\n33.125,0\n");

  assert.equal(REQUIRED_STIMULUS_COLUMN, "Stim");
  assert.deepEqual(parsed.samples, [-12.5, 0, 33.125]);
  assert.equal(parsed.sampleIntervalMs, 0.1);
  assert.ok(Math.abs(parsed.durationMs - 0.3) < 1e-12);
  assert.equal(parsed.minimum, -12.5);
  assert.equal(parsed.maximum, 33.125);
  assert.equal(parsed.hasTriggerColumn, true);
  assert.equal(parsed.hasTimeColumn, false);
});

test("CSV import accepts optional BOM, CRLF, whitespace and quoted desktop fields", () => {
  const parsed = parseCustomStimulusCsv(
    '\uFEFF"Stim","Trigger","Notes"\r\n" -1.25 ",1,"a, b"\r\n"2e1",0,"a ""quote"""\r\n',
  );

  assert.deepEqual(parsed.samples, [-1.25, 20]);
  assert.equal(parsed.hasTriggerColumn, true);
});

test("quoted metadata can contain newlines without changing sample interpretation", () => {
  const parsed = parseCustomStimulusCsv('Stim,Notes\n1,"first\nsecond"\n2,plain\n');
  assert.deepEqual(parsed.samples, [1, 2]);
});

test("optional desktop timestamps must match the exact 0.1 ms model timestep", () => {
  for (const column of ["Time (ms)", "timeMs", "time_ms"]) {
    const parsed = parseCustomStimulusCsv(column + ",Stim\n2,1\n2.1,-3\n2.2,7");
    assert.equal(parsed.hasTimeColumn, true);
    assert.deepEqual(parsed.samples, [1, -3, 7]);
  }

  rejectsCsv("Time (ms),Stim\n0,1\n0.2,2", "sample-interval", 3);
  rejectsCsv("Time (ms),Stim\n0.1,1\n0,2", "sample-interval", 3);
  rejectsCsv("timeMs,Stim\nnever,1", "invalid-timestamp", 2);
});

test("CSV import requires an exact, unique Stim column", () => {
  rejectsCsv("stim\n1", "missing-stim-column", 1);
  rejectsCsv("Stimulus\n1", "missing-stim-column", 1);
  rejectsCsv("Stim,Stim\n1,2", "duplicate-column", 1);
  rejectsCsv("Stim,timeMs,time_ms\n1,0,0", "duplicate-column", 1);
});

test("empty files, blank files and headers with no samples are rejected explicitly", () => {
  rejectsCsv("", "empty-file");
  rejectsCsv("  \r\n \t", "empty-file");
  rejectsCsv("\uFEFF", "empty-file");
  rejectsCsv(",,\n,\n", "empty-file");
  rejectsCsv("Stim\n\n", "empty-samples", 1);
});

test("malformed quoting and inconsistent column counts include actionable line numbers", () => {
  rejectsCsv('Stim\n"1', "malformed-csv", 2);
  rejectsCsv('Stim\n1"2', "malformed-csv", 2);
  rejectsCsv('Stim\n"1"oops', "malformed-csv", 2);
  rejectsCsv('Stim\n"1""2', "malformed-csv", 2);
  rejectsCsv("Stim,Trigger\n1", "malformed-csv", 2);
  rejectsCsv("Stim\n1,2", "malformed-csv", 2);
});

test("non-finite, missing and non-decimal scientific values cannot enter the model", () => {
  for (const invalid of ["NaN", "Infinity", "-Infinity", "0x10", "1_000", "1e999", "true"]) {
    rejectsCsv("Stim\n" + invalid, "invalid-sample", 2);
  }
  rejectsCsv("Stim,Trigger\n,0", "invalid-sample", 2);

  assert.deepEqual(parseCustomStimulusCsv("Stim\n+.5\n-2.\n1E-3").samples, [0.5, -2, 0.001]);
});

test("configurable byte and sample limits are enforced before model mutation", () => {
  assert.throws(
    () => parseCustomStimulusCsv("Stim\n12345", { maxBytes: 5 }),
    (error: unknown) => error instanceof CustomStimulusError && error.code === "file-size",
  );
  assert.throws(
    () => parseCustomStimulusCsv("Stim\n1\n2\n3", { maxSamples: 2 }),
    (error: unknown) => error instanceof CustomStimulusError && error.code === "sample-limit" && error.line === 4,
  );

  assert.equal(MAX_CUSTOM_STIMULUS_BYTES, 8 * 1024 * 1024);
  assert.equal(MAX_CUSTOM_STIMULUS_SAMPLES, 250_000);
});

test("unsafe CSV byte and sample limit settings are rejected", () => {
  for (const invalid of [0, -1, 1.5, Number.POSITIVE_INFINITY, Number.NaN]) {
    assert.throws(() => parseCustomStimulusCsv("Stim\n1", { maxBytes: invalid }), RangeError);
    assert.throws(() => parseCustomStimulusCsv("Stim\n1", { maxSamples: invalid }), RangeError);
  }
});

test("UTF-8 byte limits measure bytes rather than JavaScript string length", () => {
  const csv = "Stim,Notes\n1,λ";
  assert.throws(
    () => parseCustomStimulusCsv(csv, { maxBytes: csv.length }),
    (error: unknown) => error instanceof CustomStimulusError && error.code === "file-size",
  );
});

test("local file import accepts case-insensitive CSV extensions", async () => {
  const parsed = await parseCustomStimulusFile(localFile("experiment.CSV", "Stim\n4\n-9"));
  assert.deepEqual(parsed.samples, [4, -9]);
});

test("invalid local file types and declared sizes are rejected before reading", async () => {
  let reads = 0;
  const content = "Stim\n1";
  const text = async () => {
    reads += 1;
    return content;
  };

  await assert.rejects(
    parseCustomStimulusFile({ name: "experiment.txt", size: 6, text }),
    (error: unknown) => error instanceof CustomStimulusError && error.code === "file-type",
  );
  for (const size of [-1, Number.NaN, Number.POSITIVE_INFINITY, 101]) {
    await assert.rejects(
      parseCustomStimulusFile({ name: "experiment.csv", size, text }, { maxBytes: 100 }),
      (error: unknown) => error instanceof CustomStimulusError && error.code === "file-size",
    );
  }
  assert.equal(reads, 0);
});

test("actual decoded file bytes are rechecked when a declared size is inaccurate", async () => {
  await assert.rejects(
    parseCustomStimulusFile(localFile("stim.csv", "Stim\n123456789", 2), { maxBytes: 8 }),
    (error: unknown) => error instanceof CustomStimulusError && error.code === "file-size",
  );
});

test("custom desktop CSV samples loop and preserve source-matched rollover triggers", () => {
  const parsed = parseCustomStimulusCsv("Stim,Trigger\n9,0\n-4,1\n2,0");
  const model = new SpikelingModel({
    controls: { stimulus: { mode: "custom", customSamples: [...parsed.samples] } },
  });
  const sequence = model.run(8);

  assert.deepEqual(sequence.map((sample) => sample.stimulus), [9, -4, 2, 9, -4, 2, 9, -4]);
  assert.deepEqual(sequence.map((sample) => sample.trigger), [1, 0, 0, 1, 0, 0, 1, 0]);
  assert.deepEqual(sequence.map((sample) => sample.timeMs), [0, 0.1, 0.2, 0.30000000000000004, 0.4, 0.5, 0.6000000000000001, 0.7000000000000001]);
});

test("empty preview paints a high-DPI background without inventing stimulus points", () => {
  const canvas = new RecordingCanvas(160, 48);
  const result = renderStimulusPreview(canvas, [], 2);

  assert.deepEqual(result, { samples: 0, displayedPoints: 0, minimum: 0, maximum: 0 });
  assert.equal(canvas.width, 320);
  assert.equal(canvas.height, 96);
  assert.deepEqual(canvas.context.transforms.at(-1), [2, 0, 0, 2, 0, 0]);
  assert.equal(canvas.context.strokes.length, 0);
});

test("stimulus preview preserves every sample when the waveform is shorter than its canvas", () => {
  const canvas = new RecordingCanvas(320, 48);
  const result = renderStimulusPreview(canvas, [-2, 5, -1], 1);

  assert.equal(result.displayedPoints, 3);
  assert.equal(result.minimum, -2);
  assert.equal(result.maximum, 5);
  assert.equal(canvas.context.strokes.at(-1)?.points.length, 3);
});

test("stimulus preview retains narrow signed extrema during per-pixel decimation", () => {
  const canvas = new RecordingCanvas(4, 36);
  const samples = Array.from({ length: 400 }, () => 0);
  samples[207] = 90;
  samples[208] = -70;
  const result = renderStimulusPreview(canvas, samples, 1);
  const signal = canvas.context.strokes.at(-1)!;

  assert.equal(result.minimum, -70);
  assert.equal(result.maximum, 90);
  assert.ok(result.displayedPoints < samples.length);
  assert.ok(signal.points.some((point) => point.y === 6));
  assert.ok(signal.points.some((point) => point.y === 30));
  assert.ok(signal.points.every((point, index) => index === 0 || point.x >= signal.points[index - 1].x));
});

test("single-valued and single-sample previews remain finite and correctly scaled", () => {
  for (const samples of [[0], [5], [-8], [3, 3, 3]]) {
    const canvas = new RecordingCanvas(100, 40);
    const result = renderStimulusPreview(canvas, samples, 1);
    assert.equal(result.samples, samples.length);
    assert.ok(canvas.context.strokes.every((stroke) => stroke.points.every((point) => Number.isFinite(point.x) && Number.isFinite(point.y))));
  }
});

test("preview rejects unavailable Canvas contexts, invalid pixel ratios and non-finite samples", () => {
  const unavailable = {
    width: 0,
    height: 0,
    getBoundingClientRect: () => ({ width: 100, height: 40 }),
    getContext: () => null,
  };
  assert.throws(() => renderStimulusPreview(unavailable, [1]), /2D Canvas/);

  for (const ratio of [0, -1, Number.NaN, Number.POSITIVE_INFINITY]) {
    assert.throws(() => renderStimulusPreview(new RecordingCanvas(), [1], ratio), /pixel ratio/);
  }
  assert.throws(() => renderStimulusPreview(new RecordingCanvas(), [1, Number.NaN]), /finite/);
});
