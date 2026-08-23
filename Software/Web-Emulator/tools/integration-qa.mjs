// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

import { assessLaunchReadiness } from "../src/integration/launch-readiness.ts";
import { NEURON_PRESETS } from "../src/model/presets.ts";
import { DESKTOP_STEPS_PER_UPDATE } from "../src/simulation/speed.ts";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const PRODUCTION_GZIP_BUDGETS = Object.freeze({
  application: 50_000,
  worker: 15_000,
  stylesheet: 7_000,
  total: 75_000,
});

function digest(content) {
  return createHash("sha256").update(content).digest("hex");
}

/** Validate only manifest-referenced files; unrelated local build artefacts are never deleted. */
export async function validateProductionAssets(assetDirectory, manifest) {
  assert.match(manifest.version, /^[a-f0-9]{16}$/, "Invalid reproducible production manifest version.");
  const content = {};
  let compressedBytes = 0;

  for (const name of ["application", "worker", "stylesheet"]) {
    const entry = manifest[name];
    assert.ok(entry && typeof entry.file === "string", "Missing " + name + " manifest entry.");
    const extension = name === "stylesheet" ? "css" : "js";
    const prefix = name === "worker" ? "spikeling-worker" : "spikeling-emulator";
    assert.match(entry.file, new RegExp("^" + prefix + "\\.[a-f0-9]{12}\\." + extension + "$"),
      "Unsafe or invalid " + name + " asset filename.");
    const bytes = await readFile(resolve(assetDirectory, entry.file));
    const sha256 = digest(bytes);
    assert.equal(entry.sha256, sha256, name + " content does not match its SHA-256 digest.");
    assert.ok(entry.file.includes(sha256.slice(0, 12)), name + " filename does not match its content hash.");
    assert.equal(entry.bytes, bytes.byteLength, name + " byte count is inaccurate.");
    assert.equal(entry.gzipBytes, gzipSync(bytes, { level: 9 }).byteLength,
      name + " gzip byte count is inaccurate.");
    assert.ok(entry.gzipBytes < PRODUCTION_GZIP_BUDGETS[name], name + " exceeds its compressed budget.");
    compressedBytes += entry.gzipBytes;
    content[name] = bytes.toString("utf8");
  }

  assert.ok(compressedBytes < PRODUCTION_GZIP_BUDGETS.total, "Combined production payload exceeds its compressed budget.");
  assert.equal(manifest.version,
    digest(content.application + "\n" + content.worker + "\n" + content.stylesheet).slice(0, 16),
    "Manifest version does not reflect its complete production payload.");
  assert.ok(content.application.includes('new URL("./' + manifest.worker.file + '", import.meta.url)'),
    "Application does not use its manifest-pinned scientific worker.");
  assert.doesNotMatch(content.application + "\n" + content.worker,
    /\bfetch\s*\(|XMLHttpRequest|navigator\.serial/,
    "Production simulation must not make network requests or claim hardware-serial support.");
  assert.doesNotMatch(content.stylesheet, /(?:^|\n)\s*(?:html|body|button|input|canvas|\*)\s*\{/,
    "Production CSS contains an unscoped global selector.");
  for (const marker of ["(max-width: 1024px)", "(max-width: 767px)",
    "(prefers-reduced-motion: reduce)", "(forced-colors: active)"]) {
    assert.ok(content.stylesheet.includes(marker), "Missing responsive or accessibility rule: " + marker);
  }

  return { compressedBytes, content };
}

/** Reproducible local structural audit plus a deliberately honest captured-site assessment. */
export async function runIntegrationQa({ root = ROOT, evidence } = {}) {
  const assets = resolve(root, "wordpress/spikeling-emulator/assets");
  const [manifest, fixture, plugin, lock, capturedEvidence] = await Promise.all([
    readFile(resolve(assets, "manifest.json"), "utf8").then(JSON.parse),
    readFile(resolve(root, "tests/fixtures/golden/desktop-reference.json"), "utf8").then(JSON.parse),
    readFile(resolve(root, "wordpress/spikeling-emulator/spikeling-emulator.php"), "utf8"),
    readFile(resolve(root, "package-lock.json"), "utf8").then(JSON.parse),
    evidence === undefined
      ? readFile(resolve(root, "wordpress/phase-9-evidence.json"), "utf8").then(JSON.parse)
      : Promise.resolve(evidence),
  ]);
  const production = await validateProductionAssets(assets, manifest);

  assert.equal(NEURON_PRESETS.length, 20, "The emulator must retain all 20 desktop neuronal presets.");
  assert.equal(DESKTOP_STEPS_PER_UPDATE.length, 10, "The emulator must retain all ten desktop speeds.");
  assert.equal(fixture.metadata.scenarioCount, fixture.scenarios.length, "Golden-fixture scenario metadata is inaccurate.");
  assert.ok(fixture.scenarios.length >= 33, "The pinned desktop-reference regression matrix is incomplete.");
  assert.equal(capturedEvidence.desktopReferenceScenarios, fixture.scenarios.length,
    "Captured launch evidence no longer matches committed desktop-reference fixtures.");
  assert.equal(capturedEvidence.neuronPresetCount, NEURON_PRESETS.length,
    "Captured launch evidence no longer matches the neuronal preset inventory.");
  assert.equal(capturedEvidence.speedCount, DESKTOP_STEPS_PER_UPDATE.length,
    "Captured launch evidence no longer matches the simulation speed inventory.");
  assert.deepEqual(Object.keys(lock.packages), [""], "The emulator acquired an unaudited npm dependency.");
  for (const marker of ["add_shortcode", "is_singular()", "has_shortcode", "_elementor_data",
    "wp_unique_id", "wp_enqueue_style", "wp_enqueue_script"]) {
    assert.ok(plugin.includes(marker), "WordPress isolation contract is missing: " + marker);
  }
  assert.doesNotMatch(plugin, /register_rest_route|update_option|register_activation_hook/,
    "WordPress integration must not introduce global settings, REST endpoints or activation side effects.");

  const readiness = assessLaunchReadiness(capturedEvidence);
  return {
    manifestVersion: manifest.version,
    compressedBytes: production.compressedBytes,
    referenceScenarios: fixture.scenarios.length,
    presetCount: NEURON_PRESETS.length,
    speedCount: DESKTOP_STEPS_PER_UPDATE.length,
    capturedAt: capturedEvidence.capturedAt,
    readiness,
  };
}

const invokedDirectly = process.argv[1] !== undefined
  && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  try {
    const report = await runIntegrationQa();
    process.stdout.write("Phase 9 production integration audit: PASS\n");
    process.stdout.write("  SHA-256-pinned assets: " + report.manifestVersion + "; "
      + report.compressedBytes.toLocaleString("en-GB") + " bytes combined gzip\n");
    process.stdout.write("  Scientific matrix: " + report.referenceScenarios + " desktop scenarios, "
      + report.presetCount + " presets, " + report.speedCount + " speeds\n");
    process.stdout.write("  Captured WordPress evidence: " + report.capturedAt + "\n");
    for (const gate of report.readiness.gates) {
      process.stdout.write("  " + gate.status.toUpperCase().padEnd(7) + " " + gate.id + ": " + gate.detail + "\n");
    }
    process.stdout.write("  Production publication permitted: "
      + (report.readiness.publishAllowed ? "YES" : "NO") + "\n");
  } catch (error) {
    process.stderr.write("Phase 9 production integration audit: FAIL\n  "
      + (error instanceof Error ? error.message : String(error)) + "\n");
    process.exitCode = 1;
  }
}
