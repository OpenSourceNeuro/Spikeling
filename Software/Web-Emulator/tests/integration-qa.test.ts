// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import {
  APPROVED_WEBSITE_ORIGIN,
  EXISTING_DESKTOP_RELEASE_URL,
  EXPECTED_EMULATOR_CTA_COUNT,
  REQUIRED_RELEASE_BROWSERS,
  REQUIRED_RELEASE_VIEWPORTS,
  assessBrowserCoverage,
  assessEmulatorCallsToAction,
  assessLaunchReadiness,
  assessViewportCoverage,
} from "../src/index.ts";
import type { LaunchEvidence, ReleaseBrowser, ReleaseViewport } from "../src/index.ts";
import { PRODUCTION_GZIP_BUDGETS, runIntegrationQa, validateProductionAssets } from "../tools/integration-qa.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const assetDirectory = resolve(root, "wordpress/spikeling-emulator/assets");
const manifest = JSON.parse(await readFile(resolve(assetDirectory, "manifest.json"), "utf8"));
const captured: LaunchEvidence = JSON.parse(
  await readFile(resolve(root, "wordpress/phase-9-evidence.json"), "utf8"),
);
const publicUrl = APPROVED_WEBSITE_ORIGIN + "/index.php/spikeling-web-emulator/";

function approvedEvidence(): LaunchEvidence {
  return {
    ...captured,
    verifiedBrowsers: [...REQUIRED_RELEASE_BROWSERS],
    realViewports: [...REQUIRED_RELEASE_VIEWPORTS],
    elementorEditorVerified: true,
    anonymousFrontendVerified: true,
    ctas: captured.ctas.map((link) => ({ ...link, href: publicUrl })),
    finalPublicUrl: publicUrl,
    publishingApproved: true,
  };
}

function gate(evidence: LaunchEvidence, id: string) {
  const found = assessLaunchReadiness(evidence).gates.find((entry) => entry.id === id);
  assert.ok(found, "Missing launch gate: " + id);
  return found;
}

test("release matrix requires actual Chrome, Edge, Firefox and Safari coverage", () => {
  assert.deepEqual(REQUIRED_RELEASE_BROWSERS, ["Chrome", "Edge", "Firefox", "Safari"]);
  assert.deepEqual(assessBrowserCoverage(["Chrome"]), [
    { name: "Chrome", evidence: "browser", status: "pass" },
    { name: "Edge", evidence: "missing", status: "pending" },
    { name: "Firefox", evidence: "missing", status: "pending" },
    { name: "Safari", evidence: "missing", status: "pending" },
  ]);
});

test("complete real-browser coverage passes every required browser exactly once", () => {
  const entries = assessBrowserCoverage(["Safari", "Chrome", "Edge", "Firefox", "Chrome"]);
  assert.equal(entries.length, 4);
  assert.ok(entries.every((entry) => entry.evidence === "browser" && entry.status === "pass"));
});

test("unknown browser evidence cannot silently masquerade as a required browser", () => {
  assert.throws(() => assessBrowserCoverage(["Chromium" as ReleaseBrowser]), /Unknown launch-matrix entry: Chromium/);
});

test("responsive matrix preserves every required desktop, laptop, tablet and mobile class", () => {
  assert.deepEqual(REQUIRED_RELEASE_VIEWPORTS, ["large-desktop", "laptop", "tablet", "mobile"]);
});

test("automated responsive coverage remains pending until a genuine browser verifies the viewport", () => {
  const entries = assessViewportCoverage(["large-desktop"], [...REQUIRED_RELEASE_VIEWPORTS]);
  assert.deepEqual(entries, [
    { name: "large-desktop", evidence: "browser", status: "pass" },
    { name: "laptop", evidence: "automated", status: "pending" },
    { name: "tablet", evidence: "automated", status: "pending" },
    { name: "mobile", evidence: "automated", status: "pending" },
  ]);
});

test("missing responsive coverage is distinguishable from an automated breakpoint check", () => {
  const entries = assessViewportCoverage([], ["tablet"]);
  assert.equal(entries.find((entry) => entry.name === "tablet")?.evidence, "automated");
  assert.equal(entries.find((entry) => entry.name === "mobile")?.evidence, "missing");
  assert.ok(entries.every((entry) => entry.status === "pending"));
});

test("unknown viewport evidence fails explicitly", () => {
  assert.throws(() => assessViewportCoverage(["phablet" as ReleaseViewport]), /Unknown launch-matrix entry: phablet/);
});

test("the two current GitHub desktop-release buttons are pending, not production-ready", () => {
  assert.equal(EXPECTED_EMULATOR_CTA_COUNT, 2);
  const result = assessEmulatorCallsToAction(captured.ctas);
  assert.equal(result.status, "pending");
  assert.match(result.detail, /desktop release/);
  assert.ok(captured.ctas.every((link) => link.href === EXISTING_DESKTOP_RELEASE_URL));
});

test("exactly two confirmed public Open Source Neuro emulator buttons pass", () => {
  const approved = approvedEvidence();
  assert.equal(assessEmulatorCallsToAction(approved.ctas, publicUrl).status, "pass");
});

test("browser-specific emulator button wording remains supported", () => {
  const links = [
    { label: "Try the browser emulator", href: publicUrl },
    { label: "Try emulator", href: publicUrl },
  ];
  assert.equal(assessEmulatorCallsToAction(links, publicUrl).status, "pass");
});

test("missing or unexpected numbers of emulator buttons block publication", () => {
  assert.equal(assessEmulatorCallsToAction([]).status, "blocked");
  assert.equal(assessEmulatorCallsToAction(captured.ctas.slice(0, 1)).status, "blocked");
  assert.equal(assessEmulatorCallsToAction([...captured.ctas, captured.ctas[0]]).status, "blocked");
});

test("unrelated desktop-download links are never mistaken for emulator buttons", () => {
  const links = [...approvedEvidence().ctas, { label: "Download desktop software", href: EXISTING_DESKTOP_RELEASE_URL }];
  assert.equal(assessEmulatorCallsToAction(links, publicUrl).status, "pass");
});

test("mixed desktop-release and browser-emulator destinations block publication", () => {
  const links = [captured.ctas[0], { ...captured.ctas[1], href: publicUrl }];
  assert.equal(assessEmulatorCallsToAction(links, publicUrl).status, "blocked");
});

test("authenticated draft-preview destinations are never accepted as public CTA URLs", () => {
  for (const url of [
    APPROVED_WEBSITE_ORIGIN + "/?page_id=1196&preview=true",
    APPROVED_WEBSITE_ORIGIN + "/index.php/spikeling-web-emulator/?preview=true",
    APPROVED_WEBSITE_ORIGIN + "/index.php/spikeling-web-emulator/#private",
  ]) {
    const links = captured.ctas.map((link) => ({ ...link, href: url }));
    assert.equal(assessEmulatorCallsToAction(links, url).status, "blocked", url);
  }
});

test("foreign origins, insecure origins, invalid URLs and website roots are rejected", () => {
  for (const url of [
    "https://example.com/index.php/spikeling-web-emulator/",
    "http://www.opensourceneuro.com/index.php/spikeling-web-emulator/",
    "not a url",
    APPROVED_WEBSITE_ORIGIN + "/",
  ]) {
    const links = captured.ctas.map((link) => ({ ...link, href: url }));
    assert.equal(assessEmulatorCallsToAction(links, url).status, "blocked", url);
  }
});

test("captured deployed evidence never permits draft publication or hides missing environments", () => {
  const result = assessLaunchReadiness(captured);
  assert.equal(result.status, "blocked");
  assert.equal(result.publishAllowed, false);
  assert.equal(gate(captured, "editorial-safety").status, "pass");
  assert.equal(gate(captured, "browser-matrix").status, "pending");
  assert.equal(gate(captured, "responsive-matrix").status, "pending");
  assert.equal(gate(captured, "elementor-editor").status, "pending");
  assert.equal(gate(captured, "anonymous-frontend").status, "pending");
  assert.equal(gate(captured, "spikeling-ctas").status, "pending");
  assert.equal(gate(captured, "publication-approval").status, "blocked");
});

test("complete genuine evidence plus explicit owner permission permits publication", () => {
  const result = assessLaunchReadiness(approvedEvidence());
  assert.equal(result.status, "pass");
  assert.equal(result.publishAllowed, true);
  assert.ok(result.gates.every((entry) => entry.status === "pass"));
});

test("publication without explicit owner approval is blocked even when all technical checks pass", () => {
  const evidence = { ...approvedEvidence(), publishingApproved: false };
  assert.equal(gate(evidence, "publication-approval").status, "blocked");
  assert.equal(assessLaunchReadiness(evidence).publishAllowed, false);
});

test("a prematurely published emulator page is treated as an unauthorised editorial change", () => {
  const evidence: LaunchEvidence = { ...approvedEvidence(), pageStatus: "published", publishingApproved: false };
  assert.equal(gate(evidence, "editorial-safety").status, "blocked");
  assert.match(gate(evidence, "editorial-safety").detail, /without explicit approval/);
});

test("explicitly approved published pages do not trigger a false editorial-safety failure", () => {
  const evidence: LaunchEvidence = { ...approvedEvidence(), pageStatus: "published" };
  assert.equal(gate(evidence, "editorial-safety").status, "pass");
});

test("inactive WordPress plugins, asset leakage and site-origin errors block release", () => {
  assert.equal(gate({ ...approvedEvidence(), pluginActive: false }, "wordpress-plugin").status, "blocked");
  assert.equal(gate({ ...approvedEvidence(), assetIsolationVerified: false }, "asset-isolation").status, "blocked");
  assert.equal(gate({ ...approvedEvidence(), noSiteConsoleErrors: false }, "site-console").status, "blocked");
});

test("missing scientific presets, speeds or pinned desktop scenarios block release", () => {
  for (const patch of [
    { desktopReferenceScenarios: 32 },
    { neuronPresetCount: 19 },
    { speedCount: 9 },
  ]) {
    assert.equal(gate({ ...approvedEvidence(), ...patch }, "scientific-regressions").status, "blocked");
  }
});

test("genuine missing editor, anonymous, browser or viewport evidence remains pending after approval", () => {
  for (const [patch, id] of [
    [{ elementorEditorVerified: false }, "elementor-editor"],
    [{ anonymousFrontendVerified: false }, "anonymous-frontend"],
    [{ verifiedBrowsers: ["Chrome"] as const }, "browser-matrix"],
    [{ realViewports: ["large-desktop"] as const }, "responsive-matrix"],
  ] as const) {
    const evidence = { ...approvedEvidence(), ...patch };
    assert.equal(gate(evidence, id).status, "pending");
    assert.equal(assessLaunchReadiness(evidence).publishAllowed, false);
  }
});

test("launch assessment does not mutate the audited captured evidence", () => {
  const before = JSON.stringify(captured);
  assessLaunchReadiness(captured);
  assert.equal(JSON.stringify(captured), before);
});

test("committed production assets pass genuine content, gzip and reproducibility validation", async () => {
  const report = await validateProductionAssets(assetDirectory, manifest);
  assert.equal(report.compressedBytes, 48_660);
  assert.ok(report.compressedBytes < PRODUCTION_GZIP_BUDGETS.total);
  assert.match(report.content.application, /\[data-spikeling-emulator\]/);
});

test("tampered application, worker or stylesheet SHA-256 digests fail the integration audit", async () => {
  for (const name of ["application", "worker", "stylesheet"] as const) {
    const modified = structuredClone(manifest);
    modified[name].sha256 = "0".repeat(64);
    await assert.rejects(validateProductionAssets(assetDirectory, modified), new RegExp(name + " content"));
  }
});

test("path traversal or invalid production asset names are rejected before filesystem access", async () => {
  const modified = structuredClone(manifest);
  modified.application.file = "../../phase-9-evidence.json";
  await assert.rejects(validateProductionAssets(assetDirectory, modified), /Unsafe or invalid application asset filename/);
});

test("incorrect uncompressed or compressed production byte counts fail explicitly", async () => {
  for (const key of ["bytes", "gzipBytes"] as const) {
    const modified = structuredClone(manifest);
    modified.worker[key] += 1;
    await assert.rejects(validateProductionAssets(assetDirectory, modified), /worker .*byte count is inaccurate/);
  }
});

test("tampered reproducible production versions cannot pass a structural integration audit", async () => {
  const modified = { ...manifest, version: "0".repeat(16) };
  await assert.rejects(validateProductionAssets(assetDirectory, modified), /complete production payload/);
});

test("the complete integration gate combines pinned artefacts with honest draft-only launch evidence", async () => {
  const report = await runIntegrationQa();
  assert.equal(report.referenceScenarios, 33);
  assert.equal(report.presetCount, 20);
  assert.equal(report.speedCount, 10);
  assert.equal(report.compressedBytes, 48_660);
  assert.equal(report.readiness.publishAllowed, false);
});

test("integration evidence drifting from committed scientific inventories fails safely", async () => {
  await assert.rejects(
    runIntegrationQa({ evidence: { ...captured, desktopReferenceScenarios: 32 } }),
    /no longer matches committed desktop-reference fixtures/,
  );
  await assert.rejects(
    runIntegrationQa({ evidence: { ...captured, neuronPresetCount: 19 } }),
    /no longer matches the neuronal preset inventory/,
  );
  await assert.rejects(
    runIntegrationQa({ evidence: { ...captured, speedCount: 9 } }),
    /no longer matches the simulation speed inventory/,
  );
});

test("integration CLI reports a structural pass while explicitly refusing unauthorised publication", () => {
  const result = spawnSync(process.execPath, [resolve(root, "tools/integration-qa.mjs")], {
    encoding: "utf8",
    cwd: root,
  });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Phase 9 production integration audit: PASS/);
  assert.match(result.stdout, /PENDING\s+browser-matrix/);
  assert.match(result.stdout, /BLOCKED\s+publication-approval/);
  assert.match(result.stdout, /Production publication permitted: NO/);
});
