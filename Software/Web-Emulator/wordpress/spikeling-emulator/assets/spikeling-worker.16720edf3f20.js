/*! SPDX-License-Identifier: GPL-3.0-or-later | Open Source Neuro Spikeling */
const __spkModules = {
"src/worker/emulator.worker.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                                     
const { createEmulatorWorkerRuntime } = __spkRequire("src/worker/emulator-runtime.ts");

                              
                   
                    
                                                                      
          
                                                                         
 

const scope = globalThis                                 ;
const runtime = createEmulatorWorkerRuntime({
  postMessage: (message, transfer) => scope.postMessage(message, transfer),
});

scope.addEventListener("message", (event) => {
  runtime.handleMessage(event.data);
});



},
"src/worker/emulator-runtime.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { SimulationEngine } = __spkRequire("src/simulation/clock.ts");
                                                                  
             
                      
                      
                                   
const { packSamples } = __spkRequire("src/simulation/ring-buffer.ts");

                                               
                         
                                 
                                      
            
                                           
 

                                        
                                                    
                  
 

/** Transport-independent worker core; the entry point only supplies its port. */
function createEmulatorWorkerRuntime(
  options                              ,
)                        {
  let engine                              ;

  function requireEngine()                   {
    if (engine === undefined) {
      throw new Error("Initialise the emulator worker before sending commands.");
    }
    return engine;
  }

  function reportError(error         )       {
    options.postMessage({
      type: "error",
      message: error instanceof Error ? error.message : String(error),
    });
  }

  return {
    handleMessage(message)       {
      try {
        switch (message.type) {
          case "initialise": {
            engine?.dispose();
            engine = new SimulationEngine({
              modelOptions: message.options,
              historyCapacity: message.historyCapacity,
              speedIndex: message.speedIndex,
              maxStepsPerSlice: message.maxStepsPerSlice,
              maxCatchUpTicks: message.maxCatchUpTicks,
              scheduler: options.scheduler,
              onSamples(samples) {
                const packed = packSamples(samples);
                const buffer = packed.buffer               ;
                options.postMessage(
                  {
                    type: "samples",
                    count: samples.length,
                    firstTimeMs: samples[0].timeMs,
                    lastTimeMs: samples[samples.length - 1].timeMs,
                    buffer,
                  },
                  [buffer],
                );
              },
              onState(snapshot) {
                options.postMessage({ type: "state", snapshot });
              },
              onError: reportError,
            });
            options.postMessage({ type: "ready", snapshot: engine.getSnapshot() });
            break;
          }

          case "start":
            requireEngine().start();
            break;
          case "pause":
            requireEngine().pause();
            break;
          case "stop":
            requireEngine().stop();
            break;
          case "reset":
            requireEngine().reset(message.options);
            break;
          case "set-speed":
            requireEngine().setSpeed(message.index);
            break;
          case "update-controls":
            requireEngine().updateControls(message.patch);
            break;
          case "snapshot":
            options.postMessage({
              type: "snapshot",
              snapshot: requireEngine().getSnapshot(),
            });
            break;
          case "dispose":
            requireEngine().dispose();
            engine = undefined;
            break;
          default:
            throw new TypeError("Unknown emulator-worker command.");
        }
      } catch (error) {
        reportError(error);
      }
    },

    dispose()       {
      engine?.dispose();
      engine = undefined;
    },
  };
}

__spkExports.createEmulatorWorkerRuntime = createEmulatorWorkerRuntime;

},
"src/simulation/clock.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { SpikelingModel } = __spkRequire("src/model/simulation.ts");
             
                
                     
                    
                   
                           
                                                                         
const { DEFAULT_HISTORY_CAPACITY, SampleRingBuffer } = __spkRequire("src/simulation/ring-buffer.ts");
const { DEFAULT_SPEED_INDEX, DESKTOP_UPDATE_INTERVAL_MS, getSimulationSpeed } = __spkRequire("src/simulation/speed.ts");

                                      
                
                                                             
                                      
 

                                          
                                  
                                            
                                    
                               
                                     
                                    
                                           
                                                                      
                                                        
                                            
 

const defaultScheduler                      = {
  now: () => performance.now(),
  setTimeout: (callback, delayMs) => setTimeout(callback, delayMs),
  clearTimeout: (handle) => clearTimeout(handle                                 ),
};

function positiveInteger(value        , label        )         {
  if (!Number.isSafeInteger(value) || value < 1) {
    throw new RangeError(label + " must be a positive safe integer.");
  }
  return value;
}

/**
 * Fixed-step model scheduler. Numerical time never depends on paint frequency;
 * large desktop-equivalent updates yield between bounded worker slices.
 */
class SimulationEngine {
           history                  ;
           model                ;
           maxStepsPerSlice        ;
           maxCatchUpTicks        ;

                   scheduler                     ;
                   onSamples                                                              ;
                   onState                                                  ;
                   onError                                      ;
          lifecycle                      = "idle";
          speedIndex        ;
          timeoutHandle         ;
          timeoutScheduled = false;
          nextTickAt = 0;
          pendingSteps = 0;
          droppedSteps = 0;

  constructor(options                          = {}) {
    if (options.model !== undefined && options.modelOptions !== undefined) {
      throw new TypeError("Supply either an existing model or model options, not both.");
    }

    this.model = options.model ?? new SpikelingModel(options.modelOptions);
    this.history = new SampleRingBuffer(
      options.historyCapacity ?? DEFAULT_HISTORY_CAPACITY,
    );
    this.speedIndex = options.speedIndex ?? DEFAULT_SPEED_INDEX;
    getSimulationSpeed(this.speedIndex);
    this.maxStepsPerSlice = positiveInteger(
      options.maxStepsPerSlice ?? 250,
      "Maximum steps per slice",
    );
    this.maxCatchUpTicks = positiveInteger(
      options.maxCatchUpTicks ?? 4,
      "Maximum catch-up ticks",
    );
    this.scheduler = options.scheduler ?? defaultScheduler;
    this.onSamples = options.onSamples;
    this.onState = options.onState;
    this.onError = options.onError;
  }

  getSnapshot()                 {
    return {
      lifecycle: this.lifecycle,
      speed: getSimulationSpeed(this.speedIndex),
      stepIndex: this.model.getState().stepIndex,
      retainedSamples: this.history.length,
      historyCapacity: this.history.capacity,
      historyBytes: this.history.allocatedBytes,
      pendingSteps: this.pendingSteps,
      droppedSteps: this.droppedSteps,
      controls: this.model.getControls(),
    };
  }

  start()       {
    if (this.lifecycle === "running") {
      return;
    }

    this.lifecycle = "running";
    this.nextTickAt = this.scheduler.now() + DESKTOP_UPDATE_INTERVAL_MS;
    this.publishState();
    this.schedule(DESKTOP_UPDATE_INTERVAL_MS);
  }

  pause()       {
    if (this.lifecycle !== "running") {
      return;
    }

    this.cancelScheduledWork();
    this.pendingSteps = 0;
    this.lifecycle = "paused";
    this.publishState();
  }

  stop()       {
    this.cancelScheduledWork();
    this.pendingSteps = 0;
    this.droppedSteps = 0;
    this.model.reset();
    this.history.clear();
    this.lifecycle = "stopped";
    this.publishState();
  }

  reset(
    options                                                                           = {},
  )       {
    const wasRunning = this.lifecycle === "running";
    this.cancelScheduledWork();
    this.pendingSteps = 0;
    this.droppedSteps = 0;
    this.model.reset(options);
    this.history.clear();
    this.lifecycle = wasRunning ? "running" : "idle";

    if (wasRunning) {
      this.nextTickAt = this.scheduler.now() + DESKTOP_UPDATE_INTERVAL_MS;
      this.schedule(DESKTOP_UPDATE_INTERVAL_MS);
    }

    this.publishState();
  }

  setSpeed(index        )       {
    getSimulationSpeed(index);
    this.speedIndex = index;
    this.publishState();
  }

  updateControls(patch               )       {
    this.model.updateControls(patch);
    this.publishState();
  }

  dispose()       {
    this.cancelScheduledWork();
    this.pendingSteps = 0;
    this.lifecycle = "stopped";
  }

          publishState()       {
    this.onState?.(this.getSnapshot());
  }

          cancelScheduledWork()       {
    if (this.timeoutScheduled) {
      this.scheduler.clearTimeout(this.timeoutHandle);
      this.timeoutScheduled = false;
      this.timeoutHandle = undefined;
    }
  }

          schedule(delayMs        )       {
    this.cancelScheduledWork();
    this.timeoutScheduled = true;
    this.timeoutHandle = this.scheduler.setTimeout(() => {
      this.timeoutScheduled = false;
      this.timeoutHandle = undefined;
      this.runSlice();
    }, Math.max(0, delayMs));
  }

          runSlice()       {
    if (this.lifecycle !== "running") {
      return;
    }

    try {
      const now = this.scheduler.now();
      if (now >= this.nextTickAt) {
        const elapsedTicks =
          Math.floor((now - this.nextTickAt) / DESKTOP_UPDATE_INTERVAL_MS) + 1;
        const retainedTicks = Math.min(elapsedTicks, this.maxCatchUpTicks);
        const stepsPerUpdate = getSimulationSpeed(this.speedIndex).stepsPerUpdate;
        this.pendingSteps += retainedTicks * stepsPerUpdate;
        this.droppedSteps += (elapsedTicks - retainedTicks) * stepsPerUpdate;
        this.nextTickAt += elapsedTicks * DESKTOP_UPDATE_INTERVAL_MS;
      }

      const sliceLength = Math.min(this.pendingSteps, this.maxStepsPerSlice);
      if (sliceLength > 0) {
        const samples                     = [];
        for (let index = 0; index < sliceLength; index += 1) {
          const sample = this.model.step();
          this.history.push(sample);
          samples.push(sample);
        }
        this.pendingSteps -= sliceLength;
        this.onSamples?.(samples);
      }

      if (this.lifecycle === "running") {
        const delay =
          this.pendingSteps > 0 ? 0 : this.nextTickAt - this.scheduler.now();
        this.schedule(delay);
      }
    } catch (caught) {
      this.cancelScheduledWork();
      this.pendingSteps = 0;
      this.lifecycle = "paused";
      this.publishState();
      const error = caught instanceof Error ? caught : new Error(String(caught));
      this.onError?.(error);
    }
  }
}

__spkExports.SimulationEngine = SimulationEngine;

},
"src/model/simulation.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { defaultControls, mergeControls } = __spkRequire("src/model/controls.ts");
const { integrateNeuron, TIMESTEP_MS } = __spkRequire("src/model/izhikevich.ts");
const { createPhotoreceptorState, stepPhotoreceptor } = __spkRequire("src/model/photoreceptor.ts");
const { getPreset } = __spkRequire("src/model/presets.ts");
const { DEFAULT_RANDOM_SEED, SeededRandomSource } = __spkRequire("src/model/random.ts");
const { createStimulusState, stepStimulus } = __spkRequire("src/model/stimulus.ts");
             
               
            
                       
                
                     
               
                     
                    
                   
                  
                  
               
                    

                             
                      
                           
 

function createCellState(
  controls              ,
  initialisation                    ,
)            {
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
  controls                 ,
  initialisation                    ,
)               {
  return {
    ...createCellState(controls, initialisation),
    current: 0,
  };
}

function createState(
  controls                    ,
  initialisation                    ,
)                  {
  return {
    stepIndex: 0,
    main: createCellState(controls.main, initialisation),
    synapse1: createSynapseState(controls.synapse1, initialisation),
    synapse2: createSynapseState(controls.synapse2, initialisation),
    stimulus: createStimulusState(),
  };
}

function gaussianCurrent(random              , noiseLevel        )         {
  // The desktop evaluates numpy.random.normal even when the scale is zero.
  // Preserve draw ordering so enabled auxiliary-neuron noise is reproducible.
  return random.nextGaussian() * (noiseLevel / 4);
}

function stepSynapse(
  state              ,
  controls                 ,
  stimulus        ,
  random              ,
  legacyDecayBug         ,
)                    {
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
class SpikelingModel {
          controls                    ;
          state                 ;
          random              ;
          seed        ;
                   suppliedRandomSource                          ;
          initialisation                    ;
                   compatibility                      ;

  constructor(options                    = {}) {
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

  getControls()                     {
    return structuredClone(this.controls);
  }

  getState()                  {
    return structuredClone(this.state);
  }

  updateControls(patch               )       {
    const previousMode = this.controls.stimulus.mode;
    this.controls = mergeControls(this.controls, patch);

    if (
      patch.stimulus?.customSamples !== undefined ||
      (previousMode !== "custom" && this.controls.stimulus.mode === "custom")
    ) {
      this.state.stimulus.customResetPending = true;
    }
  }

  reset(options                                                         = {})       {
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

  step()                   {
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

    const sample                   = {
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

  run(steps        )                     {
    if (!Number.isSafeInteger(steps) || steps < 0) {
      throw new RangeError("steps must be a non-negative safe integer.");
    }

    const samples                     = [];
    for (let index = 0; index < steps; index += 1) {
      samples.push(this.step());
    }
    return samples;
  }
}

__spkExports.SpikelingModel = SpikelingModel;

},
"src/model/controls.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { getPreset } = __spkRequire("src/model/presets.ts");
             
               
            
                
                        
                     
                  
               
                    

function defaultPhotoreceptor()                        {
  return { gain: 0, decaySlider: 100, recoverySlider: 25 };
}

function defaultCell()               {
  return {
    presetId: 1,
    patchCurrent: 0,
    noiseLevel: 0,
    directCurrentEnabled: false,
    lightEnabled: false,
    photoreceptor: defaultPhotoreceptor(),
  };
}

function defaultSynapse(decaySlider        )                  {
  return {
    ...defaultCell(),
    enabled: false,
    gain: 0,
    decaySlider,
  };
}

function defaultControls()                     {
  return {
    main: defaultCell(),
    synapse1: defaultSynapse(995),
    synapse2: defaultSynapse(990),
    stimulus: {
      mode: "internal",
      strength: 0,
      frequencySlider: 0,
      customSamples: [],
    },
  };
}

function mergeCell(base              , patch            = {})               {
  return {
    ...base,
    ...patch,
    photoreceptor: {
      ...base.photoreceptor,
      ...patch.photoreceptor,
    },
  };
}

function mergeSynapse(
  base                 ,
  patch               = {},
)                  {
  return {
    ...base,
    ...patch,
    photoreceptor: {
      ...base.photoreceptor,
      ...patch.photoreceptor,
    },
  };
}

function integerInRange(
  name        ,
  value        ,
  minimum        ,
  maximum        ,
)       {
  if (!Number.isInteger(value) || value < minimum || value > maximum) {
    throw new RangeError(
      name + " must be an integer from " + minimum + " to " + maximum + ".",
    );
  }
}

function validatePhotoreceptor(
  name        ,
  controls                       ,
)       {
  integerInRange(name + ".gain", controls.gain, -100, 100);
  integerInRange(name + ".decaySlider", controls.decaySlider, 10, 125);
  integerInRange(name + ".recoverySlider", controls.recoverySlider, 1, 100);
}

function validateCell(
  name        ,
  controls              ,
  minimumPatch        ,
  maximumPatch        ,
)       {
  getPreset(controls.presetId);
  integerInRange(name + ".patchCurrent", controls.patchCurrent, minimumPatch, maximumPatch);
  integerInRange(name + ".noiseLevel", controls.noiseLevel, 0, 100);
  validatePhotoreceptor(name + ".photoreceptor", controls.photoreceptor);
}

function validateSynapse(name        , controls                 )       {
  // Correct the desktop UI defect: its labels promise -50..50, but Qt exposed
  // 0..100. The browser model accepts the intended signed range.
  validateCell(name, controls, -50, 50);
  integerInRange(name + ".gain", controls.gain, -100, 100);
  integerInRange(name + ".decaySlider", controls.decaySlider, 975, 1000);
}

function mergeControls(
  base                    ,
  patch                = {},
)                     {
  const result                     = {
    main: mergeCell(base.main, patch.main),
    synapse1: mergeSynapse(base.synapse1, patch.synapse1),
    synapse2: mergeSynapse(base.synapse2, patch.synapse2),
    stimulus: {
      ...base.stimulus,
      ...patch.stimulus,
      customSamples: [
        ...(patch.stimulus?.customSamples ?? base.stimulus.customSamples),
      ],
    },
  };

  validateCell("main", result.main, -100, 100);
  validateSynapse("synapse1", result.synapse1);
  validateSynapse("synapse2", result.synapse2);
  integerInRange("stimulus.strength", result.stimulus.strength, -100, 100);
  integerInRange(
    "stimulus.frequencySlider",
    result.stimulus.frequencySlider,
    -100,
    100,
  );

  if (result.stimulus.mode !== "internal" && result.stimulus.mode !== "custom") {
    throw new TypeError("stimulus.mode must be internal or custom.");
  }
  if (result.stimulus.customSamples.some((value) => !Number.isFinite(value))) {
    throw new TypeError("Custom stimulus samples must all be finite numbers.");
  }
  if (result.stimulus.mode === "custom" && result.stimulus.customSamples.length === 0) {
    throw new RangeError("A custom stimulus must contain at least one sample.");
  }

  return result;
}

__spkExports.defaultControls = defaultControls;
__spkExports.mergeControls = mergeControls;

},
"src/model/presets.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                               

function preset(
  id        ,
  key        ,
  label        ,
  a        ,
  b        ,
  c        ,
  d        ,
  restingPotential        ,
)               {
  return Object.freeze({ id, key, label, a, b, c, d, restingPotential });
}

const NEURON_PRESETS                          = Object.freeze([
  preset(1, "tonic-spiking", "Tonic Spiking", 0.02, 0.2, -65, 6, -70),
  preset(2, "phasic-spiking", "Phasic Spiking", 0.02, 0.25, -65, 6, -64),
  preset(3, "tonic-bursting", "Tonic Bursting", 0.02, 0.2, -50, 2, -70),
  preset(4, "phasic-bursting", "Phasic Bursting", 0.02, 0.25, -55, 0.05, -64),
  preset(5, "mixed-mode", "Mixed Mode", 0.02, 0.2, -55, 4, -70),
  preset(
    6,
    "spike-frequency-adaptation",
    "Spike Frequency Adaptation",
    0.01,
    0.22,
    -65,
    8,
    -70,
  ),
  preset(7, "class-1-excitability", "Class 1 Excitability", 0.02, -0.1, -55, 6, -60),
  preset(8, "class-2-excitability", "Class 2 Excitability", 0.2, 0.26, -65, 0, -64),
  preset(9, "spike-latency", "Spike Latency", 0.02, 0.2, -65, 6, -70),
  preset(
    10,
    "sub-threshold-oscillations",
    "Sub-threshold Oscillations",
    0.05,
    0.26,
    -60,
    0,
    -62,
  ),
  preset(11, "resonator", "Resonator", 0.1, 0.26, -60, -1, -62),
  preset(12, "integrator", "Integrator", 0.02, -0.1, -55, 6, -60),
  preset(13, "rebound-spike", "Rebound Spike", 0.03, 0.25, -60, 4, -64),
  preset(14, "rebound-burst", "Rebound Burst", 0.03, 0.25, -52, 0, -64),
  preset(
    15,
    "threshold-variability",
    "Threshold Variability",
    0.03,
    0.25,
    -60,
    4,
    -64,
  ),
  preset(16, "bistability", "Bistability", 0.1, 0.26, -60, 0, -61),
  preset(
    17,
    "depolarizing-after-potential",
    "Depolarizing after potential",
    1,
    0.2,
    -60,
    -21,
    -70,
  ),
  preset(18, "accommodation", "Accommodation", 0.02, 1, -55, 4, -65),
  preset(
    19,
    "inhibition-induced-spiking",
    "Inhibition Induced Spiking",
    0.02,
    1,
    -60,
    8,
    -63.8,
  ),
  preset(
    20,
    "inhibition-induced-bursting",
    "Inhibition Induced Bursting",
    0.026,
    -1,
    -45,
    -2,
    -63.8,
  ),
]);

function getPreset(identifier                 )               {
  const found =
    typeof identifier === "number"
      ? NEURON_PRESETS.find((entry) => entry.id === identifier)
      : NEURON_PRESETS.find(
          (entry) => entry.key === identifier || entry.label === identifier,
        );

  if (found === undefined) {
    throw new RangeError("Unknown Spikeling neuron preset: " + String(identifier));
  }

  return found;
}

__spkExports.NEURON_PRESETS = NEURON_PRESETS;
__spkExports.getPreset = getPreset;

},
"src/model/izhikevich.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                                               

const TIMESTEP_MS = 0.1;
const RESET_THRESHOLD_MV = 30;
const DISPLAY_PEAK_MV = 30;
const MINIMUM_POTENTIAL_MV = -110;

/**
 * Match Graph_Emulator.py exactly: update v first, use that v for u, reset
 * before the display-peak rule, and clamp the lower membrane potential.
 */
function integrateNeuron(
  state             ,
  preset              ,
)                    {
  let v =
    state.v +
    TIMESTEP_MS *
      (0.04 * state.v * state.v +
        5 * state.v +
        140 -
        state.u +
        state.totalCurrent);

  let u = state.u + TIMESTEP_MS * (preset.a * (preset.b * v - state.u));

  if (v >= RESET_THRESHOLD_MV) {
    v = preset.c;
    u += preset.d;
  }

  if (v < MINIMUM_POTENTIAL_MV) {
    v = MINIMUM_POTENTIAL_MV;
  }

  let spiked = false;
  if (v >= 0) {
    v = DISPLAY_PEAK_MV;
    spiked = true;
  }

  return { v, u, spiked };
}

__spkExports.TIMESTEP_MS = TIMESTEP_MS;
__spkExports.RESET_THRESHOLD_MV = RESET_THRESHOLD_MV;
__spkExports.DISPLAY_PEAK_MV = DISPLAY_PEAK_MV;
__spkExports.MINIMUM_POTENTIAL_MV = MINIMUM_POTENTIAL_MV;
__spkExports.integrateNeuron = integrateNeuron;

},
"src/model/photoreceptor.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                                            

function createPhotoreceptorState()                     {
  return {
    recovery: 1,
    decay: 0.001,
    recoveryRate: 0.025,
  };
}

/**
 * Preserve the desktop ordering: use the previous decay/recovery coefficients
 * for this sample, then refresh those coefficients from the current controls.
 */
function stepPhotoreceptor(
  state                    ,
  stimulus        ,
  controls                       ,
)         {
  const polarity = controls.gain >= 0 ? 1 : -1;
  const current = (stimulus / 25) * (controls.gain / 0.5) * state.recovery;

  if (state.recovery > 0) {
    state.recovery -= polarity * state.decay * current;
  }
  if (state.recovery < 0) {
    state.recovery = 0;
  }
  if (state.recovery < 1) {
    state.recovery += state.recoveryRate;
  }

  state.decay = controls.decaySlider / 100000;
  state.recoveryRate = controls.recoverySlider / 1000;

  return current;
}

__spkExports.createPhotoreceptorState = createPhotoreceptorState;
__spkExports.stepPhotoreceptor = stepPhotoreceptor;

},
"src/model/random.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                               

const DEFAULT_RANDOM_SEED = 0x5350494b;

/**
 * Portable xorshift32 + Box-Muller generator.
 *
 * The reference Python generator implements the same unsigned operations so
 * stochastic fixtures can be reproduced without depending on NumPy internals.
 */
class SeededRandomSource                         {
          state        ;
          spare                    ;

  constructor(seed         = DEFAULT_RANDOM_SEED) {
    if (!Number.isInteger(seed) || seed < 1 || seed > 0xffffffff) {
      throw new RangeError("A random seed must be an integer from 1 to 4294967295.");
    }

    this.state = seed >>> 0;
    this.spare = undefined;
  }

  nextGaussian()         {
    if (this.spare !== undefined) {
      const value = this.spare;
      this.spare = undefined;
      return value;
    }

    const u1 = this.nextUniform();
    const u2 = this.nextUniform();
    const radius = Math.sqrt(-2 * Math.log(u1));
    const angle = 2 * Math.PI * u2;

    this.spare = radius * Math.sin(angle);
    return radius * Math.cos(angle);
  }

          nextUniform()         {
    let value = this.state;
    value ^= value << 13;
    value ^= value >>> 17;
    value ^= value << 5;
    this.state = value >>> 0;

    // Keep both endpoints open so Box-Muller never takes log(0).
    return (this.state + 1) / 4294967297;
  }
}

class SequenceRandomSource                         {
                   values                   ;
          position = 0;

  constructor(values                   ) {
    if (values.length === 0 || values.some((value) => !Number.isFinite(value))) {
      throw new TypeError("A Gaussian sequence must contain finite numeric values.");
    }
    this.values = [...values];
  }

  nextGaussian()         {
    const value = this.values[this.position % this.values.length];
    this.position += 1;
    return value;
  }
}

__spkExports.DEFAULT_RANDOM_SEED = DEFAULT_RANDOM_SEED;
__spkExports.SeededRandomSource = SeededRandomSource;
__spkExports.SequenceRandomSource = SequenceRandomSource;

},
"src/model/stimulus.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                                                  

const INITIAL_STIMULUS_PERIOD_STEPS = 1000;
const STIMULUS_DUTY_CYCLE_STEPS = 500;
const MINIMUM_STIMULUS_PERIOD_OFFSET = 10;

function createStimulusState()                {
  return {
    counter: 0,
    steps: INITIAL_STIMULUS_PERIOD_STEPS,
    triggerPending: false,
    customIndex: 0,
    customResetPending: true,
  };
}

function stepStimulus(
  state               ,
  controls                  ,
)                 {
  if (controls.mode === "custom" && controls.customSamples.length > 0) {
    let trigger        = 0;

    if (state.customResetPending) {
      state.customIndex = 0;
      state.customResetPending = false;
      trigger = 1;
    }

    if (state.customIndex >= controls.customSamples.length) {
      state.customIndex = 0;
      trigger = 1;
    }

    const value = controls.customSamples[state.customIndex];
    state.customIndex += 1;
    return { value, trigger };
  }

  const trigger        = state.triggerPending ? 1 : 0;
  state.triggerPending = false;

  const halfPeriod = Math.floor(state.steps / 2);
  const value = state.counter < halfPeriod ? controls.strength : 0;

  state.counter += 1;
  if (state.counter >= state.steps) {
    state.counter = 0;
    state.triggerPending = true;

    const frequency = Math.max(
      -100,
      Math.min(100, Math.trunc(-controls.frequencySlider)),
    );

    state.steps = Math.max(
      1,
      Math.trunc(
        STIMULUS_DUTY_CYCLE_STEPS +
          (frequency * STIMULUS_DUTY_CYCLE_STEPS) / 100 +
          MINIMUM_STIMULUS_PERIOD_OFFSET,
      ),
    );
  }

  return { value, trigger };
}

__spkExports.INITIAL_STIMULUS_PERIOD_STEPS = INITIAL_STIMULUS_PERIOD_STEPS;
__spkExports.STIMULUS_DUTY_CYCLE_STEPS = STIMULUS_DUTY_CYCLE_STEPS;
__spkExports.MINIMUM_STIMULUS_PERIOD_OFFSET = MINIMUM_STIMULUS_PERIOD_OFFSET;
__spkExports.createStimulusState = createStimulusState;
__spkExports.stepStimulus = stepStimulus;

},
"src/simulation/ring-buffer.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                          

const DEFAULT_HISTORY_CAPACITY = 50_000;
const DEFAULT_VISIBLE_SAMPLES = 5_000;

/** Stable row order for transferable, full-precision worker batches. */
const SAMPLE_COLUMNS = [
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
]                                                         ;

const SAMPLE_WIDTH = SAMPLE_COLUMNS.length;

function packSamples(samples                             )               {
  const packed = new Float64Array(samples.length * SAMPLE_WIDTH);

  for (let row = 0; row < samples.length; row += 1) {
    const sample = samples[row];
    for (let column = 0; column < SAMPLE_WIDTH; column += 1) {
      packed[row * SAMPLE_WIDTH + column] = sample[SAMPLE_COLUMNS[column]];
    }
  }

  return packed;
}

function unpackSamples(packed              )                     {
  if (packed.length % SAMPLE_WIDTH !== 0) {
    throw new RangeError("A packed sample batch must contain complete sample rows.");
  }

  const samples                     = [];
  for (let offset = 0; offset < packed.length; offset += SAMPLE_WIDTH) {
    const trigger = packed[offset + 11];
    if (trigger !== 0 && trigger !== 1) {
      throw new RangeError("A packed sample trigger must be zero or one.");
    }

    samples.push({
      timeMs: packed[offset],
      mainVm: packed[offset + 1],
      mainRecovery: packed[offset + 2],
      stimulus: packed[offset + 3],
      totalCurrent: packed[offset + 4],
      synapse1Vm: packed[offset + 5],
      synapse1Recovery: packed[offset + 6],
      synapse1Current: packed[offset + 7],
      synapse2Vm: packed[offset + 8],
      synapse2Recovery: packed[offset + 9],
      synapse2Current: packed[offset + 10],
      trigger,
    });
  }

  return samples;
}

/**
 * Preallocated, column-oriented Float64 history. No scientific value is
 * downsampled, rounded to Float32 or retained in an ever-growing array.
 */
class SampleRingBuffer {
           capacity        ;

                   columns                ;
          writeIndex = 0;
          sampleCount = 0;
          writtenCount = 0;

  constructor(capacity = DEFAULT_HISTORY_CAPACITY) {
    if (!Number.isSafeInteger(capacity) || capacity < 1) {
      throw new RangeError("History capacity must be a positive safe integer.");
    }

    this.capacity = capacity;
    this.columns = SAMPLE_COLUMNS.map(() => new Float64Array(capacity));
  }

  get length()         {
    return this.sampleCount;
  }

  get totalWritten()         {
    return this.writtenCount;
  }

  get allocatedBytes()         {
    return this.capacity * SAMPLE_WIDTH * Float64Array.BYTES_PER_ELEMENT;
  }

  push(sample                  )       {
    for (let column = 0; column < SAMPLE_WIDTH; column += 1) {
      this.columns[column][this.writeIndex] = sample[SAMPLE_COLUMNS[column]];
    }

    this.writeIndex = (this.writeIndex + 1) % this.capacity;
    this.sampleCount = Math.min(this.sampleCount + 1, this.capacity);
    this.writtenCount += 1;
  }

  pushBatch(samples                             )       {
    for (const sample of samples) {
      this.push(sample);
    }
  }

  at(index        )                               {
    if (!Number.isInteger(index)) {
      throw new RangeError("A history index must be an integer.");
    }

    const normalised = index < 0 ? this.sampleCount + index : index;
    if (normalised < 0 || normalised >= this.sampleCount) {
      return undefined;
    }

    const oldest =
      (this.writeIndex - this.sampleCount + this.capacity) % this.capacity;
    const physical = (oldest + normalised) % this.capacity;

    return {
      timeMs: this.columns[0][physical],
      mainVm: this.columns[1][physical],
      mainRecovery: this.columns[2][physical],
      stimulus: this.columns[3][physical],
      totalCurrent: this.columns[4][physical],
      synapse1Vm: this.columns[5][physical],
      synapse1Recovery: this.columns[6][physical],
      synapse1Current: this.columns[7][physical],
      synapse2Vm: this.columns[8][physical],
      synapse2Recovery: this.columns[9][physical],
      synapse2Current: this.columns[10][physical],
      trigger: this.columns[11][physical]         ,
    };
  }

  latest(count = this.sampleCount)                     {
    if (!Number.isSafeInteger(count) || count < 0) {
      throw new RangeError("Requested history length must be a non-negative integer.");
    }

    const retained = Math.min(count, this.sampleCount);
    const samples                     = [];
    for (let index = this.sampleCount - retained; index < this.sampleCount; index += 1) {
      samples.push(this.at(index) );
    }
    return samples;
  }

  clear()       {
    this.writeIndex = 0;
    this.sampleCount = 0;
    this.writtenCount = 0;
  }
}

__spkExports.DEFAULT_HISTORY_CAPACITY = DEFAULT_HISTORY_CAPACITY;
__spkExports.DEFAULT_VISIBLE_SAMPLES = DEFAULT_VISIBLE_SAMPLES;
__spkExports.SAMPLE_COLUMNS = SAMPLE_COLUMNS;
__spkExports.SAMPLE_WIDTH = SAMPLE_WIDTH;
__spkExports.packSamples = packSamples;
__spkExports.unpackSamples = unpackSamples;
__spkExports.SampleRingBuffer = SampleRingBuffer;

},
"src/simulation/speed.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { TIMESTEP_MS } = __spkRequire("src/model/izhikevich.ts");

/** The existing desktop emulator advances its model every 50 wall-clock ms. */
const DESKTOP_UPDATE_INTERVAL_MS = 50;

/** Source-audited model-step counts for the desktop's ten speed positions. */
const DESKTOP_STEPS_PER_UPDATE = [
  10, 20, 50, 100, 200, 500, 1_000, 2_000, 5_000, 10_000,
]         ;

const DEFAULT_SPEED_INDEX = 2;

                                  
                         
                                  
                                  
                                                  
                                      
                                          
 

/**
 * The desktop's x0.001..x1 label is not a wall-clock multiplier. Preserve the
 * historical label separately and expose the scientifically correct ratio.
 */
function getSimulationSpeed(index        )                  {
  if (
    !Number.isInteger(index) ||
    index < 0 ||
    index >= DESKTOP_STEPS_PER_UPDATE.length
  ) {
    throw new RangeError("Simulation speed must be an integer between 0 and 9.");
  }

  const stepsPerUpdate = DESKTOP_STEPS_PER_UPDATE[index];
  const simulatedMillisecondsPerUpdate = stepsPerUpdate * TIMESTEP_MS;

  return {
    index,
    stepsPerUpdate,
    stepsPerSecond: stepsPerUpdate * (1_000 / DESKTOP_UPDATE_INTERVAL_MS),
    simulatedMillisecondsPerUpdate,
    realtimeMultiplier:
      simulatedMillisecondsPerUpdate / DESKTOP_UPDATE_INTERVAL_MS,
    desktopLabelMultiplier: stepsPerUpdate / 10_000,
  };
}

__spkExports.DESKTOP_UPDATE_INTERVAL_MS = DESKTOP_UPDATE_INTERVAL_MS;
__spkExports.DESKTOP_STEPS_PER_UPDATE = DESKTOP_STEPS_PER_UPDATE;
__spkExports.DEFAULT_SPEED_INDEX = DEFAULT_SPEED_INDEX;
__spkExports.getSimulationSpeed = getSimulationSpeed;

}
};
const __spkCache = Object.create(null);
function __spkRequire(id) {
  if (__spkCache[id] !== undefined) return __spkCache[id];
  if (__spkModules[id] === undefined) throw new Error('Missing Spikeling production module: ' + id);
  const exports = Object.create(null);
  __spkCache[id] = exports;
  __spkModules[id](exports, __spkRequire);
  return exports;
}
__spkRequire("src/worker/emulator.worker.ts");
