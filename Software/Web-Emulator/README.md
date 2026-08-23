# Spikeling Web Emulator

Phases 1–9 implement the numerically validated, worker-based simulation engine,
scientific oscilloscope, desktop-faithful main-neuron controls and two complete
virtual presynaptic neurons, private full-resolution scientific recording and an
accessible responsive application shell for the Open Source Neuro Spikeling
emulator. The
package includes the browser-independent model, a dedicated worker,
desktop-equivalent timing, bounded full-precision histories, a UI-independent
data-source interface, a responsive dual-axis rolling oscilloscope, two signed
synaptic input channels, validated local custom-stimulus import, exact
desktop-compatible recording CSV import/export and keyboard-native
desktop/tablet/mobile interaction and an isolated, production-ready WordPress
shortcode integration. The integration is packaged for an explicitly approved,
unpublished draft; committing these assets does not install a plugin, publish a
page or modify any existing website. Physical-hardware serial support is not
implemented.

## Requirements

- Node.js 24 or later. Node runs the erasable TypeScript syntax directly.
- Python 3.10 or later.
- A complete checkout of the Spikeling repository, including the existing
  desktop emulator under Software/GUI - PyQt6-PySide6.

There are no third-party runtime or test dependencies.

## Run the checks

From Software/Web-Emulator:

    npm run fixtures
    npm run qa:integration
    npm run verify

The first command regenerates committed Python desktop-reference fixtures. The
integration audit verifies the actual SHA-256-pinned production assets, payload
budgets, responsive/accessibility contracts, isolated WordPress plugin, pinned
scientific fixtures and the honestly recorded browser/editor/publication gates.
The final command checks that those fixtures still match the pinned desktop source,
repeats the integration audit and then runs the TypeScript model, cross-language
parity, engine, worker, oscilloscope,
main-neuron controls, dual-synapse, custom-stimulus, scientific-recording,
accessibility, responsive-interface and performance tests.

Run individual groups with:

    npm run test:model
    npm run test:parity
    npm run test:engine
    npm run test:worker
    npm run test:performance
    npm run test:visualisation
    npm run test:controls
    npm run test:synapses
    npm run test:recording
    npm run test:accessibility
    npm run test:wordpress
    npm run test:integration

## Phase 9 integration QA and launch readiness

The complete release matrix and remaining genuine production blockers are in
`LAUNCH-CHECKLIST.md`. `wordpress/phase-9-evidence.json` records observed,
date-stamped evidence from the active WordPress plugin and unpublished page
1196; it is a captured observation, not an assertion that the script can probe
a live private website. `npm run qa:integration` deliberately distinguishes a
successful local structural audit from production publication permission.

Chrome and the live desktop draft were exercised end to end. Edge, Firefox,
Safari, real tablet/mobile devices, a genuine Elementor editing session and an
anonymous frontend remain explicitly pending until the relevant environment is
available. Automated responsive and scientific coverage does not impersonate a
physical-browser sign-off. The existing published Spikeling redesign contains
exactly two emulator buttons that still link to the desktop release;
`wordpress/CTA-INTEGRATION.md` specifies their safe future migration without
editing either existing page during Phase 9.

Publishing the draft, changing live navigation or retargeting those existing
buttons always requires separate, explicit owner approval. The checked-in
readiness evidence sets `publishingApproved` to `false`; running a local QA
command cannot grant that approval.

## Reproducible production WordPress assets

Build the complete installable plugin payload from Software/Web-Emulator:

    npm run build

The dependency-free Node build writes a content-hashed application module,
separate dedicated scientific worker, six concatenated root-scoped stylesheets
and a SHA-256 manifest under wordpress/spikeling-emulator/assets/. Identical
source inputs produce identical filenames, bytes and manifest versions; there
is no framework runtime, third-party package installation, external asset
request or CDN. Typical compressed transfer sizes are approximately 35 KB for
the application, 9.5 KB for the worker and 3.8 KB for the stylesheet.

The production worker executes the same fixed 0.1 ms model and Float64 sample
transport as the development build. Regression tests execute the generated
worker itself and compare its complete scientific output against the validated
unbundled model. The PHP plugin verifies the content-hashed asset names before
enqueueing them and gives WordPress the deterministic manifest version.

## Minimal, isolated WordPress integration

The complete plugin lives under wordpress/spikeling-emulator/ and registers one
shortcode:

    [osn_spikeling_emulator speed="2" seed="123456" max_samples="250000"]

Speed is restricted to approved positions 0–5, random seeds to 1–4,294,967,295
and local scientific-recording capacity to at most 1,000,000 samples. Defaults
match the approved desktop-equivalent demonstration. Every generated root has
a unique identifier, validated data attributes and escaped accessible markup.

Assets load only on singular pages that contain this shortcode in ordinary
WordPress post content or Elementor's stored widget content. Shortcode render
provides a narrow defensive enqueue fallback; unrelated pages and scripts remain
untouched. A dedicated observer safely supports late Elementor rendering,
deduplicates repeated frontend initialisation and releases workers/listeners on
page exit. All emulator and OSN outer-page styling remains under explicit
.spk-emulator or .osn-spikeling-emulator root selectors. The plugin creates no
database tables, options, global CSS variables, REST endpoints, activation
hooks, analytics, network requests or physical-hardware integrations.

### Draft-only installation and editorial workflow

Installing or activating the plugin requires an authenticated WordPress
administrator and explicit deployment approval. After approval, install only
the wordpress/spikeling-emulator/ directory, including its manifest and the
three manifest-referenced content-hashed files. Create a new unpublished page
and insert the approved block content from wordpress/draft-page.html, or place
the shortcode in one isolated Elementor Shortcode widget. Save only as Draft.

Do not publish the page, change an existing Spikeling page, modify an Elementor
global template or alter production navigation without separate approval. A
GitHub feature-branch commit is not a WordPress deployment. Where the local
environment does not provide PHP, the test suite validates PHP integration
contracts statically; authenticated WordPress/PHP runtime and editor checks
remain explicit deployment/integration-QA steps.

## Run the local oscilloscope preview

From Software/Web-Emulator:

    npm run dev

Open the printed local address, normally http://127.0.0.1:4173/, and select
Start. The standalone preview runs the actual dedicated worker, displays
desktop-matched membrane-voltage, stimulus and current traces, and exposes the
existing start/pause/stop/reset and speed controls beside the complete
main-neuron control panel, two independently configurable presynaptic neurons
and accessible local recording controls. It starts with the desktop's disabled control defaults and speed
position 2. Enable Injected current and adjust its slider to elicit main-neuron
activity, or enable a synapse, its auxiliary Injected current and its Synaptic
gain to observe excitatory or inhibitory input. Relevant auxiliary voltage and
current traces appear automatically. All trace checkboxes, routing toggles,
sliders and neuron selectors use semantic, keyboard-operable native controls.
Use Start recording and Stop recording independently of simulation transport,
then select Download CSV to save the captured values locally. Existing desktop
recordings can be loaded with Import desktop-compatible recording CSV.

The standalone preview does not require WordPress. Building or committing the
optional WordPress integration does not modify a live website, Elementor
template, unpublished page or production deployment.

The local server strips Node-supported erasable TypeScript syntax on demand and
serves native browser modules with their correct MIME types. It requires no
Vite installation, third-party framework, package download, WordPress access or
website deployment. Set SPIKELING_DEV_PORT to select a different local port.

## Responsive accessible application shell

Mount all previously validated components behind one isolated root without
directly coupling the interface to a particular worker or future hardware
implementation:

    const source = new EmulatorSource({
      speedIndex: 2,
      simulation: { seed: 123456 },
    });

    const emulator = new SpikelingEmulator(containerElement, source, {
      recorder: { maxSamples: 250_000 },
      synapses: { autoShowTraces: true },
    });

    await source.connect();
    emulator.controls.setControlEnabled("injectedCurrent", true);
    emulator.controls.setControlValue("injectedCurrent", 18);
    emulator.recorder.start();

    // Panel visibility is keyboard-native and independently addressable.
    emulator.setPanelOpen("synapses", true);
    const layout = emulator.getLayout();

    // Removing the interface releases every component and media-query listener.
    emulator.dispose();
    await source.disconnect();

Load src/styles/emulator.css after the oscilloscope, controls, synapses and
recording stylesheets. The shell is scoped exclusively to .spk-emulator and
contains no global button, input, body, Canvas or Elementor selectors. Its
maximum content width is 1,240 px, matching the approved OSN layout system.

### Deliberate responsive layouts

| Viewport | Width | Graph and parameter behaviour |
| --- | --- | --- |
| Desktop | 1,025 px or wider | Prominent left-hand oscilloscope, recording and synapses; separate right-hand main-neuron/stimulus panel; all panels initially open. |
| Tablet | 768–1,024 px | One graph-first column followed by expanded main controls, recording and synapses; no forced horizontal overflow. |
| Mobile | Below 768 px | Graph first; native, initially collapsed control/recording/synapse panels; two-column transport; full-width selects and readable stacked values. |

The scientific plot is always first in both DOM and reading order. Responsive
changes do not clone components, reset the model, modify sample rates or create
additional worker subscriptions. Synapse columns collapse into one column on
narrow displays, and all interactive targets retain a minimum 44 px hit area.

Every expandable panel uses native details/summary elements, an explicit
aria-expanded state and a labelled region. Simulation transport buttons are
semantically disabled until a real worker snapshot arrives, then truthfully
reflect ready/running/paused/stopped state. The simulation speed selector
distinguishes real-time multiplier and wall-clock model-step throughput from
the fixed 10,000 samples per simulated second used for integration/recording.

### Keyboard, assistive technology and reduced motion

Every slider, toggle, select, file picker, action button, expandable summary
and source link has a genuine native or explicit accessible name. Three-pixel
focus-visible outlines are scoped to the emulator and remain visible in forced
colour modes. Status changes have polite, atomic screen-reader announcements;
high-frequency plot and recording readings deliberately keep aria-live off to
avoid narrating every scientific sample. Essential membrane voltage, signed
input current, stimulus and presynaptic outputs retain textual equivalents.

The emulator observes prefers-reduced-motion and disables non-essential CSS
transitions, animation and smooth scrolling without pausing the actual
scientific Canvas or changing simulation timing. prefers-contrast and
forced-colors media queries provide stronger borders and platform-native focus
outlines where needed.

### Verified scientific colour semantics and text contrast

The original source-pinned stimulus blue #268BD2, cell green #859900, Synapse 1
cyan #2AA198, Synapse 2 magenta #D33682 and membrane red #DC322F remain
unchanged for traces, slider fills and control accents. Some of those genuine
desktop accents do not achieve the WCAG 4.5:1 normal-text threshold on the dark
Solarized backgrounds, so a separate audited text palette is used only for
readable headings, numerical values, status and errors:

| Functional text | Accessible colour | Contrast on #002B36 | Contrast on #073642 |
| --- | --- | ---: | ---: |
| Stimulus | #80C9FF | 7.36:1 | 6.22:1 |
| Cell input | #B4CA60 | 7.31:1 | 6.18:1 |
| Synapse 1 | #67D3C7 | 7.33:1 | 6.20:1 |
| Synapse 2 | #F08AC3 | 5.90:1 | 4.99:1 |
| Warning | #E4C36A | 7.70:1 | 6.51:1 |
| Error | #FF8E8B | 6.07:1 | 5.13:1 |

The exported relativeLuminance, contrastRatio and meetsTextContrast utilities
use the WCAG 2.x sRGB transfer function. Regression tests independently verify
every functional text colour against both dark surfaces, all breakpoint
boundaries, native accessible names, screen-reader announcements, keyboard
semantics, source isolation, real worker batches and complete disposal.

## Public model API

Import SpikelingModel and the 20 NEURON_PRESETS from src/index.ts:

    const model = new SpikelingModel({
      controls: {
        main: { presetId: 1, patchCurrent: 18 },
      },
      seed: 123456,
    });

    const firstSample = model.step();
    const nextThousandSamples = model.run(1000);
    model.updateControls({ main: { patchCurrent: 24 } });
    model.reset();

The model exposes a 0.1 ms fixed timestep; main and auxiliary-neuron recovery
states; internal and custom stimuli; deterministic Gaussian noise; a recovering
photoreceptor; and two signed, decaying synaptic inputs.

## Worker-backed data source

Browser rendering and controls should depend on the DataSource boundary instead
of importing the model or managing a worker directly:

    const source = new EmulatorSource({
      simulation: {
        seed: 123456,
        controls: { main: { presetId: 1, patchCurrent: 18 } },
      },
      speedIndex: 5,
    });

    source.subscribe((fullResolutionSamples) => {
      // Supply every scientific sample to a recorder or visualisation.
    });

    source.subscribeState((state) => {
      // Observe run state, true speed, retained history and background drops.
    });

    await source.connect();
    source.start();
    source.updateControls({ main: { patchCurrent: 24 } });
    source.setSpeed(6);
    source.pause();
    source.start();
    source.reset();
    source.stop();
    await source.disconnect();

EmulatorSource creates a dedicated ES-module Web Worker. Its worker core owns
the scientific model, scheduler and bounded history. Each bounded simulation
slice is packed into a transferable Float64Array; the browser-side source
maintains a second bounded history for the oscilloscope and provides complete
0.1 ms samples to subscribers. No scientific value is downsampled or converted to
Float32.

The DataSource interface deliberately permits a later physical-hardware source
without making the oscilloscope depend on emulator implementation details. Web
Serial is not implemented and is not required for this phase.

## Timing and simulation speed

Numerical integration always uses the existing fixed 0.1 ms timestep. The
desktop-equivalent scheduler ticks every 50 wall-clock milliseconds, independently
of monitor refresh or the oscilloscope visualisation/render loop. The six
approved simulation-speed positions have the following audited meanings:

| Slider | Steps / 50 ms | Scientific samples / s | True real-time speed |
| --- | ---: | ---: | ---: |
| 0 | 12.5 average | 250 | 0.025× |
| 1 | 25 | 500 | 0.05× |
| 2 | 50 | 1,000 | 0.1× |
| 3 | 125 | 2,500 | 0.25× |
| 4 | 250 | 5,000 | 0.5× |
| 5 | 500 | 10,000 | 1× |

At 0.025×, the scheduler alternates 12 and 13 genuine integration steps per
50 ms tick, yielding exactly 250 model steps per real-world second without
changing the 0.1 ms scientific timestep. Position 2 remains the 0.1× default.
The legacy desktop-label multiplier remains available for compatibility but is
never presented as a physical real-time measurement.

By default, a simulation slice contains at most 250 model steps before the
worker yields. Therefore stop, pause, reset, speed changes and parameter changes
can be handled between slices, even at the maximum speed setting. A late or
background-throttled tick catches up at most four desktop intervals; additional
work is discarded deliberately and is visible in the droppedSteps diagnostic.

Pause preserves scientific state; start after pause resumes that state. Stop
clears history and restores the model's initial state without discarding chosen
controls. Reset clears history and reproducibly restarts the seeded model;
resetting an already-running engine keeps it running.

## Bounded scientific history

The default desktop-sized history retains 50,000 full-resolution samples, or
5,000 ms at the fixed 0.1 ms timestep. Its 12 preallocated Float64 columns use
exactly 4,800,000 bytes per ring buffer; the browser and worker each own one
independent bounded ring. The oscilloscope requests the desktop-sized visible
window of approximately 5,000 samples, corresponding to 500 ms.

When the ring fills, the oldest samples are overwritten in chronological order.
Display decimation is applied only to rendering and does not change the values
delivered to scientific consumers or full-resolution recording.

The performance tests verify maximum-speed slicing, 10,000-sample scientific
parity, 70,000-sample bounded-history runs and a simulated one-minute background
suspension. They also measure complete 5,000-sample, three-trace oscilloscope
frames and verify that rendering never changes scientific source samples.

## Desktop-matched scientific oscilloscope

Mount the oscilloscope against any object implementing DataSource:

    const source = new EmulatorSource({
      speedIndex: 5,
      simulation: {
        controls: {
          main: { patchCurrent: 18, directCurrentEnabled: true },
          stimulus: { strength: 25 },
        },
      },
    });

    const scope = new SpikelingOscilloscope(containerElement, source);
    await source.connect();
    source.start();
    scope.setTraceVisible("synapse1Current", true);

    // When removing the instrument:
    scope.dispose();
    await source.disconnect();

Load src/styles/oscilloscope.css alongside the component. Its named Solarized
CSS custom properties are scoped to .spk-oscilloscope and do not alter global
WordPress, Elementor or host-page styling.

The desktop Graph_Emulator.py plotting contract is preserved:

- Rolling x-axis: −500 to 0 ms of simulation time.
- Left axis: membrane potential, −90 to +30 mV.
- Right axis: current input, −100 to +100 arbitrary units.
- One CSS-pixel straight-segment traces; no spline or aesthetic interpolation.
- Device-pixel-ratio-aware backing Canvas with narrower mobile axis margins.
- Native keyboard-operable trace checkboxes and textual live signal readings.

| Desktop signal | Browser sample field | Axis | Source-matched colour | Initially visible |
| --- | --- | --- | --- | --- |
| Main membrane potential | mainVm | Voltage | Red #DC322F | Yes |
| Stimulus | stimulus | Current | Blue #268BD2 | Yes |
| Input current | totalCurrent | Current | Green #859900 | Yes |
| Synapse 1 membrane potential | synapse1Vm | Voltage | Orange #CB4B16 | No |
| Synapse 1 input current | synapse1Current | Current | Cyan #2AA198 | No |
| Synapse 2 membrane potential | synapse2Vm | Voltage | Yellow #B58900 | No |
| Synapse 2 input current | synapse2Current | Current | Magenta #D33682 | No |

The display decimator retains each horizontal pixel bucket's first, minimum,
maximum and last genuine samples in chronological order. Consequently a narrow
+30 mV action-potential peak or abrupt stimulus edge cannot disappear merely
because the chart is narrower than the full-resolution scientific window. No
new sample values are invented, and worker/recording data remains unchanged.

Worker batches invalidate an independent requestAnimationFrame-driven visual
loop. Multiple incoming batches are coalesced into a single paint; a frame is
not requested when the simulation is paused, stopped or the browser tab is
hidden. ResizeObserver updates Canvas geometry without changing the simulation
timestep, history or axis ranges.

## Desktop-faithful main-neuron controls

Mount the main-neuron controls against the same DataSource used by the
oscilloscope; the component never imports, resets or directly owns a model or
worker:

    const source = new EmulatorSource({ simulation: { seed: 123456 } });
    const scope = new SpikelingOscilloscope(scopeContainer, source);
    const panel = new SpikelingMainControls(controlContainer, source, {
      devicePixelRatio: () => window.devicePixelRatio,
    });

    await source.connect();
    source.start();
    panel.setControlEnabled("injectedCurrent", true);
    panel.setControlValue("injectedCurrent", 18);
    panel.selectPreset(11);

    panel.dispose();
    scope.dispose();
    await source.disconnect();

Load both src/styles/oscilloscope.css and src/styles/controls.css. Control styles
and Solarized custom properties are scoped to .spk-controls and do not change
WordPress, Elementor or other host-page styling.

All 20 audited Python-source neuron presets appear in the native selector. The
display immediately updates the actual selected a, b, c, d and resting
potential, with appropriate millivolt units. Changing a preset retains existing
membrane voltage, recovery state, simulation time, injected current and synapse
settings; only the main photoreceptor controls return to their desktop defaults.

Every slider is initially disabled with a separate keyboard-native on/off
toggle. Switching a control off restores its source-pinned desktop default.
Direct current stimulation and Light stimulation are independent routing
checkboxes.

| Control | Raw slider range | Desktop default/off value | Scientifically labelled display |
| --- | ---: | ---: | --- |
| Stimulus frequency | −100 to +100 | 0 | Nonlinear frequency, approximately 10 to 1,000 Hz |
| Stimulus strength | −100 to +100 | 0 | Signed percentage |
| Injected current | −100 to +100 | 0 | Signed arbitrary units |
| Noise level | 0 to 100 | 0 | Percentage and Gaussian standard deviation in arbitrary units |
| Photo-gain | −100 to +100 | 0 | Signed percentage |
| Photo decay λ | 10 to 125 | 100 | Actual coefficient, slider / 100,000 ms⁻¹ |
| Photo recovery λ | 1 to 100 | 25 | Actual coefficient, slider / 1,000 ms⁻¹ |

The desktop frequency display is round(10000 / (510 − 5 × slider)) Hz. Thus raw
slider values −100, 0 and +100 display 10, 20 and 1,000 Hz respectively; the
signed raw slider value is sent to the model without incorrectly substituting
the displayed frequency. As in the original model, the first internal-waveform
period remains 1,000 samples before the next rollover applies a changed period.

Gaussian noise displays its genuine σ = noise slider / 4 a.u. Photoreceptor
decay and recovery display the coefficients actually used by the numerical
model, not raw unlabeled slider values. Parameter changes are forwarded through
the existing worker protocol without changing the 0.1 ms integration timestep,
resetting simulation state or bypassing the source-matched one-sample current
delay.

## Local custom-stimulus CSV files

The desktop's bundled custom stimuli contain an exact, case-sensitive Stim
column and optionally a Trigger column:

    Stim,Trigger
    12.5,1
    0,0
    -8.25,0

Trigger values are retained as format metadata only: scientific trigger timing
comes from the model's source-matched first-sample and rollover behaviour. Each
Stim row is played at exactly 0.1 ms, with full Float64 precision, signed
values and automatic looping. An optional Time (ms), timeMs or time_ms column
is accepted only when adjacent timestamps are precisely 0.1 ms apart.

Selecting a file reads it exclusively through the browser's local File.text()
API. No upload, fetch request, server storage, third-party parsing service or
network transfer is performed. Invalid extensions, duplicate/missing columns,
malformed quotes, uneven rows, missing/non-finite samples, incompatible
timestamps, files exceeding 8 MiB and inputs exceeding 250,000 samples are
rejected before the model is changed. Both limits are configurable downwards or
upwards through MainNeuronControlsOptions.

After a valid import, the panel shows its filename, exact sample count, 0.1 ms
sample interval, total duration and a small native-Canvas waveform preview. The
preview retains each pixel bucket's actual signed minima and maxima without
inventing or modifying scientific values. Custom playback is enabled explicitly;
while enabled, only the internal frequency/strength controls are temporarily
disabled, and their original values return unchanged when playback switches
back to the internal waveform.

## Two independently configurable virtual synapses

Mount the synapse component against the same DataSource as the oscilloscope and
main-neuron panel. Supplying the optional oscilloscope reference automatically
reveals the matching presynaptic membrane-voltage and input-current traces when
a channel is enabled:

    const source = new EmulatorSource({ simulation: { seed: 123456 } });
    const scope = new SpikelingOscilloscope(scopeContainer, source);
    const main = new SpikelingMainControls(mainContainer, source);
    const synapses = new SpikelingSynapseControls(synapseContainer, source, {
      oscilloscope: scope,
    });

    await source.connect();
    source.start();

    synapses.setSynapseEnabled("synapse1", true);
    synapses.selectPreset("synapse1", 3);
    synapses.setControlEnabled("synapse1", "injectedCurrent", true);
    synapses.setControlValue("synapse1", "injectedCurrent", 45);
    synapses.setControlEnabled("synapse1", "gain", true);
    synapses.setControlValue("synapse1", "gain", 30);

    synapses.setSynapseEnabled("synapse2", true);
    synapses.setControlEnabled("synapse2", "injectedCurrent", true);
    synapses.setControlValue("synapse2", "injectedCurrent", 43);
    synapses.setControlEnabled("synapse2", "gain", true);
    synapses.setControlValue("synapse2", "gain", -25);
    synapses.setControlEnabled("synapse2", "decay", true);
    synapses.setControlValue("synapse2", "decay", 980);

    // When removing the complete instrument:
    synapses.dispose();
    main.dispose();
    scope.dispose();
    await source.disconnect();

Load src/styles/synapses.css after src/styles/oscilloscope.css and
src/styles/controls.css. Synapse 1 uses the desktop's cyan #2AA198; Synapse 2
uses its magenta #D33682. Shared auxiliary cell-input, noise and photoreceptor
controls remain green, and direct stimulus routing remains blue. All additional
styles are scoped to .spk-synapses.

Each auxiliary neuron independently exposes all 20 audited presets, a/b/c/d and
resting-voltage displays, signed injected current, deterministic Gaussian noise,
direct-current stimulation, light stimulation and three recovering
photoreceptor controls:

| Per-synapse control | Raw slider range | Synapse 1 default | Synapse 2 default | Scientific interpretation |
| --- | ---: | ---: | ---: | --- |
| Synaptic gain | −100 to +100 | 0 | 0 | Positive excitation or negative inhibition |
| Synaptic decay | 975 to 1,000 | 995 | 990 | Current-retention factor slider / 1,000 per 0.1 ms step |
| Injected current | −50 to +50 | 0 | 0 | Signed auxiliary-neuron current in arbitrary units |
| Noise level | 0 to 100 | 0 | 0 | Gaussian σ = slider / 4 arbitrary units |
| Photo-gain | −100 to +100 | 0 | 0 | Signed photoreceptor response |
| Photo decay λ | 10 to 125 | 100 | 100 | Coefficient slider / 100,000 ms⁻¹ |
| Photo recovery λ | 1 to 100 | 25 | 25 | Coefficient slider / 1,000 ms⁻¹ |

Synaptic gain and decay are independently configurable even while their
presynaptic neuron is inactive, matching the desktop's separate connection
controls. Auxiliary injected-current/noise/routing controls become available
only when that neuron is enabled. Its photoreceptor controls become available
only after its own Light stimulation switch is enabled; disabling light resets
gain/decay/recovery to the desktop defaults without affecting the other channel.

Changing a presynaptic preset resets only that cell's photoreceptor settings. It
does not reset membrane voltage, recovery state, simulation time, synaptic gain,
decay, the main neuron or the other auxiliary neuron. Disabling a channel clears
its visible synaptic current while preserving its hidden membrane-voltage and
recovery state, matching the source-pinned desktop simulation contract.

The desktop labels synaptic decay with a misleading rate-like unit, but its
simulation actually multiplies existing current by slider / 1,000 after every
0.1 ms integration step. The browser therefore labels 995 truthfully as
"0.995 / step" and additionally exposes its equivalent exponential time
constant τ = −0.1 / ln(0.995) ≈ 19.95 ms. A value of 1,000 means no decay.
Synapse 2 always uses its own chosen multiplier; it does not reproduce the
desktop's accidental hard-coded 0.995 unless legacy compatibility is explicitly
requested in the underlying scientific model.

The generated Qt auxiliary-current widgets expose 0–100 because their minimum
was never set, even though their visible labels promise −50 to +50. Both browser
controls deliberately implement the intended signed −50 to +50 range already
validated by the scientific model. Synapse 2's generated widget initially shows
995, while its controller's off/reset path and the validated model use 990; the
browser consistently preserves the controller/model default of 990.

Each panel includes a live, non-intrusive readout of its actual presynaptic
membrane voltage and signed synaptic current. Existing main-neuron total current
remains the algebraic sum of its own inputs plus both independently decaying
synaptic contributions. Set autoShowTraces: false if the host page should retain
exclusive manual ownership of oscilloscope trace visibility.

## Desktop-compatible full-resolution scientific recording

Recording subscribes to the same DataSource as the oscilloscope and controls;
it never samples rendered pixels, reads the rolling display history or owns a
simulation worker:

    const source = new EmulatorSource({ simulation: { seed: 123456 } });
    const recorder = new SpikelingRecorder(source, {
      maxSamples: 250_000,
    });
    const panel = new SpikelingRecordingControls(recordingContainer, recorder);

    await source.connect();
    source.start();
    recorder.start();
    // Every complete worker-delivered model sample is retained at Float64 precision.
    recorder.stop();

    const csv = recorder.exportCsv();
    const scientificSamples = recorder.samples();
    const state = recorder.getSnapshot();

    // Existing desktop files are validated before replacing the prior recording.
    recorder.importCsv(existingDesktopCsv, "original-desktop-export.csv");

    panel.dispose();
    recorder.dispose();
    await source.disconnect();

Load src/styles/recording.css after src/styles/controls.css. Every selector is
scoped to .spk-recording, so WordPress, Elementor and unrelated host-page styles
remain unchanged. Start recording, Stop recording, Download CSV, Clear
recording, the local file picker and capacity progress use semantic native
controls and accessible live status/error messages.

### Exact desktop CSV schema

Graph_Emulator.py SavePlotData at pinned desktop commit
4d5dbf8d5c14c6e9f95d4f2f2e8307ed3d164918 emits the following exact nine names
in this exact order. The browser exporter preserves all nine names, units and
order without adding hidden recovery-state columns that would break existing
desktop-analysis workflows:

| CSV column | Scientific source | Units |
| --- | --- | --- |
| Time (ms) | Recording-local sample time, starting at zero | Milliseconds |
| Spikeling Vm (mV) | Main-neuron membrane potential | Millivolts |
| Stimulus (%) | Signed model stimulus | Percentage |
| Total Current Input (a.u.) | Main-neuron total input current | Arbitrary units |
| Synapse 1 Vm (mV) | First auxiliary-neuron membrane potential | Millivolts |
| Synapse 1 Input (a.u.) | First signed synaptic current | Arbitrary units |
| Synapse 2 Vm (mV) | Second auxiliary-neuron membrane potential | Millivolts |
| Synapse 2 Input (a.u.) | Second signed synaptic current | Arbitrary units |
| Trigger | Source-matched binary model trigger | Zero or one |

As in the original desktop implementation, recording-local time begins at zero
even when capture starts after the simulation has advanced. Subsequent samples
are exactly index × 0.1 ms. All other values are copied directly from the
full-resolution worker batch; JavaScript's shortest round-trip numeric
representation retains the complete original Float64 value, including
scientific notation and signed synaptic currents. No fixed-decimal rounding,
Float32 conversion, interpolation, display decimation or artificial samples are
applied.

### Three independent timing measurements

- Scientific integration and recording always capture one sample per 0.1 ms of
  simulation time: exactly 10,000 samples per simulated second.
- Wall-clock simulation throughput depends on the selected speed: from 250 to
  10,000 model samples per real-world second under normal scheduling.
  The recording panel exposes the current target without presenting it as the
  scientific sampling frequency.
- Display rendering uses an independent, coalesced animation-frame loop. Paint
  rate never determines recording frequency, even when the display drops frames
  or its bounded history overwrites older values.

Pause leaves a recording armed without adding samples; resume continues the
existing 0.1 ms sequence. Simulation stop or reset safely stops recording while
preserving captured data. A discontinuous worker sample stream or worker error
also stops recording explicitly instead of inventing missing values or mixing
two scientific timelines.

### Bounded memory and local-only file handling

The default 250,000-sample maximum retains 25 seconds of scientific simulation
time. Nine Float64 columns are allocated lazily in chunks of 1,024 samples,
with a strict maximum of 18,000,000 bytes of numerical recording storage.
Unlike the display ring buffer, recording never overwrites an earlier sample:
the recorder automatically stops and reports its full state when capacity is
reached. Choose a different maxSamples or chunkSamples when embedding the
instrument; clear releases every allocated chunk.

CSV imports accept only the exact nine desktop names, with reordered or quoted
headers permitted. Duplicate/missing/unknown columns, uneven rows, malformed
quotes, empty or non-finite values, non-binary triggers, negative timestamps,
timestamps not spaced by exactly 0.1 ms, invalid extensions, files larger than
64 MiB and recordings longer than the configured sample limit are rejected.
Validation completes before an existing recording is replaced. Input is read
exclusively with the local browser File.text() API; export uses a local Blob
download. No backend, fetch request, server upload, analytics transfer or
third-party parsing service receives scientific samples.

## Desktop numerical contract

The reference is pinned to commit
4d5dbf8d5c14c6e9f95d4f2f2e8307ed3d164918 and verifies the exact Git blob hashes
of Graph_Emulator.py and Parameters_Izhikevich.py before generating fixtures.

The model preserves the desktop's:

- Izhikevich voltage update followed by a recovery update using the new voltage.
- 30 mV reset threshold, 30 mV displayed peak, and -110 mV lower clamp.
- One-sample delay before a newly assembled input current reaches the neuron.
- First 1,000-sample internal stimulus period and one-sample rollover trigger.
- Photoreceptor adaptation order and one-sample coefficient-update delay.
- Auxiliary-cell hidden-state retention when a synapse is switched off.
- Full 0.1 ms sample timestamps and unmodified scientific values.

Golden parity uses a maximum absolute error of 1e-8 and exact trigger timing.
Both implementations use the same portable xorshift32 plus Box-Muller generator
for deterministic noise.

## Approved differences from the desktop

The default browser initialisation honours the selected preset, including its
resting potential and its own a, b, c and d parameters. The initial recovery
state remains zero, as in the desktop. The alternative desktop initialisation
starts at -65 mV for direct reference comparisons.

All 20 desktop-source presets are exposed, although the current Qt combo boxes
only show the first 12. Spike Frequency Adaptation intentionally retains the
Python source value b=0.22; the firmware currently uses 0.20.

The desktop-compatible Inhibition Induced Bursting preset did not generate
displayed spikes under the tested negative-current conditions with its existing
u=0 initialisation. Its fixture therefore uses a documented positive-current
control to exercise the preset; its educational phenotype needs separate review
before a UI presents it as a validated inhibition-triggered demonstration.

Synapse 2 correctly uses its selected decay slider. The source-pinned desktop
bug can be reproduced only when legacySynapse2DecayBug is explicitly enabled
for parity tests. Auxiliary patch current accepts the intended signed -50..50
range instead of the desktop slider's erroneous 0..100 range.

## Next phase

Phase 6 can introduce full scientific recording, start/stop capture, validated
data handling and CSV export while preserving the Phase 1 scientific contract,
Phase 2 worker/data-source boundary, Phase 3 truthful rolling oscilloscope,
Phase 4 main-neuron controls and Phase 5 independently configured synapses.

## Licence

GPL-3.0-or-later, consistent with the Spikeling software repository.
