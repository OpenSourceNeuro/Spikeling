# Extracellular acquisition contract

The board supplies neuronal input for a simulated extracellular acquisition. The GUI emulator supplies model-generated neuronal input and native model spikes. Scope produces four synthetic contact voltages in E1–E4 order.

## In-memory interface

`spikeling_gui/features/extracellular/acquisition.py` defines the read-only NumPy block interface. Scope delivers blocks through `_publish_acquisition_block` and boundary evidence through `_publish_discontinuity`. The controller retains the latest block and most recent boundary for diagnostics. A later consumer can subscribe at those boundaries and persist its own history.

| Object | Meaning |
|---|---|
| Acquisition and capture | Separate IDs for one live source attachment and one legacy CSV capture. A capture can start inside an ongoing filter or detection group. |
| Sample span | Acquisition, segment and epoch IDs, dense first accepted index and row count, model tick anchor, clock provenance, optional receive ordinal and host observation. Row offsets are shared across all signal stages. |
| Neuronal input | Sample-major Vm in mV in `main, aux1, aux2` order, stimulus in percent, trigger field, optional emulator milliseconds and aligned native flags. The native availability tuple identifies enabled neuronal sources outside somatic VC. |
| Broadband contacts | Four float64 contaminated synthetic contact potentials in µV before digital common average referencing and bandpass. |
| Processed contacts | Four float64 contact potentials in µV, applied threshold, accepted grouped flags and count of leading warm-up rows. The 100-row warm-up marker after a causal state reset is an analysis exclusion marker. Live display and legacy CSV retain the corresponding values and flags. |
| Epoch | Immutable effective settings, affected categories and first index. The following epoch's first index closes the previous interval. Equivalent snapshots reuse the epoch. Visibility, ranges, overlays and theme are display preferences. |
| Discontinuity | First affected accepted index, reason, surrounding evidence where available, exact known local losses, optional model-step loss count or host stall duration. A terminal boundary can have no following row. |

The hardware adapter counts arrivals before queue insertion. Local capacity eviction, deliberate trimming and malformed rows have separate counters. Legacy board frames have nominal 0.1 ms model ticks with upstream continuity unknown. Identical frames are legitimate. Host observation uses a monotonic clock and an inter-arrival pause exceeding one second marks a host stall. It supplies no device timestamps or upstream loss count. Hardware pacing is a host request with uncertain row-level applicability.

The emulator advances an integer tick each integration step, including when Scope is closed. A scope connected mid-run starts its accepted index at zero and keeps the producer tick. Timestamp-only compatibility accepts values within 0.001 ms of the corresponding 0.1 ms model tick. Duplicate steps, resets, invalid rows and missing steps are classified before processing. Timing and signal arrays retain producer milliseconds on the uninterrupted compatible path. Playback speed changes pacing with the same model interval.

Hardware queue data drain under the previous Scope configuration ahead of a geometry, mode, reference, bandpass, noise or pacing edit. The emulator provides a snapshot of its controls and effective stimulus program. Relevant settings changes reset their dependent processing state. On a break, Scope clears the rolling display, primes comparisons from the next valid row and resets filter, launch and detection histories while retaining RNG continuity. A legacy capture ends before the first incompatible row.

## Event meaning

| Event | Interpretation |
|---|---|
| Native model spike | Source integrator flag identified by neuron. Somatic VC and disabled auxiliaries make that source's native comparator unavailable. |
| Waveform launch | Existing Vm-derived launch used by the forward model and the legacy `GT Spike` columns. |
| Trigger edge | Observed transition of the input trigger field. The stimulus level remains a separate signal. |
| Contact crossing | Accepted processed downward crossing after per-contact refractory, identified by E1–E4. |
| Grouped detection | Existing first-crossing-anchored merge decision. Every member carries the group ID, including members delivered in a subsequent block. The same decision produces the legacy `Event` flag. |

An event ID includes acquisition, accepted index, kind and channel. Pressing Record inside an open group retains the live detector history. A capture can therefore contain subsequent members with no in-capture grouped flag. Event and epoch storage, waveform extraction and replay belong to Phase 1b and later. Phase 0 CSV captures still use their original processed columns, metadata and save/retry paths.

## Windows verification

From PowerShell in the updated feature branch, run:

```powershell
Set-Location 'C:\Users\mjyzi\Documents\GitHub\Spikeling-V2\Software\GUI - PyQt6-PySide6'
python -m pytest -q tests/test_extracellular_acquisition.py tests/test_extracellular_recording.py tests/test_extracellular_geometry.py
python -m pytest -q
python Main.py
```

1. Start the emulator in CC. Open Extracellular Scope, select Emulator and connect. Hover over Connect to check model-time and sample-flow status. Open Imaging on Emulator and verify both displays update. Disconnect and reconnect Scope while the emulator continues.
2. Change emulator speed twice. Compare the model-time display and confirm that speed alters delivery. Toggle one auxiliary neuron and switch to VC. A capture that crosses a scientific source-setting change must finalise before new-condition rows. Check normal recording Stop and then stop the emulator during a fresh capture. Inspect both CSVs and sidecars and confirm no automatic resume after restart.
3. Toggle CAR, Ch4, thresholds and event overlays. Check the shared amplitude scale, bottom time axis, source units and geometry position readouts. Repeat in both Solarized themes. Check ordinary Neuron Interface and Imaging recording workflows and open a tutorial.
4. In Neuron Interface connect the physical board using its normal port. Switch Scope source to Spikeling. Confirm the Connect tooltip declares nominal model time and unknown continuity. Capture CC and VC separately, test Stop while idle and during flow, and unplug the board during capture. Confirm the saved row count and metadata, reconnect and start a distinct capture. Check that both files can reopen and that board controls respond.
5. For performance acceptance, run baseline and feature branch on the same classroom PC at usual and fastest supported pacing. Measure queue high-water mark, local loss counters, GUI callback percentiles, processes' CPU and peak RSS for a practical-length run. Compare with the same controls, source and recording state. Check zero unexplained loss, bounded live memory, UI responsiveness and successful saves. Host arrival observations cannot establish device-time fidelity.
