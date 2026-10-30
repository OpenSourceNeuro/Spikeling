# Guarded USB diagnostic prototype — Windows

The extended capture reproduced a 22.022 ms loop. Its frozen trace places
20.501 ms in the serial-write span, with only 0.276 ms in the HH solve. This
source revision targets transmission-side waiting without changing the neuron,
receptor, release or pharmacological equations or any acceptance thresholds.
It is an experimental mitigation, not yet a demonstrated physical timing fix.

## What changes

Hardware CDC transmit storage is allocated once at boot, before Serial.begin,
at 4,096 bytes instead of the audited driver's default 256 bytes. During active
VC2 diagnostic streaming, writes use zero wait and first require space for the
entire record. Normal USB/host scheduling gaps can be buffered. If capacity
runs out, a whole record is skipped without waiting and a transport fault is
latched; the capture still FAILS. A genuine short driver write also latches a
fault. The model is not slowed to accommodate telemetry.

Flag 128 means transport fault. Trace version 2 separately counts capacity
skips (reason bit 16), actual short writes, overruns, late starts and overflow.
The original 2 ms deadline, sequence continuity and cadence checks all remain.
The ordinary GUI/CC binary layout is unchanged; its original 100 ms driver
timeout is restored outside active VC2 diagnostics. Passive VC1 is not covered
by the guarded-write change.

## 1. Verify and upload to the receiving unit

1. Extract the complete ZIP into a new folder. It contains new firmware, Python
   runner 1.4 and the previous 3d78f06 source for rollback.
2. Leave the SOURCE in ordinary CC with Patch centred. Close GUI/Serial Monitor
   on the receiving port, COM13.
3. In Arduino IDE Boards Manager select **esp32 by Espressif Systems, version
   3.3.12**. This prototype intentionally requires that exact version: its
   zero-timeout write loop was audited for bounded retries. Older cores can
   spin with a zero timeout. The source stops compilation with a clear error
   if another core version is selected for Hardware CDC.
4. Open **Firmware/Spikeling_V3/Spikeling_V3.ino** from the new folder. Keep all
   headers beside it and retain your existing working external libraries.
5. Select **ESP32S3 Dev Module**, **USB Mode: Hardware CDC and JTAG**, **USB CDC
   On Boot: Enabled**, **240 MHz**, **4 MB flash**, **PSRAM Disabled**, and
   **Core Debug Level: None**. Retain other settings that worked previously.
6. Click **Verify**. If compilation fails, stop and send the first compiler
   error and its context. After Verify succeeds, upload to the **receiving**
   unit on COM13. Do not upload this firmware to the SOURCE. Close Serial
   Monitor after uploading; check that the receiving port is still COM13.

The current runtime lacks the ESP32 toolchain, so **this revision has not been
ESP32 cross-compiled here**. Native tests use the actual sketch/parser with a
simulated finite USB FIFO and host stalls, not the real ESP32 driver. No
precompiled binary is supplied; local Verify is required before upload.

## 2. Run one extended capture

Open PowerShell in the newly extracted folder and run:

```powershell
$vcPython = "C:\Users\Agatrhe\Desktop\Spikeling_VC_Prototype_d245d07\.venv-vc\Scripts\python.exe"
& $vcPython -u .\Firmware\tools\run_vc_synapse_tests.py COM13 --case 20_gvia --synapse 1 --timing-trace --phase-seconds 60
```

Identity must contain **trace=2,tx=guarded4096**. Runner 1.4 refuses older trace
firmware before capture, rather than treating an old run as a transport test.
Its normal non-trace analysis still supports the earlier datasets.

Use the same stereo TRS connection: SOURCE Synapse/Axon Out -> receiving
Synapse 1 In. Current-In and other incoming synapses remain disconnected.
Start SOURCE quiet; when prompted establish steady **1–3 visible wall-clock
spikes per second** and leave it fixed. Keep postsynaptic knobs fixed through
60-second control, simulated 10 nM GVIA and washout phases. Centre SOURCE Patch
only when asked, then let recovery, frozen-trace retrieval and cleanup finish.

Expected event contributions remain -0.099 / -0.055590046875 / -0.099 nA.
No real drug washout kinetics or stochastic release-failure statistics are
being tested. Run **once**, regardless of outcome, and keep the whole result.

## 3. Send the complete evidence

Compress the folder printed after `Results:` and upload its ZIP. Include the
CSV, report, any plot, `serial_rx.bin`, `serial_rx_chunks.csv` and
`trace_query_rx.bin`. A capacity skip, short write, missing sequence, timing
fault or truncated capture remains FAIL; no rows or flags are discarded to
obtain a pass. After cleanup finishes, check ordinary knob-controlled CC firing
in the GUI, and keep SOURCE Patch centred.

## Rollback

Verify/upload **ROLLBACK_3d78f06/Firmware/Spikeling_V3/Spikeling_V3.ino** to the
receiving unit with the same settings. Use the earlier abd0c53 Python kit
(runner 1.3, trace=1). That revision has a short passing physical trace capture
and the retained extended timing FAIL; it is not claimed to be fault-free.

## Audited dependency

Espressif Arduino core 3.3.12 [HWCDC.cpp](https://github.com/espressif/arduino-esp32/blob/3.3.12/cores/esp32/HWCDC.cpp),
[HWCDC.h](https://github.com/espressif/arduino-esp32/blob/3.3.12/cores/esp32/HWCDC.h)
and [main.cpp](https://github.com/espressif/arduino-esp32/blob/3.3.12/cores/esp32/main.cpp)
were reviewed. Hardware CDC does not auto-begin before setup in that path;
the ring is allocated before Serial.begin, never resized while its ISR owns
it. The audited zero-timeout implementation has a finite retry cap. Scheduling
pre-emption and driver/USB faults remain possible and must still be measured;
this is not a hard-real-time guarantee.
