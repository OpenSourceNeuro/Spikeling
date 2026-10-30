# Extended VC diagnostic capture — Windows

Use the **trace=1 firmware already installed** on the receiving Spikeling.
This package updates Python tools only; no Arduino upload is needed.
Runner 1.3 adds a pre-defined longer observation window. It does not fix or
explain the earlier intermittent pauses, and changes no model parameters,
2 ms deadline or existing response/numerical/cadence criteria.

The first instrumented physical GVIA capture passed, with intact raw data and
no trace exceptions. A clean capture cannot identify a fault that did not
occur. Next is **one 60 / 60 / 60 second control / drug / washout capture**,
keeping source activity and receiving-unit settings steady throughout.

## Run once

1. Extract this complete Python-only ZIP into a new folder. Keep its
   `Firmware/tools` files together. The installed firmware and existing venv
   remain suitable.
2. Connect SOURCE Synapse/Axon Out -> receiving Synapse 1 In with the same
   stereo TRS cable. Current-In and other incoming synapses stay disconnected.
   SOURCE remains in ordinary CC, Patch initially centred, no spikes.
3. Close GUI/Serial Monitor on COM13. Open PowerShell in the new extracted
   folder and run the following, including the variable assignment (new
   PowerShell windows do not retain `$vcPython`):

```powershell
$vcPython = "C:\Users\Agatrhe\Desktop\Spikeling_VC_Prototype_d245d07\.venv-vc\Scripts\python.exe"
& $vcPython -u .\Firmware\tools\run_vc_synapse_tests.py COM13 --case 20_gvia --synapse 1 --timing-trace --phase-seconds 60
```

4. Confirm identity includes **trace=1**. Follow the initial quiet-source
   prompt. When asked, turn SOURCE Patch up for steady **1–3 visible spikes
   per wall second**, then leave it fixed. Do not move postsynaptic knobs.
5. The runner now prints **60 seconds** for each automatic phase. Keep the
   source firing through all three (about three minutes plus setup/recovery).
   Centre SOURCE Patch only when asked. Respond promptly to prompts: the
   receive thread retains its five-minute overall acquisition limit.
6. Allow recovery, trace retrieval, analysis and cleanup to finish. Do not
   disconnect or open the GUI while the capture owns COM13.

Expected receptor contribution per resolved event remains:

| Phase | Setting | Contribution |
| --- | --- | --- |
| Control | GVIA setting zero | -0.099 nA |
| Drug | Simulated 10 nM GVIA | -0.055590046875 nA |
| Washout | GVIA setting returned to zero | -0.099 nA |

The deterministic event efficacy is 0.561515625 during drug. This tests
received-event amplitude, not stochastic release failures or independently
counted source spikes. No real drug application or washout kinetics are tested.

## Return the complete result

Compress the exact folder printed after `Results:` and upload that ZIP,
whether PASS or FAIL. Include `recording.csv`, `report.json`, any plot,
`serial_rx.bin`, `serial_rx_chunks.csv` and `trace_query_rx.bin`.
Do not rerun for a clean outcome; one pre-defined extended capture is the
experiment. Keep SOURCE Patch centred after testing.

Runner 1.3 checks that every requested long phase is present for at least
59.75 seconds and has at least 29,277 samples, alongside all original timing,
integrity, numerical and pharmacological checks. A short correct-response
recording cannot pass as the three-minute test. Raw bytes are still capped at
32 MiB; timestamp capacity increases from 250,000 to 600,000 batches to cover
the longer observation. Either truncation remains an explicit FAIL.

The default phase length remains 12 seconds. Automatic cases 15–20 support
`--phase-seconds 12`, `30` or `60`; case 14 keeps its original interactive
protocol. Raw-byte and firmware trace collection still require `--timing-trace`.
Extended serial QA uses the actual native sketch/parser with simulated IO;
it does not establish physical ESP32 timing. Existing failures remain retained.
