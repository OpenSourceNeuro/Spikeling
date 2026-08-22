// SPDX-License-Identifier: GPL-3.0-or-later

export interface NeuronPreset {
  readonly id: number;
  readonly key: string;
  readonly label: string;
  readonly a: number;
  readonly b: number;
  readonly c: number;
  readonly d: number;
  readonly restingPotential: number;
}

export interface PhotoreceptorControls {
  readonly gain: number;
  readonly decaySlider: number;
  readonly recoverySlider: number;
}

export interface CellControls {
  readonly presetId: number;
  readonly patchCurrent: number;
  readonly noiseLevel: number;
  readonly directCurrentEnabled: boolean;
  readonly lightEnabled: boolean;
  readonly photoreceptor: PhotoreceptorControls;
}

export interface SynapseControls extends CellControls {
  readonly enabled: boolean;
  readonly gain: number;
  readonly decaySlider: number;
}

export interface StimulusControls {
  readonly mode: "internal" | "custom";
  readonly strength: number;
  readonly frequencySlider: number;
  readonly customSamples: readonly number[];
}

export interface SimulationControls {
  readonly main: CellControls;
  readonly synapse1: SynapseControls;
  readonly synapse2: SynapseControls;
  readonly stimulus: StimulusControls;
}

export type PhotoreceptorPatch = Partial<PhotoreceptorControls>;

export type CellPatch = Partial<Omit<CellControls, "photoreceptor">> & {
  readonly photoreceptor?: PhotoreceptorPatch;
};

export type SynapsePatch = Partial<Omit<SynapseControls, "photoreceptor">> & {
  readonly photoreceptor?: PhotoreceptorPatch;
};

export interface ControlsPatch {
  readonly main?: CellPatch;
  readonly synapse1?: SynapsePatch;
  readonly synapse2?: SynapsePatch;
  readonly stimulus?: Partial<StimulusControls>;
}

export interface NeuronState {
  v: number;
  u: number;
  totalCurrent: number;
}

export interface PhotoreceptorState {
  recovery: number;
  decay: number;
  recoveryRate: number;
}

export interface CellState {
  neuron: NeuronState;
  photoreceptor: PhotoreceptorState;
}

export interface SynapseState extends CellState {
  current: number;
}

export interface StimulusState {
  counter: number;
  steps: number;
  triggerPending: boolean;
  customIndex: number;
  customResetPending: boolean;
}

export interface SimulationState {
  stepIndex: number;
  main: CellState;
  synapse1: SynapseState;
  synapse2: SynapseState;
  stimulus: StimulusState;
}

export interface SimulationSample {
  readonly timeMs: number;
  readonly mainVm: number;
  readonly mainRecovery: number;
  readonly stimulus: number;
  readonly totalCurrent: number;
  readonly synapse1Vm: number;
  readonly synapse1Recovery: number;
  readonly synapse1Current: number;
  readonly synapse2Vm: number;
  readonly synapse2Recovery: number;
  readonly synapse2Current: number;
  readonly trigger: 0 | 1;
}

export interface RandomSource {
  nextGaussian(): number;
}

export type InitialisationMode = "preset" | "desktop";

export interface CompatibilityOptions {
  readonly legacySynapse2DecayBug?: boolean;
}

export interface SimulationOptions {
  readonly controls?: ControlsPatch;
  readonly seed?: number;
  readonly randomSource?: RandomSource;
  readonly initialisation?: InitialisationMode;
  readonly compatibility?: CompatibilityOptions;
}

export interface IntegrationResult {
  readonly v: number;
  readonly u: number;
  readonly spiked: boolean;
}

export interface StimulusResult {
  readonly value: number;
  readonly trigger: 0 | 1;
}
