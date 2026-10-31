# Spikeling VC timing diagnostics — Windows

This is an experimental diagnostic source build, not a timing fix or a release.
It investigates recurrent loop overruns and one missing exported VC2 record.
Keep the four failed captures. Do not change physiological parameters, the
2 ms wall period, or acceptance criteria to obtain a PASS.

The model equations and original CC binary packet layout are unchanged.
Instrumentation is disabled at boot and enabled only by `--timing-trace`.
It uses a fixed firmware buffer and sends no extra per-tick telemetry.
Eight elapsed spans cover command handling, inputs, release/receptors,
stimulus, membrane, outputs, formatting and serial writing. The first 16
exceptional ticks are retained; counters expose any buffer overflow. A frozen
query after capture retrieves the results. A long span includes any scheduling
pre-emption during that span; it does not alone identify a USB/host/OS cause.

## Validation status

The native regression suite and real pyserial/PTY checks use the actual sketch
and command parser with simulated clock/IO. They cannot verify ESP32 execution
time. The current environment has no installed ESP32 core and cannot download
the toolchain, so **this diagnostic revision has not been cross-compiled for
ESP32 here**. Compile it in your existing Arduino IDE before uploading. No
precompiled binary is supplied. The package includes the previously tested
5c2e063 firmware source for rollback.

## 1. Prepare the receiving Spikeling

1. Extract the entire diagnostic ZIP into a new folder. Keep your old folders.
2. Keep the SOURCE in ordinary CC with Patch centred and no spikes.
3. Close the GUI and every Serial Monitor on the receiving unit, COM13.
4. In Arduino IDE open **Firmware/Spikeling_V3/Spikeling_V3.ino** from the new
   folder. All its headers must remain beside the sketch. Use your existing
   working MCP_ADC, MCP_DAC, Gaussian and SerialCommand libraries.
5. Retain the working settings: **ESP32S3 Dev Module**, **240 MHz**,
   **Hardware CDC and JTAG**, **USB CDC On Boot: Enabled**, **4 MB flash**,
   **PSRAM Disabled**. Core 3.3.12 was used for earlier prototype builds; keep
   your existing working core/settings rather than upgrading for this test.
6. Click **Verify**. If compilation fails, stop and copy the first compiler
   error and its context; do not upload a different sketch to work around it.
7. Once Verify succeeds, upload to the **receiving** unit on COM13. Do not
   upload this diagnostic firmware to the SOURCE. Close Serial Monitor after
   upload. Windows may briefly re-enumerate the port; check COM13 is still the
   receiving unit.

## 2. Run one diagnostic capture

Open PowerShell in the extracted diagnostic folder. Reuse the existing venv:

```powershell
$vcPython = "C:\Users\Agatrhe\Desktop\Spikeling_VC_Prototype_d245d07\.venv-vc\Scripts\python.exe"
& $vcPython -u .\Firmware\tools\run_vc_synapse_tests.py COM13 --case 20_gvia --synapse 1 --timing-trace
```

The identity must end with **trace=1**. Without that marker the runner stops
before capture and requests normal cleanup. The new runner also supports the
older firmware when `--timing-trace` is omitted.

Keep the same cable: SOURCE Synapse/Axon Out -> receiving Synapse 1 In, using
stereo TRS. Current-In and other incoming synapses remain disconnected. Start
SOURCE quiet; when prompted establish steady 1–3 visible wall-clock spikes
per second. Keep postsynaptic knobs fixed. Leave the source firing through
the automatic control / simulated 10 nM GVIA / washout phases (12 seconds each).
Centre SOURCE Patch only when prompted, then allow recovery and cleanup.

Expected event contributions remain -0.099 / -0.055590046875 / -0.099 nA.
The deterministic GVIA/control ratio is 0.561515625; stochastic release-failure
statistics are not being tested. A FAIL is useful diagnostic evidence: **run
once and send the result, rather than repeating until it passes**.

## 3. Return the whole result folder

The usual `recording.csv`, plot (when analysis completes) and `report.json`
are supplemented by:

| File or report field | Purpose |
| --- | --- |
| serial_rx.bin | Exact received bytes, before line parsing, including non-VC2 content |
| serial_rx_chunks.csv | Receive time, byte offset and length of each stored batch |
| trace_query_rx.bin | Bytes received while retrieving the frozen firmware trace |
| report.json: timing_trace | Stage maxima, exceptional ticks, short-write/format/overflow counters |

Raw acquisition storage is capped at 32 MiB and 250,000 chunk timestamps.
Acquisition continues if either cap is reached, and the report explicitly
fails incomplete forensic collection. Data stays in memory during acquisition;
disk files are written after capture stops. Raw bytes include startup/quiet
and stop traffic around the analysed CSV, so the two files need not start or
end at the same sample. Query traffic occurs after the frozen capture and is
not a new qualification measurement. The reader stops before the query takes
ownership of serial reads. Cleanup still requests original CC, pharmacology
off, cleared synaptic states and normal knob control; the report separately
confirms whether binary streaming resumed.

Compress the exact folder printed after `Results:` and upload the ZIP, even
if the test fails or no plot was produced. Keep SOURCE Patch centred.

## Rollback

Open **ROLLBACK_5c2e063/Firmware/Spikeling_V3/Spikeling_V3.ino**, Verify and upload
to the receiving unit using the same settings. Use the existing 797f054 Python
kit without `--timing-trace`. Earlier physical passes and failures remain tied
to that firmware; they do not establish performance of the new diagnostic build.
