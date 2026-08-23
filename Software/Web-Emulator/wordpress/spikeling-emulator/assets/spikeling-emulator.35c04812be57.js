/*! SPDX-License-Identifier: GPL-3.0-or-later | Open Source Neuro Spikeling */
const __spkModules = {
"src/integration/wordpress-entry.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { initialiseWordPressEmulators } = __spkRequire("src/integration/wordpress.ts");

/** This module is enqueued only on WordPress pages containing the shortcode. */
if (typeof document !== "undefined") {
  initialiseWordPressEmulators(document);
}



},
"src/integration/wordpress.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                               
const { EmulatorSource } = __spkRequire("src/data-source/EmulatorSource.ts");
const { SpikelingEmulator } = __spkRequire("src/interface/emulator.ts");
                                                                         
const { DEFAULT_RECORDING_MAX_SAMPLES } = __spkRequire("src/recording/csv.ts");
const { DEFAULT_SPEED_INDEX, DESKTOP_STEPS_PER_UPDATE } = __spkRequire("src/simulation/speed.ts");

const WORDPRESS_EMULATOR_SELECTOR = "[data-spikeling-emulator]";
const DEFAULT_WORDPRESS_SEED = 123_456;
const MAX_WORDPRESS_RECORDING_SAMPLES = 1_000_000;

                                         
                              
                        
                              
 

                                           
                             
                              
                                       
                                                 
                           
 

                                    
                                                             
                     
 

                                              
                                                                                 
                                                       
                                                                         
                                                                                  
 

                                                 
               
                           
 

const mountedRoots = new WeakMap                                                ();
const activeDocuments = new WeakMap                                          ();

function integerAttribute(value                    , fallback        , minimum        , maximum        , name        )         {
  if (value === undefined || value === "") return fallback;
  if (!/^\d+$/.test(value)) throw new RangeError(name + " must be a positive integer.");
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new RangeError(name + " must be between " + minimum + " and " + maximum + ".");
  }
  return parsed;
}

/** Read only the safely bounded attributes emitted by the WordPress shortcode. */
function parseWordPressConfiguration(host             )                         {
  return {
    speedIndex: integerAttribute(host.dataset.spikelingSpeed, DEFAULT_SPEED_INDEX, 0,
      DESKTOP_STEPS_PER_UPDATE.length - 1, "Simulation speed"),
    seed: integerAttribute(host.dataset.spikelingSeed, DEFAULT_WORDPRESS_SEED, 1,
      0xffff_ffff, "Simulation random seed"),
    maxSamples: integerAttribute(host.dataset.spikelingMaxSamples, DEFAULT_RECORDING_MAX_SAMPLES, 1,
      MAX_WORDPRESS_RECORDING_SAMPLES, "Scientific recording capacity"),
  };
}

function reportFailure(host             , failure         )       {
  host.dataset.spikelingState = "error";
  const alert = host.ownerDocument.createElement("p");
  alert.className = "osn-spikeling-emulator__error";
  alert.setAttribute("role", "alert");
  alert.textContent = failure instanceof Error ? failure.message : "Unable to initialise the neuronal emulator.";
  host.append(alert);
}

/** Idempotent per root even when Elementor and DOM observers initialise together. */
function mountWordPressEmulator(
  host             ,
  options                              = {},
)                                    {
  const existing = mountedRoots.get(host);
  if (existing !== undefined) return existing;

  let configuration                        ;
  try {
    configuration = parseWordPressConfiguration(host);
  } catch (failure) {
    reportFailure(host, failure);
    return Promise.reject(failure);
  }

  host.dataset.spikelingState = "mounting";
  let source            ;
  let emulator                   ;
  try {
    source = options.sourceFactory?.(configuration) ?? new EmulatorSource({
      speedIndex: configuration.speedIndex,
      simulation: { seed: configuration.seed },
    });
    emulator = new SpikelingEmulator(host, source, {
      ...options.interfaceOptions,
      recorder: { ...options.interfaceOptions?.recorder, maxSamples: configuration.maxSamples },
    });
  } catch (failure) {
    reportFailure(host, failure);
    return Promise.reject(failure);
  }

  let disposed = false;
  const connection = Promise.resolve()
    .then(() => source.connect())
    .then(() => {
      host.dataset.spikelingState = "ready";
      return {
        host,
        source,
        emulator,
        configuration,
        async dispose()                {
          if (disposed) return;
          disposed = true;
          emulator.dispose();
          await source.disconnect();
          host.dataset.spikelingState = "disposed";
          mountedRoots.delete(host);
        },
      }                                   ;
    })
    .catch(async (failure         ) => {
      emulator.dispose();
      try {
        await source.disconnect();
      } catch {
        // Preserve the original connection failure after best-effort cleanup.
      }
      mountedRoots.delete(host);
      reportFailure(host, failure);
      throw failure;
    });
  mountedRoots.set(host, connection);
  return connection;
}

/** Conditional root discovery supports Elementor-rendered and later-added shortcodes. */
function initialiseWordPressEmulators(
  owner          ,
  options                              = {},
)                                 {
  const previous = activeDocuments.get(owner);
  if (previous !== undefined) return previous;

  const connections = new Set                                   ();
  let disposed = false;
  let observer                               ;
  const target = options.eventTarget ?? owner.defaultView ?? undefined;

  function scan()       {
    if (disposed) return;
    for (const element of owner.querySelectorAll             (WORDPRESS_EMULATOR_SELECTOR)) {
      const pending = mountWordPressEmulator(element, options);
      if (!connections.has(pending)) {
        connections.add(pending);
        void pending.catch(() => {});
      }
    }
  }

  function begin()       {
    scan();
    const factory = options.observerFactory
      ?? (typeof MutationObserver === "undefined" ? undefined : (callback            ) => new MutationObserver(callback));
    if (factory !== undefined && owner.body !== null) {
      observer = factory(scan);
      observer.observe(owner.body, { childList: true, subtree: true });
    }
  }

  async function dispose()                {
    if (disposed) return;
    disposed = true;
    observer?.disconnect();
    owner.removeEventListener("DOMContentLoaded", begin);
    target?.removeEventListener("pagehide", handlePageHide);
    target?.removeEventListener("elementor/frontend/init", scan);
    const completed = await Promise.allSettled(connections);
    await Promise.all(completed
      .filter((result)                                                             => result.status === "fulfilled")
      .map((result) => result.value.dispose()));
    connections.clear();
    activeDocuments.delete(owner);
  }

  function handlePageHide()       { void dispose(); }
  const controller = { scan, dispose };
  activeDocuments.set(owner, controller);
  target?.addEventListener("pagehide", handlePageHide);
  target?.addEventListener("elementor/frontend/init", scan);

  if (owner.readyState === "loading") owner.addEventListener("DOMContentLoaded", begin, { once: true });
  else begin();
  return controller;
}

__spkExports.WORDPRESS_EMULATOR_SELECTOR = WORDPRESS_EMULATOR_SELECTOR;
__spkExports.DEFAULT_WORDPRESS_SEED = DEFAULT_WORDPRESS_SEED;
__spkExports.MAX_WORDPRESS_RECORDING_SAMPLES = MAX_WORDPRESS_RECORDING_SAMPLES;
__spkExports.parseWordPressConfiguration = parseWordPressConfiguration;
__spkExports.mountWordPressEmulator = mountWordPressEmulator;
__spkExports.initialiseWordPressEmulators = initialiseWordPressEmulators;

},
"src/data-source/EmulatorSource.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                                                             
             
                 
                      
                                
                      
                                   
const { DEFAULT_HISTORY_CAPACITY, SAMPLE_WIDTH, SampleRingBuffer, unpackSamples } = __spkRequire("src/simulation/ring-buffer.ts");
             
             
                
                 
                
              
                         

                                       
                                                  
                   
                    
                                                                      
          
                      
                    
                                                                      
          
                       
 

                                        
                                                      
                                    
                               
                                     
                                    
                                                      
 

/**
 * Browser-side worker adapter. Rendering code consumes DataSource batches and
 * bounded history without knowing whether a future source is physical hardware.
 */
class EmulatorSource                       {
           kind = "emulator";
           history                  ;

                   options                       ;
                   sampleListeners = new Set                ();
                   stateListeners = new Set               ();
                   errorListeners = new Set               ();
          worker                                  ;
          connection                           ;
          resolveConnection                          ;
          rejectConnection                                      ;
          snapshot                            ;

  constructor(options                        = {}) {
    this.options = options;
    this.history = new SampleRingBuffer(
      options.historyCapacity ?? DEFAULT_HISTORY_CAPACITY,
    );
  }

  connect()                {
    if (this.connection !== undefined) {
      return this.connection;
    }

    const factory =
      this.options.workerFactory ??
      (() =>
        new Worker(new URL("./spikeling-worker.e60975b9f106.js", import.meta.url), {
          type: "module",
        })                                   );

    this.worker = factory();
    this.worker.addEventListener("message", this.handleMessage);
    this.connection = new Promise      ((resolve, reject) => {
      this.resolveConnection = resolve;
      this.rejectConnection = reject;
    });
    this.worker.postMessage({
      type: "initialise",
      options: this.options.simulation,
      historyCapacity: this.options.historyCapacity,
      speedIndex: this.options.speedIndex,
      maxStepsPerSlice: this.options.maxStepsPerSlice,
      maxCatchUpTicks: this.options.maxCatchUpTicks,
    });

    return this.connection;
  }

  async disconnect()                {
    if (this.worker === undefined) {
      return;
    }

    this.worker.postMessage({ type: "dispose" });
    this.worker.removeEventListener("message", this.handleMessage);
    await this.worker.terminate();
    this.rejectConnection?.(new Error("The emulator worker was disconnected."));
    this.resolveConnection = undefined;
    this.rejectConnection = undefined;
    this.connection = undefined;
    this.worker = undefined;
    this.snapshot = undefined;
    this.history.clear();
  }

  start()       {
    this.send({ type: "start" });
  }

  pause()       {
    this.send({ type: "pause" });
  }

  stop()       {
    this.send({ type: "stop" });
  }

  reset(
    options                                                                           ,
  )       {
    this.send({ type: "reset", options });
  }

  setSpeed(index        )       {
    this.send({ type: "set-speed", index });
  }

  updateControls(patch               )       {
    this.send({ type: "update-controls", patch });
  }

  requestSnapshot()       {
    this.send({ type: "snapshot" });
  }

  getSnapshot()                             {
    return this.snapshot;
  }

  latest(count         )                     {
    return this.history.latest(count);
  }

  subscribe(listener                )              {
    this.sampleListeners.add(listener);
    return () => this.sampleListeners.delete(listener);
  }

  subscribeState(listener               )              {
    this.stateListeners.add(listener);
    if (this.snapshot !== undefined) {
      listener(this.snapshot);
    }
    return () => this.stateListeners.delete(listener);
  }

  subscribeErrors(listener               )              {
    this.errorListeners.add(listener);
    return () => this.errorListeners.delete(listener);
  }

          send(message                     )       {
    if (this.worker === undefined) {
      throw new Error("Connect the emulator source before sending commands.");
    }
    this.worker.postMessage(message);
  }

                   handleMessage = (event   
                                       
   )       => {
    const message = event.data;

    switch (message.type) {
      case "ready":
        this.publishState(message.snapshot);
        this.resolveConnection?.();
        this.resolveConnection = undefined;
        this.rejectConnection = undefined;
        break;

      case "state":
      case "snapshot":
        if (message.snapshot.stepIndex === 0 && this.history.length > 0) {
          this.history.clear();
        }
        this.publishState(message.snapshot);
        break;

      case "samples": {
        const packed = new Float64Array(message.buffer);
        if (packed.length !== message.count * SAMPLE_WIDTH) {
          this.publishError(new Error("The worker sent a malformed sample batch."));
          return;
        }

        const samples = unpackSamples(packed);
        this.history.pushBatch(samples);
        for (const listener of this.sampleListeners) {
          listener(samples);
        }
        break;
      }

      case "error":
        this.publishError(new Error(message.message));
        break;
    }
  };

          publishState(snapshot                )       {
    this.snapshot = snapshot;
    for (const listener of this.stateListeners) {
      listener(snapshot);
    }
  }

          publishError(error       )       {
    this.rejectConnection?.(error);
    this.resolveConnection = undefined;
    this.rejectConnection = undefined;
    for (const listener of this.errorListeners) {
      listener(error);
    }
  }
}

__spkExports.EmulatorSource = EmulatorSource;

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
"src/interface/emulator.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { SpikelingMainControls } = __spkRequire("src/controls/main-controls.ts");
                                                                              
const { SpikelingSynapseControls } = __spkRequire("src/controls/synapse-controls.ts");
                                                                              
                                                                            
const { SpikelingRecorder } = __spkRequire("src/recording/recorder.ts");
                                                                 
const { SpikelingRecordingControls } = __spkRequire("src/recording/recording-controls.ts");
                                                                                   
                                                                
const { DESKTOP_STEPS_PER_UPDATE, getSimulationSpeed } = __spkRequire("src/simulation/speed.ts");
const { SpikelingOscilloscope } = __spkRequire("src/visualisation/oscilloscope.ts");
                                                                            
const { MOBILE_MEDIA_QUERY, REDUCED_MOTION_MEDIA_QUERY, TABLET_MEDIA_QUERY } = __spkRequire("src/interface/accessibility.ts");
                                                         

                                    
                            
                                                               
                                                                  
 

                                           
                                              
                                                
                                                                   
                                       
                                                
                                                                    
                              
 

                                                             

                         
                                       
                                
                                
 

let instanceCount = 0;

function node                                       (
  owner          ,
  tag   ,
  className        ,
  text         ,
)                           {
  const created = owner.createElement(tag);
  created.className = className;
  if (text !== undefined) created.textContent = text;
  return created;
}

/** Reusable standalone and isolated WordPress-embeddable instrument. */
class SpikelingEmulator {
           element             ;
           oscilloscope                       ;
           controls                       ;
           synapses                          ;
           recorder                   ;
           recording                            ;

                   source            ;
                   owner          ;
                   prefix        ;
                   panels = new Map                              ();
                   subscriptions                = [];
                   mediaQueries                      = [];
                   startButton                   ;
                   pauseButton                   ;
                   stopButton                   ;
                   resetButton                   ;
                   speed                   ;
                   status             ;
                   error             ;
          layout                 = "desktop";
          disposed = false;

  constructor(host             , source            , options                           = {}) {
    this.owner = host.ownerDocument;
    this.source = source;
    instanceCount += 1;
    this.prefix = "spk-emulator-" + instanceCount + "-";
    this.element = node(this.owner, "section", "spk-emulator");
    this.element.setAttribute("aria-label", "Interactive Spikeling neuronal emulator");
    this.element.dataset.layout = this.layout;
    this.element.dataset.motion = "standard";

    const introduction = node(this.owner, "header", "spk-emulator__introduction");
    const title = node(this.owner, "h2", "spk-emulator__title", "Explore a spiking neuron");
    const scope = node(this.owner, "p", "spk-emulator__scope",
      "A real-time Izhikevich educational model and interface — not a biological preparation or a research-grade electrophysiology recorder.");
    scope.id = this.prefix + "scope";
    introduction.append(title, scope);
    this.element.append(introduction);

    const transport = node(this.owner, "div", "spk-emulator__transport");
    transport.setAttribute("role", "group");
    transport.setAttribute("aria-label", "Simulation transport and speed");
    this.startButton = this.transportButton("Start simulation", "start");
    this.pauseButton = this.transportButton("Pause simulation", "pause");
    this.stopButton = this.transportButton("Stop simulation", "stop");
    this.resetButton = this.transportButton("Reset simulation", "reset");
    const speedLabel = node(this.owner, "label", "spk-emulator__speed-label", "Simulation speed");
    this.speed = node(this.owner, "select", "spk-emulator__speed");
    this.speed.id = this.prefix + "speed";
    speedLabel.htmlFor = this.speed.id;
    this.speed.setAttribute("aria-describedby", scope.id);
    for (const [index] of DESKTOP_STEPS_PER_UPDATE.entries()) {
      const setting = getSimulationSpeed(index);
      const option = node(this.owner, "option", "", setting.realtimeMultiplier + "× real time · "
        + setting.stepsPerSecond.toLocaleString("en-GB") + " samples/s");
      option.value = String(index);
      this.speed.append(option);
    }
    speedLabel.append(this.speed);
    this.status = node(this.owner, "p", "spk-emulator__status", "Waiting for the simulation to connect.");
    this.status.setAttribute("role", "status");
    this.status.setAttribute("aria-live", "polite");
    this.status.setAttribute("aria-atomic", "true");
    transport.append(this.startButton, this.pauseButton, this.stopButton, this.resetButton, speedLabel, this.status);
    this.element.append(transport);

    const workspace = node(this.owner, "div", "spk-emulator__workspace");
    const scopeHost = node(this.owner, "div", "spk-emulator__oscilloscope");
    workspace.append(scopeHost);
    const main = this.addPanel(workspace, "main", "Neuron parameters");
    const stimulus = this.addPanel(workspace, "stimulus", "Stimulus parameters");
    const synapses = this.addPanel(workspace, "synapses", "Synapse 1 and Synapse 2");
    this.element.append(workspace);

    this.error = node(this.owner, "p", "spk-emulator__error");
    this.error.setAttribute("role", "alert");
    this.element.append(this.error);

    const footer = node(this.owner, "footer", "spk-emulator__footer");
    const sourceLink = node(this.owner, "a", "spk-emulator__source", "View open-source project");
    sourceLink.href = options.sourceUrl ?? "https://github.com/OpenSourceNeuro/Spikeling";
    footer.append(sourceLink);
    this.element.append(footer);
    host.append(this.element);

    this.oscilloscope = new SpikelingOscilloscope(scopeHost, source, options.oscilloscope);
    this.controls = new SpikelingMainControls(main.content, source, {
      ...options.controls,
      compact: true,
      stimulusHost: stimulus.content,
    });
    this.recorder = new SpikelingRecorder(source, options.recorder);
    const recordingHost = node(this.owner, "div", "spk-emulator__background-recording");
    this.recording = new SpikelingRecordingControls(recordingHost, this.recorder, options.recording);
    this.synapses = new SpikelingSynapseControls(synapses.content, source, {
      ...options.synapses,
      oscilloscope: this.oscilloscope,
    });

    this.disableTransport();
    this.startButton.addEventListener("click", () => this.command(() => source.start()));
    this.pauseButton.addEventListener("click", () => this.command(() => source.pause()));
    this.stopButton.addEventListener("click", () => this.command(() => source.stop()));
    this.resetButton.addEventListener("click", () => this.command(() => source.reset()));
    this.speed.addEventListener("change", () => this.command(() => source.setSpeed(Number(this.speed.value))));
    this.subscriptions.push(
      source.subscribeState((snapshot) => this.synchronise(snapshot)),
      source.subscribeErrors((failure) => this.showError(failure)),
    );
    this.initialiseMedia(options.mediaQueryFactory);
  }

  getLayout()                 { return this.layout; }

  isPanelOpen(panel               )          {
    return this.panel(panel).details.open;
  }

  setPanelOpen(panel               , open         )       {
    const selected = this.panel(panel);
    selected.details.open = open;
    selected.summary.setAttribute("aria-expanded", String(open));
  }

  dispose()       {
    if (this.disposed) return;
    this.disposed = true;
    for (const unsubscribe of this.subscriptions) unsubscribe();
    for (const query of this.mediaQueries) query.removeEventListener("change", this.handleMedia);
    this.recording.dispose();
    this.recorder.dispose();
    this.synapses.dispose();
    this.controls.dispose();
    this.oscilloscope.dispose();
    this.element.remove();
  }

          transportButton(label        , action        )                    {
    const button = node(this.owner, "button", "spk-emulator__button", label);
    button.type = "button";
    button.dataset.action = action;
    button.setAttribute("aria-label", label);
    return button;
  }

          addPanel(parent             , panel               , label        )                {
    const details = node(this.owner, "details", "spk-emulator__panel");
    details.dataset.panel = panel;
    details.open = true;
    const summary = node(this.owner, "summary", "spk-emulator__panel-summary", label);
    summary.id = this.prefix + panel + "-label";
    summary.setAttribute("aria-expanded", "true");
    const content = node(this.owner, "div", "spk-emulator__panel-content");
    content.id = this.prefix + panel + "-content";
    content.setAttribute("role", "region");
    content.setAttribute("aria-labelledby", summary.id);
    summary.setAttribute("aria-controls", content.id);
    details.append(summary, content);
    details.addEventListener("toggle", () => summary.setAttribute("aria-expanded", String(details.open)));
    parent.append(details);
    const elements = { details, summary, content };
    this.panels.set(panel, elements);
    return elements;
  }

          panel(identifier               )                {
    const selected = this.panels.get(identifier);
    if (selected === undefined) throw new RangeError("Unknown emulator control panel.");
    return selected;
  }

          disableTransport()       {
    this.startButton.disabled = true;
    this.pauseButton.disabled = true;
    this.stopButton.disabled = true;
    this.resetButton.disabled = true;
    this.speed.disabled = true;
  }

          synchronise(snapshot                )       {
    const running = snapshot.lifecycle === "running";
    this.startButton.disabled = running;
    this.pauseButton.disabled = !running;
    this.stopButton.disabled = snapshot.lifecycle === "idle" || snapshot.lifecycle === "stopped";
    this.resetButton.disabled = false;
    this.speed.disabled = false;
    this.speed.value = String(snapshot.speed.index);
    const label = snapshot.lifecycle === "idle" ? "Ready" : snapshot.lifecycle[0].toUpperCase() + snapshot.lifecycle.slice(1);
    this.status.textContent = label + " · " + snapshot.speed.realtimeMultiplier + "× real time · "
      + snapshot.speed.stepsPerSecond.toLocaleString("en-GB") + " samples/s wall-clock target.";
    this.status.dataset.state = snapshot.lifecycle;
  }

          initialiseMedia(factory                                       )       {
    const view = this.owner.defaultView;
    const match = factory ?? (typeof view?.matchMedia === "function" ? view.matchMedia.bind(view) : undefined);
    if (match === undefined) return;
    for (const query of [TABLET_MEDIA_QUERY, MOBILE_MEDIA_QUERY, REDUCED_MOTION_MEDIA_QUERY]) {
      const media = match(query);
      this.mediaQueries.push(media);
      media.addEventListener("change", this.handleMedia);
    }
    this.handleMedia();
  }

                   handleMedia = ()       => {
    const [tablet, mobile, reduced] = this.mediaQueries;
    const next                 = mobile.matches ? "mobile" : tablet.matches ? "tablet" : "desktop";
    if (next !== this.layout) {
      this.layout = next;
      this.element.dataset.layout = next;
      for (const panel of this.panels.keys()) this.setPanelOpen(panel, next !== "mobile");
      this.oscilloscope.resize();
    }
    this.element.dataset.motion = reduced.matches ? "reduced" : "standard";
  };

          command(action            )       {
    this.error.textContent = "";
    try {
      action();
    } catch (failure) {
      this.showError(failure instanceof Error ? failure : new Error("Unable to update the emulator."));
    }
  }

          showError(error       )       {
    this.error.textContent = error.message;
  }
}

__spkExports.SpikelingEmulator = SpikelingEmulator;

},
"src/controls/main-controls.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                                            
const { defaultControls } = __spkRequire("src/model/controls.ts");
const { getPreset, NEURON_PRESETS } = __spkRequire("src/model/presets.ts");
                                                                                         
                                                                
const { MAX_CUSTOM_STIMULUS_BYTES, MAX_CUSTOM_STIMULUS_SAMPLES, parseCustomStimulusCsv, parseCustomStimulusFile } = __spkRequire("src/stimulus/custom-csv.ts");
             
                        
                    
                       
                                   
const { renderStimulusPreview } = __spkRequire("src/stimulus/preview.ts");
const { MAIN_CONTROL_SPECIFICATIONS, formatMainControlValue, getMainControlSpecification, validateMainControlValue } = __spkRequire("src/controls/specifications.ts");
                                                                                      

                          
                                                      
                            
                                    
                                    
                                     
                                  
 

                                                                          
                                           
                             
                                      
 

let controlsInstanceCount = 0;

function element                                       (
  owner          ,
  tag   ,
  className        ,
  text         ,
)                           {
  const created = owner.createElement(tag);
  created.className = className;
  if (text !== undefined) {
    created.textContent = text;
  }
  return created;
}

function formattedNumber(value        )         {
  return String(value).replace("-", "−");
}

/** Desktop-faithful main-neuron controls talking only to the DataSource seam. */
class SpikelingMainControls {
           element             ;

                   owner          ;
                   source            ;
                   instancePrefix        ;
                   options                           ;
                   controls = new Map                               ();
                   enabled = new Map                        ();
                   auxiliaryElements                = [];
                   subscriptions                = [];
                   neuronSelect                   ;
                   parameters             ;
                   directCurrent                  ;
                   light                  ;
                   customToggle                  ;
                   fileInput                  ;
                   customStatus             ;
                   preview                   ;
                   errorMessage             ;
          currentControls = defaultControls();
          customSignature = "";
          importedSamples                    = [];
          disposed = false;

  constructor(host             , source            , options                            = {}) {
    this.owner = host.ownerDocument;
    this.source = source;
    this.options = options;
    controlsInstanceCount += 1;
    this.instancePrefix = "spk-main-" + controlsInstanceCount + "-";
    this.element = element(this.owner, "section", "spk-controls");
    this.element.setAttribute("aria-label", options.compact ? "Main neuron controls" : "Main neuron and stimulus controls");

    const neuron = this.group(options.compact ? "Neuron mode" : "Neuron parameters", "neuron");
    this.neuronSelect = element(this.owner, "select", "spk-controls__select");
    this.neuronSelect.id = this.instancePrefix + "neuron-mode";
    if (options.compact) {
      this.neuronSelect.setAttribute("aria-label", "Neuron mode");
    } else {
      const selectorLabel = element(this.owner, "label", "spk-controls__select-label", "Neuron mode");
      selectorLabel.htmlFor = this.neuronSelect.id;
      neuron.append(selectorLabel);
    }
    for (const preset of NEURON_PRESETS) {
      const choice = element(this.owner, "option", "", preset.label);
      choice.value = String(preset.id);
      this.neuronSelect.append(choice);
    }
    this.neuronSelect.value = "1";
    this.neuronSelect.addEventListener("change", () => this.selectPreset(Number(this.neuronSelect.value)));
    this.parameters = element(this.owner, "dl", "spk-controls__parameters");
    neuron.append(this.neuronSelect, this.parameters);

    if (options.compact) {
      const input = this.group("Current input", "cell");
      this.addSlider(input, "injectedCurrent", { alwaysEnabled: true, label: "Current input" });
      const noise = this.group("Noise", "cell");
      this.addSlider(noise, "noiseLevel", { alwaysEnabled: true, label: "Noise" });
    }

    let stimulusParent = this.element;
    if (options.stimulusHost !== undefined) {
      stimulusParent = element(this.owner, "section", "spk-controls");
      stimulusParent.setAttribute("aria-label", "Stimulus controls");
      options.stimulusHost.append(stimulusParent);
      this.auxiliaryElements.push(stimulusParent);
    }
    const stimulus = this.group("Stimulus parameters", "stimulus", stimulusParent);
    const routing = element(this.owner, "div", "spk-controls__routing");
    this.directCurrent = this.standaloneToggle(routing, "Direct current stimulation", "stimulus");
    this.light = this.standaloneToggle(routing, "Light stimulation", "cell");
    this.directCurrent.addEventListener("change", () => {
      this.applyPatch({ main: { directCurrentEnabled: this.directCurrent.checked } });
    });
    this.light.addEventListener("change", () => {
      this.applyPatch({ main: { lightEnabled: this.light.checked } });
    });
    stimulus.append(routing);
    this.addSlider(stimulus, "stimulusFrequency");
    this.addSlider(stimulus, "stimulusStrength");

    const custom = element(this.owner, "div", "spk-controls__custom");
    this.customToggle = this.standaloneToggle(custom, "Use custom stimulus", "stimulus");
    this.customToggle.disabled = true;
    this.customToggle.addEventListener("change", () => this.setCustomStimulusEnabled(this.customToggle.checked));
    const fileLabel = element(this.owner, "label", "spk-controls__file-label", "Load custom stimulus (.csv)");
    this.fileInput = element(this.owner, "input", "spk-controls__file");
    this.fileInput.id = this.instancePrefix + "custom-file";
    this.fileInput.type = "file";
    this.fileInput.accept = ".csv,text/csv";
    fileLabel.htmlFor = this.fileInput.id;
    this.fileInput.addEventListener("change", () => {
      const selected = this.fileInput.files?.[0];
      if (selected !== undefined) {
        void this.loadCustomStimulusFile(selected).catch((failure) => this.showError(failure));
      }
    });
    this.customStatus = element(this.owner, "p", "spk-controls__custom-status", "No custom stimulus loaded.");
    this.customStatus.setAttribute("role", "status");
    this.customStatus.setAttribute("aria-live", "polite");
    this.preview = element(this.owner, "canvas", "spk-controls__preview");
    this.preview.setAttribute("role", "img");
    this.preview.setAttribute("aria-label", "Imported custom stimulus preview.");
    custom.append(fileLabel, this.fileInput, this.customStatus, this.preview);
    stimulus.append(custom);

    if (!options.compact) {
      const input = this.group("Cell input", "cell");
      this.addSlider(input, "injectedCurrent");
      this.addSlider(input, "noiseLevel");
    }

    const photo = options.compact
      ? element(this.owner, "div", "spk-controls__legacy-photoreceptor")
      : this.group("Photoreceptor", "cell");
    this.addSlider(photo, "photoreceptorGain");
    this.addSlider(photo, "photoreceptorDecay");
    this.addSlider(photo, "photoreceptorRecovery");

    this.errorMessage = element(this.owner, "p", "spk-controls__error");
    this.errorMessage.setAttribute("role", "alert");
    this.element.append(this.errorMessage);
    host.append(this.element);

    this.updatePresetParameters(getPreset(1));
    this.drawPreview([]);
    this.syncControls(defaultControls(), true);
    this.subscriptions.push(
      source.subscribeState((snapshot) => this.handleSnapshot(snapshot)),
      source.subscribeErrors((failure) => this.showError(failure)),
    );
  }

  getControls()                     {
    return structuredClone(this.currentControls);
  }

  isEnabled(id               )          {
    getMainControlSpecification(id);
    return this.enabled.get(id) ?? false;
  }

  selectPreset(identifier        )       {
    const preset = getPreset(identifier);
    for (const id of ["photoreceptorGain", "photoreceptorDecay", "photoreceptorRecovery"]         ) {
      this.enabled.set(id, false);
    }
    this.neuronSelect.value = String(preset.id);
    this.updatePresetParameters(preset);
    this.applyPatch({
      main: {
        presetId: preset.id,
        photoreceptor: { gain: 0, decaySlider: 100, recoverySlider: 25 },
      },
    });
  }

  setControlEnabled(id               , active         )       {
    const specification = getMainControlSpecification(id);
    const controls = this.controls.get(id) ;
    const enabled = controls.alwaysEnabled || active;
    this.enabled.set(id, enabled);
    controls.toggle.checked = enabled;
    if (!enabled) {
      controls.slider.value = String(specification.defaultValue);
      this.updateSliderDisplay(controls, specification.defaultValue);
    }
    this.updateControlAvailability();
    this.applyPatch(this.patchForControl(id, Number(controls.slider.value)));
  }

  setControlValue(id               , value        )       {
    const valid = validateMainControlValue(id, value);
    const controls = this.controls.get(id) ;
    controls.slider.value = String(valid);
    this.updateSliderDisplay(controls, valid);
    this.applyPatch(this.patchForControl(id, valid));
  }

  async loadCustomStimulusFile(file                   )                                {
    const parsed = await parseCustomStimulusFile(file, this.options);
    this.installCustomStimulus(parsed, file.name);
    return parsed;
  }

  loadCustomStimulusText(content        , name = "custom-stimulus.csv")                       {
    const parsed = parseCustomStimulusCsv(content, this.options);
    this.installCustomStimulus(parsed, name);
    return parsed;
  }

  setCustomStimulusEnabled(active         )       {
    if (
      active &&
      this.currentControls.stimulus.customSamples.length === 0 &&
      this.importedSamples.length === 0
    ) {
      throw new RangeError("Load a valid stimulus CSV before enabling custom playback.");
    }
    this.customToggle.checked = active;
    this.applyPatch({ stimulus: { mode: active ? "custom" : "internal" } });
    this.updateControlAvailability();
  }

  dispose()       {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    for (const unsubscribe of this.subscriptions) {
      unsubscribe();
    }
    for (const auxiliary of this.auxiliaryElements) {
      auxiliary.remove();
    }
    this.element.remove();
  }

          group(title        , accent                   , parent = this.element)              {
    const section = element(this.owner, "section", "spk-controls__group");
    section.dataset.accent = accent;
    const heading = element(this.owner, "h3", "spk-controls__heading", title);
    section.append(heading);
    parent.append(section);
    return section;
  }

          standaloneToggle(parent             , label        , accent                   )                   {
    const wrapper = element(this.owner, "label", "spk-controls__toggle-row");
    wrapper.dataset.accent = accent;
    const input = element(this.owner, "input", "spk-controls__toggle");
    input.type = "checkbox";
    input.setAttribute("aria-label", label);
    const text = element(this.owner, "span", "spk-controls__toggle-label", label);
    wrapper.append(input, text);
    parent.append(wrapper);
    return input;
  }

          addSlider(
    parent             ,
    id               ,
    options                                                                = {},
  )       {
    const specification = getMainControlSpecification(id);
    const labelText = options.label ?? specification.label;
    const alwaysEnabled = options.alwaysEnabled ?? false;
    const enabled = alwaysEnabled || specification.enabledByDefault;
    const row = element(this.owner, "div", "spk-controls__control");
    row.dataset.control = id;
    row.dataset.accent = specification.accent;
    const header = element(this.owner, "div", "spk-controls__control-header");

    const toggle = element(this.owner, "input", "spk-controls__toggle");
    toggle.type = "checkbox";
    toggle.checked = enabled;
    toggle.setAttribute("aria-label", "Enable " + labelText.toLowerCase());
    const toggleTarget = element(this.owner, "label", "spk-controls__enable");
    toggleTarget.append(toggle);
    this.enabled.set(id, enabled);

    const slider = element(this.owner, "input", "spk-controls__range");
    slider.type = "range";
    slider.id = this.instancePrefix + id;
    slider.min = String(specification.minimum);
    slider.max = String(specification.maximum);
    slider.step = String(specification.step);
    slider.value = String(specification.defaultValue);
    slider.disabled = !enabled;
    slider.setAttribute("aria-label", labelText + " (" + specification.unit + ")");

    const label = element(this.owner, "label", "spk-controls__control-label", labelText);
    label.htmlFor = slider.id;
    const output = element(this.owner, "output", "spk-controls__value");
    output.setAttribute("for", slider.id);
    if (alwaysEnabled) {
      row.dataset.alwaysEnabled = "true";
      header.append(output);
    } else {
      header.append(toggleTarget, label, output);
    }

    const ticks = element(this.owner, "datalist", "spk-controls__ticks");
    ticks.id = slider.id + "-ticks";
    for (let value = specification.minimum; value <= specification.maximum; value += specification.tickInterval) {
      const mark = element(this.owner, "option", "");
      mark.value = String(value);
      ticks.append(mark);
    }
    slider.setAttribute("list", ticks.id);
    row.append(header, slider, ticks);
    if (alwaysEnabled) {
      const scale = element(this.owner, "div", "spk-controls__scale");
      scale.setAttribute("aria-hidden", "true");
      const values = id === "injectedCurrent"
        ? ["-100%", "0%", "100%"]
        : ["0%", "100%"];
      for (const value of values) {
        scale.append(element(this.owner, "span", "spk-controls__scale-mark", value));
      }
      row.append(scale);
    }
    parent.append(row);

    const references = { specification, row, toggle, slider, output, alwaysEnabled };
    this.controls.set(id, references);
    this.updateSliderDisplay(references, specification.defaultValue);

    toggle.addEventListener("change", () => this.setControlEnabled(id, toggle.checked));
    slider.addEventListener("input", () => this.setControlValue(id, Number(slider.value)));
  }

          updateSliderDisplay(elements                , value        )       {
    elements.output.textContent = formatMainControlValue(elements.specification.id, value);
    const percent =
      ((value - elements.specification.minimum) /
        (elements.specification.maximum - elements.specification.minimum)) *
      100;
    elements.slider.style.setProperty("--spk-fill", percent + "%");
    elements.slider.setAttribute("aria-valuetext", elements.output.textContent);
  }

          patchForControl(id               , value        )                {
    switch (id) {
      case "stimulusFrequency":
        return { stimulus: { frequencySlider: value } };
      case "stimulusStrength":
        return { stimulus: { strength: value } };
      case "injectedCurrent":
        return { main: { patchCurrent: value } };
      case "noiseLevel":
        return { main: { noiseLevel: value } };
      case "photoreceptorGain":
        return { main: { photoreceptor: { gain: value } } };
      case "photoreceptorDecay":
        return { main: { photoreceptor: { decaySlider: value } } };
      case "photoreceptorRecovery":
        return { main: { photoreceptor: { recoverySlider: value } } };
    }
  }

          controlValue(id               , controls                    )         {
    switch (id) {
      case "stimulusFrequency":
        return controls.stimulus.frequencySlider;
      case "stimulusStrength":
        return controls.stimulus.strength;
      case "injectedCurrent":
        return controls.main.patchCurrent;
      case "noiseLevel":
        return controls.main.noiseLevel;
      case "photoreceptorGain":
        return controls.main.photoreceptor.gain;
      case "photoreceptorDecay":
        return controls.main.photoreceptor.decaySlider;
      case "photoreceptorRecovery":
        return controls.main.photoreceptor.recoverySlider;
    }
  }

          applyPatch(patch               )       {
    this.errorMessage.textContent = "";
    this.source.updateControls(patch);
  }

          handleSnapshot(snapshot                )       {
    this.syncControls(snapshot.controls, false);
  }

          syncControls(controls                    , initialise         )       {
    this.currentControls = structuredClone(controls);
    this.neuronSelect.value = String(controls.main.presetId);
    this.updatePresetParameters(getPreset(controls.main.presetId));
    this.directCurrent.checked = controls.main.directCurrentEnabled;
    this.light.checked = controls.main.lightEnabled;

    for (const specification of MAIN_CONTROL_SPECIFICATIONS) {
      const references = this.controls.get(specification.id) ;
      const value = this.controlValue(specification.id, controls);
      if (!initialise && value !== specification.defaultValue) {
        this.enabled.set(specification.id, true);
      }
      references.toggle.checked = this.enabled.get(specification.id) ?? false;
      references.slider.value = String(value);
      this.updateSliderDisplay(references, value);
    }

    const imported = controls.stimulus.customSamples;
    this.customToggle.disabled = imported.length === 0;
    this.customToggle.checked = controls.stimulus.mode === "custom";
    const signature = imported.length + ":" + imported[0] + ":" + imported[imported.length - 1];
    if (imported.length > 0 && signature !== this.customSignature) {
      this.customSignature = signature;
      this.drawPreview(imported);
      if (this.customStatus.textContent === "No custom stimulus loaded.") {
        this.customStatus.textContent =
          imported.length.toLocaleString("en-GB") + " samples · 0.1 ms/sample";
      }
    }
    this.updateControlAvailability();
  }

          updateControlAvailability()       {
    const custom = this.customToggle.checked;
    for (const [id, references] of this.controls) {
      const internalOnly = id === "stimulusFrequency" || id === "stimulusStrength";
      references.toggle.disabled = internalOnly && custom;
      references.slider.disabled = !(this.enabled.get(id) ?? false) || (internalOnly && custom);
      references.row.dataset.disabled = String(references.slider.disabled);
    }
  }

          updatePresetParameters(preset              )       {
    this.parameters.replaceChildren();
    for (const [label, value, unit] of [
      ["a", preset.a, ""],
      ["b", preset.b, ""],
      ["c", preset.c, "mV"],
      ["d", preset.d, ""],
      ["Vrest", preset.restingPotential, "mV"],
    ]         ) {
      const term = element(this.owner, "dt", "spk-controls__parameter-name", label);
      const definition = element(
        this.owner,
        "dd",
        "spk-controls__parameter-value",
        formattedNumber(value) + (unit ? " " + unit : ""),
      );
      this.parameters.append(term, definition);
    }
  }

          installCustomStimulus(parsed                      , name        )       {
    this.importedSamples = parsed.samples;
    this.customStatus.textContent =
      name +
      " · " +
      parsed.samples.length.toLocaleString("en-GB") +
      " samples · " +
      parsed.sampleIntervalMs +
      " ms/sample · " +
      parsed.durationMs.toFixed(1) +
      " ms";
    this.customToggle.disabled = false;
    this.customSignature =
      parsed.samples.length + ":" + parsed.samples[0] + ":" + parsed.samples[parsed.samples.length - 1];
    this.drawPreview(parsed.samples);
    this.applyPatch({ stimulus: { customSamples: [...parsed.samples] } });
  }

          drawPreview(samples                   )       {
    renderStimulusPreview(this.preview, samples, this.options.devicePixelRatio?.() ?? 1);
  }

          showError(failure         )       {
    this.errorMessage.textContent =
      failure instanceof Error ? failure.message : "The neuron controls encountered an unexpected error.";
  }
}

                                                        

const CUSTOM_STIMULUS_LIMITS = Object.freeze({
  bytes: MAX_CUSTOM_STIMULUS_BYTES,
  samples: MAX_CUSTOM_STIMULUS_SAMPLES,
});

__spkExports.SpikelingMainControls = SpikelingMainControls;
__spkExports.CUSTOM_STIMULUS_LIMITS = CUSTOM_STIMULUS_LIMITS;

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
"src/stimulus/custom-csv.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { TIMESTEP_MS } = __spkRequire("src/model/izhikevich.ts");

const MAX_CUSTOM_STIMULUS_BYTES = 8 * 1_024 * 1_024;
const MAX_CUSTOM_STIMULUS_SAMPLES = 250_000;
const REQUIRED_STIMULUS_COLUMN = "Stim";

const TIME_COLUMN_NAMES = ["Time (ms)", "timeMs", "time_ms"]         ;
const NUMERIC_FIELD = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;

                                     
               
               
                
                   
                         
                      
                   
                    
                  
                       
                      

class CustomStimulusError extends Error {
           code                         ;
           line                    ;

  constructor(code                         , message        , line         ) {
    super(message);
    this.name = "CustomStimulusError";
    this.code = code;
    this.line = line;
  }
}

                                        
                             
                               
 

                                       
                                      
                                    
                              
                           
                           
                                     
                                  
 

                                    
                        
                        
                          
 

                  
                        
                            
 

function positiveLimit(value                    , fallback        , name        )         {
  const limit = value ?? fallback;
  if (!Number.isSafeInteger(limit) || limit < 1) {
    throw new RangeError(name + " must be a positive safe integer.");
  }
  return limit;
}

function readCsvRows(content        )           {
  const rows           = [];
  let fields           = [];
  let field = "";
  let line = 1;
  let rowLine = 1;
  let quoted = false;
  let closedQuote = false;

  function finishRow()       {
    fields.push(field.trim());
    if (fields.some((value) => value.length > 0)) {
      rows.push({ line: rowLine, fields });
    }
    fields = [];
    field = "";
    closedQuote = false;
  }

  for (let index = 0; index < content.length; index += 1) {
    const character = content[index];

    if (quoted) {
      if (character === '"' && content[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
        closedQuote = true;
      } else {
        if (character === "\n") {
          line += 1;
        }
        field += character;
      }
      continue;
    }

    if (character === '"') {
      if (field.trim().length > 0 || closedQuote) {
        throw new CustomStimulusError("malformed-csv", "Unexpected quote in CSV data.", line);
      }
      field = "";
      quoted = true;
      continue;
    }

    if (closedQuote && character !== "," && character !== "\n" && character !== "\r") {
      if (character.trim().length > 0) {
        throw new CustomStimulusError("malformed-csv", "Unexpected text after a quoted CSV field.", line);
      }
      continue;
    }

    if (character === ",") {
      fields.push(field.trim());
      field = "";
      closedQuote = false;
    } else if (character === "\n" || character === "\r") {
      if (character === "\r" && content[index + 1] === "\n") {
        index += 1;
      }
      finishRow();
      line += 1;
      rowLine = line;
    } else {
      field += character;
    }
  }

  if (quoted) {
    throw new CustomStimulusError("malformed-csv", "The CSV contains an unterminated quoted field.", line);
  }
  if (field.length > 0 || fields.length > 0 || closedQuote) {
    finishRow();
  }

  return rows;
}

function numericField(value        , code                                        , line        )         {
  if (!NUMERIC_FIELD.test(value)) {
    throw new CustomStimulusError(
      code,
      (code === "invalid-sample" ? "Stimulus value" : "Timestamp") +
        " on line " +
        line +
        " must be a finite decimal number.",
      line,
    );
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    throw new CustomStimulusError(code, "Numeric CSV value is not finite on line " + line + ".", line);
  }
  return parsed;
}

/** Parse the desktop's exact Stim[,Trigger] format entirely in local memory. */
function parseCustomStimulusCsv(
  content        ,
  options                        = {},
)                       {
  const maxBytes = positiveLimit(options.maxBytes, MAX_CUSTOM_STIMULUS_BYTES, "CSV byte limit");
  const maxSamples = positiveLimit(options.maxSamples, MAX_CUSTOM_STIMULUS_SAMPLES, "CSV sample limit");
  const bytes = new TextEncoder().encode(content).byteLength;
  if (bytes > maxBytes) {
    throw new CustomStimulusError("file-size", "The stimulus CSV exceeds the allowed " + maxBytes + " bytes.");
  }

  const cleaned = content.replace(/^\uFEFF/, "");
  if (cleaned.trim().length === 0) {
    throw new CustomStimulusError("empty-file", "The stimulus CSV is empty.");
  }

  const rows = readCsvRows(cleaned);
  if (rows.length === 0) {
    throw new CustomStimulusError("empty-file", "The stimulus CSV contains no readable rows.");
  }

  const header = rows[0].fields;
  const stimulusIndices = header.flatMap((name, index) =>
    name === REQUIRED_STIMULUS_COLUMN ? [index] : [],
  );
  if (stimulusIndices.length === 0) {
    throw new CustomStimulusError("missing-stim-column", 'The CSV must contain an exact "Stim" column.', rows[0].line);
  }
  if (stimulusIndices.length > 1) {
    throw new CustomStimulusError("duplicate-column", 'The CSV contains more than one "Stim" column.', rows[0].line);
  }

  const timeIndices = header.flatMap((name, index) =>
    TIME_COLUMN_NAMES.includes(name                                      ) ? [index] : [],
  );
  if (timeIndices.length > 1) {
    throw new CustomStimulusError("duplicate-column", "The CSV contains ambiguous timestamp columns.", rows[0].line);
  }

  const samples           = [];
  let minimum = Number.POSITIVE_INFINITY;
  let maximum = Number.NEGATIVE_INFINITY;
  let previousTime                    ;

  for (const row of rows.slice(1)) {
    if (row.fields.length !== header.length) {
      throw new CustomStimulusError("malformed-csv", "CSV row " + row.line + " has an unexpected number of columns.", row.line);
    }
    if (samples.length >= maxSamples) {
      throw new CustomStimulusError("sample-limit", "The stimulus CSV exceeds " + maxSamples + " samples.", row.line);
    }

    const sample = numericField(row.fields[stimulusIndices[0]], "invalid-sample", row.line);
    if (timeIndices.length === 1) {
      const timestamp = numericField(row.fields[timeIndices[0]], "invalid-timestamp", row.line);
      if (
        previousTime !== undefined &&
        Math.abs(timestamp - previousTime - TIMESTEP_MS) > 1e-8
      ) {
        throw new CustomStimulusError(
          "sample-interval",
          "Timestamp spacing on line " + row.line + " must match the 0.1 ms simulation timestep.",
          row.line,
        );
      }
      previousTime = timestamp;
    }

    samples.push(sample);
    minimum = Math.min(minimum, sample);
    maximum = Math.max(maximum, sample);
  }

  if (samples.length === 0) {
    throw new CustomStimulusError("empty-samples", 'The "Stim" column contains no samples.', rows[0].line);
  }

  return {
    samples,
    sampleIntervalMs: TIMESTEP_MS,
    durationMs: samples.length * TIMESTEP_MS,
    minimum,
    maximum,
    hasTriggerColumn: header.includes("Trigger"),
    hasTimeColumn: timeIndices.length === 1,
  };
}

async function parseCustomStimulusFile(
  file                   ,
  options                        = {},
)                                {
  if (!/\.csv$/i.test(file.name)) {
    throw new CustomStimulusError("file-type", "A custom stimulus must be a .csv file.");
  }
  const maxBytes = positiveLimit(options.maxBytes, MAX_CUSTOM_STIMULUS_BYTES, "CSV byte limit");
  if (!Number.isFinite(file.size) || file.size < 0 || file.size > maxBytes) {
    throw new CustomStimulusError("file-size", "The stimulus file exceeds the allowed " + maxBytes + " bytes.");
  }
  return parseCustomStimulusCsv(await file.text(), options);
}

__spkExports.MAX_CUSTOM_STIMULUS_BYTES = MAX_CUSTOM_STIMULUS_BYTES;
__spkExports.MAX_CUSTOM_STIMULUS_SAMPLES = MAX_CUSTOM_STIMULUS_SAMPLES;
__spkExports.REQUIRED_STIMULUS_COLUMN = REQUIRED_STIMULUS_COLUMN;
__spkExports.CustomStimulusError = CustomStimulusError;
__spkExports.parseCustomStimulusCsv = parseCustomStimulusCsv;
__spkExports.parseCustomStimulusFile = parseCustomStimulusFile;

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
"src/stimulus/preview.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { SPIKELING_PALETTE } = __spkRequire("src/visualisation/theme.ts");

                                         
                
                 
                                                                               
                                                             
 

                                            
                           
                                   
                           
                           
 

/** Compact local-file waveform preview, keeping per-pixel minima and maxima. */
function renderStimulusPreview(
  canvas                        ,
  samples                   ,
  pixelRatio = globalThis.devicePixelRatio ?? 1,
)                            {
  const context = canvas.getContext("2d");
  if (context === null) {
    throw new Error("The stimulus preview requires a 2D Canvas rendering context.");
  }
  if (!Number.isFinite(pixelRatio) || pixelRatio <= 0) {
    throw new RangeError("The stimulus-preview device pixel ratio must be positive.");
  }

  const bounds = canvas.getBoundingClientRect();
  const width = Math.max(1, Math.round(bounds.width));
  const height = Math.max(1, Math.round(bounds.height));
  canvas.width = Math.round(width * pixelRatio);
  canvas.height = Math.round(height * pixelRatio);
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  context.fillStyle = SPIKELING_PALETTE.backgroundDeep;
  context.fillRect(0, 0, width, height);

  if (samples.length === 0) {
    return { samples: 0, displayedPoints: 0, minimum: 0, maximum: 0 };
  }

  let minimum = Number.POSITIVE_INFINITY;
  let maximum = Number.NEGATIVE_INFINITY;
  for (const sample of samples) {
    if (!Number.isFinite(sample)) {
      throw new RangeError("Stimulus-preview samples must be finite.");
    }
    minimum = Math.min(minimum, sample);
    maximum = Math.max(maximum, sample);
  }

  const low = Math.min(minimum, 0);
  const high = Math.max(maximum, 0);
  const span = high - low || 1;
  const verticalPadding = 6;
  const availableHeight = Math.max(1, height - verticalPadding * 2);
  const projectY = (value        ) =>
    verticalPadding + ((high - value) / span) * availableHeight;

  context.strokeStyle = SPIKELING_PALETTE.panel;
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(0, projectY(0));
  context.lineTo(width, projectY(0));
  context.stroke();

  context.strokeStyle = SPIKELING_PALETTE.stimulus;
  context.beginPath();
  let displayedPoints = 0;
  let first = true;

  const columns = Math.min(width, samples.length);
  for (let pixel = 0; pixel < columns; pixel += 1) {
    const start = Math.floor((pixel / columns) * samples.length);
    const end = Math.min(
      samples.length,
      Math.max(start + 1, Math.floor(((pixel + 1) / columns) * samples.length)),
    );
    let lowIndex = start;
    let highIndex = start;
    for (let index = start + 1; index < end; index += 1) {
      if (samples[index] < samples[lowIndex]) {
        lowIndex = index;
      }
      if (samples[index] > samples[highIndex]) {
        highIndex = index;
      }
    }
    const indices = Array.from(new Set([start, lowIndex, highIndex, end - 1])).sort(
      (left, right) => left - right,
    );
    for (const index of indices) {
      const x = samples.length === 1 ? 0 : (index / (samples.length - 1)) * width;
      const y = projectY(samples[index]);
      if (first) {
        context.moveTo(x, y);
        first = false;
      } else {
        context.lineTo(x, y);
      }
      displayedPoints += 1;
    }
  }
  context.stroke();

  return { samples: samples.length, displayedPoints, minimum, maximum };
}

__spkExports.renderStimulusPreview = renderStimulusPreview;

},
"src/visualisation/theme.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

/** Palette values are pinned to the existing desktop Parameters_Settings.py. */
const SPIKELING_PALETTE = Object.freeze({
  backgroundDeep: "#001E26",
  background: "#002B36",
  panel: "#073642",
  muted: "#586E75",
  secondary: "#93A1A1",
  text: "#BECDCD",
  light: "#FDF6E3",
  membrane: "#DC322F",
  cell: "#859900",
  stimulus: "#268BD2",
  synapse1Voltage: "#CB4B16",
  synapse1Current: "#2AA198",
  synapse2Voltage: "#B58900",
  synapse2Current: "#D33682",
});

                                    
                              
                         
                        
                         
                        
 

const DEFAULT_OSCILLOSCOPE_THEME                    = Object.freeze({
  background: SPIKELING_PALETTE.backgroundDeep,
  panel: SPIKELING_PALETTE.background,
  grid: SPIKELING_PALETTE.panel,
  muted: SPIKELING_PALETTE.secondary,
  text: SPIKELING_PALETTE.text,
});

__spkExports.SPIKELING_PALETTE = SPIKELING_PALETTE;
__spkExports.DEFAULT_OSCILLOSCOPE_THEME = DEFAULT_OSCILLOSCOPE_THEME;

},
"src/controls/specifications.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { TIMESTEP_MS } = __spkRequire("src/model/izhikevich.ts");

                           
                       
                      
                     
                
                       
                        
                            

                                                

                                              
                             
                                 
                         
                           
                           
                        
                                
                                
                                     
                                 
                        
 

/** Source-pinned to generated UI_Spikeling.py and its emulator controller. */
const MAIN_CONTROL_SPECIFICATIONS                                         =
  Object.freeze([
    {
      id: "stimulusFrequency",
      desktopWidget: "Emulator_StimFre_slider",
      label: "Stimulus frequency",
      minimum: -100,
      maximum: 100,
      step: 1,
      tickInterval: 20,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "stimulus",
      unit: "Hz",
    },
    {
      id: "stimulusStrength",
      desktopWidget: "Emulator_StimStrSlider",
      label: "Stimulus strength",
      minimum: -100,
      maximum: 100,
      step: 1,
      tickInterval: 20,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "stimulus",
      unit: "%",
    },
    {
      id: "injectedCurrent",
      desktopWidget: "Emulator_PatchClamp_slider",
      label: "Injected current",
      minimum: -100,
      maximum: 100,
      step: 1,
      tickInterval: 20,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "cell",
      unit: "a.u.",
    },
    {
      id: "noiseLevel",
      desktopWidget: "Emulator_Noise_slider",
      label: "Noise level",
      minimum: 0,
      maximum: 100,
      step: 1,
      tickInterval: 10,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "cell",
      unit: "%",
    },
    {
      id: "photoreceptorGain",
      desktopWidget: "Emulator_PR_PhotoGain_slider",
      label: "Photo-gain",
      minimum: -100,
      maximum: 100,
      step: 1,
      tickInterval: 20,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "cell",
      unit: "%",
    },
    {
      id: "photoreceptorDecay",
      desktopWidget: "Emulator_PR_Decay_slider",
      label: "Photo decay λ",
      minimum: 10,
      maximum: 125,
      step: 1,
      tickInterval: 10,
      defaultValue: 100,
      enabledByDefault: false,
      accent: "cell",
      unit: "ms⁻¹",
    },
    {
      id: "photoreceptorRecovery",
      desktopWidget: "Emulator_PR_Recovery_slider",
      label: "Photo recovery λ",
      minimum: 1,
      maximum: 100,
      step: 1,
      tickInterval: 10,
      defaultValue: 25,
      enabledByDefault: false,
      accent: "cell",
      unit: "ms⁻¹",
    },
  ]);

function getMainControlSpecification(id               )                              {
  const specification = MAIN_CONTROL_SPECIFICATIONS.find((candidate) => candidate.id === id);
  if (specification === undefined) {
    throw new RangeError("Unknown main-neuron control: " + String(id));
  }
  return specification;
}

function validateMainControlValue(id               , value        )         {
  const specification = getMainControlSpecification(id);
  if (
    !Number.isInteger(value) ||
    value < specification.minimum ||
    value > specification.maximum
  ) {
    throw new RangeError(
      specification.label +
        " must be an integer from " +
        specification.minimum +
        " to " +
        specification.maximum +
        ".",
    );
  }
  return value;
}

/** Desktop UI formula: round(10000 / (500 + (-slider * 500 / 100) + 10)). */
function stimulusFrequencyHz(slider        )         {
  validateMainControlValue("stimulusFrequency", slider);
  const periodSteps = 500 + (-slider * 500) / 100 + 10;
  return 1_000 / (periodSteps * TIMESTEP_MS);
}

function photoreceptorDecayRate(slider        )         {
  return validateMainControlValue("photoreceptorDecay", slider) / 100_000;
}

function photoreceptorRecoveryRate(slider        )         {
  return validateMainControlValue("photoreceptorRecovery", slider) / 1_000;
}

function gaussianNoiseStandardDeviation(slider        )         {
  return validateMainControlValue("noiseLevel", slider) / 4;
}

function formatMainControlValue(id               , slider        )         {
  validateMainControlValue(id, slider);
  switch (id) {
    case "stimulusFrequency":
      return Math.round(stimulusFrequencyHz(slider)) + " Hz";
    case "stimulusStrength":
    case "photoreceptorGain":
      return slider + "%";
    case "injectedCurrent":
      return slider + " a.u.";
    case "noiseLevel":
      return slider + "% · σ " + gaussianNoiseStandardDeviation(slider) + " a.u.";
    case "photoreceptorDecay":
      return photoreceptorDecayRate(slider) + " ms⁻¹";
    case "photoreceptorRecovery":
      return photoreceptorRecoveryRate(slider) + " ms⁻¹";
  }
}

__spkExports.MAIN_CONTROL_SPECIFICATIONS = MAIN_CONTROL_SPECIFICATIONS;
__spkExports.getMainControlSpecification = getMainControlSpecification;
__spkExports.validateMainControlValue = validateMainControlValue;
__spkExports.stimulusFrequencyHz = stimulusFrequencyHz;
__spkExports.photoreceptorDecayRate = photoreceptorDecayRate;
__spkExports.photoreceptorRecoveryRate = photoreceptorRecoveryRate;
__spkExports.gaussianNoiseStandardDeviation = gaussianNoiseStandardDeviation;
__spkExports.formatMainControlValue = formatMainControlValue;

},
"src/controls/synapse-controls.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                                            
const { defaultControls } = __spkRequire("src/model/controls.ts");
const { getPreset, NEURON_PRESETS } = __spkRequire("src/model/presets.ts");
             
                
               
                     
                   
                  
               
                           
                                                                
                                                             
const { SYNAPSE_CONTROL_SPECIFICATIONS, SYNAPSE_IDS, formatSynapseControlValue, getSynapseControlSpecification, synapticTimeConstantMs, validateSynapseControlValue, validateSynapseId } = __spkRequire("src/controls/synapse-specifications.ts");
             
                   
                              
            
                                     

                                         
                                                             
 

                                         
                                                 
                                    
 

                                 
                                                      
                            
                                    
                                    
                                     
 

                           
                              
                                
                                    
                                       
                                   
                                           
                                   
                                
                                                                  
                                                   
 

let synapseInstanceCount = 0;

function element                                       (
  owner          ,
  tag   ,
  className        ,
  text         ,
)                           {
  const created = owner.createElement(tag);
  created.className = className;
  if (text !== undefined) {
    created.textContent = text;
  }
  return created;
}

function channelNumber(channel           )         {
  return channel === "synapse1" ? "1" : "2";
}

function photoControl(id                  )          {
  return id === "photoreceptorGain" || id === "photoreceptorDecay" || id === "photoreceptorRecovery";
}

function independentControl(id                  )          {
  return id === "gain" || id === "decay";
}

function scientificNumber(value        , digits = 1)         {
  return value.toFixed(digits).replace("-", "−");
}

/** Two desktop-faithful auxiliary neurons and their independent signed synaptic outputs. */
class SpikelingSynapseControls {
           element             ;

                   owner          ;
                   source            ;
                   options                        ;
                   instancePrefix        ;
                   channels = new Map                            ();
                   subscriptions                = [];
                   error             ;
          current = defaultControls();
          latestSample                              ;
          disposed = false;

  constructor(host             , source            , options                         = {}) {
    this.owner = host.ownerDocument;
    this.source = source;
    this.options = options;
    synapseInstanceCount += 1;
    this.instancePrefix = "spk-synapses-" + synapseInstanceCount + "-";
    this.element = element(this.owner, "section", "spk-controls spk-synapses");
    this.element.setAttribute("aria-label", "Virtual presynaptic neuron controls");

    for (const channel of SYNAPSE_IDS) {
      this.buildChannel(channel);
    }

    this.error = element(this.owner, "p", "spk-controls__error spk-synapses__error");
    this.error.setAttribute("role", "alert");
    this.element.append(this.error);
    host.append(this.element);

    this.synchronise(defaultControls(), true);
    this.subscriptions.push(
      source.subscribe((samples) => this.handleSamples(samples)),
      source.subscribeState((snapshot) => this.handleSnapshot(snapshot)),
      source.subscribeErrors((failure) => this.showError(failure)),
    );
  }

  getControls(channel           )                  {
    return structuredClone(this.current[validateSynapseId(channel)]);
  }

  isSynapseEnabled(channel           )          {
    return this.current[validateSynapseId(channel)].enabled;
  }

  isControlEnabled(channel           , id                  )          {
    getSynapseControlSpecification(channel, id);
    return this.channels.get(channel) .enabled.get(id) ?? false;
  }

  setSynapseEnabled(channel           , active         )       {
    const references = this.channel(channel);
    references.master.checked = active;

    if (active) {
      this.applyPatch(channel, { enabled: true });
      return;
    }

    for (const id of [
      "injectedCurrent",
      "noiseLevel",
      "photoreceptorGain",
      "photoreceptorDecay",
      "photoreceptorRecovery",
    ]         ) {
      references.enabled.set(id, false);
    }

    this.applyPatch(channel, {
      enabled: false,
      patchCurrent: 0,
      noiseLevel: 0,
      directCurrentEnabled: false,
      lightEnabled: false,
      photoreceptor: { gain: 0, decaySlider: 100, recoverySlider: 25 },
    });
  }

  selectPreset(channel           , identifier        )       {
    const references = this.channel(channel);
    const preset = getPreset(identifier);
    for (const id of ["photoreceptorGain", "photoreceptorDecay", "photoreceptorRecovery"]         ) {
      references.enabled.set(id, false);
    }
    references.selector.value = String(preset.id);
    this.updateParameters(references, preset);
    this.applyPatch(channel, {
      presetId: preset.id,
      photoreceptor: { gain: 0, decaySlider: 100, recoverySlider: 25 },
    });
  }

  setControlEnabled(channel           , id                  , active         )       {
    const references = this.channel(channel);
    const specification = getSynapseControlSpecification(channel, id);
    if (active && !independentControl(id) && !this.current[channel].enabled) {
      throw new RangeError("Enable Synapse " + channelNumber(channel) + " before adjusting its auxiliary neuron.");
    }
    if (active && photoControl(id) && !this.current[channel].lightEnabled) {
      throw new RangeError("Enable light stimulation before adjusting photoreceptor controls.");
    }

    const slider = references.controls.get(id) ;
    references.enabled.set(id, active);
    slider.toggle.checked = active;
    if (!active) {
      slider.slider.value = String(specification.defaultValue);
      this.updateSlider(references, slider, specification.defaultValue);
    }

    this.updateAvailability(references);
    this.applyPatch(channel, this.controlPatch(id, Number(slider.slider.value)));
  }

  setControlValue(channel           , id                  , value        )       {
    const references = this.channel(channel);
    const valid = validateSynapseControlValue(channel, id, value);
    const slider = references.controls.get(id) ;
    slider.slider.value = String(valid);
    this.updateSlider(references, slider, valid);
    this.applyPatch(channel, this.controlPatch(id, valid));
  }

  setDirectCurrentEnabled(channel           , active         )       {
    this.requireActive(channel, "direct current stimulation");
    const references = this.channel(channel);
    references.directCurrent.checked = active;
    this.applyPatch(channel, { directCurrentEnabled: active });
  }

  setLightEnabled(channel           , active         )       {
    this.requireActive(channel, "light stimulation");
    const references = this.channel(channel);
    references.light.checked = active;
    if (active) {
      this.applyPatch(channel, { lightEnabled: true });
      return;
    }

    for (const id of ["photoreceptorGain", "photoreceptorDecay", "photoreceptorRecovery"]         ) {
      references.enabled.set(id, false);
    }
    this.applyPatch(channel, {
      lightEnabled: false,
      photoreceptor: { gain: 0, decaySlider: 100, recoverySlider: 25 },
    });
  }

  dispose()       {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    for (const unsubscribe of this.subscriptions) {
      unsubscribe();
    }
    this.element.remove();
  }

          buildChannel(channel           )       {
    const number = channelNumber(channel);
    const root = element(this.owner, "section", "spk-controls__group spk-synapses__channel");
    root.dataset.synapse = channel;
    root.setAttribute("aria-label", "Synapse " + number + " and auxiliary neuron " + number);

    const heading = element(this.owner, "div", "spk-synapses__heading");
    const title = element(this.owner, "h3", "spk-synapses__title", "Synapse " + number);
    const activation = element(this.owner, "label", "spk-synapses__activation");
    const master = element(this.owner, "input", "spk-controls__toggle");
    master.type = "checkbox";
    master.setAttribute("aria-label", "Enable Synapse " + number);
    activation.append(master, element(this.owner, "span", "spk-synapses__activation-label", "Active"));
    heading.append(title, activation);
    root.append(heading);

    const selectorLabel = element(this.owner, "label", "spk-controls__select-label", "Auxiliary neuron " + number + " mode");
    const selector = element(this.owner, "select", "spk-controls__select");
    selector.id = this.instancePrefix + channel + "-mode";
    selectorLabel.htmlFor = selector.id;
    selector.setAttribute("aria-label", "Synapse " + number + " neuron mode");
    for (const preset of NEURON_PRESETS) {
      const option = element(this.owner, "option", "", preset.label);
      option.value = String(preset.id);
      selector.append(option);
    }
    selector.value = "1";
    const parameters = element(this.owner, "dl", "spk-controls__parameters");
    root.append(selectorLabel, selector, parameters);

    const output = this.subgroup(root, "Synaptic output", "channel");
    const cell = this.subgroup(root, "Auxiliary cell input", "cell");
    const routing = this.subgroup(root, "Stimulus routing", "cell");
    const directCurrent = this.toggle(routing, "Synapse " + number + " direct current stimulation", "stimulus");
    const light = this.toggle(routing, "Synapse " + number + " light stimulation", "cell");
    const photo = this.subgroup(root, "Photoreceptor", "cell");
    const reading = element(this.owner, "p", "spk-synapses__reading", "Inactive · output 0.0 a.u.");
    reading.setAttribute("aria-live", "off");

    const references                  = {
      channel,
      element: root,
      master,
      selector,
      parameters,
      directCurrent,
      light,
      reading,
      controls: new Map(),
      enabled: new Map(),
    };
    this.channels.set(channel, references);

    for (const id of ["gain", "decay"]         ) {
      this.addSlider(references, output, id);
    }
    for (const id of ["injectedCurrent", "noiseLevel"]         ) {
      this.addSlider(references, cell, id);
    }
    for (const id of ["photoreceptorGain", "photoreceptorDecay", "photoreceptorRecovery"]         ) {
      this.addSlider(references, photo, id);
    }

    root.append(reading);
    this.element.append(root);
    this.updateParameters(references, getPreset(1));

    master.addEventListener("change", () => this.setSynapseEnabled(channel, master.checked));
    selector.addEventListener("change", () => this.selectPreset(channel, Number(selector.value)));
    directCurrent.addEventListener("change", () => this.setDirectCurrentEnabled(channel, directCurrent.checked));
    light.addEventListener("change", () => this.setLightEnabled(channel, light.checked));
  }

          subgroup(parent             , title        , accent                    )              {
    const group = element(this.owner, "section", "spk-synapses__subgroup");
    group.dataset.accent = accent;
    group.append(element(this.owner, "h4", "spk-synapses__subheading", title));
    parent.append(group);
    return group;
  }

          toggle(parent             , label        , accent                     )                   {
    const wrapper = element(this.owner, "label", "spk-controls__toggle-row");
    wrapper.dataset.accent = accent;
    const control = element(this.owner, "input", "spk-controls__toggle");
    control.type = "checkbox";
    control.setAttribute("aria-label", label);
    const visible = label.replace(/^Synapse [12] /, "");
    wrapper.append(control, element(this.owner, "span", "spk-controls__toggle-label", visible));
    parent.append(wrapper);
    return control;
  }

          addSlider(references                 , parent             , id                  )       {
    const specification = getSynapseControlSpecification(references.channel, id);
    const row = element(this.owner, "div", "spk-controls__control");
    row.dataset.control = id;
    row.dataset.synapse = references.channel;
    row.dataset.accent = specification.accent === "channel" ? references.channel : "cell";
    const header = element(this.owner, "div", "spk-controls__control-header");
    const target = element(this.owner, "label", "spk-controls__enable");
    const toggle = element(this.owner, "input", "spk-controls__toggle");
    toggle.type = "checkbox";
    toggle.checked = specification.enabledByDefault;
    toggle.setAttribute(
      "aria-label",
      "Enable Synapse " + channelNumber(references.channel) + " " + specification.label.toLowerCase(),
    );
    target.append(toggle);
    references.enabled.set(id, specification.enabledByDefault);

    const slider = element(this.owner, "input", "spk-controls__range");
    slider.type = "range";
    slider.id = this.instancePrefix + references.channel + "-" + id;
    slider.min = String(specification.minimum);
    slider.max = String(specification.maximum);
    slider.step = String(specification.step);
    slider.value = String(specification.defaultValue);
    slider.disabled = true;
    slider.setAttribute(
      "aria-label",
      "Synapse " + channelNumber(references.channel) + " " + specification.label + " (" + specification.unit + ")",
    );

    const label = element(this.owner, "label", "spk-controls__control-label", specification.label);
    label.htmlFor = slider.id;
    const output = element(this.owner, "output", "spk-controls__value");
    output.setAttribute("for", slider.id);
    header.append(target, label, output);

    const ticks = element(this.owner, "datalist", "spk-controls__ticks");
    ticks.id = slider.id + "-ticks";
    for (let value = specification.minimum; value <= specification.maximum; value += specification.tickInterval) {
      const option = element(this.owner, "option", "");
      option.value = String(value);
      ticks.append(option);
    }
    slider.setAttribute("list", ticks.id);
    row.append(header, slider, ticks);
    parent.append(row);

    const controls = { specification, row, toggle, slider, output };
    references.controls.set(id, controls);
    this.updateSlider(references, controls, specification.defaultValue);

    toggle.addEventListener("change", () => this.setControlEnabled(references.channel, id, toggle.checked));
    slider.addEventListener("input", () => this.setControlValue(references.channel, id, Number(slider.value)));
  }

          updateSlider(references                 , controls                       , value        )       {
    controls.output.textContent = formatSynapseControlValue(references.channel, controls.specification.id, value);
    const percent =
      ((value - controls.specification.minimum) /
        (controls.specification.maximum - controls.specification.minimum)) *
      100;
    controls.slider.style.setProperty("--spk-fill", percent + "%");

    let description = controls.output.textContent;
    if (controls.specification.id === "decay") {
      const time = synapticTimeConstantMs(value);
      const detail = Number.isFinite(time) ? "τ " + time.toFixed(2) + " ms" : "no decay";
      controls.output.setAttribute("title", detail);
      description += "; " + detail;
    }
    controls.slider.setAttribute("aria-valuetext", description);
  }

          updateParameters(references                 , preset              )       {
    references.parameters.replaceChildren();
    for (const [label, value, unit] of [
      ["a", preset.a, ""],
      ["b", preset.b, ""],
      ["c", preset.c, "mV"],
      ["d", preset.d, ""],
      ["Vrest", preset.restingPotential, "mV"],
    ]         ) {
      references.parameters.append(
        element(this.owner, "dt", "spk-controls__parameter-name", label),
        element(
          this.owner,
          "dd",
          "spk-controls__parameter-value",
          String(value).replace("-", "−") + (unit ? " " + unit : ""),
        ),
      );
    }
  }

          controlPatch(id                  , value        )               {
    switch (id) {
      case "gain": return { gain: value };
      case "decay": return { decaySlider: value };
      case "injectedCurrent": return { patchCurrent: value };
      case "noiseLevel": return { noiseLevel: value };
      case "photoreceptorGain": return { photoreceptor: { gain: value } };
      case "photoreceptorDecay": return { photoreceptor: { decaySlider: value } };
      case "photoreceptorRecovery": return { photoreceptor: { recoverySlider: value } };
    }
  }

          controlValue(id                  , controls                 )         {
    switch (id) {
      case "gain": return controls.gain;
      case "decay": return controls.decaySlider;
      case "injectedCurrent": return controls.patchCurrent;
      case "noiseLevel": return controls.noiseLevel;
      case "photoreceptorGain": return controls.photoreceptor.gain;
      case "photoreceptorDecay": return controls.photoreceptor.decaySlider;
      case "photoreceptorRecovery": return controls.photoreceptor.recoverySlider;
    }
  }

          applyPatch(channel           , patch              )       {
    this.error.textContent = "";
    const update                = channel === "synapse1" ? { synapse1: patch } : { synapse2: patch };
    this.source.updateControls(update);
  }

          requireActive(channel           , action        )       {
    if (!this.current[validateSynapseId(channel)].enabled) {
      throw new RangeError("Enable Synapse " + channelNumber(channel) + " before " + action + ".");
    }
  }

          channel(channel           )                  {
    return this.channels.get(validateSynapseId(channel)) ;
  }

          handleSnapshot(snapshot                )       {
    if (snapshot.stepIndex === 0) {
      this.latestSample = undefined;
    }
    this.synchronise(snapshot.controls, false);
  }

          handleSamples(samples                             )       {
    if (samples.length === 0) {
      return;
    }
    this.latestSample = samples[samples.length - 1];
    for (const channel of SYNAPSE_IDS) {
      this.updateReading(this.channel(channel));
    }
  }

          synchronise(controls                    , initialise         )       {
    const previous = this.current;
    this.current = structuredClone(controls);

    for (const channel of SYNAPSE_IDS) {
      const references = this.channel(channel);
      const state = controls[channel];
      references.master.checked = state.enabled;
      references.element.dataset.active = String(state.enabled);
      references.selector.value = String(state.presetId);
      references.directCurrent.checked = state.directCurrentEnabled;
      references.light.checked = state.lightEnabled;
      this.updateParameters(references, getPreset(state.presetId));

      for (const specification of SYNAPSE_CONTROL_SPECIFICATIONS[channel]) {
        const slider = references.controls.get(specification.id) ;
        const value = this.controlValue(specification.id, state);
        if (!initialise && value !== specification.defaultValue) {
          references.enabled.set(specification.id, true);
        }
        slider.toggle.checked = references.enabled.get(specification.id) ?? false;
        slider.slider.value = String(value);
        this.updateSlider(references, slider, value);
      }

      this.updateAvailability(references);
      this.updateReading(references);
      if (!initialise && previous[channel].enabled !== state.enabled) {
        this.updateTraces(channel, state.enabled);
      }
    }
  }

          updateAvailability(references                 )       {
    const state = this.current[references.channel];
    references.directCurrent.disabled = !state.enabled;
    references.light.disabled = !state.enabled;

    for (const [id, controls] of references.controls) {
      const available = independentControl(id) || (state.enabled && (!photoControl(id) || state.lightEnabled));
      controls.toggle.disabled = !available;
      controls.slider.disabled = !available || !(references.enabled.get(id) ?? false);
      controls.row.dataset.disabled = String(controls.slider.disabled);
    }
  }

          updateReading(references                 )       {
    if (!this.current[references.channel].enabled) {
      references.reading.textContent = "Inactive · output 0.0 a.u.";
      return;
    }

    if (this.latestSample === undefined) {
      references.reading.textContent = "Ready · Vm — mV · output 0.0 a.u.";
      return;
    }

    const first = references.channel === "synapse1";
    const potential = first ? this.latestSample.synapse1Vm : this.latestSample.synapse2Vm;
    const current = first ? this.latestSample.synapse1Current : this.latestSample.synapse2Current;
    references.reading.textContent =
      "Vm " + scientificNumber(potential) + " mV · output " + scientificNumber(current, 2) + " a.u.";
  }

          updateTraces(channel           , visible         )       {
    if (this.options.autoShowTraces === false || this.options.oscilloscope === undefined) {
      return;
    }
    const voltage = channel === "synapse1" ? "synapse1Vm" : "synapse2Vm";
    const current = channel === "synapse1" ? "synapse1Current" : "synapse2Current";
    this.options.oscilloscope.setTraceVisible(voltage, visible);
    this.options.oscilloscope.setTraceVisible(current, visible);
  }

          showError(failure         )       {
    this.error.textContent =
      failure instanceof Error ? failure.message : "The synapse controls encountered an unexpected error.";
  }
}

__spkExports.SpikelingSynapseControls = SpikelingSynapseControls;

},
"src/controls/synapse-specifications.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { TIMESTEP_MS } = __spkRequire("src/model/izhikevich.ts");
const { gaussianNoiseStandardDeviation, photoreceptorDecayRate, photoreceptorRecoveryRate } = __spkRequire("src/controls/specifications.ts");

                                                

                              
          
           
                     
                
                       
                        
                            

                                                      

                                              
                                
                                 
                         
                           
                           
                        
                                
                                
                                     
                                        
                        
 

const SYNAPSE_IDS                       = Object.freeze(["synapse1", "synapse2"]);

function specificationsFor(channel           )                                         {
  const number = channel === "synapse1" ? "1" : "2";
  const prefix = "Emulator_Syn" + number + "_";
  const synapsePrefix = "Emulator_Synapse" + number + "_";

  return Object.freeze([
    {
      id: "gain",
      desktopWidget: synapsePrefix + "slider",
      label: "Synaptic gain",
      minimum: -100,
      maximum: 100,
      step: 1,
      tickInterval: 20,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "channel",
      unit: "%",
    },
    {
      id: "decay",
      desktopWidget: synapsePrefix + "Decay_slider",
      label: "Synaptic decay",
      minimum: 975,
      maximum: 1000,
      step: 1,
      tickInterval: 2,
      defaultValue: channel === "synapse1" ? 995 : 990,
      enabledByDefault: false,
      accent: "channel",
      unit: "retention / step",
    },
    {
      id: "injectedCurrent",
      desktopWidget: prefix + "PatchClamp_slider",
      label: "Injected current",
      minimum: -50,
      maximum: 50,
      step: 1,
      tickInterval: 10,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "cell",
      unit: "a.u.",
    },
    {
      id: "noiseLevel",
      desktopWidget: prefix + "Noise_slider",
      label: "Noise level",
      minimum: 0,
      maximum: 100,
      step: 1,
      tickInterval: 10,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "cell",
      unit: "%",
    },
    {
      id: "photoreceptorGain",
      desktopWidget: prefix + "PR_PhotoGain_slider",
      label: "Photo-gain",
      minimum: -100,
      maximum: 100,
      step: 1,
      tickInterval: 20,
      defaultValue: 0,
      enabledByDefault: false,
      accent: "cell",
      unit: "%",
    },
    {
      id: "photoreceptorDecay",
      desktopWidget: prefix + "PR_Decay_slider",
      label: "Photo decay λ",
      minimum: 10,
      maximum: 125,
      step: 1,
      tickInterval: 10,
      defaultValue: 100,
      enabledByDefault: false,
      accent: "cell",
      unit: "ms⁻¹",
    },
    {
      id: "photoreceptorRecovery",
      desktopWidget: prefix + "PR_Recovery_slider",
      label: "Photo recovery λ",
      minimum: 1,
      maximum: 100,
      step: 1,
      tickInterval: 10,
      defaultValue: 25,
      enabledByDefault: false,
      accent: "cell",
      unit: "ms⁻¹",
    },
  ]         );
}

/** Source-pinned desktop controls; auxiliary patch range intentionally fixes Qt's 0..100 defect. */
const SYNAPSE_CONTROL_SPECIFICATIONS           
                                                           
  = Object.freeze({
  synapse1: specificationsFor("synapse1"),
  synapse2: specificationsFor("synapse2"),
});

function validateSynapseId(channel           )            {
  if (channel !== "synapse1" && channel !== "synapse2") {
    throw new RangeError("Unknown Spikeling synapse: " + String(channel));
  }
  return channel;
}

function getSynapseControlSpecification(
  channel           ,
  id                  ,
)                              {
  const specifications = SYNAPSE_CONTROL_SPECIFICATIONS[validateSynapseId(channel)];
  const specification = specifications.find((candidate) => candidate.id === id);
  if (specification === undefined) {
    throw new RangeError("Unknown synapse control: " + String(id));
  }
  return specification;
}

function validateSynapseControlValue(
  channel           ,
  id                  ,
  value        ,
)         {
  const specification = getSynapseControlSpecification(channel, id);
  if (
    !Number.isInteger(value) ||
    value < specification.minimum ||
    value > specification.maximum
  ) {
    throw new RangeError(
      specification.label +
        " must be an integer from " +
        specification.minimum +
        " to " +
        specification.maximum +
        ".",
    );
  }
  return value;
}

/** Actual dimensionless fraction of synaptic current retained per 0.1 ms step. */
function synapticRetentionFactor(slider        )         {
  return validateSynapseControlValue("synapse1", "decay", slider) / 1_000;
}

/** Equivalent exponential time constant; a retention factor of one never decays. */
function synapticTimeConstantMs(slider        )         {
  const retained = synapticRetentionFactor(slider);
  return retained === 1 ? Number.POSITIVE_INFINITY : -TIMESTEP_MS / Math.log(retained);
}

function formatSynapseControlValue(
  channel           ,
  id                  ,
  slider        ,
)         {
  validateSynapseControlValue(channel, id, slider);
  switch (id) {
    case "gain":
    case "photoreceptorGain":
      return slider + "%";
    case "decay":
      return synapticRetentionFactor(slider).toFixed(3) + " / step";
    case "injectedCurrent":
      return slider + " a.u.";
    case "noiseLevel":
      return slider + "% · σ " + gaussianNoiseStandardDeviation(slider) + " a.u.";
    case "photoreceptorDecay":
      return photoreceptorDecayRate(slider) + " ms⁻¹";
    case "photoreceptorRecovery":
      return photoreceptorRecoveryRate(slider) + " ms⁻¹";
  }
}

__spkExports.SYNAPSE_IDS = SYNAPSE_IDS;
__spkExports.SYNAPSE_CONTROL_SPECIFICATIONS = SYNAPSE_CONTROL_SPECIFICATIONS;
__spkExports.validateSynapseId = validateSynapseId;
__spkExports.getSynapseControlSpecification = getSynapseControlSpecification;
__spkExports.validateSynapseControlValue = validateSynapseControlValue;
__spkExports.synapticRetentionFactor = synapticRetentionFactor;
__spkExports.synapticTimeConstantMs = synapticTimeConstantMs;
__spkExports.formatSynapseControlValue = formatSynapseControlValue;

},
"src/recording/recorder.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                                            
const { TIMESTEP_MS } = __spkRequire("src/model/izhikevich.ts");
                                                          
                                                                                     
const { DEFAULT_RECORDING_MAX_SAMPLES, DESKTOP_RECORDING_COLUMNS, MAX_RECORDING_FILE_BYTES, RECORDING_SAMPLE_RATE_HZ, parseRecordingCsv, parseRecordingFile, recordingLimit, serialiseRecordingCsv } = __spkRequire("src/recording/csv.ts");
                                                                    

const RECORDING_CHUNK_SAMPLES = 1_024;
                                                                           
                                                  

                                    
                                         
                                   
                               
                              
                                  
                                
                              
                                    
                                          
                                         
                                                       
                                                                
                                        
                                     
 

                                   
                               
                             
                                 
 

                                                                      
const WIDTH = DESKTOP_RECORDING_COLUMNS.length;

/** Lazily allocated Float64 chunks; a full recording stops instead of overwriting. */
class RecordingBuffer {
           capacity        ;
           chunkSamples        ;
                   chunks                 = [];
          count = 0;

  constructor(capacity = DEFAULT_RECORDING_MAX_SAMPLES, chunkSamples = RECORDING_CHUNK_SAMPLES) {
    this.capacity = recordingLimit(capacity, DEFAULT_RECORDING_MAX_SAMPLES, "Recording capacity");
    this.chunkSamples = recordingLimit(chunkSamples, RECORDING_CHUNK_SAMPLES, "Recording chunk size");
  }

  get length()         { return this.count; }
  get allocatedBytes()         { return this.chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0); }
  get maximumBytes()         { return this.capacity * WIDTH * Float64Array.BYTES_PER_ELEMENT; }

  push(sample                 )          {
    if (this.count === this.capacity) return false;
    for (const column of DESKTOP_RECORDING_COLUMNS) {
      if (!Number.isFinite(sample[column.field])) {
        throw new RangeError("Recorded scientific values must be finite.");
      }
    }
    if (sample.trigger !== 0 && sample.trigger !== 1) {
      throw new RangeError("Recorded trigger values must be zero or one.");
    }
    const chunkIndex = Math.floor(this.count / this.chunkSamples);
    let chunk = this.chunks[chunkIndex];
    if (chunk === undefined) {
      const size = Math.min(this.chunkSamples, this.capacity - chunkIndex * this.chunkSamples);
      chunk = new Float64Array(size * WIDTH);
      this.chunks.push(chunk);
    }
    const offset = (this.count % this.chunkSamples) * WIDTH;
    for (let index = 0; index < WIDTH; index += 1) {
      chunk[offset + index] = sample[DESKTOP_RECORDING_COLUMNS[index].field];
    }
    this.count += 1;
    return true;
  }

  at(index        )                              {
    if (!Number.isInteger(index)) throw new RangeError("A recording index must be an integer.");
    const actual = index < 0 ? this.count + index : index;
    if (actual < 0 || actual >= this.count) return undefined;
    const chunk = this.chunks[Math.floor(actual / this.chunkSamples)];
    const offset = (actual % this.chunkSamples) * WIDTH;
    return {
      timeMs: chunk[offset],
      mainVm: chunk[offset + 1],
      stimulus: chunk[offset + 2],
      totalCurrent: chunk[offset + 3],
      synapse1Vm: chunk[offset + 4],
      synapse1Current: chunk[offset + 5],
      synapse2Vm: chunk[offset + 6],
      synapse2Current: chunk[offset + 7],
      trigger: chunk[offset + 8]         ,
    };
  }

  samples()                    {
    return Array.from({ length: this.count }, (_, index) => this.at(index) );
  }

  clear()       {
    this.chunks.length = 0;
    this.count = 0;
  }
}

/** A display-independent scientific consumer of the existing DataSource seam. */
class SpikelingRecorder {
           buffer                 ;
                   maxBytes        ;
                   listeners = new Set                   ();
                   subscriptions                = [];
          lifecycle                     = "idle";
          origin                  = "live";
          filename                    ;
          error                    ;
          sourceSnapshot                            ;
          lastSourceTime                    ;
          disposed = false;

  constructor(source            , options                   = {}) {
    this.buffer = new RecordingBuffer(options.maxSamples, options.chunkSamples);
    this.maxBytes = recordingLimit(options.maxBytes, MAX_RECORDING_FILE_BYTES, "Recording file-size limit");
    this.subscriptions.push(
      source.subscribe((samples) => this.handleSamples(samples)),
      source.subscribeState((snapshot) => this.handleSourceState(snapshot)),
      source.subscribeErrors((error) => this.handleSourceError(error)),
    );
  }

  getSnapshot()                    {
    return {
      lifecycle: this.lifecycle,
      origin: this.origin,
      sampleCount: this.buffer.length,
      maxSamples: this.buffer.capacity,
      allocatedBytes: this.buffer.allocatedBytes,
      maximumBytes: this.buffer.maximumBytes,
      durationMs: this.buffer.length * TIMESTEP_MS,
      sampleIntervalMs: TIMESTEP_MS,
      scientificSampleRateHz: RECORDING_SAMPLE_RATE_HZ,
      recordingSampleRateHz: RECORDING_SAMPLE_RATE_HZ,
      wallClockStepsPerSecond: this.sourceSnapshot?.speed.stepsPerSecond,
      simulationLifecycle: this.sourceSnapshot?.lifecycle,
      filename: this.filename,
      error: this.error,
    };
  }

  subscribe(listener                   )              {
    this.requireActive();
    this.listeners.add(listener);
    listener(this.getSnapshot());
    return () => this.listeners.delete(listener);
  }

  start()       {
    this.requireActive();
    if (this.lifecycle === "recording") return;
    this.buffer.clear();
    this.origin = "live";
    this.filename = undefined;
    this.error = undefined;
    this.lastSourceTime = undefined;
    this.lifecycle = "recording";
    this.publish();
  }

  stop()       {
    this.requireActive();
    if (this.lifecycle !== "recording") return;
    this.lifecycle = "stopped";
    this.publish();
  }

  clear()       {
    this.requireActive();
    this.buffer.clear();
    this.lifecycle = "idle";
    this.origin = "live";
    this.filename = undefined;
    this.error = undefined;
    this.lastSourceTime = undefined;
    this.publish();
  }

  samples()                    { return this.buffer.samples(); }

  exportCsv()         {
    this.requireActive();
    if (this.lifecycle === "recording") {
      throw new Error("Stop recording before exporting the scientific samples.");
    }
    return serialiseRecordingCsv(this.buffer.samples());
  }

  importCsv(content        , filename         )       {
    this.requireActive();
    if (this.lifecycle === "recording") {
      throw new Error("Stop recording before importing another recording.");
    }
    const parsed = parseRecordingCsv(content, { maxSamples: this.buffer.capacity, maxBytes: this.maxBytes });
    this.replaceImported(parsed.samples, filename);
  }

  async importFile(file                    )                {
    this.requireActive();
    if (this.lifecycle === "recording") {
      throw new Error("Stop recording before importing another recording.");
    }
    const parsed = await parseRecordingFile(file, { maxSamples: this.buffer.capacity, maxBytes: this.maxBytes });
    this.requireActive();
    if (this.lifecycle === "recording") {
      throw new Error("Stop recording before importing another recording.");
    }
    this.replaceImported(parsed.samples, file.name);
  }

  dispose()       {
    if (this.disposed) return;
    this.disposed = true;
    for (const unsubscribe of this.subscriptions) unsubscribe();
    this.listeners.clear();
    this.buffer.clear();
  }

          replaceImported(samples                            , filename         )       {
    this.buffer.clear();
    for (const sample of samples) this.buffer.push(sample);
    this.lifecycle = "stopped";
    this.origin = "imported";
    this.filename = filename;
    this.error = undefined;
    this.lastSourceTime = undefined;
    this.publish();
  }

          handleSamples(samples                             )       {
    if (this.lifecycle !== "recording" || samples.length === 0) return;
    for (const sample of samples) {
      if (this.lastSourceTime !== undefined && Math.abs(sample.timeMs - this.lastSourceTime - TIMESTEP_MS) > 1e-8) {
        this.error = "The simulation sample stream was discontinuous; recording stopped without inventing samples.";
        this.lifecycle = "stopped";
        break;
      }
      const recorded                  = {
        timeMs: this.buffer.length * TIMESTEP_MS,
        mainVm: sample.mainVm,
        stimulus: sample.stimulus,
        totalCurrent: sample.totalCurrent,
        synapse1Vm: sample.synapse1Vm,
        synapse1Current: sample.synapse1Current,
        synapse2Vm: sample.synapse2Vm,
        synapse2Current: sample.synapse2Current,
        trigger: sample.trigger,
      };
      this.buffer.push(recorded);
      this.lastSourceTime = sample.timeMs;
      if (this.buffer.length === this.buffer.capacity) {
        this.lifecycle = "full";
        break;
      }
    }
    this.publish();
  }

          handleSourceState(snapshot                )       {
    const reset = this.sourceSnapshot !== undefined && snapshot.stepIndex === 0 && this.buffer.length > 0;
    this.sourceSnapshot = snapshot;
    if (this.lifecycle === "recording" && (snapshot.lifecycle === "stopped" || reset)) {
      this.lifecycle = "stopped";
    }
    this.publish();
  }

          handleSourceError(error       )       {
    this.error = error.message;
    if (this.lifecycle === "recording") this.lifecycle = "stopped";
    this.publish();
  }

          publish()       {
    const snapshot = this.getSnapshot();
    for (const listener of this.listeners) listener(snapshot);
  }

          requireActive()       {
    if (this.disposed) throw new Error("The scientific recorder has been disposed.");
  }
}

__spkExports.RECORDING_CHUNK_SAMPLES = RECORDING_CHUNK_SAMPLES;
__spkExports.RecordingBuffer = RecordingBuffer;
__spkExports.SpikelingRecorder = SpikelingRecorder;

},
"src/recording/csv.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { TIMESTEP_MS } = __spkRequire("src/model/izhikevich.ts");
                                                          

/** Exact names and order emitted by the desktop Graph_Emulator.SavePlotData. */
const DESKTOP_RECORDING_COLUMNS = [
  { header: "Time (ms)", field: "timeMs" },
  { header: "Spikeling Vm (mV)", field: "mainVm" },
  { header: "Stimulus (%)", field: "stimulus" },
  { header: "Total Current Input (a.u.)", field: "totalCurrent" },
  { header: "Synapse 1 Vm (mV)", field: "synapse1Vm" },
  { header: "Synapse 1 Input (a.u.)", field: "synapse1Current" },
  { header: "Synapse 2 Vm (mV)", field: "synapse2Vm" },
  { header: "Synapse 2 Input (a.u.)", field: "synapse2Current" },
  { header: "Trigger", field: "trigger" },
]                                                                                    ;

const RECORDING_SAMPLE_RATE_HZ = 1_000 / TIMESTEP_MS;
const DEFAULT_RECORDING_MAX_SAMPLES = 250_000;
const MAX_RECORDING_FILE_BYTES = 64 * 1_024 * 1_024;

                                                                                 
                                                                     
                                
               
               
                
                   
                    
                      
                   
                    
                     
                       
                     
                   

class RecordingError extends Error {
           code                    ;
           line                    ;

  constructor(code                    , message        , line         ) {
    super(message);
    this.name = "RecordingError";
    this.code = code;
    this.line = line;
  }
}

                                      
                             
                               
 

                                  
                                               
                                    
                              
 

                                     
                        
                        
                          
 

const NUMBER_PATTERN = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;

function recordingLimit(value                    , fallback        , name        )         {
  const limit = value ?? fallback;
  if (!Number.isSafeInteger(limit) || limit < 1) {
    throw new RangeError(name + " must be a positive safe integer.");
  }
  return limit;
}

function readRows(content        , visit                                          )       {
  let fields           = [];
  let field = "";
  let line = 1;
  let rowLine = 1;
  let quoted = false;
  let closed = false;

  function finish()       {
    fields.push(field.trim());
    if (fields.some((value) => value.length > 0)) {
      visit(fields, rowLine);
    }
    fields = [];
    field = "";
    closed = false;
  }

  for (let index = 0; index < content.length; index += 1) {
    const character = content[index];
    if (quoted) {
      if (character === '"') {
        if (content[index + 1] === '"') {
          field += '"';
          index += 1;
        } else {
          quoted = false;
          closed = true;
        }
      } else {
        if (character === "\n") line += 1;
        field += character;
      }
      continue;
    }
    if (character === '"') {
      if (field.trim().length > 0 || closed) {
        throw new RecordingError("malformed-csv", "Unexpected quotation mark in recording CSV.", line);
      }
      field = "";
      quoted = true;
    } else if (character === ",") {
      fields.push(field.trim());
      field = "";
      closed = false;
    } else if (character === "\n" || character === "\r") {
      finish();
      if (character === "\r" && content[index + 1] === "\n") index += 1;
      line += 1;
      rowLine = line;
    } else if (closed && !/\s/.test(character)) {
      throw new RecordingError("malformed-csv", "Unexpected text after a quoted recording field.", line);
    } else if (!closed) {
      field += character;
    }
  }

  if (quoted) {
    throw new RecordingError("malformed-csv", "Unterminated quoted field in recording CSV.", rowLine);
  }
  if (field.length > 0 || fields.length > 0 || closed) finish();
}

function numeric(value        , line        , header        )         {
  if (!NUMBER_PATTERN.test(value)) {
    throw new RecordingError("invalid-sample", header + " must contain a finite number.", line);
  }
  const number = Number(value);
  if (!Number.isFinite(number)) {
    throw new RecordingError("invalid-sample", header + " must contain a finite number.", line);
  }
  return number;
}

/** Parse source-pinned desktop files without accepting invented or missing signals. */
function parseRecordingCsv(content        , options                      = {})                  {
  const maxBytes = recordingLimit(options.maxBytes, MAX_RECORDING_FILE_BYTES, "Recording file-size limit");
  const maxSamples = recordingLimit(options.maxSamples, DEFAULT_RECORDING_MAX_SAMPLES, "Recording sample limit");
  if (new TextEncoder().encode(content).byteLength > maxBytes) {
    throw new RecordingError("file-size", "Recording CSV exceeds its configured file-size limit.");
  }
  if (content.trim().length === 0) {
    throw new RecordingError("empty-file", "Recording CSV is empty.");
  }

  const samples                    = [];
  let indices                      ;
  readRows(content.replace(/^\uFEFF/, ""), (fields, line) => {
    if (indices === undefined) {
      if (new Set(fields).size !== fields.length) {
        throw new RecordingError("duplicate-column", "Recording CSV contains duplicate column names.", line);
      }
      const expected = DESKTOP_RECORDING_COLUMNS.map((column) => column.header);
      if (fields.length !== expected.length || fields.some((header) => !expected.includes(header                           ))) {
        throw new RecordingError("invalid-header", "Recording CSV must contain all nine exact desktop signal columns.", line);
      }
      indices = expected.map((header) => fields.indexOf(header));
      return;
    }

    if (fields.length !== DESKTOP_RECORDING_COLUMNS.length) {
      throw new RecordingError("malformed-csv", "Recording CSV row has an incorrect number of columns.", line);
    }
    if (samples.length >= maxSamples) {
      throw new RecordingError("sample-limit", "Recording CSV exceeds its configured sample limit.", line);
    }
    const values = DESKTOP_RECORDING_COLUMNS.map((column, index) => numeric(fields[indices [index]], line, column.header));
    const timeMs = values[0];
    if (timeMs < 0) {
      throw new RecordingError("invalid-timestamp", "Recording timestamps must be non-negative.", line);
    }
    if (samples.length > 0 && Math.abs(timeMs - samples[samples.length - 1].timeMs - TIMESTEP_MS) > 1e-8) {
      throw new RecordingError("sample-interval", "Recording samples must be exactly 0.1 ms apart.", line);
    }
    const trigger = values[8];
    if (trigger !== 0 && trigger !== 1) {
      throw new RecordingError("invalid-trigger", "Recording trigger values must be zero or one.", line);
    }
    samples.push({
      timeMs,
      mainVm: values[1],
      stimulus: values[2],
      totalCurrent: values[3],
      synapse1Vm: values[4],
      synapse1Current: values[5],
      synapse2Vm: values[6],
      synapse2Current: values[7],
      trigger,
    });
  });

  if (indices === undefined) {
    throw new RecordingError("empty-file", "Recording CSV has no header row.");
  }
  if (samples.length === 0) {
    throw new RecordingError("empty-samples", "Recording CSV contains no scientific samples.");
  }
  return { samples, sampleIntervalMs: TIMESTEP_MS, durationMs: samples.length * TIMESTEP_MS };
}

async function parseRecordingFile(file                    , options                      = {})                           {
  if (!/\.csv$/i.test(file.name)) {
    throw new RecordingError("file-type", "Select a recording with a .csv extension.");
  }
  const maxBytes = recordingLimit(options.maxBytes, MAX_RECORDING_FILE_BYTES, "Recording file-size limit");
  if (!Number.isSafeInteger(file.size) || file.size < 0 || file.size > maxBytes) {
    throw new RecordingError("file-size", "Recording CSV exceeds its configured file-size limit.");
  }
  return parseRecordingCsv(await file.text(), options);
}

/** ECMAScript's shortest Float64 representation round-trips without rounding. */
function serialiseRecordingCsv(samples                            )         {
  if (samples.length === 0) {
    throw new RecordingError("empty-samples", "There are no recorded scientific samples to export.");
  }
  const lines = [DESKTOP_RECORDING_COLUMNS.map((column) => column.header).join(",")];
  for (const sample of samples) {
    const fields = DESKTOP_RECORDING_COLUMNS.map((column) => {
      const value = sample[column.field];
      if (!Number.isFinite(value)) {
        throw new RecordingError("invalid-sample", column.header + " must contain a finite number.");
      }
      if (column.field === "trigger" && value !== 0 && value !== 1) {
        throw new RecordingError("invalid-trigger", "Recording trigger values must be zero or one.");
      }
      return String(value);
    });
    lines.push(fields.join(","));
  }
  return lines.join("\n") + "\n";
}

__spkExports.DESKTOP_RECORDING_COLUMNS = DESKTOP_RECORDING_COLUMNS;
__spkExports.RECORDING_SAMPLE_RATE_HZ = RECORDING_SAMPLE_RATE_HZ;
__spkExports.DEFAULT_RECORDING_MAX_SAMPLES = DEFAULT_RECORDING_MAX_SAMPLES;
__spkExports.MAX_RECORDING_FILE_BYTES = MAX_RECORDING_FILE_BYTES;
__spkExports.RecordingError = RecordingError;
__spkExports.recordingLimit = recordingLimit;
__spkExports.parseRecordingCsv = parseRecordingCsv;
__spkExports.parseRecordingFile = parseRecordingFile;
__spkExports.serialiseRecordingCsv = serialiseRecordingCsv;

},
"src/recording/recording-controls.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                                
                                                   
                                                       
const { SpikelingRecorder } = __spkRequire("src/recording/recorder.ts");

                                    
                            
                           
                            
 

                                           
                                                             
                            
 

function create                                       (
  owner          ,
  tag   ,
  className        ,
  text         ,
)                           {
  const node = owner.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function count(value        )         {
  return value.toLocaleString("en-GB");
}

/** Accessible, entirely local recording transport alongside the scientific scope. */
class SpikelingRecordingControls {
           element             ;
                   recorder                   ;
                   owner          ;
                   options                          ;
                   startButton                   ;
                   stopButton                   ;
                   downloadButton                   ;
                   clearButton                   ;
                   input                  ;
                   status             ;
                   statistics             ;
                   rates             ;
                   progress                     ;
                   error             ;
          unsubscribe                         ;
          disposed = false;

  constructor(host             , recorder                   , options                           = {}) {
    this.owner = host.ownerDocument;
    this.recorder = recorder;
    this.options = options;
    this.element = create(this.owner, "section", "spk-controls spk-recording");
    this.element.setAttribute("aria-label", "Scientific recording and local CSV files");

    const heading = create(this.owner, "h2", "spk-recording__heading", "Scientific recording");
    this.status = create(this.owner, "p", "spk-recording__status");
    this.status.setAttribute("role", "status");
    this.status.setAttribute("aria-live", "polite");
    this.element.append(heading, this.status);

    const transport = create(this.owner, "div", "spk-recording__transport");
    transport.setAttribute("aria-label", "Recording transport controls");
    this.startButton = this.button("Start recording", "start");
    this.stopButton = this.button("Stop recording", "stop");
    this.downloadButton = this.button("Download CSV", "download");
    this.clearButton = this.button("Clear recording", "clear");
    transport.append(this.startButton, this.stopButton, this.downloadButton, this.clearButton);
    this.element.append(transport);

    const importLabel = create(this.owner, "label", "spk-recording__import", "Import desktop-compatible recording CSV");
    this.input = create(this.owner, "input", "spk-recording__file");
    this.input.type = "file";
    this.input.accept = ".csv,text/csv";
    this.input.setAttribute("aria-label", "Import recording CSV");
    importLabel.append(this.input);
    this.element.append(importLabel);

    this.progress = create(this.owner, "progress", "spk-recording__progress");
    this.progress.setAttribute("aria-label", "Recording capacity used");
    this.statistics = create(this.owner, "p", "spk-recording__statistics");
    this.statistics.setAttribute("aria-live", "off");
    this.rates = create(this.owner, "p", "spk-recording__rates");
    this.rates.setAttribute("aria-live", "off");
    this.error = create(this.owner, "p", "spk-recording__error");
    this.error.setAttribute("role", "alert");
    this.element.append(this.progress, this.statistics, this.rates, this.error);
    host.append(this.element);

    this.startButton.addEventListener("click", () => this.run(() => this.recorder.start()));
    this.stopButton.addEventListener("click", () => this.run(() => this.recorder.stop()));
    this.clearButton.addEventListener("click", () => this.run(() => this.recorder.clear()));
    this.downloadButton.addEventListener("click", () => this.run(() => this.download()));
    this.input.addEventListener("change", () => {
      const file = this.input.files?.[0];
      if (file !== undefined) void this.importFile(file);
    });
    this.unsubscribe = this.recorder.subscribe((snapshot) => this.synchronise(snapshot));
  }

  async importFile(file                    )                {
    this.error.textContent = "";
    try {
      await this.recorder.importFile(file);
    } catch (failure) {
      this.showError(failure);
    }
  }

  download()                    {
    const content = this.recorder.exportCsv();
    const now = (this.options.now ?? (() => new Date()))();
    const stamp = now.toISOString().replace(/[:.]/g, "-");
    const recording = {
      filename: "spikeling-recording-" + stamp + ".csv",
      content,
      mimeType: "text/csv;charset=utf-8",
    };
    if (this.options.download !== undefined) {
      this.options.download(recording);
    } else {
      const object = URL.createObjectURL(new Blob([content], { type: recording.mimeType }));
      const link = this.owner.createElement("a");
      link.href = object;
      link.download = recording.filename;
      link.click();
      setTimeout(() => URL.revokeObjectURL(object), 0);
    }
    return recording;
  }

  dispose()       {
    if (this.disposed) return;
    this.disposed = true;
    this.unsubscribe?.();
    this.element.remove();
  }

          button(label        , action        )                    {
    const button = create(this.owner, "button", "spk-recording__button", label);
    button.type = "button";
    button.dataset.action = action;
    button.setAttribute("aria-label", label);
    return button;
  }

          synchronise(snapshot                   )       {
    const active = snapshot.lifecycle === "recording";
    this.startButton.disabled = active;
    this.stopButton.disabled = !active;
    this.downloadButton.disabled = active || snapshot.sampleCount === 0;
    this.clearButton.disabled = !active && snapshot.lifecycle === "idle";
    this.input.disabled = active;
    this.progress.max = snapshot.maxSamples;
    this.progress.value = snapshot.sampleCount;

    if (snapshot.lifecycle === "full") {
      this.status.textContent = "Recording complete: capacity reached without overwriting samples.";
    } else if (active && snapshot.simulationLifecycle === "paused") {
      this.status.textContent = "Recording armed; simulation paused.";
    } else if (active) {
      this.status.textContent = "Recording every scientific simulation sample.";
    } else if (snapshot.origin === "imported") {
      this.status.textContent = "Imported " + (snapshot.filename ?? "desktop-compatible recording") + ".";
    } else if (snapshot.lifecycle === "stopped") {
      this.status.textContent = "Recording stopped; samples remain available locally.";
    } else {
      this.status.textContent = "Ready to record locally; no files are uploaded.";
    }

    this.statistics.textContent = count(snapshot.sampleCount) + " / " + count(snapshot.maxSamples)
      + " samples · " + count(snapshot.durationMs) + " ms of simulation time";
    const wallClock = snapshot.wallClockStepsPerSecond === undefined
      ? "waiting for simulation"
      : count(snapshot.wallClockStepsPerSecond) + " samples/s wall-clock target";
    this.rates.textContent = "Timestep " + snapshot.sampleIntervalMs + " ms · capture "
      + count(snapshot.recordingSampleRateHz) + " samples/s of simulation time · "
      + wallClock + " · display refresh independent";
    if (snapshot.error !== undefined) this.error.textContent = snapshot.error;
  }

          run(action            )       {
    this.error.textContent = "";
    try {
      action();
    } catch (failure) {
      this.showError(failure);
    }
  }

          showError(failure         )       {
    this.error.textContent = failure instanceof Error ? failure.message : "Unable to process the scientific recording.";
  }
}

__spkExports.SpikelingRecordingControls = SpikelingRecordingControls;

},
"src/simulation/speed.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const { TIMESTEP_MS } = __spkRequire("src/model/izhikevich.ts");

/** The existing desktop emulator advances its model every 50 wall-clock ms. */
const DESKTOP_UPDATE_INTERVAL_MS = 50;

/** Average model-step counts for the six supported 50 ms speed positions. */
const DESKTOP_STEPS_PER_UPDATE = [
  12.5, 25, 50, 125, 250, 500,
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
    throw new RangeError(
      "Simulation speed must be an integer between 0 and " +
        (DESKTOP_STEPS_PER_UPDATE.length - 1) + ".",
    );
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

},
"src/visualisation/oscilloscope.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                                            
const { TIMESTEP_MS } = __spkRequire("src/model/izhikevich.ts");
                                                          
                                                                
const { OscilloscopeCanvasRenderer } = __spkRequire("src/visualisation/canvas-renderer.ts");
                                                             
const { OscilloscopeRenderLoop } = __spkRequire("src/visualisation/render-loop.ts");
             
                          
                       
                          
const { OSCILLOSCOPE_TRACES, defaultVisibleTraces, getOscilloscopeTrace } = __spkRequire("src/visualisation/traces.ts");
                                              

                                        
                                  
                     
 

                                      
                             
                                                    
                                             
                                           
                                                                                   
 

function createElement                                       (
  owner          ,
  tag   ,
  className        ,
  text         ,
)                           {
  const element = owner.createElement(tag);
  element.className = className;
  if (text !== undefined) {
    element.textContent = text;
  }
  return element;
}

function formatReading(value                    )         {
  if (value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  return value.toFixed(1).replace("-", "−");
}

function lifecycleLabel(snapshot                            )         {
  const lifecycle = snapshot?.lifecycle ?? "idle";
  switch (lifecycle) {
    case "running":
      return "Running";
    case "paused":
      return "Paused";
    case "stopped":
      return "Stopped";
    default:
      return "Ready";
  }
}

/** Accessible desktop-matched instrument component backed only by DataSource. */
class SpikelingOscilloscope {
           element             ;
           canvas                   ;
           renderer                            ;
           renderLoop                        ;

                   source            ;
                   status             ;
                   readings             ;
                   traceInputs = new Map                              ();
                   visible = defaultVisibleTraces();
                   subscriptions                = [];
                   resizeObserver                                   ;
          latestSample                              ;
          currentSnapshot                            ;
          statistics                              ;
          disposed = false;

  constructor(host             , source            , options                      = {}) {
    const owner = host.ownerDocument;
    this.source = source;
    this.element = createElement(owner, "section", "spk-oscilloscope");
    this.element.setAttribute("aria-label", "Spikeling neuronal oscilloscope");

    const header = createElement(owner, "div", "spk-oscilloscope__header");
    const title = createElement(owner, "h2", "spk-oscilloscope__title", "Neuronal oscilloscope");
    this.status = createElement(owner, "span", "spk-oscilloscope__status", "Ready");
    this.status.setAttribute("role", "status");
    this.status.setAttribute("aria-live", "polite");
    header.append(title, this.status);

    this.canvas = createElement(owner, "canvas", "spk-oscilloscope__canvas");
    this.canvas.setAttribute("role", "img");
    this.canvas.setAttribute(
      "aria-label",
      "Rolling membrane potential and input current plotted against time.",
    );

    this.readings = createElement(owner, "p", "spk-oscilloscope__readings");
    this.readings.setAttribute("aria-live", "off");
    this.readings.setAttribute("aria-atomic", "true");

    const controls = createElement(owner, "fieldset", "spk-oscilloscope__traces");
    const legend = createElement(owner, "legend", "spk-oscilloscope__legend", "Visible traces");
    controls.append(legend);

    for (const trace of OSCILLOSCOPE_TRACES) {
      const label = createElement(owner, "label", "spk-oscilloscope__trace");
      label.style.setProperty("--spk-trace-colour", "var(" + trace.colourVariable + ")");
      const input = createElement(owner, "input", "spk-oscilloscope__trace-input");
      input.type = "checkbox";
      input.checked = this.visible.has(trace.id);
      input.setAttribute("aria-label", "Show " + trace.label.toLowerCase());
      input.addEventListener("change", () => {
        this.setTraceVisible(trace.id, input.checked);
      });
      const name = createElement(owner, "span", "spk-oscilloscope__trace-label", trace.label);
      label.append(input, name);
      controls.append(label);
      this.traceInputs.set(trace.id, input);
    }

    this.element.append(header, this.canvas, this.readings, controls);
    host.append(this.element);

    this.renderer = new OscilloscopeCanvasRenderer(this.canvas, {
      windowMs: options.windowMs,
      devicePixelRatio: options.devicePixelRatio,
    });
    this.renderLoop = new OscilloscopeRenderLoop(() => this.render(), {
      scheduler: options.frameScheduler,
      visibility:
        options.visibility ??
        (typeof owner.hidden === "boolean" ? (owner                        ) : undefined),
    });

    const observerFactory =
      options.resizeObserverFactory ??
      (typeof ResizeObserver === "undefined"
        ? undefined
        : (callback            ) => new ResizeObserver(callback));
    this.resizeObserver = observerFactory?.(() => this.resize());
    this.resizeObserver?.observe(this.canvas);

    this.subscriptions.push(
      source.subscribe((samples) => this.handleSamples(samples)),
      source.subscribeState((snapshot) => this.handleState(snapshot)),
    );
    this.updateReadings();
    this.render();
  }

  setTraceVisible(field            , visible         )       {
    getOscilloscopeTrace(field);
    if (visible) {
      this.visible.add(field);
    } else {
      this.visible.delete(field);
    }

    const input = this.traceInputs.get(field);
    if (input !== undefined) {
      input.checked = visible;
    }
    this.invalidate();
  }

  isTraceVisible(field            )          {
    getOscilloscopeTrace(field);
    return this.visible.has(field);
  }

  getStatistics()                               {
    return this.statistics;
  }

  resize()       {
    if (this.disposed) {
      return;
    }
    this.renderer.resize();
    this.invalidate();
  }

  dispose()       {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    this.renderLoop.dispose();
    this.resizeObserver?.disconnect();
    for (const unsubscribe of this.subscriptions) {
      unsubscribe();
    }
    this.element.remove();
  }

          handleSamples(samples                             )       {
    if (samples.length > 0) {
      this.latestSample = samples[samples.length - 1];
      this.updateReadings();
      this.renderLoop.invalidate();
    }
  }

          handleState(snapshot                )       {
    this.currentSnapshot = snapshot;
    this.status.textContent = lifecycleLabel(snapshot);
    this.status.dataset.state = snapshot.lifecycle;

    if (snapshot.stepIndex === 0) {
      this.latestSample = undefined;
      this.updateReadings();
    }

    if (snapshot.lifecycle === "running") {
      this.renderLoop.start();
    } else {
      this.renderLoop.stop();
      this.render();
    }
  }

          updateReadings()       {
    this.readings.textContent =
      lifecycleLabel(this.currentSnapshot) +
      " · Vm " +
      formatReading(this.latestSample?.mainVm) +
      " mV · Input " +
      formatReading(this.latestSample?.totalCurrent) +
      " a.u. · Stimulus " +
      formatReading(this.latestSample?.stimulus) +
      " a.u.";
  }

          invalidate()       {
    if (this.renderLoop.running) {
      this.renderLoop.invalidate();
    } else {
      this.render();
    }
  }

          render()       {
    const visibleSamples = Math.ceil(this.renderer.windowMs / TIMESTEP_MS) + 1;
    this.statistics = this.renderer.render(this.source.latest(visibleSamples), this.visible);
  }
}

__spkExports.SpikelingOscilloscope = SpikelingOscilloscope;

},
"src/visualisation/canvas-renderer.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                          
const { DESKTOP_CURRENT_RANGE, DESKTOP_TRACE_WIDTH_PX, DESKTOP_VISIBLE_WINDOW_MS, DESKTOP_VOLTAGE_RANGE, buildAxisTicks, calculatePlotLayout, formatAxisValue, projectX, projectY } = __spkRequire("src/visualisation/axes.ts");
                                                       
const { decimateTrace } = __spkRequire("src/visualisation/decimation.ts");
const { DEFAULT_OSCILLOSCOPE_THEME } = __spkRequire("src/visualisation/theme.ts");
                                                    
const { OSCILLOSCOPE_TRACES, getOscilloscopeTrace } = __spkRequire("src/visualisation/traces.ts");
                                                                 

                                         
                
                 
                                                                               
                                                             
 

                                              
                             
                                    
                                    
                                     
                                           
 

                                   
                                 
                                   
                                 
                         
                          
 

function validateRange(range           , label        )            {
  if (
    !Number.isFinite(range.minimum) ||
    !Number.isFinite(range.maximum) ||
    range.minimum >= range.maximum
  ) {
    throw new RangeError(label + " must have finite, increasing limits.");
  }
  return range;
}

/** Dual-axis, straight-segment Canvas oscilloscope; no spline interpolation. */
class OscilloscopeCanvasRenderer {
           windowMs        ;
           voltageRange           ;
           currentRange           ;

                   canvas                        ;
                   context                          ;
                   theme                   ;
                   getPixelRatio              ;
          layout            ;

  constructor(canvas                        , options                              = {}) {
    const context = canvas.getContext("2d");
    if (context === null) {
      throw new Error("The oscilloscope requires a 2D Canvas rendering context.");
    }

    this.windowMs = options.windowMs ?? DESKTOP_VISIBLE_WINDOW_MS;
    if (!Number.isFinite(this.windowMs) || this.windowMs <= 0) {
      throw new RangeError("The oscilloscope time window must be finite and positive.");
    }

    this.voltageRange = validateRange(
      options.voltageRange ?? DESKTOP_VOLTAGE_RANGE,
      "The voltage axis",
    );
    this.currentRange = validateRange(
      options.currentRange ?? DESKTOP_CURRENT_RANGE,
      "The current axis",
    );
    this.canvas = canvas;
    this.context = context;
    this.theme = options.theme ?? DEFAULT_OSCILLOSCOPE_THEME;
    this.getPixelRatio =
      options.devicePixelRatio ?? (() => globalThis.devicePixelRatio ?? 1);
    this.layout = calculatePlotLayout(1, 1);
    this.resize();
  }

  getLayout()             {
    return this.layout;
  }

  resize()             {
    const bounds = this.canvas.getBoundingClientRect();
    const width = Math.max(1, Math.round(bounds.width));
    const height = Math.max(1, Math.round(bounds.height));
    const suppliedRatio = this.getPixelRatio();
    const ratio = Number.isFinite(suppliedRatio) && suppliedRatio > 0 ? suppliedRatio : 1;
    this.canvas.width = Math.max(1, Math.round(width * ratio));
    this.canvas.height = Math.max(1, Math.round(height * ratio));
    this.context.setTransform(ratio, 0, 0, ratio, 0, 0);
    this.layout = calculatePlotLayout(width, height);
    return this.layout;
  }

  render(
    samples                             ,
    enabledTraces                         ,
  )                   {
    const context = this.context;
    const layout = this.layout;
    context.clearRect(0, 0, layout.width, layout.height);
    context.fillStyle = this.theme.background;
    context.fillRect(0, 0, layout.width, layout.height);
    this.drawAxes();

    let displayedPoints = 0;
    let enabled = 0;

    context.save();
    context.beginPath();
    context.rect(layout.left, layout.top, layout.plotWidth, layout.plotHeight);
    context.clip();

    for (const trace of OSCILLOSCOPE_TRACES) {
      if (!enabledTraces.has(trace.id)) {
        continue;
      }
      enabled += 1;
      displayedPoints += this.drawTrace(samples, trace);
    }

    context.restore();

    return {
      sourceSamples: samples.length,
      displayedPoints,
      enabledTraces: enabled,
      width: layout.width,
      height: layout.height,
    };
  }

  traceColour(field            )         {
    return getOscilloscopeTrace(field).colour;
  }

          drawAxes()       {
    const context = this.context;
    const layout = this.layout;
    const xTicks = buildAxisTicks({ minimum: -this.windowMs, maximum: 0 }, this.windowMs / 5);
    const voltageTicks = buildAxisTicks(this.voltageRange, 30);
    const currentTicks = buildAxisTicks(this.currentRange, 50);

    context.lineWidth = 1;
    context.strokeStyle = this.theme.grid;
    context.fillStyle = this.theme.muted;
    context.font = layout.compact
      ? "11px system-ui, sans-serif"
      : "12px system-ui, sans-serif";

    for (const tick of xTicks) {
      const x = projectX(tick, this.windowMs, layout);
      context.beginPath();
      context.moveTo(x, layout.top);
      context.lineTo(x, layout.top + layout.plotHeight);
      context.stroke();
      context.textAlign = "center";
      context.textBaseline = "top";
      context.fillText(formatAxisValue(tick), x, layout.top + layout.plotHeight + 8);
    }

    for (const tick of voltageTicks) {
      const y = projectY(tick, this.voltageRange, layout);
      context.beginPath();
      context.moveTo(layout.left, y);
      context.lineTo(layout.left + layout.plotWidth, y);
      context.stroke();
      context.textAlign = "right";
      context.textBaseline = "middle";
      context.fillText(formatAxisValue(tick), layout.left - 8, y);
    }

    for (const tick of currentTicks) {
      const y = projectY(tick, this.currentRange, layout);
      context.textAlign = "left";
      context.textBaseline = "middle";
      context.fillText(formatAxisValue(tick), layout.left + layout.plotWidth + 8, y);
    }

    context.fillStyle = this.theme.text;
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(
      "Time (ms)",
      layout.left + layout.plotWidth / 2,
      layout.height - (layout.compact ? 10 : 14),
    );

    context.save();
    context.translate(layout.compact ? 12 : 16, layout.top + layout.plotHeight / 2);
    context.rotate(-Math.PI / 2);
    context.fillText(layout.compact ? "Vm (mV)" : "Membrane potential (mV)", 0, 0);
    context.restore();

    context.save();
    context.translate(
      layout.width - (layout.compact ? 10 : 14),
      layout.top + layout.plotHeight / 2,
    );
    context.rotate(Math.PI / 2);
    context.fillText(layout.compact ? "I (a.u.)" : "Current input (a.u.)", 0, 0);
    context.restore();
  }

          drawTrace(samples                             , trace                   )         {
    const points = decimateTrace(samples, {
      field: trace.id,
      pixelWidth: this.layout.plotWidth,
      windowMs: this.windowMs,
    });

    if (points.length === 0) {
      return 0;
    }

    const range = trace.axis === "voltage" ? this.voltageRange : this.currentRange;
    const context = this.context;
    context.strokeStyle = trace.colour;
    context.lineWidth = DESKTOP_TRACE_WIDTH_PX;
    context.beginPath();

    for (let index = 0; index < points.length; index += 1) {
      const point = points[index];
      const x = projectX(point.relativeTimeMs, this.windowMs, this.layout);
      const y = projectY(point.value, range, this.layout);
      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    }

    context.stroke();
    return points.length;
  }
}

__spkExports.OscilloscopeCanvasRenderer = OscilloscopeCanvasRenderer;

},
"src/visualisation/axes.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

const DESKTOP_VISIBLE_WINDOW_MS = 500;
const DESKTOP_VOLTAGE_MIN_MV = -90;
const DESKTOP_VOLTAGE_MAX_MV = 30;
const DESKTOP_CURRENT_MIN = -100;
const DESKTOP_CURRENT_MAX = 100;
const DESKTOP_TRACE_WIDTH_PX = 1;

                            
                           
                           
 

                             
                         
                          
                        
                         
                       
                          
                             
                              
                            
 

const DESKTOP_VOLTAGE_RANGE            = Object.freeze({
  minimum: DESKTOP_VOLTAGE_MIN_MV,
  maximum: DESKTOP_VOLTAGE_MAX_MV,
});

const DESKTOP_CURRENT_RANGE            = Object.freeze({
  minimum: DESKTOP_CURRENT_MIN,
  maximum: DESKTOP_CURRENT_MAX,
});

function calculatePlotLayout(width        , height        )             {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    throw new RangeError("Oscilloscope dimensions must be finite positive numbers.");
  }

  const compact = width < 540;
  const left = compact ? 56 : 76;
  const right = compact ? 52 : 72;
  const top = compact ? 18 : 24;
  const bottom = compact ? 46 : 56;

  return {
    width,
    height,
    left,
    right,
    top,
    bottom,
    plotWidth: Math.max(1, width - left - right),
    plotHeight: Math.max(1, height - top - bottom),
    compact,
  };
}

function buildAxisTicks(range           , interval        )           {
  if (
    !Number.isFinite(range.minimum) ||
    !Number.isFinite(range.maximum) ||
    range.minimum >= range.maximum ||
    !Number.isFinite(interval) ||
    interval <= 0
  ) {
    throw new RangeError("Axis ticks require an increasing range and positive interval.");
  }

  const ticks           = [];
  const first = Math.ceil(range.minimum / interval) * interval;
  for (let value = first; value <= range.maximum + interval * 1e-9; value += interval) {
    ticks.push(Object.is(value, -0) ? 0 : Number(value.toPrecision(12)));
  }
  return ticks;
}

function projectX(relativeTimeMs        , windowMs        , layout            )         {
  return layout.left + ((relativeTimeMs + windowMs) / windowMs) * layout.plotWidth;
}

function projectY(value        , range           , layout            )         {
  return (
    layout.top +
    ((range.maximum - value) / (range.maximum - range.minimum)) * layout.plotHeight
  );
}

function formatAxisValue(value        )         {
  const normalised = Math.abs(value) < 1e-10 ? 0 : value;
  return String(normalised).replace("-", "−");
}

__spkExports.DESKTOP_VISIBLE_WINDOW_MS = DESKTOP_VISIBLE_WINDOW_MS;
__spkExports.DESKTOP_VOLTAGE_MIN_MV = DESKTOP_VOLTAGE_MIN_MV;
__spkExports.DESKTOP_VOLTAGE_MAX_MV = DESKTOP_VOLTAGE_MAX_MV;
__spkExports.DESKTOP_CURRENT_MIN = DESKTOP_CURRENT_MIN;
__spkExports.DESKTOP_CURRENT_MAX = DESKTOP_CURRENT_MAX;
__spkExports.DESKTOP_TRACE_WIDTH_PX = DESKTOP_TRACE_WIDTH_PX;
__spkExports.DESKTOP_VOLTAGE_RANGE = DESKTOP_VOLTAGE_RANGE;
__spkExports.DESKTOP_CURRENT_RANGE = DESKTOP_CURRENT_RANGE;
__spkExports.calculatePlotLayout = calculatePlotLayout;
__spkExports.buildAxisTicks = buildAxisTicks;
__spkExports.projectX = projectX;
__spkExports.projectY = projectY;
__spkExports.formatAxisValue = formatAxisValue;

},
"src/visualisation/decimation.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                          
                                              

                             
                               
                          
                                  
                         
 

                                         
                             
                              
                            
                                 
 

/**
 * Retain each pixel bucket's first, minimum, maximum and last actual samples.
 * Narrow +30 mV action-potential peaks therefore survive display decimation;
 * scientific history and worker batches are never modified.
 */
function decimateTrace(
  samples                             ,
  options                        ,
)               {
  if (
    !Number.isFinite(options.pixelWidth) ||
    options.pixelWidth < 1 ||
    !Number.isFinite(options.windowMs) ||
    options.windowMs <= 0
  ) {
    throw new RangeError("Display decimation requires a positive width and time window.");
  }

  if (samples.length === 0) {
    return [];
  }

  const anchor = options.anchorTimeMs ?? samples[samples.length - 1].timeMs;
  if (!Number.isFinite(anchor)) {
    throw new RangeError("The display anchor must be a finite timestamp.");
  }

  const width = Math.max(1, Math.floor(options.pixelWidth));
  const result               = [];
  let bucket = -1;
  let first = -1;
  let minimum = -1;
  let maximum = -1;
  let last = -1;

  function append(index        )       {
    const sample = samples[index];
    result.push({
      sampleIndex: index,
      timeMs: sample.timeMs,
      relativeTimeMs: sample.timeMs - anchor,
      value: sample[options.field],
    });
  }

  function flush()       {
    if (first < 0) {
      return;
    }

    const indices = Array.from(new Set([first, minimum, maximum, last])).sort(
      (left, right) => left - right,
    );
    for (const index of indices) {
      append(index);
    }
  }

  for (let index = 0; index < samples.length; index += 1) {
    const sample = samples[index];
    const relativeTimeMs = sample.timeMs - anchor;
    if (relativeTimeMs < -options.windowMs || relativeTimeMs > 0) {
      continue;
    }

    const position = Math.min(
      width - 1,
      Math.max(0, Math.floor(((relativeTimeMs + options.windowMs) / options.windowMs) * width)),
    );

    if (position !== bucket) {
      flush();
      bucket = position;
      first = index;
      minimum = index;
      maximum = index;
      last = index;
      continue;
    }

    if (sample[options.field] < samples[minimum][options.field]) {
      minimum = index;
    }
    if (sample[options.field] > samples[maximum][options.field]) {
      maximum = index;
    }
    last = index;
  }

  flush();
  return result;
}

__spkExports.decimateTrace = decimateTrace;

},
"src/visualisation/traces.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                                          
const { SPIKELING_PALETTE } = __spkRequire("src/visualisation/theme.ts");

                                              

                        
            
              
                  
                
                     
                
                      

                                    
                          
                         
                           
                          
                                  
                                   
 

/** The order, separate axes and colours match SetPlot in Graph_Emulator.py. */
const OSCILLOSCOPE_TRACES                               = Object.freeze([
  {
    id: "mainVm",
    label: "Membrane potential",
    axis: "voltage",
    colour: SPIKELING_PALETTE.membrane,
    colourVariable: "--spk-membrane",
    defaultVisible: true,
  },
  {
    id: "stimulus",
    label: "Stimulus",
    axis: "current",
    colour: SPIKELING_PALETTE.stimulus,
    colourVariable: "--spk-stimulus",
    defaultVisible: true,
  },
  {
    id: "totalCurrent",
    label: "Input current",
    axis: "current",
    colour: SPIKELING_PALETTE.cell,
    colourVariable: "--spk-cell",
    defaultVisible: true,
  },
  {
    id: "synapse1Vm",
    label: "Synapse 1 membrane potential",
    axis: "voltage",
    colour: SPIKELING_PALETTE.synapse1Voltage,
    colourVariable: "--spk-syn1-voltage",
    defaultVisible: false,
  },
  {
    id: "synapse1Current",
    label: "Synapse 1 input",
    axis: "current",
    colour: SPIKELING_PALETTE.synapse1Current,
    colourVariable: "--spk-syn1",
    defaultVisible: false,
  },
  {
    id: "synapse2Vm",
    label: "Synapse 2 membrane potential",
    axis: "voltage",
    colour: SPIKELING_PALETTE.synapse2Voltage,
    colourVariable: "--spk-syn2-voltage",
    defaultVisible: false,
  },
  {
    id: "synapse2Current",
    label: "Synapse 2 input",
    axis: "current",
    colour: SPIKELING_PALETTE.synapse2Current,
    colourVariable: "--spk-syn2",
    defaultVisible: false,
  },
]                          
                                      
                         
                           
                          
                                  
                                   
  );

function getOscilloscopeTrace(id            )                    {
  const trace = OSCILLOSCOPE_TRACES.find((candidate) => candidate.id === id);
  if (trace === undefined) {
    throw new RangeError("Unknown oscilloscope trace: " + String(id));
  }
  return trace;
}

function defaultVisibleTraces()                  {
  return new Set(
    OSCILLOSCOPE_TRACES.filter((trace) => trace.defaultVisible).map(
      (trace) => trace.id,
    ),
  );
}

__spkExports.OSCILLOSCOPE_TRACES = OSCILLOSCOPE_TRACES;
__spkExports.getOscilloscopeTrace = getOscilloscopeTrace;
__spkExports.defaultVisibleTraces = defaultVisibleTraces;

},
"src/visualisation/render-loop.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

                                          
                                                         
                               
 

                                       
                           
                                                                         
                                                                            
 

                                                
                                               
                                             
 

const browserScheduler                          = {
  request: (callback) => requestAnimationFrame(callback),
  cancel: (handle) => cancelAnimationFrame(handle),
};

/** Coalesces any number of worker batches into at most one browser paint. */
class OscilloscopeRenderLoop {
                   render                             ;
                   scheduler                         ;
                   visibility                                  ;
          active = false;
          dirty = false;
          frameHandle                    ;

  constructor(
    render                             ,
    options                                = {},
  ) {
    this.render = render;
    this.scheduler = options.scheduler ?? browserScheduler;
    this.visibility = options.visibility;
    this.visibility?.addEventListener("visibilitychange", this.handleVisibility);
  }

  get running()          {
    return this.active;
  }

  get scheduled()          {
    return this.frameHandle !== undefined;
  }

  start()       {
    if (this.active) {
      return;
    }
    this.active = true;
    this.invalidate();
  }

  stop()       {
    this.active = false;
    this.dirty = false;
    this.cancelFrame();
  }

  invalidate()       {
    this.dirty = true;
    if (this.active && !this.visibility?.hidden && this.frameHandle === undefined) {
      this.frameHandle = this.scheduler.request(this.handleFrame);
    }
  }

  dispose()       {
    this.stop();
    this.visibility?.removeEventListener("visibilitychange", this.handleVisibility);
  }

          cancelFrame()       {
    if (this.frameHandle !== undefined) {
      this.scheduler.cancel(this.frameHandle);
      this.frameHandle = undefined;
    }
  }

                   handleFrame = (timestamp        )       => {
    this.frameHandle = undefined;
    if (!this.active || this.visibility?.hidden || !this.dirty) {
      return;
    }

    this.dirty = false;
    this.render(timestamp);
    if (this.dirty) {
      this.invalidate();
    }
  };

                   handleVisibility = ()       => {
    if (this.visibility?.hidden) {
      this.cancelFrame();
    } else if (this.active) {
      this.invalidate();
    }
  };
}

__spkExports.OscilloscopeRenderLoop = OscilloscopeRenderLoop;

},
"src/interface/accessibility.ts": function (__spkExports, __spkRequire) {
// SPDX-License-Identifier: GPL-3.0-or-later

/** Desktop trace colours remain unchanged; these lighter variants are for text. */
const ACCESSIBLE_SPIKELING_PALETTE = Object.freeze({
  background: "#002B36",
  panel: "#073642",
  foreground: "#EEE8D5",
  secondary: "#A3B1B1",
  stimulusText: "#80C9FF",
  cellText: "#B4CA60",
  synapse1Text: "#67D3C7",
  synapse2Text: "#F08AC3",
  warningText: "#E4C36A",
  errorText: "#FF8E8B",
  focus: "#FDF6E3",
});

const DESKTOP_MINIMUM_WIDTH = 1_025;
const TABLET_MINIMUM_WIDTH = 768;
const TABLET_MEDIA_QUERY = "(max-width: 1024px)";
const MOBILE_MEDIA_QUERY = "(max-width: 767px)";
const REDUCED_MOTION_MEDIA_QUERY = "(prefers-reduced-motion: reduce)";

                                                             
                                               

                                  
                                       
                               
 

/** WCAG 2.x sRGB relative luminance for a validated six-digit CSS colour. */
function relativeLuminance(colour        )         {
  if (!/^#[0-9a-fA-F]{6}$/.test(colour)) {
    throw new RangeError("Accessible colours must use a six-digit hexadecimal value.");
  }
  const components = [1, 3, 5].map((offset) => {
    const value = Number.parseInt(colour.slice(offset, offset + 2), 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * components[0] + 0.7152 * components[1] + 0.0722 * components[2];
}

function contrastRatio(first        , second        )         {
  const left = relativeLuminance(first);
  const right = relativeLuminance(second);
  return (Math.max(left, right) + 0.05) / (Math.min(left, right) + 0.05);
}

function meetsTextContrast(foreground        , background        , options                  = {})          {
  const level = options.level ?? "AA";
  if (level !== "AA" && level !== "AAA") {
    throw new RangeError("Contrast conformance must be WCAG AA or AAA.");
  }
  const minimum = level === "AAA" ? (options.largeText ? 4.5 : 7) : (options.largeText ? 3 : 4.5);
  return contrastRatio(foreground, background) >= minimum;
}

/** Keep responsive boundaries explicit and independently testable. */
function emulatorLayout(width        )                 {
  if (!Number.isFinite(width) || width <= 0) {
    throw new RangeError("An emulator viewport width must be a positive finite number.");
  }
  if (width < TABLET_MINIMUM_WIDTH) return "mobile";
  if (width < DESKTOP_MINIMUM_WIDTH) return "tablet";
  return "desktop";
}

__spkExports.ACCESSIBLE_SPIKELING_PALETTE = ACCESSIBLE_SPIKELING_PALETTE;
__spkExports.DESKTOP_MINIMUM_WIDTH = DESKTOP_MINIMUM_WIDTH;
__spkExports.TABLET_MINIMUM_WIDTH = TABLET_MINIMUM_WIDTH;
__spkExports.TABLET_MEDIA_QUERY = TABLET_MEDIA_QUERY;
__spkExports.MOBILE_MEDIA_QUERY = MOBILE_MEDIA_QUERY;
__spkExports.REDUCED_MOTION_MEDIA_QUERY = REDUCED_MOTION_MEDIA_QUERY;
__spkExports.relativeLuminance = relativeLuminance;
__spkExports.contrastRatio = contrastRatio;
__spkExports.meetsTextContrast = meetsTextContrast;
__spkExports.emulatorLayout = emulatorLayout;

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
__spkRequire("src/integration/wordpress-entry.ts");
