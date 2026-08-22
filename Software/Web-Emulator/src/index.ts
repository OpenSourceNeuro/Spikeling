// SPDX-License-Identifier: GPL-3.0-or-later

export { defaultControls, mergeControls } from "./model/controls.ts";
export {
  DISPLAY_PEAK_MV,
  MINIMUM_POTENTIAL_MV,
  RESET_THRESHOLD_MV,
  TIMESTEP_MS,
  integrateNeuron,
} from "./model/izhikevich.ts";
export { createPhotoreceptorState, stepPhotoreceptor } from "./model/photoreceptor.ts";
export { NEURON_PRESETS, getPreset } from "./model/presets.ts";
export {
  DEFAULT_RANDOM_SEED,
  SeededRandomSource,
  SequenceRandomSource,
} from "./model/random.ts";
export { SpikelingModel } from "./model/simulation.ts";
export {
  INITIAL_STIMULUS_PERIOD_STEPS,
  MINIMUM_STIMULUS_PERIOD_OFFSET,
  STIMULUS_DUTY_CYCLE_STEPS,
  createStimulusState,
  stepStimulus,
} from "./model/stimulus.ts";
export type {
  CellControls,
  CellPatch,
  CellState,
  CompatibilityOptions,
  ControlsPatch,
  InitialisationMode,
  IntegrationResult,
  NeuronPreset,
  NeuronState,
  PhotoreceptorControls,
  PhotoreceptorPatch,
  PhotoreceptorState,
  RandomSource,
  SimulationControls,
  SimulationOptions,
  SimulationSample,
  SimulationState,
  StimulusControls,
  StimulusResult,
  StimulusState,
  SynapseControls,
  SynapsePatch,
  SynapseState,
} from "./model/types.ts";
