// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, readdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { Script } from "node:vm";
import { gzipSync } from "node:zlib";

import { SpikelingModel, unpackSamples } from "../src/index.ts";
import type { MainToWorkerMessage, SimulationSample, WorkerToMainMessage } from "../src/index.ts";
import { buildProductionAssets, bundleProductionEntry, PRODUCTION_STYLE_SOURCES } from "../tools/build.mjs";
import { ManualScheduler } from "./helpers/manual-scheduler.ts";

const outputDirectory = await mkdtemp(join(tmpdir(), "spikeling-production-"));
const manifest = await buildProductionAssets({ outputDirectory });

async function asset(name: "application" | "worker" | "stylesheet"): Promise<string> {
  return readFile(join(outputDirectory, manifest[name].file), "utf8");
}

function hash(content: string): string {
  return createHash("sha256").update(content).digest("hex");
}

test("production builder emits only one manifest and three content-hashed static assets", async () => {
  assert.deepEqual((await readdir(outputDirectory)).sort(), [
    "manifest.json",
    manifest.application.file,
    manifest.stylesheet.file,
    manifest.worker.file,
  ].sort());
  assert.match(manifest.version, /^[a-f0-9]{16}$/);
  assert.match(manifest.application.file, /^spikeling-emulator\.[a-f0-9]{12}\.js$/);
  assert.match(manifest.worker.file, /^spikeling-worker\.[a-f0-9]{12}\.js$/);
  assert.match(manifest.stylesheet.file, /^spikeling-emulator\.[a-f0-9]{12}\.css$/);
  assert.deepEqual(JSON.parse(await readFile(join(outputDirectory, "manifest.json"), "utf8")), manifest);
});

test("each production manifest reports genuine SHA-256, raw bytes and maximum-compression gzip bytes", async () => {
  for (const name of ["application", "worker", "stylesheet"] as const) {
    const content = await asset(name);
    const expected = hash(content);
    assert.equal(manifest[name].sha256, expected);
    assert.ok(manifest[name].file.includes(expected.slice(0, 12)));
    assert.equal(manifest[name].bytes, Buffer.byteLength(content));
    assert.equal(manifest[name].gzipBytes, gzipSync(content, { level: 9 }).byteLength);
    assert.match(content, /^\/\*! SPDX-License-Identifier: GPL-3\.0-or-later/);
  }
  assert.equal(manifest.licence, "GPL-3.0-or-later");
});

test("production builds and complete manifest versions remain byte-for-byte reproducible", async () => {
  const secondDirectory = await mkdtemp(join(tmpdir(), "spikeling-reproducible-"));
  const second = await buildProductionAssets({ outputDirectory: secondDirectory });
  assert.deepEqual(second, manifest);
  for (const name of ["application", "worker", "stylesheet"] as const) {
    assert.equal(await readFile(join(secondDirectory, second[name].file), "utf8"), await asset(name));
  }
  assert.equal(manifest.version, hash(
    await asset("application") + "\n" + await asset("worker") + "\n" + await asset("stylesheet"),
  ).slice(0, 16));
});

test("standalone application and dedicated worker compile as browser-compatible modules", async () => {
  for (const name of ["application", "worker"] as const) {
    const result = spawnSync(process.execPath, ["--input-type=module", "--check"], {
      input: await asset(name),
      encoding: "utf8",
    });
    assert.equal(result.status, 0, result.stderr);
  }
});

test("production application references only its manifest-pinned dedicated worker", async () => {
  const application = await asset("application");
  assert.ok(application.includes('new URL("./' + manifest.worker.file + '", import.meta.url)'));
  assert.doesNotMatch(application, /emulator\.worker\.ts|from\s+["'][^"']+\.ts["']/);
  assert.match(application, /\[data-spikeling-emulator\]/);
  assert.match(application, /https:\/\/github\.com\/OpenSourceNeuro\/Spikeling/);
  assert.doesNotMatch(application, /\bfetch\s*\(|XMLHttpRequest|navigator\.serial|document\.body\.innerHTML/);
});

test("six stylesheets remain concatenated in their deterministic component-to-page order", async () => {
  const stylesheet = await asset("stylesheet");
  assert.deepEqual(manifest.sourceStylesheets, PRODUCTION_STYLE_SOURCES);
  assert.equal(PRODUCTION_STYLE_SOURCES.length, 6);
  let previous = -1;
  for (const source of PRODUCTION_STYLE_SOURCES) {
    const current = stylesheet.indexOf("/* Source: " + source + " */");
    assert.ok(current > previous, source + " should retain its cascade position");
    previous = current;
  }
  assert.match(stylesheet, /\.spk-emulator/);
  assert.match(stylesheet, /\.osn-spikeling-emulator-page/);
  assert.doesNotMatch(stylesheet, /(?:^|\n)\s*(?:html|body|button|input|canvas|\*)\s*\{/);
});

test("compressed production payload remains small without npm or runtime dependencies", async () => {
  assert.ok(manifest.application.gzipBytes < 50_000);
  assert.ok(manifest.worker.gzipBytes < 15_000);
  assert.ok(manifest.stylesheet.gzipBytes < 7_000);
  assert.ok(manifest.application.gzipBytes + manifest.worker.gzipBytes + manifest.stylesheet.gzipBytes < 75_000);
  assert.ok(manifest.application.bytes < 250_000);

  const lock = JSON.parse(await readFile(new URL("../package-lock.json", import.meta.url), "utf8"));
  assert.deepEqual(Object.keys(lock.packages), [""]);
  const builder = await readFile(new URL("../tools/build.mjs", import.meta.url), "utf8");
  for (const imported of builder.matchAll(/from\s+["']([^"']+)["']/g)) {
    assert.ok(imported[1].startsWith("node:"), imported[1]);
  }
});

test("standalone bundle builder pins explicitly supplied worker filenames without package imports", async () => {
  const application = await bundleProductionEntry("src/integration/wordpress-entry.ts", {
    workerFilename: "spikeling-worker.0123456789ab.js",
  });
  assert.match(application, /\.\/spikeling-worker\.0123456789ab\.js/);
  assert.doesNotMatch(application, /^\s*import\s+/m);
});

test("generated production worker executes exact source-equivalent Float64 scientific samples", async () => {
  const scheduler = new ManualScheduler();
  const messages: WorkerToMainMessage[] = [];
  let receive: ((event: { data: MainToWorkerMessage }) => void) | undefined;
  const sandbox = {
    structuredClone,
    addEventListener(type: string, listener: (event: { data: MainToWorkerMessage }) => void): void {
      assert.equal(type, "message");
      receive = listener;
    },
    postMessage(message: WorkerToMainMessage, transfer?: readonly ArrayBuffer[]): void {
      messages.push(structuredClone(message, { transfer: transfer === undefined ? [] : [...transfer] }));
    },
    performance: { now: () => scheduler.now() },
    setTimeout: (callback: () => void, delay: number) => scheduler.setTimeout(callback, delay),
    clearTimeout: (handle: unknown) => scheduler.clearTimeout(handle),
  };

  new Script(await asset("worker"), { filename: manifest.worker.file }).runInNewContext(sandbox);
  assert.ok(receive);
  const options = { seed: 700, controls: { main: { patchCurrent: 18 } } };
  receive({ data: { type: "initialise", options, speedIndex: 0, maxStepsPerSlice: 4 } });
  assert.equal(messages[0]?.type, "ready", JSON.stringify(messages[0]));
  receive({ data: { type: "start" } });
  scheduler.advance(50);

  const actual: SimulationSample[] = messages.flatMap((message) =>
    message.type === "samples" ? unpackSamples(new Float64Array(message.buffer)) : [],
  );
  assert.equal(actual.length, 10);
  assert.deepEqual(actual, new SpikelingModel(options).run(10));
  assert.deepEqual(messages.filter((message) => message.type === "samples").map((message) => message.count), [4, 4, 2]);
  receive({ data: { type: "dispose" } });
  assert.equal(scheduler.pending, 0);
});

test("production worker reports invalid commands without exposing network or document dependencies", async () => {
  const messages: WorkerToMainMessage[] = [];
  let receive: ((event: { data: MainToWorkerMessage }) => void) | undefined;
  new Script(await asset("worker")).runInNewContext({
    addEventListener(_type: string, listener: typeof receive): void { receive = listener; },
    postMessage(message: WorkerToMainMessage): void { messages.push(message); },
  });
  assert.ok(receive);
  receive({ data: { type: "snapshot" } });
  assert.equal(messages[0]?.type, "error");
  assert.match(messages[0]?.type === "error" ? messages[0].message : "", /Initialise/);
  const worker = await asset("worker");
  assert.doesNotMatch(worker, /\bfetch\s*\(|XMLHttpRequest|navigator\.serial|\bdocument\b/);
});
