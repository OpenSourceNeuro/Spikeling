# Extracellular Phase 1b

Choose **Spikeling broadband session** in Scope’s **Recording format** selector, enter a new filename and click **Record**. Spikeling creates a `.spikeling` directory in the same portable Data/Recordings folder as its CSV recordings. Use **Extracellular → Data Analysis → Recording** to open its `manifest.json`. The same chooser accepts historical extracellular CSVs and explicitly labelled interval exports.

## Session schema 1.0

All sample indices are the original Phase 1a accepted indices. Intervals are half-open `[first_index, end_index)`. A capture UUID identifies the files. The acquisition UUID and source generation identify the live source. Contacts always use E1, E2, E3 and E4 in that order.

| File | Contents |
|---|---|
| `manifest.json` | Format `spikeling.extracellular`, major/minor version and required features, application version, capture and acquisition identities, source capabilities, model clock and nominal rate, stream and event schemas, capture start context, first and committed end indices, committed journal length, status and stop reason. Unavailable build, physical board ID, licensing and synthetic noise seed use null. |
| `NNNNNNNNNNNN.json` | One zero-based journal record. A chunk declares its sample range, stream shapes and SHA-256 hashes, epoch digest and contiguous Phase 1a spans. A boundary record has zero samples and records the source, segment, index, reason and available loss evidence. |
| `NNNNNNNNNNNN-{broadband,processed,observations,model_time}.npy` | C-contiguous, little-endian float64, samples × channels. Broadband and processed each contain four contact voltages in µV. Observations contain main, aux1 and aux2 Vm in mV, stimulus in percent and the trigger field. Model time has one column in ms. |
| `epoch-EEEEEEEEEEEEEEEEEEE.json` | The Phase 1a epoch ID, segment, effective index, change categories and settings snapshot. Synthetic settings include mode, source-to-contact distances and positions in µm where available, noise controls and hum phase. Processing includes CAR, effective bandpass limits and SOS coefficients. Detection and pacing use the Phase 1a recipe. |
| `NNNNNNNNNNNN-events.jsonl` | Public UTF-8 typed-event dataset. Each record carries the original `(acquisition UUID, sample, kind, channel)` identity, stream, segment, epoch, provenance and group reference. The pre-capture relationship flag explicitly identifies a member of a detection whose first crossing preceded the capture. Group membership can continue across journal chunks. |
| `NNNNNNNNNNNN-truth.jsonl` | Optional native model-event companion. The GUI creates sessions without this file. The Python writer supports an explicit instructor opt-in with `include_truth=True`, and the reader requires `iter_events(truth=True)` to retrieve it. The companion shares the session directory. Review which files are included before sharing. |
| `failure.json` | Best-effort failure note for an unpublished session. Includes the known accepted and rejected boundaries, last committed index, failure and stop reason. Missing notes after a crash or disk exhaustion leave the interruption reason unknown. |

Spans include the accepted index, segment, epoch, first model tick, source clock provenance, host observation and receive ordinal where available, threshold, warm-up extent, clamp state and native event availability. Emulator times retain the original producer values. Board time follows nominal receiver-derived model ticks with unknown upstream continuity. Host monotonic observations indicate callback timing and stalls. Until firmware supplies a qualified device clock, a board session has no exact physical per-sample time. Missing sample ranges appear as boundaries between the saved spans.

Recording can begin while the causal filter and detector already have history. Scope snapshots the SOS, delay state, previous contact/crossing values, group identity and warm-up state at the capture boundary. A null delay state means the first block uses the existing zero-initialised SOS path. An epoch or discontinuity effective on the first saved row can reset that boundary state. Live processed observations are saved independently. A deterministic regression reproduces the first unchanged-epoch processed block from the saved broadband and SOS state. Phase 2 replay across arbitrary epochs and resets has yet to be validated.

## Writing, publishing and recovery

The GUI offers read-only acquisition blocks to a single writer thread. Defaults are 4,096 rows per chunk and 16 queued blocks, with a producer block ceiling of 8,192 rows. The writer flushes early at an epoch or segment boundary. Queue and pending chunk memory stay bounded by these capacities. On saturation the writer accepts no further blocks, commits the already queued valid prefix and reports a failure. The rejected block end and last committed index remain available when the failure note can be written. Live acquisition can continue.

File writes use same-directory temporary files, flush, `fsync` and atomic replacement. The writer validates each journal record and referenced files before advancing the checkpoint. Stop freezes acceptance, drains queued work and validates the whole committed prefix again. It publishes with an atomic same-filesystem directory rename that refuses an existing target. Windows uses native no-overwrite rename, Linux uses `renameat2` and macOS uses `renamex_np`. Filesystems lacking the required rename semantics leave a recoverable partial. POSIX also syncs directory entries. The Windows code flushes file contents but provides no portable directory-flush guarantee against sudden power loss. An interrupted publish can leave a finalised manifest inside an unpublished directory. Its `.partial` suffix still identifies it as incomplete.

Stop, source replacement, emulator stop, hardware unplug and window close share the writer finalisation path. Known sample gaps and host stalls within a compatible source write boundaries and can continue into a new segment. Reversed emulator clocks and incompatible clock provenance finish the capture. The UI stays responsive while finalising. Closing the window waits asynchronously and a failed close returns to Scope with the recovery path in the status tooltip.

For recovery, choose the partial directory’s `manifest.json`. The reader stops at the first invalid or missing committed record and exposes only the validated prefix. Uncommitted chunk files and abandoned temporaries are counted as ignored. Recovery leaves the evidence untouched and the overview marks it **Recovered · incomplete**. A corrupted complete session is rejected. An empty normal capture can be completed with zero rows.

## Reader API

`SessionReader(directory)` validates an entire recording or recovers a partial prefix. Validation streams through one chunk at a time. Metadata inspection incurs a validation scan with bounded memory. The reader validates schema, fixed file locations, checksums, finite values, dtype, shapes, clocks, index continuity, epoch ranges and event identities and relationships. Incompatible formats raise `SessionError`. Minor versions with compatible descriptors and no unknown required features can add optional top-level metadata.

- `reader.summary` reports status, source, sample counts, ranges, continuity, segment and epoch counts and diagnostics.
- `iter_interval(stage, start, stop, channels, time_ms=(first_ms,last_ms))` yields original first index, segment, model-time points and selected values. Accepted-index queries seek directly to eligible chunk records. Time bounds are inclusive within each segment.
- `iter_metadata()` streams epochs, span lists and boundary evidence.
- `iter_events()` streams public event records. `iter_events(truth=True)` explicitly selects the optional companion.
- `export_csv(path, stage, start, stop, channels)` streams the chosen contact interval and writes a sidecar identifying stage, units, source and capture. Existing outputs are protected from overwriting.
- `partial_sessions(directory)` lists unpublished candidates.
- `LegacyRecording(path)` scans historical CSV and an optional `_meta.json` or `.metadata.json` sidecar. Historical contact traces are processed observations. The importer exposes the legacy `Event` field only with `sample_aligned_merged_detection_v1`, and exposes `GT Spike` flags as launch proxies. Versioned interval exports retain explicitly declared stage and selected channel IDs. Legacy CSV remains the default live recording choice.

The Recording view validates on a background thread, allows a preview of up to 40,000 selected rows, and shows the initial provenance and epoch records. A trace break represents a segment boundary in the preview only. The GUI makes stage availability visible and keeps the same Y scale across preview contacts. The API provides the full metadata stream. Offline filtering, threshold calibration, waveform extraction, event-aligned analysis and sorting belong to later phases.

## Windows 11 validation

```powershell
Set-Location 'C:\Users\mjyzi\Documents\GitHub\Spikeling-V2\Software\GUI - PyQt6-PySide6'
python -m pytest -q tests/test_extracellular_session.py tests/test_extracellular_session_ui.py
python -m pytest -q
python .\Main.py
```

1. Start Emulator in CC. On Extracellular Scope choose Emulator, Connect, and select **Spikeling broadband session**. Use four contacts with the default tetrode configuration, choose a new filename and record. Keep the emulator firing long enough to create several chunks. Toggle CAR or change emulator pacing partway through. Stop and wait for **Saved**.
2. Open **Extracellular → Data Analysis → Recording**. Select that directory’s `manifest.json`. Confirm **Validated · complete**, E1–E4, source and clock metadata. Switch between broadband and processed. Preview a nonzero accepted interval and export it to CSV. Reopen the export and confirm the declared stage and units. Check both Solarized themes and reopen a historical processed-only CSV.
3. Start a second recording, then Stop Emulator while capturing. Repeat with a source switch and with the main window close button. Each capture should reopen independently. The deterministic GUI test feeds ticks 21–169 and 175–210 across a CAR change, confirms a plot break and checks exact broadband samples, event IDs and the first filter-state replay. Use it to reproduce a known gap without introducing uncontrolled loss into a real experiment.
4. Connect the physical board using its ordinary binary protocol. Run CC and VC separately, record briefly in both, then unplug the board during a fresh recording. Check finalisation, source provenance, absence of a device-time claim and independent capture on reconnect. The storage tests simulate a known local board loss. A host stall or arbitrary USB dropout alone cannot quantify upstream packet loss.

### Controlled recovery on Windows

Run the loss, failure and recovery tests above. For a GUI check, choose a **completed multi-chunk test session** and corrupt only a disposable copy.

```powershell
$session = 'C:\path\to\your-test.spikeling'
$copy = Join-Path $env:TEMP ("spikeling-recovery-" + [guid]::NewGuid() + ".partial")
Copy-Item -LiteralPath $session -Destination $copy -Recurse -ErrorAction Stop
$chunks = @(Get-ChildItem -LiteralPath $copy -Filter '*-broadband.npy' | Sort-Object Name)
if ($chunks.Count -lt 2) { throw 'Use a completed session with at least two chunks.' }
[IO.File]::WriteAllBytes($chunks[-1].FullName, [byte[]]@(1, 2, 3))
Join-Path $copy 'manifest.json'
```

Open the printed manifest in Recording. Confirm the recovered label, diagnostic and shortened range. Reopen the original and confirm it is marked complete. Avoid changing files in a running writer’s partial session.

For a practical-length test, repeat short and long Emulator and board captures on the same machine and note sample count, elapsed time, CPU and peak working set in Task Manager, and Stop-to-Saved time. Comparing at matched pacing matters because wall throughput varies with model speed. Queue pressure, exact sample counts and bounded-memory synthetic throughput are covered independently by the automated tests and implementation benchmark. Hardware and Windows timings require local measurement.
