// SPDX-License-Identifier: GPL-3.0-or-later

import { defaultControls, mergeControls } from "./controls.ts";
import { integrateNeuron, TIMESTEP_MS } from "./izhikevich.ts";
import { createPhotoreceptorState, stepPhotoreceptor } from "./photoreceptor.ts";
import { getPreset } from "./presets.ts";
import { DEFAULT_RANDOM_SEED, SeededRandomSource } from "./random.ts";
import { createStimulusState, stepStimulus } from "./stimulus.ts";
import type {
  CellControls,
  CellState,
  CompatibilityOptions,
  ControlsPatch,
  InitialisationMode,
  RandomSource,
  SimulationControls,
  SimulationOptions,
  SimulationSample,
  SimulationState,
  SynapseControls,
  SynapseState,
} from "./types.ts";

interface SynapseStepResult {
  readonly vm: number;
  readonly current: number;
}

function createCellState(
  controls: CellControls,
  initialisation: InitialisationMode,
): CellState {
  const preset = getPreset(controls.presetId);

  return {
    neuron: {
      v: initialisation === "desktop" ? -65 : preset.restingPotential,
      u: 0,
      totalCurrent: 0,
    },
    photoreceptor: createPhotoreceptorState(),
  };
}

function createSynapseState(
  controls: SynapseControls,
  initialisation: InitialisationMode,
): SynapseState {
  return {
    ...createCellState(controls, initialisation),
    current: 0,
  };
}

function createState(
  controls: SimulationControls,
  initialisation: InitialisationMode,
): SimulationState {
  return {
    stepIndex: 0,
    main: createCellState(controls.main, initialisation),
    synapse1: createSynapseState(controls.synapse1, initialisation),
    synapse2: createSynapseState(controls.synapse2, initialisation),
    stimulus: createStimulusState(),
  };
}

function gaussianCurrent(random: RandomSource, noiseLevel: number): number {
  // The desktop evaluates numpy.random.normal even when the scale is zero.
  // Preserve draw ordering so enabled auxiliary-neuron noise is reproducible.
  return random.nextGaussian() * (noiseLevel / 4);
}

function stepSynapse(
  state: SynapseState,
  controls: SynapseControls,
  stimulus: number,
  random: RandomSource,
  legacyDecayBug: boolean,
): SynapseStepResult {
  if (!controls.enabled) {
    // The desktop clears visible current but retains hidden neuronal state.
    state.current = 0;
    return { vm: 0, current: 0 };
  }

  const noise = gaussianCurrent(random, controls.noiseLevel);
  const integrated = integrateNeuron(state.neuron, getPreset(controls.presetId));
  state.neuron.v = integrated.v;
  state.neuron.u = integrated.u;

  const directCurrent = controls.directCurrentEnabled ? stimulus : 0;
  const photoreceptor = controls.lightEnabled
    ? stepPhotoreceptor(state.photoreceptor, stimulus, controls.photoreceptor)
    : 0;

  if (integrated.spiked) {
    state.current += controls.gain;
  }

  const decay = legacyDecayBug ? 0.995 : controls.decaySlider / 1000;
  state.current *= decay;

  state.neuron.totalCurrent =
    controls.patchCurrent + noise + directCurrent + photoreceptor;

  return { vm: integrated.v, current: state.current };
}

/**
 * Deterministic, browser-independent simulation API.
 *
 * Default initialisation honours the selected preset. The desktop mode exists
 * solely for source-pinned golden fixtures and reproduces its -65 mV start.
 */
export class SpikelingModel {
  private controls: SimulationControls;
  private state: SimulationState;
  private random: RandomSource;
  private seed: number;
  private readonly suppliedRandomSource: RandomSource | undefined;
  private initialisation: InitialisationMode;
  private readonly compatibility: CompatibilityOptions;

  constructor(options: SimulationOptions = {}) {
    this.controls = mergeControls(defaultControls(), options.controls);
    this.seed = options.seed ?? DEFAULT_RANDOM_SEED;
    this.suppliedRandomSource = options.randomSource;
    this.random = options.randomSource ?? new SeededRandomSource(this.seed);
    this.initialisation = options.initialisation ?? "preset";
    this.compatibility = options.compatibility ?? {};

    if (this.initialisation !== "preset" && this.initialisation !== "desktop") {
      throw new TypeError("initialisation must be preset or desktop.");
    }

    this.state = createState(this.controls, this.initialisation);
  }

  getControls(): SimulationControls {
    return structuredClone(this.controls);
  }

  getState(): SimulationState {
    return structuredClone(this.state);
  }

  updateControls(patch: ControlsPatch): void {
    const previousMode = this.controls.stimulus.mode;
    this.controls = mergeControls(this.controls, patch);

    if (
      patch.stimulus?.customSamples !== undefined ||
      (previousMode !== "custom" && this.controls.stimulus.mode === "custom")
    ) {
      this.state.stimulus.customResetPending = true;
    }
  }

  reset(options: { seed?: number; initialisation?: InitialisationMode } = {}): void {
    if (options.seed !== undefined && this.suppliedRandomSource !== undefined) {
      throw new TypeError("A supplied random source cannot be reset with a numeric seed.");
    }

    this.seed = options.seed ?? this.seed;
    this.initialisation = options.initialisation ?? this.initialisation;
    if (this.initialisation !== "preset" && this.initialisation !== "desktop") {
      throw new TypeError("initialisation must be preset or desktop.");
    }
    this.random = this.suppliedRandomSource ?? new SeededRandomSource(this.seed);
    this.state = createState(this.controls, this.initialisation);
  }

  step(): SimulationSample {
    const mainPreset = getPreset(this.controls.main.presetId);
    const integrated = integrateNeuron(this.state.main.neuron, mainPreset);
    this.state.main.neuron.v = integrated.v;
    this.state.main.neuron.u = integrated.u;

    const stimulus = stepStimulus(this.state.stimulus, this.controls.stimulus);
    const noise = gaussianCurrent(this.random, this.controls.main.noiseLevel);

    const photoreceptor = this.controls.main.lightEnabled
      ? stepPhotoreceptor(
          this.state.main.photoreceptor,
          stimulus.value,
          this.controls.main.photoreceptor,
        )
      : 0;

    const directCurrent = this.controls.main.directCurrentEnabled ? stimulus.value : 0;

    const synapse1 = stepSynapse(
      this.state.synapse1,
      this.controls.synapse1,
      stimulus.value,
      this.random,
      false,
    );
    const synapse2 = stepSynapse(
      this.state.synapse2,
      this.controls.synapse2,
      stimulus.value,
      this.random,
      this.compatibility.legacySynapse2DecayBug === true,
    );

    const totalCurrent =
      this.controls.main.patchCurrent +
      noise +
      photoreceptor +
      directCurrent +
      synapse1.current +
      synapse2.current;

    this.state.main.neuron.totalCurrent = totalCurrent;

    const sample: SimulationSample = {
      timeMs: this.state.stepIndex * TIMESTEP_MS,
      mainVm: integrated.v,
      mainRecovery: integrated.u,
      stimulus: stimulus.value,
      totalCurrent,
      synapse1Vm: synapse1.vm,
      synapse1Recovery: this.state.synapse1.neuron.u,
      synapse1Current: synapse1.current,
      synapse2Vm: synapse2.vm,
      synapse2Recovery: this.state.synapse2.neuron.u,
      synapse2Current: synapse2.current,
      trigger: stimulus.trigger,
    };

    this.state.stepIndex += 1;
    return sample;
  }

  run(steps: number): SimulationSample[] {
    if (!Number.isSafeInteger(steps) || steps < 0) {
      throw new RangeError("steps must be a non-negative safe integer.");
    }

    const samples: SimulationSample[] = [];
    for (let index = 0; index < steps; index += 1) {
      samples.push(this.step());
    }
    return samples;
  }
}
