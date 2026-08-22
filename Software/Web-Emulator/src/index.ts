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
export { EmulatorSource } from "./data-source/EmulatorSource.ts";
export type {
  DataSource,
  ErrorListener,
  SampleListener,
  StateListener,
  Unsubscribe,
} from "./data-source/DataSource.ts";
export type {
  EmulatorSourceOptions,
  EmulatorSourceWorker,
} from "./data-source/EmulatorSource.ts";
export { SimulationEngine } from "./simulation/clock.ts";
export type {
  SimulationEngineOptions,
  SimulationScheduler,
} from "./simulation/clock.ts";
export type {
  EngineSnapshot,
  MainToWorkerMessage,
  SimulationLifecycle,
  TransferableSimulationOptions,
  WorkerToMainMessage,
} from "./simulation/protocol.ts";
export {
  DEFAULT_HISTORY_CAPACITY,
  DEFAULT_VISIBLE_SAMPLES,
  SAMPLE_COLUMNS,
  SAMPLE_WIDTH,
  SampleRingBuffer,
  packSamples,
  unpackSamples,
} from "./simulation/ring-buffer.ts";
export {
  DEFAULT_SPEED_INDEX,
  DESKTOP_STEPS_PER_UPDATE,
  DESKTOP_UPDATE_INTERVAL_MS,
  getSimulationSpeed,
} from "./simulation/speed.ts";
export type { SimulationSpeed } from "./simulation/speed.ts";
export { createEmulatorWorkerRuntime } from "./worker/emulator-runtime.ts";
export type {
  EmulatorWorkerRuntime,
  EmulatorWorkerRuntimeOptions,
} from "./worker/emulator-runtime.ts";
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
