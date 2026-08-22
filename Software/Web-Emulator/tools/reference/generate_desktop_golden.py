#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate source-pinned, deterministic fixtures for the Spikeling web model."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import runpy
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SOURCE_COMMIT = "4d5dbf8d5c14c6e9f95d4f2f2e8307ed3d164918"
GRAPH_BLOB_SHA = "5501cacb7f5936b2190e760cf0c0ba9d88b97afa"
PRESETS_BLOB_SHA = "88e9eb78a0c8462b48968a8a3817681bf5a43960"
TIMESTEP_MS = 0.1
MASK_32 = 0xFFFFFFFF
DEFAULT_SEED = 0x5350494B

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SOFTWARE_ROOT = PACKAGE_ROOT.parent
GRAPH_SOURCE = SOFTWARE_ROOT / "GUI - PyQt6-PySide6" / "Graph_Emulator.py"
PRESETS_SOURCE = SOFTWARE_ROOT / "GUI - PyQt6-PySide6" / "Parameters_Izhikevich.py"
OUTPUT = PACKAGE_ROOT / "tests" / "fixtures" / "golden" / "desktop-reference.json"

SAMPLE_COLUMNS = [
    "timeMs",
    "mainVm",
    "mainRecovery",
    "stimulus",
    "totalCurrent",
    "synapse1Vm",
    "synapse1Recovery",
    "synapse1Current",
    "synapse2Vm",
    "synapse2Recovery",
    "synapse2Current",
    "trigger",
]


def git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    header = ("blob " + str(len(content)) + "\0").encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def load_presets() -> list[list[float]]:
    if not GRAPH_SOURCE.is_file() or not PRESETS_SOURCE.is_file():
        raise RuntimeError(
            "Run from a full Spikeling checkout containing the desktop GUI sources."
        )

    graph_sha = git_blob_sha(GRAPH_SOURCE)
    presets_sha = git_blob_sha(PRESETS_SOURCE)
    if graph_sha != GRAPH_BLOB_SHA or presets_sha != PRESETS_BLOB_SHA:
        raise RuntimeError(
            "Desktop source does not match audited commit "
            + SOURCE_COMMIT
            + "; review and update the reference contract before regenerating fixtures."
        )

    graph_text = GRAPH_SOURCE.read_text(encoding="utf-8")
    required_fragments = [
        "Emulator_sampleinterval = 0.1",
        "self.Emulator_v = self.Emulator_v + self.Emulator_timestep_ms",
        "self.Emulator_u = self.Emulator_u + self.Emulator_timestep_ms",
        "self.Emulator_Syn2Input_Data *= self.Emulator_Syn2_Decay",
    ]
    for fragment in required_fragments:
        if fragment not in graph_text:
            raise RuntimeError("Desktop reference fragment missing: " + fragment)

    namespace = runpy.run_path(str(PRESETS_SOURCE))
    presets = namespace["IzhikevichNeurons"]
    if len(presets) != 20:
        raise RuntimeError("Expected exactly 20 audited Izhikevich presets.")
    return presets


class SeededRandom:
    """Same xorshift32 and Box-Muller sequence as src/model/random.ts."""

    def __init__(self, seed: int = DEFAULT_SEED) -> None:
        if not isinstance(seed, int) or seed < 1 or seed > MASK_32:
            raise ValueError("Seed must be an unsigned, non-zero 32-bit integer.")
        self.state = seed
        self.spare: float | None = None

    def uniform(self) -> float:
        value = self.state
        value ^= (value << 13) & MASK_32
        value ^= value >> 17
        value ^= (value << 5) & MASK_32
        self.state = value & MASK_32
        return (self.state + 1) / 4294967297

    def gaussian(self) -> float:
        if self.spare is not None:
            value = self.spare
            self.spare = None
            return value
        first = self.uniform()
        second = self.uniform()
        radius = math.sqrt(-2 * math.log(first))
        angle = 2 * math.pi * second
        self.spare = radius * math.sin(angle)
        return radius * math.cos(angle)


def photoreceptor_defaults() -> dict[str, Any]:
    return {"gain": 0, "decaySlider": 100, "recoverySlider": 25}


def cell_defaults() -> dict[str, Any]:
    return {
        "presetId": 1,
        "patchCurrent": 0,
        "noiseLevel": 0,
        "directCurrentEnabled": False,
        "lightEnabled": False,
        "photoreceptor": photoreceptor_defaults(),
    }


def controls_defaults() -> dict[str, Any]:
    synapse1 = cell_defaults()
    synapse1.update({"enabled": False, "gain": 0, "decaySlider": 995})
    synapse2 = cell_defaults()
    synapse2.update({"enabled": False, "gain": 0, "decaySlider": 990})
    return {
        "main": cell_defaults(),
        "synapse1": synapse1,
        "synapse2": synapse2,
        "stimulus": {
            "mode": "internal",
            "strength": 0,
            "frequencySlider": 0,
            "customSamples": [],
        },
    }


def merge_controls(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for group, values in patch.items():
        for name, value in values.items():
            if name == "photoreceptor":
                result[group][name].update(value)
            else:
                result[group][name] = copy.deepcopy(value)
    return result


def photoreceptor_state() -> dict[str, float]:
    return {"recovery": 1.0, "decay": 0.001, "recoveryRate": 0.025}


def cell_state(
    controls: dict[str, Any],
    presets: list[list[float]],
    initialisation: str,
) -> dict[str, Any]:
    initial_v = -65.0 if initialisation == "desktop" else float(
        presets[controls["presetId"] - 1][4]
    )
    return {
        "neuron": {"v": initial_v, "u": 0.0, "totalCurrent": 0.0},
        "photoreceptor": photoreceptor_state(),
    }


def synapse_state(
    controls: dict[str, Any],
    presets: list[list[float]],
    initialisation: str,
) -> dict[str, Any]:
    result = cell_state(controls, presets, initialisation)
    result["current"] = 0.0
    return result


def integrate(neuron: dict[str, float], preset: list[float]) -> tuple[float, float, bool]:
    a, b, c, d = preset[:4]
    v_previous = neuron["v"]
    u_previous = neuron["u"]
    v = v_previous + TIMESTEP_MS * (
        0.04 * v_previous * v_previous
        + 5.0 * v_previous
        + 140.0
        - u_previous
        + neuron["totalCurrent"]
    )
    u = u_previous + TIMESTEP_MS * (a * (b * v - u_previous))

    if v >= 30.0:
        v = c
        u += d
    if v < -110.0:
        v = -110.0

    spiked = False
    if v >= 0.0:
        v = 30.0
        spiked = True

    return float(v), float(u), spiked


def photo_step(
    state: dict[str, float],
    stimulus: float,
    controls: dict[str, Any],
) -> float:
    polarity = 1.0 if controls["gain"] >= 0 else -1.0
    current = stimulus / 25.0 * (controls["gain"] / 0.5) * state["recovery"]

    if state["recovery"] > 0.0:
        state["recovery"] -= polarity * state["decay"] * current
    if state["recovery"] < 0.0:
        state["recovery"] = 0.0
    if state["recovery"] < 1.0:
        state["recovery"] += state["recoveryRate"]

    state["decay"] = controls["decaySlider"] / 100000.0
    state["recoveryRate"] = controls["recoverySlider"] / 1000.0
    return current


class DesktopReference:
    def __init__(
        self,
        presets: list[list[float]],
        controls: dict[str, Any],
        *,
        seed: int = DEFAULT_SEED,
        initialisation: str = "desktop",
        legacy_synapse2_decay_bug: bool = False,
    ) -> None:
        self.presets = presets
        self.controls = merge_controls(controls_defaults(), controls)
        self.random = SeededRandom(seed)
        self.legacy_synapse2_decay_bug = legacy_synapse2_decay_bug
        self.step_index = 0
        self.main = cell_state(self.controls["main"], presets, initialisation)
        self.synapse1 = synapse_state(
            self.controls["synapse1"], presets, initialisation
        )
        self.synapse2 = synapse_state(
            self.controls["synapse2"], presets, initialisation
        )
        self.stimulus_state = {
            "counter": 0,
            "steps": 1000,
            "triggerPending": False,
            "customIndex": 0,
            "customResetPending": True,
        }

    def update_controls(self, patch: dict[str, Any]) -> None:
        previous_mode = self.controls["stimulus"]["mode"]
        self.controls = merge_controls(self.controls, patch)
        stimulus_patch = patch.get("stimulus", {})
        if "customSamples" in stimulus_patch or (
            previous_mode != "custom" and self.controls["stimulus"]["mode"] == "custom"
        ):
            self.stimulus_state["customResetPending"] = True

    def stimulus_step(self) -> tuple[float, int]:
        controls = self.controls["stimulus"]
        state = self.stimulus_state

        if controls["mode"] == "custom" and controls["customSamples"]:
            trigger = 0
            if state["customResetPending"]:
                state["customIndex"] = 0
                state["customResetPending"] = False
                trigger = 1
            if state["customIndex"] >= len(controls["customSamples"]):
                state["customIndex"] = 0
                trigger = 1
            value = controls["customSamples"][state["customIndex"]]
            state["customIndex"] += 1
            return float(value), trigger

        trigger = 1 if state["triggerPending"] else 0
        state["triggerPending"] = False
        value = controls["strength"] if state["counter"] < state["steps"] // 2 else 0.0
        state["counter"] += 1

        if state["counter"] >= state["steps"]:
            state["counter"] = 0
            state["triggerPending"] = True
            frequency = max(-100, min(100, int(-controls["frequencySlider"])))
            state["steps"] = max(1, int(500 + frequency * 500 / 100 + 10))

        return float(value), trigger

    def synapse_step(
        self,
        state: dict[str, Any],
        controls: dict[str, Any],
        stimulus: float,
        legacy_decay_bug: bool,
    ) -> tuple[float, float]:
        if not controls["enabled"]:
            state["current"] = 0.0
            return 0.0, 0.0

        noise = self.random.gaussian() * (controls["noiseLevel"] / 4)
        preset = self.presets[controls["presetId"] - 1]
        v, u, spiked = integrate(state["neuron"], preset)
        state["neuron"]["v"] = v
        state["neuron"]["u"] = u

        direct_current = stimulus if controls["directCurrentEnabled"] else 0.0
        photo_current = (
            photo_step(state["photoreceptor"], stimulus, controls["photoreceptor"])
            if controls["lightEnabled"]
            else 0.0
        )

        if spiked:
            state["current"] += controls["gain"]
        decay = 0.995 if legacy_decay_bug else controls["decaySlider"] / 1000
        state["current"] *= decay

        state["neuron"]["totalCurrent"] = (
            controls["patchCurrent"] + noise + direct_current + photo_current
        )
        return v, state["current"]

    def step(self) -> list[float | int]:
        main_controls = self.controls["main"]
        main_preset = self.presets[main_controls["presetId"] - 1]
        main_v, main_u, _ = integrate(self.main["neuron"], main_preset)
        self.main["neuron"]["v"] = main_v
        self.main["neuron"]["u"] = main_u

        stimulus, trigger = self.stimulus_step()
        noise = self.random.gaussian() * (main_controls["noiseLevel"] / 4)
        photo_current = (
            photo_step(
                self.main["photoreceptor"], stimulus, main_controls["photoreceptor"]
            )
            if main_controls["lightEnabled"]
            else 0.0
        )
        direct_current = stimulus if main_controls["directCurrentEnabled"] else 0.0

        synapse1_v, synapse1_current = self.synapse_step(
            self.synapse1, self.controls["synapse1"], stimulus, False
        )
        synapse2_v, synapse2_current = self.synapse_step(
            self.synapse2,
            self.controls["synapse2"],
            stimulus,
            self.legacy_synapse2_decay_bug,
        )

        total_current = (
            main_controls["patchCurrent"]
            + noise
            + photo_current
            + direct_current
            + synapse1_current
            + synapse2_current
        )
        self.main["neuron"]["totalCurrent"] = total_current

        result: list[float | int] = [
            self.step_index * TIMESTEP_MS,
            main_v,
            main_u,
            stimulus,
            total_current,
            synapse1_v,
            self.synapse1["neuron"]["u"],
            synapse1_current,
            synapse2_v,
            self.synapse2["neuron"]["u"],
            synapse2_current,
            trigger,
        ]
        self.step_index += 1
        return result


@dataclass(frozen=True)
class Scenario:
    name: str
    steps: int
    controls: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    seed: int = DEFAULT_SEED
    initialisation: str = "desktop"
    legacy_synapse2_decay_bug: bool = False
    description: str = ""


def scenarios() -> list[Scenario]:
    return [
        Scenario("zero-input-rest", 256, description="No injected current or stimulus."),
        Scenario("tonic-spiking", 640, {"main": {"presetId": 1, "patchCurrent": 18}}),
        Scenario("phasic-spiking", 640, {"main": {"presetId": 2, "patchCurrent": 18}}),
        Scenario("tonic-bursting", 640, {"main": {"presetId": 3, "patchCurrent": 18}}),
        Scenario("phasic-bursting", 640, {"main": {"presetId": 4, "patchCurrent": 18}}),
        Scenario("mixed-mode", 640, {"main": {"presetId": 5, "patchCurrent": 18}}),
        Scenario(
            "spike-frequency-adaptation",
            900,
            {"main": {"presetId": 6, "patchCurrent": 22}},
        ),
        Scenario(
            "class-1-excitability",
            480,
            {"main": {"presetId": 7, "patchCurrent": 35}},
        ),
        Scenario(
            "class-2-excitability",
            480,
            {"main": {"presetId": 8, "patchCurrent": 18}},
        ),
        Scenario("spike-latency", 480, {"main": {"presetId": 9, "patchCurrent": 18}}),
        Scenario(
            "sub-threshold-oscillations",
            480,
            {"main": {"presetId": 10, "patchCurrent": 0}},
        ),
        Scenario(
            "resonator",
            700,
            {"main": {"presetId": 11, "patchCurrent": 0}},
            events=[
                {"step": 120, "patch": {"main": {"patchCurrent": 22}}},
                {"step": 150, "patch": {"main": {"patchCurrent": 0}}},
                {"step": 250, "patch": {"main": {"patchCurrent": 22}}},
                {"step": 280, "patch": {"main": {"patchCurrent": 0}}},
            ],
        ),
        Scenario("integrator", 480, {"main": {"presetId": 12, "patchCurrent": 35}}),
        Scenario(
            "rebound-spike",
            1200,
            {"main": {"presetId": 13, "patchCurrent": -20}},
            events=[{"step": 800, "patch": {"main": {"patchCurrent": 0}}}],
        ),
        Scenario(
            "rebound-burst",
            1200,
            {"main": {"presetId": 14, "patchCurrent": -20}},
            events=[{"step": 800, "patch": {"main": {"patchCurrent": 0}}}],
        ),
        Scenario(
            "threshold-variability",
            480,
            {"main": {"presetId": 15, "patchCurrent": 18}},
        ),
        Scenario("bistability", 480, {"main": {"presetId": 16, "patchCurrent": 18}}),
        Scenario(
            "depolarizing-after-potential",
            480,
            {"main": {"presetId": 17, "patchCurrent": 18}},
        ),
        Scenario("accommodation", 480, {"main": {"presetId": 18, "patchCurrent": 18}}),
        Scenario(
            "inhibition-induced-spiking",
            800,
            {"main": {"presetId": 19, "patchCurrent": -25}},
        ),
        Scenario(
            "inhibition-induced-bursting",
            800,
            {"main": {"presetId": 20, "patchCurrent": 30}},
            description=(
                "The desktop-compatible u=0 initialisation did not burst under "
                "negative current in the audited model; positive current exercises "
                "the preset while preserving that source discrepancy."
            ),
        ),
        Scenario(
            "synaptic-excitation",
            760,
            {
                "synapse1": {
                    "enabled": True,
                    "patchCurrent": 45,
                    "gain": 24,
                    "decaySlider": 995,
                }
            },
        ),
        Scenario(
            "synaptic-inhibition",
            760,
            {
                "main": {"patchCurrent": 12},
                "synapse1": {
                    "enabled": True,
                    "patchCurrent": 45,
                    "gain": -24,
                    "decaySlider": 985,
                },
            },
        ),
        Scenario(
            "synapse-2-corrected-decay",
            760,
            {
                "synapse2": {
                    "enabled": True,
                    "patchCurrent": 45,
                    "gain": 20,
                    "decaySlider": 980,
                }
            },
            description="Approved correction: Synapse 2 uses its selected decay slider.",
        ),
        Scenario(
            "synapse-2-desktop-legacy-decay",
            760,
            {
                "synapse2": {
                    "enabled": True,
                    "patchCurrent": 45,
                    "gain": 20,
                    "decaySlider": 980,
                }
            },
            legacy_synapse2_decay_bug=True,
            description="Exact desktop bug: Synapse 2 ignores its slider and uses .995.",
        ),
        Scenario(
            "photoreceptor-adaptation",
            640,
            {
                "main": {
                    "lightEnabled": True,
                    "photoreceptor": {
                        "gain": 35,
                        "decaySlider": 85,
                        "recoverySlider": 18,
                    },
                },
                "stimulus": {"strength": 35},
            },
        ),
        Scenario(
            "photoreceptor-inhibitory",
            480,
            {
                "main": {
                    "lightEnabled": True,
                    "photoreceptor": {
                        "gain": -25,
                        "decaySlider": 110,
                        "recoverySlider": 20,
                    },
                },
                "stimulus": {"strength": 30},
            },
        ),
        Scenario(
            "internal-square-and-trigger",
            1040,
            {
                "main": {"directCurrentEnabled": True},
                "stimulus": {"strength": 24, "frequencySlider": 35},
            },
        ),
        Scenario(
            "custom-stimulus-wrap",
            36,
            {
                "main": {"directCurrentEnabled": True},
                "stimulus": {
                    "mode": "custom",
                    "customSamples": [0, 15, -5, 30, -10],
                },
            },
        ),
        Scenario(
            "seeded-main-and-synaptic-noise",
            320,
            {
                "main": {"noiseLevel": 24, "patchCurrent": 8},
                "synapse1": {
                    "enabled": True,
                    "noiseLevel": 16,
                    "patchCurrent": 35,
                    "gain": 12,
                },
                "synapse2": {
                    "enabled": True,
                    "noiseLevel": 12,
                    "patchCurrent": -20,
                    "gain": -8,
                },
            },
            seed=0x0BAD5EED,
        ),
        Scenario(
            "approved-preset-initialisation",
            256,
            {"main": {"presetId": 1, "patchCurrent": 12}},
            initialisation="preset",
            description="Browser starts at the selected preset resting potential.",
        ),
        Scenario(
            "auxiliary-negative-patch",
            320,
            {
                "synapse1": {
                    "enabled": True,
                    "patchCurrent": -45,
                    "gain": 18,
                }
            },
            description="Approved correction: auxiliary patch current accepts -50..50.",
        ),
        Scenario(
            "synapse-state-retention",
            460,
            {
                "synapse1": {
                    "enabled": True,
                    "patchCurrent": 45,
                    "gain": 15,
                }
            },
            events=[
                {"step": 180, "patch": {"synapse1": {"enabled": False}}},
                {"step": 260, "patch": {"synapse1": {"enabled": True}}},
            ],
        ),
    ]


def rounded_sample(values: list[float | int]) -> list[float | int]:
    result: list[float | int] = []
    for value in values:
        if isinstance(value, int):
            result.append(value)
        else:
            rounded = round(value, 12)
            result.append(0 if rounded == 0 else rounded)
    return result


def generate(presets: list[list[float]]) -> dict[str, Any]:
    generated_scenarios: list[dict[str, Any]] = []

    for scenario in scenarios():
        reference = DesktopReference(
            presets,
            scenario.controls,
            seed=scenario.seed,
            initialisation=scenario.initialisation,
            legacy_synapse2_decay_bug=scenario.legacy_synapse2_decay_bug,
        )

        events_by_step = {
            int(event["step"]): event["patch"] for event in scenario.events
        }
        samples: list[list[float | int]] = []
        for step_index in range(scenario.steps):
            if step_index in events_by_step:
                reference.update_controls(events_by_step[step_index])
            samples.append(rounded_sample(reference.step()))

        generated_scenarios.append(
            {
                "name": scenario.name,
                "description": scenario.description,
                "steps": scenario.steps,
                "controls": scenario.controls,
                "events": scenario.events,
                "seed": scenario.seed,
                "initialisation": scenario.initialisation,
                "compatibility": {
                    "legacySynapse2DecayBug": scenario.legacy_synapse2_decay_bug
                },
                "samples": samples,
            }
        )

    return {
        "metadata": {
            "sourceCommit": SOURCE_COMMIT,
            "desktopGraphBlobSha": GRAPH_BLOB_SHA,
            "desktopPresetsBlobSha": PRESETS_BLOB_SHA,
            "timestepMs": TIMESTEP_MS,
            "absoluteTolerance": 1e-8,
            "randomAlgorithm": "xorshift32+box-muller",
            "sampleColumns": SAMPLE_COLUMNS,
            "scenarioCount": len(generated_scenarios),
        },
        "presets": [
            {
                "id": index + 1,
                "a": values[0],
                "b": values[1],
                "c": values[2],
                "d": values[3],
                "restingPotential": values[4],
            }
            for index, values in enumerate(presets)
        ],
        "scenarios": generated_scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when committed fixtures do not match the audited Python reference.",
    )
    args = parser.parse_args()

    fixtures = generate(load_presets())
    rendered = json.dumps(
        fixtures,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"

    if args.check:
        if not OUTPUT.exists():
            print("Missing golden fixtures: " + str(OUTPUT), file=sys.stderr)
            return 1
        if OUTPUT.read_text(encoding="utf-8") != rendered:
            print(
                "Golden fixtures are stale. Run npm run fixtures and review the changes.",
                file=sys.stderr,
            )
            return 1
        print(
            "Verified "
            + str(fixtures["metadata"]["scenarioCount"])
            + " deterministic desktop-reference scenarios."
        )
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(
        "Generated "
        + str(fixtures["metadata"]["scenarioCount"])
        + " scenarios at "
        + str(OUTPUT)
        + " ("
        + str(OUTPUT.stat().st_size)
        + " bytes)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
