// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  DEFAULT_RECORDING_MAX_SAMPLES,
  DESKTOP_RECORDING_COLUMNS,
  MAX_RECORDING_FILE_BYTES,
  RECORDING_SAMPLE_RATE_HZ,
  RecordingError,
  SpikelingModel,
  parseRecordingCsv,
  parseRecordingFile,
  serialiseRecordingCsv,
} from "../src/index.ts";
import type { RecordingSample } from "../src/index.ts";

const HEADERS = DESKTOP_RECORDING_COLUMNS.map((column) => column.header).join(",");

function sample(timeMs = 0): RecordingSample {
  return {
    timeMs,
    mainVm: -65.12345678901234,
    stimulus: -0.000000000000012345,
    totalCurrent: 42.123456789012345,
    synapse1Vm: -57.900000000000006,
    synapse1Current: -12.98765432109876,
    synapse2Vm: 29.999999999999996,
    synapse2Current: 2.2250738585072014e-308,
    trigger: 1,
  };
}

function csv(rows: readonly RecordingSample[]): string {
  return serialiseRecordingCsv(rows);
}

function rejects(content: string, code: string, options = {}): void {
  assert.throws(() => parseRecordingCsv(content, options), (failure: unknown) => {
    assert.ok(failure instanceof RecordingError);
    assert.equal(failure.code, code);
    return true;
  });
}

test("recording headers exactly preserve the source-pinned nine desktop names and order", () => {
  assert.deepEqual(DESKTOP_RECORDING_COLUMNS.map((column) => column.header), [
    "Time (ms)",
    "Spikeling Vm (mV)",
    "Stimulus (%)",
    "Total Current Input (a.u.)",
    "Synapse 1 Vm (mV)",
    "Synapse 1 Input (a.u.)",
    "Synapse 2 Vm (mV)",
    "Synapse 2 Input (a.u.)",
    "Trigger",
  ]);
  assert.equal(RECORDING_SAMPLE_RATE_HZ, 10_000);
  assert.equal(DEFAULT_RECORDING_MAX_SAMPLES, 250_000);
  assert.equal(MAX_RECORDING_FILE_BYTES, 64 * 1_024 * 1_024);
});

test("scientific values round-trip at full Float64 precision including exponents", () => {
  const input = [sample(), { ...sample(0.1), trigger: 0 as const }];
  const output = csv(input);
  assert.equal(output.split("\n")[0], HEADERS);
  assert.match(output, /-65\.12345678901234/);
  assert.match(output, /2\.2250738585072014e-308/);
  assert.deepEqual(parseRecordingCsv(output), {
    samples: input,
    sampleIntervalMs: 0.1,
    durationMs: 0.2,
  });
  assert.ok(output.endsWith("\n"));
});

test("export remains numerically identical to seeded scientific model samples", () => {
  const model = new SpikelingModel({ seed: 4545, controls: { main: { noiseLevel: 25, patchCurrent: 18 } } });
  const input = model.run(100).map((full) => ({
    timeMs: full.timeMs,
    mainVm: full.mainVm,
    stimulus: full.stimulus,
    totalCurrent: full.totalCurrent,
    synapse1Vm: full.synapse1Vm,
    synapse1Current: full.synapse1Current,
    synapse2Vm: full.synapse2Vm,
    synapse2Current: full.synapse2Current,
    trigger: full.trigger,
  }));
  assert.deepEqual(parseRecordingCsv(csv(input)).samples, input);
});

test("desktop-compatible columns may be reordered and quoted", () => {
  const original = sample();
  const reversed = [...DESKTOP_RECORDING_COLUMNS].reverse();
  const content = reversed.map((column) => '"' + column.header + '"').join(",") + "\r\n"
    + reversed.map((column) => String(original[column.field])).join(",") + "\r\n";
  assert.deepEqual(parseRecordingCsv(content).samples, [original]);
});

test("UTF-8 BOM, surrounding whitespace, blank rows and CR-only files are supported", () => {
  const original = sample();
  const fields = DESKTOP_RECORDING_COLUMNS.map((column) => " " + original[column.field] + " ").join(",");
  const content = "\uFEFF" + HEADERS + "\r\r" + fields + "\r";
  assert.deepEqual(parseRecordingCsv(content).samples, [original]);
});

test("quoted whitespace and escaped quotes follow strict CSV semantics", () => {
  const headers = DESKTOP_RECORDING_COLUMNS.map((column) => '"' + column.header + '" ').join(",");
  assert.deepEqual(parseRecordingCsv(headers + "\n" + csv([sample()]).split("\n")[1]).samples, [sample()]);
  rejects(HEADERS.replace("Trigger", '"Trig""ger"') + "\n" + csv([sample()]).split("\n")[1], "invalid-header");
});

test("empty files and header-only files report distinct actionable errors", () => {
  rejects("   \n\t", "empty-file");
  rejects(",\n", "empty-file");
  rejects(HEADERS + "\n\n", "empty-samples");
});

test("missing, unknown and duplicate columns cannot invent scientific signals", () => {
  const line = csv([sample()]).split("\n")[1];
  rejects(HEADERS.replace(",Trigger", "") + "\n" + line, "invalid-header");
  rejects(HEADERS.replace("Trigger", "Other") + "\n" + line, "invalid-header");
  rejects(HEADERS.replace("Trigger", "Stimulus (%)") + "\n" + line, "duplicate-column");
});

test("uneven rows, misplaced quotations and unterminated quoted fields are rejected", () => {
  const line = csv([sample()]).split("\n")[1];
  rejects(HEADERS + "\n" + line + ",1\n", "malformed-csv");
  rejects(HEADERS + "\n" + line.replace("-65", '-"65'), "malformed-csv");
  rejects(HEADERS + "\n" + line.replace("-65", '"-65') , "malformed-csv");
  rejects(HEADERS + "\n" + line.replace("-65.12345678901234", '"-65"x'), "malformed-csv");
});

test("missing, non-numeric, NaN, Infinity and overflowing values are rejected", () => {
  for (const invalid of ["", "abc", "NaN", "Infinity", "-Infinity", "1e999", "0x12"]) {
    rejects(csv([sample()]).replace("-65.12345678901234", invalid), "invalid-sample");
  }
});

test("trigger samples must be genuine binary values", () => {
  rejects(csv([sample()]).replace(/,1\n$/, ",2\n"), "invalid-trigger");
  rejects(csv([sample()]).replace(/,1\n$/, ",-1\n"), "invalid-trigger");
  rejects(csv([sample()]).replace(/,1\n$/, ",0.5\n"), "invalid-trigger");
});

test("negative and discontinuous scientific timestamps are rejected", () => {
  rejects(csv([{ ...sample(), timeMs: -0.1 }]), "invalid-timestamp");
  rejects(csv([sample(), sample(0.2)]), "sample-interval");
  rejects(csv([sample(0.1), sample(0)]), "sample-interval");
});

test("sample-count and UTF-8 byte limits are enforced without unbounded growth", () => {
  rejects(csv([sample(), sample(0.1)]), "sample-limit", { maxSamples: 1 });
  rejects(csv([sample()]), "file-size", { maxBytes: 10 });
  assert.throws(() => parseRecordingCsv(csv([sample()]), { maxSamples: 0 }), /positive safe integer/);
  assert.throws(() => parseRecordingCsv(csv([sample()]), { maxBytes: 1.1 }), /positive safe integer/);
});

test("local recording files validate extension and size before reading content", async () => {
  let reads = 0;
  const text = csv([sample()]);
  const file = { name: "desktop.CSV", size: text.length, text: async () => { reads += 1; return text; } };
  assert.deepEqual((await parseRecordingFile(file)).samples, [sample()]);
  assert.equal(reads, 1);
  await assert.rejects(parseRecordingFile({ ...file, name: "recording.txt" }), /\.csv/);
  await assert.rejects(parseRecordingFile({ ...file, size: text.length + 1 }, { maxBytes: text.length }), /file-size/);
  await assert.rejects(parseRecordingFile({ ...file, size: -1 }), /file-size/);
  assert.equal(reads, 1);
});

test("empty exports and invalid outgoing numerical or trigger values are rejected", () => {
  assert.throws(() => serialiseRecordingCsv([]), /no recorded/);
  assert.throws(() => serialiseRecordingCsv([{ ...sample(), mainVm: NaN }]), /finite/);
  assert.throws(() => serialiseRecordingCsv([{ ...sample(), trigger: 2 as 0 | 1 }]), /zero or one/);
});

test("recording errors preserve machine-readable codes and source line numbers", () => {
  try {
    parseRecordingCsv(HEADERS + "\n" + csv([sample()]).split("\n")[1].replace("-65.12345678901234", "bad"));
    assert.fail("Expected invalid desktop row");
  } catch (failure) {
    assert.ok(failure instanceof RecordingError);
    assert.equal(failure.name, "RecordingError");
    assert.equal(failure.code, "invalid-sample");
    assert.equal(failure.line, 2);
  }
});
