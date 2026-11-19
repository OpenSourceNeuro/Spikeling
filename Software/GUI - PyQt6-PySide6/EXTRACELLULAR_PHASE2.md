# Extracellular Phase 2

## Why can an extracellular spike disappear while the neuron keeps firing?

Compare two analyses of the same saved recording. A changing detection count tells you how the measurement and the analysis recipe interact. In this practical the soma, contact geometry and original broadband samples are identical under both recipes.

### Generate the verified practical

From the Spikeling GUI directory on Windows, run:

```powershell
$fixture = Join-Path $env:TEMP ("Spikeling-CAR-" + [guid]::NewGuid() + ".spikeling")
python -m spikeling_gui.features.extracellular.phase2_practical $fixture
Join-Path $fixture 'manifest.json'
python .\Main.py
```

The fixture uses the existing Spikeling intrinsic model with zero drug block, continuous current injection and the existing extracellular Template generator. One soma is equidistant from the four contacts. The auxiliary sources are inactive and observation noise is zero. The generator deliberately records the verified soma event flags in the optional native companion for instructor use.

1. Open **Extracellular → Data Analysis → Recording**, then select the printed manifest. Inspect the four original broadband traces. The default preview clips to the available 3,200 rows.
2. Open **Processing & Detection**. Choose **None**, untick **Causal bandpass**, keep all four detection contacts and keep the threshold at −15 µV. Click **Run analysis B**. Then click **Set B as reference A**.
3. Change the reference to **Common average (CAR)** with all four reference contacts ticked. Keep the filter off and the detector settings fixed. Click **Run analysis B** again.
4. Compare the dashed A traces with the solid B traces. The raster marks unmatched A/B detections with ×. Open **Waveforms & Comparison** to see A’s mean and B’s valid waveform count. Select **Reveal native emulator events** and return to **Processing & Detection** to reveal the source lane. Check B against the verified simulator flags with the 2 model ms tolerance.
5. Export the analysis JSON outside the session folder. Set the reference back to None and rerun. Compare the restored detections with A.

| Verified measurement | A, None | B, four-contact CAR |
|---|---:|---:|
| Saved broadband samples | 3,200 | 3,200 |
| Verified soma events | 8 | 8 |
| Peak absolute analysed voltage | 131.366 µV | 0 µV |
| Grouped detections | 8 | 0 |
| Matching soma events at 2 model ms | 8 | 0 |
| Valid four-contact snippets | 8 | 0 |

In this symmetric model the same voltage appears on all four electrodes. Subtracting their mean removes that shared component. A four-contact mean can contain neuronal signal in a less symmetric preparation too, and the resulting referenced channels share dependencies. They represent measurements after a chosen transformation. The original files stayed byte-identical throughout the experiment.

For a second exercise use an ordinary, asymmetrical Emulator session with background noise. Hold the saved recording fixed while changing threshold or bandpass. Inspect the original and derived traces around an unmatched event before interpreting it. Optional simulator flags and inferred waveform launches are presented separately from detected groups. Noise, template alignment, filter delay and choice of threshold can all affect the agreement.

## Controls and analysis scope

| Tab | Function |
|---|---|
| Recording | Phase 1b validation, contact preview, stage selection, metadata and selected CSV export. Set the accepted-index interval here. |
| Processing & Detection | None or CAR with named reference contacts, optional causal bandpass, negative threshold, refractory time, grouping window and enabled detection contacts. Run B, pin A, then change settings and rerun B. The linked trace plot shows E1–E4 at a common amplitude scale. |
| Waveforms & Comparison | Choose pre/post duration, a 1-based group range and 0–64 display overlays. Run B again to apply waveform settings. Inspect the mean A/B waveforms and change the source evidence or matching tolerance. Export the applied recipes and measured results as JSON. |

The numerical run covers every eligible sample in the selected interval of up to 40,000 accepted rows. Select a new interval to inspect another part of a long session. This clears A and B so comparison remains tied to a single interval. The plots reduce long traces using local extrema at their original sample positions, retain gap breaks and may summarise dense event markers. The individual waveform overlay count is independent of the number contributing to the mean. The recording is read in bounded chunks after validation. Analysis is asynchronous and superseded results are discarded. A recovered session displays its incomplete status and allows analysis of its validated prefix. Historical and interval-export CSVs can be inspected in Recording. Offline analysis requires a validated versioned broadband session.

## Scientific methods and provenance

- **Reference.** None copies the original µV values. CAR subtracts the arithmetic mean of at least two selected contacts from each observation E1–E4 at each sample. All analysed channels retain the original contact order.
- **Filter.** With bandpass on, the default is the live Scope’s 300–3,000 Hz Butterworth design, using a third-order prototype (sixth-order bandpass), SOS coefficients and forward causal filtering. Cutoffs must fall strictly inside the Nyquist limit at the saved model rate. The normal model rate is 10 kHz. Clock provenance for board input is nominal model time and physical packet continuity is unknown.
- **State.** Each offline recipe starts from zero filter state at the selected interval start. State carries across consecutive file chunks and resets at gaps, segment changes, incompatible clocks and each effective settings epoch. Detection and waveforms exclude at least the first 10 model ms after a filter reset, extended where the dominant pole predicts slower decay to a 1% envelope. This is a settling estimate. The saved live observations and their initial-state provenance remain inspectable in Recording. Phase 2 produces a fresh offline run with its own state policy, so a capture that started mid-flight can yield different early values from the historical live-filtered stage.
- **Detector.** A negative contact crossing requires a previous sample strictly above threshold and a current sample at or below it. The first eligible row primes the comparison. Refractory checks use model ticks and accept at exact expiry. Crossings join the most recent group while inside its first-crossing-anchored window. A crossing at exact window expiry begins a new group. Simultaneous crossings share one anchor, including when the grouping duration is zero. Offline IDs keep each contact crossing with the group and recipe that produced it. A group can represent overlapping source events.
- **Waveforms.** Pre/post durations round to the nearest model sample, with halves rounded up. Snippets include the anchor and retain all four contact voltages. The mean uses all valid selected groups. Windows extending past the selected interval, an epoch, a segment or warm-up are excluded and their event IDs and reasons are retained. Individual overlays sample evenly from the valid group order.
- **Agreement.** A/B results must share the same capture, selected accepted indices, broadband hash and scientific boundaries. Matching is one-to-one within each segment and epoch. It maximises ordered match count, then minimises total absolute tick difference. Tolerance is 0–5 model ms. A/B matching uses the common eligible exposure. For source agreement, comparison is restricted to rows with available source evidence and excludes filter warm-up and detector priming. The comparison reports unmatched events, detections with multiple eligible reference candidates and excluded exposure. Stored native flags can cluster and vary by emulator mode. Inferred Vm launches are proxies and hardware recordings supply no independent neuronal truth. Phase 2 reports counts and ambiguity without precision or recall percentages.
- **Derivative export.** The JSON identifies capture and acquisition, accepted bounds, original broadband SHA-256, model rate, clock-bearing runs, algorithm version, complete applied recipes, source kind and tolerance if requested, group IDs and crossings, waveform IDs, exclusions and means. The export requires a new path outside the acquisition folder. Reference and comparison always start from the same saved broadband.

## Windows acceptance

From the GUI directory run the new tests, then the full suite:

```powershell
python -m pytest -q tests/test_extracellular_offline_processing.py tests/test_extracellular_offline_analysis.py tests/test_extracellular_offline_ui.py
python -m pytest -q
python .\Main.py
```

- Run the generated practical above. Verify A and B against the table, switch themes and check axis labels, dashed and solid traces, and marker and waveform visibility. Switch a recipe while a longer analysis is running, run the newer recipe and confirm the newest settings are shown on completion.
- Start the normal **Emulator** and inject current in CC until the soma fires repeatedly. In Extracellular Scope select Emulator, connect and choose the versioned broadband recording format. Capture a few seconds of data, stop, open the manifest and repeat the analysis. In a default recording the **Reveal native emulator events** option is unavailable. You can inspect inferred Vm launches as proxies.
- With a physical board on its usual port, check acquisition, normal CC and VC recording, source change and unplug finalisation. Reopen a completed board capture and confirm the nominal model-clock label. Keep the installed firmware for these tests.
- Open a legacy extracellular CSV and a recoverable partial session. Confirm the CSV stage and offline eligibility, the recovered-prefix label and rejection of a corrupt complete session. Smoke-test Neuron Interface, Emulator, Imaging Simulation and Data Analysis, Electrophysiology Data Analysis, Tutorials and Settings.

Phase 2 supports detection and waveform comparison of Spikeling’s synthetic extracellular observation. Sorting, unit classification and population analysis are later work.

## Implementation inventory

- `offline_processing.py` defines independent referencing and streaming causal processing within scientific boundaries.
- `offline_detection.py` and `waveform_analysis.py` produce accepted crossings, groups and valid four-contact waveforms.
- `analysis_comparison.py` and `offline_analysis.py` handle agreement, source provenance, independent recipes and derivative export.
- `session_reader.py` exposes clipped span metadata and bounded event queries through the existing validated session reader.
- `recording_page.py`, `analysis_page.py` and the updated `UI_ExtracellularRecording.ui` and generated binding provide the three-tab workflow.
- `phase2_practical.py` generates and verifies the instructor fixture. The three `test_extracellular_offline_*.py` files cover the numerical, storage and GUI paths.
