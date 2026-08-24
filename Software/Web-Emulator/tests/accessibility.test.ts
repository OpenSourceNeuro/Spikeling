// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  ACCESSIBLE_SPIKELING_PALETTE,
  DESKTOP_MINIMUM_WIDTH,
  MOBILE_MEDIA_QUERY,
  REDUCED_MOTION_MEDIA_QUERY,
  SPIKELING_PALETTE,
  TABLET_MEDIA_QUERY,
  TABLET_MINIMUM_WIDTH,
  contrastRatio,
  emulatorLayout,
  meetsTextContrast,
  relativeLuminance,
} from "../src/index.ts";
import { readDevelopmentAsset } from "../tools/serve.mjs";

test("WCAG relative luminance matches black, white and known sRGB reference points", () => {
  assert.equal(relativeLuminance("#000000"), 0);
  assert.equal(relativeLuminance("#FFFFFF"), 1);
  assert.equal(relativeLuminance("#ffffff"), 1);
  assert.ok(Math.abs(relativeLuminance("#ff0000") - 0.2126) < 1e-12);
  assert.ok(Math.abs(relativeLuminance("#00ff00") - 0.7152) < 1e-12);
  assert.ok(Math.abs(relativeLuminance("#0000ff") - 0.0722) < 1e-12);
  assert.ok(relativeLuminance("#010101") > 0);
});

test("WCAG contrast is symmetric and preserves the theoretical 21-to-1 extremes", () => {
  assert.equal(contrastRatio("#000000", "#ffffff"), 21);
  assert.equal(contrastRatio("#ffffff", "#000000"), 21);
  assert.equal(contrastRatio("#073642", "#073642"), 1);
});

test("malformed colour specifications never enter contrast calculations", () => {
  for (const invalid of ["", "#fff", "ffffff", "#fffffff", "#gg0000", "rgb(0,0,0)"]) {
    assert.throws(() => relativeLuminance(invalid), /six-digit hexadecimal/);
  }
});

test("all functional text colours satisfy normal-text WCAG AA on both dark surfaces", () => {
  const palette = ACCESSIBLE_SPIKELING_PALETTE;
  const textColours = [
    palette.foreground,
    palette.secondary,
    palette.stimulusText,
    palette.cellText,
    palette.synapse1Text,
    palette.synapse2Text,
    palette.warningText,
    palette.errorText,
    palette.focus,
  ];
  for (const colour of textColours) {
    for (const background of [palette.background, palette.panel]) {
      assert.ok(meetsTextContrast(colour, background), colour + " must be AA on " + background);
    }
  }
});

test("the accessible palette corrects unsafe original accent text without changing trace colours", () => {
  const background = ACCESSIBLE_SPIKELING_PALETTE.background;
  assert.equal(meetsTextContrast(SPIKELING_PALETTE.stimulus, background), false);
  assert.equal(meetsTextContrast(SPIKELING_PALETTE.synapse2Current, background), false);
  assert.equal(meetsTextContrast(SPIKELING_PALETTE.membrane, background), false);
  assert.ok(meetsTextContrast(ACCESSIBLE_SPIKELING_PALETTE.stimulusText, background));
  assert.ok(meetsTextContrast(ACCESSIBLE_SPIKELING_PALETTE.synapse2Text, background));
  assert.ok(meetsTextContrast(ACCESSIBLE_SPIKELING_PALETTE.errorText, background));
  assert.equal(SPIKELING_PALETTE.stimulus, "#268BD2");
  assert.equal(SPIKELING_PALETTE.synapse1Current, "#2AA198");
  assert.equal(SPIKELING_PALETTE.synapse2Current, "#D33682");
});

test("AA and AAA thresholds distinguish normal and large accessible text", () => {
  const accent = SPIKELING_PALETTE.stimulus;
  const background = ACCESSIBLE_SPIKELING_PALETTE.background;
  assert.equal(meetsTextContrast(accent, background), false);
  assert.equal(meetsTextContrast(accent, background, { largeText: true }), true);
  assert.equal(meetsTextContrast(accent, background, { level: "AAA", largeText: true }), false);
  assert.equal(meetsTextContrast("#ffffff", "#000000", { level: "AAA" }), true);
  assert.throws(() => meetsTextContrast("#ffffff", "#000000", { level: "A" as "AA" }), /AA or AAA/);
});

test("desktop, tablet and mobile boundaries match the approved OSN breakpoints", () => {
  assert.equal(TABLET_MINIMUM_WIDTH, 768);
  assert.equal(DESKTOP_MINIMUM_WIDTH, 1_025);
  assert.equal(emulatorLayout(320), "mobile");
  assert.equal(emulatorLayout(767.99), "mobile");
  assert.equal(emulatorLayout(768), "tablet");
  assert.equal(emulatorLayout(1_024), "tablet");
  assert.equal(emulatorLayout(1_025), "desktop");
  assert.equal(emulatorLayout(2_560), "desktop");
  assert.equal(TABLET_MEDIA_QUERY, "(max-width: 1024px)");
  assert.equal(MOBILE_MEDIA_QUERY, "(max-width: 767px)");
  assert.equal(REDUCED_MOTION_MEDIA_QUERY, "(prefers-reduced-motion: reduce)");
});

test("impossible viewport sizes are rejected before choosing a responsive layout", () => {
  for (const invalid of [0, -1, Infinity, -Infinity, NaN]) {
    assert.throws(() => emulatorLayout(invalid), /positive finite/);
  }
});

test("responsive stylesheet keeps desktop, tablet and mobile graph-first grid areas explicit", async () => {
  const { content } = await readDevelopmentAsset("/src/styles/emulator.css");
  assert.match(content, /max-width:\s*1240px/);
  assert.match(content, /grid-template-columns:\s*minmax\(0, 1fr\)\s+minmax\(360px, 440px\)/);
  assert.match(content, /"instrument main"\s*\n\s*"instrument stimulus"\s*\n\s*"synapses synapses"/);
  assert.match(content, /@media\s*\(max-width:\s*1024px\)/);
  assert.match(content, /@media\s*\(max-width:\s*767px\)/);
  assert.match(content, /"instrument"\s*\n\s*"main"\s*\n\s*"stimulus"\s*\n\s*"synapses"/);
  assert.match(content, /minmax\(0, 1fr\)/);
});

test("embedded labels use readable pixel sizes regardless of the host site's root rem scale", async () => {
  const { content } = await readDevelopmentAsset("/src/styles/emulator.css");
  assert.match(content, /\.spk-emulator__panel-summary\s*\{[^}]*font-size:\s*16px/s);
  assert.match(content, /\.spk-emulator__transport-title\s*\{[^}]*font-size:\s*16px/s);
  assert.match(content, /\.spk-emulator \.spk-controls__heading,[\s\S]*?font-size:\s*15px/);
  assert.match(content, /\.spk-emulator \.spk-controls__control-label,[\s\S]*?font-size:\s*13px/);
});

test("trace checkboxes retain theme-independent checked styling and signal-matched labels", async () => {
  const { content } = await readDevelopmentAsset("/src/styles/oscilloscope.css");
  assert.match(content, /\.spk-oscilloscope \.spk-oscilloscope__trace-input\s*\{[^}]*width:\s*18px/s);
  assert.match(content, /\.spk-oscilloscope \.spk-oscilloscope__trace-input:checked\s*\{[^}]*background:\s*var\(--spk-trace-colour\)/s);
  assert.match(content, /\.spk-oscilloscope__trace-label\s*\{[^}]*color:\s*var\(--spk-trace-colour\)/s);
  assert.match(content, /data-trace-group="synapses"\][^}]*repeat\(4,\s*minmax\(0,\s*1fr\)\)/s);
});

test("slider fills and toggle indicators remain readable under a 10px host root scale", async () => {
  const { content } = await readDevelopmentAsset("/src/styles/controls.css");
  assert.match(content, /\.spk-controls \.spk-controls__toggle\s*\{[^}]*width:\s*44px[^}]*height:\s*24px/s);
  assert.match(content, /\.spk-controls \.spk-controls__toggle::before\s*\{[^}]*width:\s*18px[^}]*height:\s*18px/s);
  assert.match(content, /::-webkit-slider-runnable-track\s*\{[^}]*height:\s*8px/s);
  assert.match(content, /::-moz-range-progress\s*\{[^}]*height:\s*8px/s);
});

test("scoped styles expose visible focus, forced-colours and touch-safe native controls", async () => {
  const { content } = await readDevelopmentAsset("/src/styles/emulator.css");
  assert.match(content, /:where\(button, input, select, summary, a\):focus-visible/);
  assert.match(content, /outline:\s*3px solid var\(--spk-focus\)/);
  assert.match(content, /@media\s*\(forced-colors:\s*active\)/);
  assert.match(content, /CanvasText/);
  assert.match(content, /min-height:\s*2\.75rem/);
  assert.match(content, /@media\s*\(prefers-contrast:\s*more\)/);
});

test("reduced-motion styles remove decoration without disabling scientific rendering", async () => {
  const { content } = await readDevelopmentAsset("/src/styles/emulator.css");
  assert.match(content, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
  assert.match(content, /animation:\s*none !important/);
  assert.match(content, /transition:\s*none !important/);
  assert.match(content, /scroll-behavior:\s*auto !important/);
  assert.doesNotMatch(content, /canvas\s*\{[^}]*display:\s*none/s);
});

test("Phase 7 CSS cannot leak generic selectors into Elementor or unrelated host pages", async () => {
  const { content } = await readDevelopmentAsset("/src/styles/emulator.css");
  assert.doesNotMatch(content, /(?:^|\n)\s*(?:html|body|button|input|select|canvas|summary|a|\*)\s*\{/);
  assert.match(content, /\.spk-emulator\s*\{/);
  assert.match(content, /\.spk-emulator\s+\*/);
  assert.match(content, /\.spk-emulator\s+\.spk-controls/);
});

test("functional accessible text tokens match the auditable TypeScript palette exactly", async () => {
  const { content } = await readDevelopmentAsset("/src/styles/emulator.css");
  const mappings = [
    ["--spk-stimulus-text", ACCESSIBLE_SPIKELING_PALETTE.stimulusText],
    ["--spk-cell-text", ACCESSIBLE_SPIKELING_PALETTE.cellText],
    ["--spk-syn1-text", ACCESSIBLE_SPIKELING_PALETTE.synapse1Text],
    ["--spk-syn2-text", ACCESSIBLE_SPIKELING_PALETTE.synapse2Text],
    ["--spk-warning-text", ACCESSIBLE_SPIKELING_PALETTE.warningText],
    ["--spk-error-text", ACCESSIBLE_SPIKELING_PALETTE.errorText],
  ];
  for (const [name, colour] of mappings) {
    assert.match(content, new RegExp(name + ":\\s*" + colour, "i"));
  }
  assert.match(content, /data-synapse="synapse1"\].*spk-synapses__subheading/);
  assert.match(content, /data-synapse="synapse2"\].*spk-synapses__subheading/);
  assert.match(content, /spk-oscilloscope__status\[data-state="running"\]/);
  assert.match(content, /spk-oscilloscope__status\[data-state="paused"\]/);
});
