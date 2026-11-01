# Stage 2 — STP × Synaptic Pharmacology × Voltage Clamp

**Status: DRAFT research firmware, 1 November 2026.** Based on the hardware-tested Stage 1 branch feature/stp-active-vc-integration-20261101. This branch is intended for review and is not yet physically qualified with pharmacology enabled. No changes to main.

## Shared event model

The original event-driven Tsodyks–Markram classroom presets (Off, Facilitation, Depression, Combined) and the existing pharmacological receptor and voltage-clamp equations are preserved.

At each presynaptic TTL rising edge, update_Synapse() first computes:

    event_gain = raw_signed_gain × STP_spikeMultiplier(stp_state, model_step, 0.1 ms)

The PH receptor pipeline consumes this SAME event_gain, and invokes pharmReleaseEvent() exactly once per presynaptic edge:

    delta_released_current = event_gain × release_multiplier

The release multiplier is either:

- **Deterministic:** R = (1 - f_N × B_GVIA)^3, normally 1;
- **Probabilistic:** K/(N×p0), where K is Binomial(N, p0×R).

Here p0 remains the original baseline release-site probability. STP does **not** change p0, N, random-number stream, or drug blockade. The joint process is an **illustrative amplitude-STP model**, not a mechanistic stochastic Tsodyks–Markram release model. STP resources advance on **every presynaptic spike**, even if stochastic release produces zero quanta. This preserves the independently validated STP and release solvers.

The same new event amplitude drives either signed current-based receptor activation or the existing AMPA/GABA-A conductance conversion. AMPA and NMDA activations share **one** glutamatergic release event; release is not sampled twice. NBQX suppresses fast AMPA output, gabazine GABA-A, APV NMDA, and GVIA acts on new presynaptic release events. Stored synaptic tails are not retroactively rescaled by a new dose.

The original raw synaptic-current states still advance alongside the receptor state for compatibility with PH E 0, but update_AllCurrent chooses only one path; the VC solver substitutes g and gE once for conductance mode. Synaptic currents are NOT double-injected. The Izhikevich and Hodgkin–Huxley/VC equations are unchanged.

## Commands and transitions

- **STP1 n / STP2 n**: select Off=0, Facilitation=1, Depression=2, Combined=3; each selection resets only that synapse's STP utilisation/resources/history. It does not erase the existing synaptic-current tail.
- **PH E 0|1**: disable/enable optional receptor and drug pathway. STP remains active independently. On enabling current-based pharmacology, the existing raw current tail is adopted as in the original PH firmware.
- **PH M 0|1**: current or conductance receptors; genuine mode changes clear receptor activations, not STP history.
- **PH R syn 0|1|2**: Legacy, AMPA or GABA-A receptors. PH N controls NMDA if conductance mode is on.
- **PH L syn 0|1**, **PH S syn N**, **PH P syn p0**, **PH Z seed**: deterministic/binomial release configuration with independent RNG streams.
- **PH C 0|1** and **PH F syn fraction**: presynaptic CaV2.2/GVIA contribution.
- **PH D drug concentration**: existing fixed-index Hill concentration-response model.
- **PH X**: resets PH receptor states, raw synaptic current tails and RNG, **not** independent STP states. To reset both subsystems, stop presynaptic firing, issue PH X, then reselect STP1/STP2 modes.

Switching between incompatible current and conductance descriptions or enabling/disabling pharmacology under ongoing current may cause a real discontinuity. STP history remains preserved, but ionic-current continuity is **not** guaranteed across every model-path switch.

## Native (no hardware) validation

From the repository root (requires Python and g++):

~~~powershell
python -m unittest discover -s Firmware/tests/stp_vc -p "test_*.py" -v
~~~

This compiles the actual sketch/serial parser with deterministic host GPIO/ADC/USB stubs. It tests current mode, dual independent synapses, AMPA/GABA and NMDA, receptor blockers, GVIA, stochastic release/RNG invariance, STP reset/mode handover, plus inherited STP × VC and USB tests. The existing VC synaptic regression battery runs in CI.

Passing these tests does not establish physical ESP32 timing, USB operation, photodiode response, source TTL edges or pharmacological model fidelity to any particular preparation.

## First physical test on COM5

**This stage requires uploading the NEW Stage 2 sketch. The Stage 1 board firmware intentionally bypassed STP inside the pharmacology pathway.**

1. Download this entire development branch and compile/upload Firmware/Spikeling_V3/Spikeling_V3.ino to the RECEIVING board. Use ESP32-S3 native USB, USB CDC On Boot enabled and Arduino-ESP32 **3.3.12** as required by its guarded-USB implementation. If compilation fails, stop and report the exact error.
2. Leave the presynaptic SOURCE unit running the previously validated normal CC firmware. Connect SOURCE Axon/Syn Out → RECEIVER Synapse 1 In using one TRS cable. Receiver on **COM5**, GUI and Arduino Serial Monitor closed.
3. On receiver, Patch and stimulus knobs centred; Noise zero; Photodiode gain zero. The script overrides the selected gain, receptor and VC command for each case.
4. Install pyserial if necessary:

~~~powershell
python -m pip install pyserial
~~~

5. Initially run three deterministic PH-current experiments (facilitation control, NBQX 0.30 µM half-block, GVIA 10 nM half-block with CaV2.2 contribution 0.35):

~~~powershell
python Firmware\tools\run_stp_ph_hardware.py COM5 --seconds 25 --output STP_PH_Current_COM5
~~~

The script prompts to **stop source firing**, changes the receptor/drug model, clears PH and STP histories, then announces RECORDING STARTED. Start presynaptic firing at ~1–3 Hz **only after** recording begins. The background serial reader continues draining USB data during prompts.

6. Only after reviewing these results, test the fast conductance pathways with AMPA facilitation/NBQX and inhibitory GABA-A depression/gabazine:

~~~powershell
python Firmware\tools\run_stp_ph_hardware.py COM5 --cases 04_ampa_conductance 05_ampa_nbqx 06_gaba_conductance 07_gaba_gabazine --seconds 25 --output STP_PH_Conductance_COM5
~~~

The script automatically selects positive/negative gain and receptor identity. This uses the **active ideal VC** backend at -70 mV and deterministic release.

7. Upload the result folder as a ZIP. Each folder contains raw VC2 samples, event comparisons and a machine-readable summary. Do **not** merge Stage 2 until the hardware tests are reviewed.

The runner restores CC, VCT off, PH off, STP off, physical gain/decay controls and DT 2000. It does not restore previous custom PH drug doses, receptor settings or RNG seed. Use a dedicated experimental receiver.

## Not yet covered physically

- NMDA slow-current and APV half-block/washout with STP.
- Stochastic vesicle-release failures, where no individual incoming TTL event timestamp appears in the aggregate VC2 output.
- Dual synapses with independent STP and probabilistic release settings.
- Cross-mode handovers during ongoing PH receptor activation.
- Timing margins and GUI behaviour with all optional features enabled simultaneously.

The resulting software is a teaching prototype, not a validated pharmacological simulator.
