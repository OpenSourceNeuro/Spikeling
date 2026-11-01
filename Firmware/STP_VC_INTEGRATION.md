# Stage 1: Short-term plasticity integrated with voltage clamp

**Status:** staged research/teaching prototype. Source-derived from the active-VC branch
at `b790a065755e7b508ed589e3f581c77dd9315f66` and validated STP header
at `a2e360c2d982cc9c2a881ac0ace221b0d54124e6`.
Neither source branch nor `main` is modified. **Do not merge before the
full-sketch/native CI and physical COM5 test battery pass.**

## Integration contract

- Model update remains 0.1 model ms per integration step; `DT 2000` is a
  2,000 **wall-microsecond** target. The STP event clock increments exactly
  once per actual step on both current-clamp and VC pathways.
- Same STP presets as the original standalone implementation:
  `STP1 n`, `STP2 n`: 0=static, 1=facilitation, 2=depression, 3=combined.
  First spike after selection has factor 1.0.
- Each channel has independent `u`, `x`, previous-event and mode state.
  STP scales only the *new* signed current increment, not the decay of the
  prior synaptic current, presynaptic membrane-voltage display, or VC solver.
- Raw synapse current contributes to `neuron.total_current`, which the
  passive/active voltage-clamp solver converts to **nA** at exactly
  `0.01 nA / legacy-current-unit`. Inward positive synaptic current
  generates a negative/outward compensating clamp-current change at fixed
  voltage, subject to ionic and capacitive terms.
- Switching between CC/VC preserves STP event state and synaptic-current
  tails. Explicitly selecting a mode resets only that synapse's STP state.
- Existing `PH` pharmacology is present in the active VC parent branch but
  **STP+PH coactivation is NOT validated**. When pharmacology is enabled,
  the pharmacology receptor pipeline replaces raw synaptic current and
  currently does not consume the STP multiplier. Stage 2 must integrate
  the two single-event calculations without double-counting release.
  For all Stage 1 experiments, explicitly issue `PH E 0`.
- No new USB packet fields and no modified VC HH/RC solver equations.
  `VCT 1` selects VC1 (passive) or VC2 (active) diagnostic ASCII streaming;
  do not connect the ordinary GUI simultaneously.

## Native regression battery (no ESP32 needed)

From the repository root:

```powershell
python -m unittest discover -s Firmware/tests/stp_vc -p "test_*.py" -v
```

Requires `g++` in PATH; C++ Arduino/SerialCommand dependencies are compiled
against the existing VC **host test stubs**. The host-only `Y` probe prints
raw STP state and is never part of the ESP32 firmware.

Additional regression (requires `numpy`, `scipy` and `matplotlib`):

```powershell
python -m unittest discover -s Firmware/tests/vc -p "test_vc_synapses.py" -v
```

Host tests use deterministic mocked GPIO/ADC/USB and simulated microseconds.
They do not prove Arduino ESP32-S3 compilation, USB throughput, actual pulse
detection or wall-clock deadlines on your physical board.

## Physical hardware, COM5

1. Flash **the entire integrated** `Firmware/Spikeling_V3` directory
   (ESP32S3 Dev Module, USB CDC On Boot Enabled); retain the correct
   firmware libraries from the repository and their Arduino dependencies.
   DO NOT flash only `STP_functions.h`. Do not replace this sketch with the
   standalone STP build: the standalone sketch lacks the active-VC backend.
2. Receiver: connect USB **COM5**. Keep the receiver GUI and Arduino Serial
   Monitor closed. One presynaptic Spikeling in current clamp drives
   SOURCE Axon/Syn Out -> RECEIVER Synapse 1 In (TRS). For Synapse 2,
   move the cable to Synapse 2 In.
3. Set receiving Patch and stimulus knobs to centre; turn noise to zero,
   photodiode gain to zero. The script overrides synaptic gain to +6
   legacy units, sets the corresponding decay to 0.990 and `DT 2000`.
4. Centre the SOURCE Patch knob (stop presynaptic firing) before each
   recording. Begin recording first, then turn SOURCE Patch to make it
   fire at approximately **1–3 Hz**. Keep the frequency steady within each
   phase. The protocol compares **model-time**, not host seconds.
5. Install Python dependency once:

   ```powershell
   python -m pip install pyserial
   ```

6. Start with passive VC (solver control), both modes on Synapse 1:

   ```powershell
   python Firmware/tools/run_stp_vc_hardware.py COM5 --backend passive --synapse 1 --all-modes --seconds 25 --output STP_VC_Passive_Syn1
   ```

7. Repeat in active HH voltage clamp, on **both** synapses:

   ```powershell
   python Firmware/tools/run_stp_vc_hardware.py COM5 --backend active --synapse 1 --all-modes --seconds 25 --output STP_VC_Active_Syn1
   python Firmware/tools/run_stp_vc_hardware.py COM5 --backend active --synapse 2 --all-modes --seconds 25 --output STP_VC_Active_Syn2
   ```

8. Check inhibitory sign as an independent experiment (negative gain):

   ```powershell
   python Firmware/tools/run_stp_vc_hardware.py COM5 --backend active --synapse 2 --mode 2 --gain -6 --seconds 25 --output STP_VC_Active_Inhibitory
   ```

The script produces one `summary.json`, per-mode `*_events.csv` and
`*_samples.csv`; uploads of these outputs allow independent verification.
Results are PASS/FAIL/INCONCLUSIVE. The script checks source event presence,
first-spike normalisation, all STP modes, clamp-current consistency, USB tick
continuity, sample cadence, compliance, solver and deadline flags. It
restores CC, static synapse modes, physical gain knobs and default DT on exit.
It cannot restore pre-test pharmacology configuration or a custom CC command;
use a dedicated experimental receiver.

**Important VC limitation:** The existing active VC implementation already
underwent a separate prototype validation cycle; not every combination of
input, pharmacology and scheduling has been physically qualified. A native
STP+VC passing result is not a substitute for repeat physical VC testing.

## Further work

After the Stage 1 PASS report, test STP current dynamics during different
`VCMD` steps and current-compliance limits; then integrate pharmacology
in Stage 2. In Stage 2, apply one STP factor and one release-event decision
per incoming edge in the receptor pipeline, with correctly separated
presynaptic and postsynaptic effects.
