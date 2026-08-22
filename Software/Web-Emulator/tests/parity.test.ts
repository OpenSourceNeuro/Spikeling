// SPDX-License-Identifier: GPL-3.0-or-later

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  NEURON_PRESETS,
  SpikelingModel,
  TIMESTEP_MS,
} from "../src/index.ts";
import type {
  ControlsPatch,
  InitialisationMode,
  SimulationSample,
} from "../src/index.ts";

interface GoldenScenario {
  readonly name: string;
  readonly steps: number;
  readonly controls: ControlsPatch;
  readonly events: readonly {
    readonly step: number;
    readonly patch: ControlsPatch;
  }[];
  readonly seed: number;
  readonly initialisation: InitialisationMode;
  readonly compatibility: {
    readonly legacySynapse2DecayBug: boolean;
  };
  readonly samples: readonly (readonly number[])[];
}

interface GoldenFixtures {
  readonly metadata: {
    readonly sourceCommit: string;
    readonly desktopGraphBlobSha: string;
    readonly desktopPresetsBlobSha: string;
    readonly timestepMs: number;
    readonly absoluteTolerance: number;
    readonly scenarioCount: number;
    readonly sampleColumns: readonly (keyof SimulationSample)[];
  };
  readonly presets: readonly {
    readonly id: number;
    readonly a: number;
    readonly b: number;
    readonly c: number;
    readonly d: number;
    readonly restingPotential: number;
  }[];
  readonly scenarios: readonly GoldenScenario[];
}

const testDirectory = dirname(fileURLToPath(import.meta.url));
const fixturePath = join(testDirectory, "fixtures", "golden", "desktop-reference.json");
const fixtures = JSON.parse(readFileSync(fixturePath, "utf8")) as GoldenFixtures;

test("golden fixtures are pinned to the audited desktop source and all 20 presets", () => {
  assert.equal(
    fixtures.metadata.sourceCommit,
    "4d5dbf8d5c14c6e9f95d4f2f2e8307ed3d164918",
  );
  assert.equal(
    fixtures.metadata.desktopGraphBlobSha,
    "5501cacb7f5936b2190e760cf0c0ba9d88b97afa",
  );
  assert.equal(
    fixtures.metadata.desktopPresetsBlobSha,
    "88e9eb78a0c8462b48968a8a3817681bf5a43960",
  );
  assert.equal(fixtures.metadata.timestepMs, TIMESTEP_MS);
  assert.equal(fixtures.presets.length, 20);
  assert.equal(fixtures.scenarios.length, fixtures.metadata.scenarioCount);

  for (const expected of fixtures.presets) {
    const actual = NEURON_PRESETS[expected.id - 1];
    assert.equal(actual.a, expected.a);
    assert.equal(actual.b, expected.b);
    assert.equal(actual.c, expected.c);
    assert.equal(actual.d, expected.d);
    assert.equal(actual.restingPotential, expected.restingPotential);
  }
});

test("named scientific fixtures exercise the behaviours they claim to cover", () => {
  const byName = new Map(
    fixtures.scenarios.map((scenario) => [scenario.name, scenario]),
  );
  const reboundSpike = byName.get("rebound-spike");
  const reboundBurst = byName.get("rebound-burst");
  const inhibitionBurst = byName.get("inhibition-induced-bursting");
  const subthreshold = byName.get("sub-threshold-oscillations");

  assert.ok(reboundSpike);
  assert.ok(reboundBurst);
  assert.ok(inhibitionBurst);
  assert.ok(subthreshold);

  assert.ok(
    reboundSpike.samples.slice(800).some((row) => row[1] === 30),
    "Rebound Spike must spike after the inhibitory pulse is released.",
  );
  assert.ok(
    reboundBurst.samples.slice(800).filter((row) => row[1] === 30).length > 1,
    "Rebound Burst must fire repeatedly after the inhibitory pulse is released.",
  );
  assert.ok(
    inhibitionBurst.samples.some((row) => row[1] === 30),
    "The inhibition-induced-bursting preset fixture must exercise visible spikes.",
  );
  assert.equal(
    subthreshold.samples.filter((row) => row[1] === 30).length,
    0,
    "The sub-threshold fixture must not contain displayed spikes.",
  );
});

for (const scenario of fixtures.scenarios) {
  test("Python desktop-reference parity: " + scenario.name, () => {
    const model = new SpikelingModel({
      controls: scenario.controls,
      seed: scenario.seed,
      initialisation: scenario.initialisation,
      compatibility: scenario.compatibility,
    });
    const events = new Map(scenario.events.map((event) => [event.step, event.patch]));
    const tolerance = fixtures.metadata.absoluteTolerance;

    assert.equal(scenario.samples.length, scenario.steps);
    for (let stepIndex = 0; stepIndex < scenario.steps; stepIndex += 1) {
      const patch = events.get(stepIndex);
      if (patch !== undefined) {
        model.updateControls(patch);
      }

      const actual = model.step();
      const expected = scenario.samples[stepIndex];

      for (
        let columnIndex = 0;
        columnIndex < fixtures.metadata.sampleColumns.length;
        columnIndex += 1
      ) {
        const column = fixtures.metadata.sampleColumns[columnIndex];
        const difference = Math.abs(actual[column] - expected[columnIndex]);
        assert.ok(
          difference <= tolerance,
          scenario.name +
            ", step " +
            stepIndex +
            ", column " +
            column +
            ": expected " +
            expected[columnIndex] +
            ", received " +
            actual[column] +
            " (difference " +
            difference +
            ")",
        );

        if (column === "trigger") {
          assert.equal(actual[column], expected[columnIndex]);
        }
      }
    }
  });
}
