# **Stimulus recipes**

This page is a practical cookbook of stimulus patterns you can run with Spikeling. Each recipe states:

- **what to select in the GUI**
- **what to set**
- **what it teaches**
- **what to look for in Vm and spikes**

Spikeling supports two main stimulus pathways:

- **Current stimulus**: inject the waveform directly as input drive (current clamp logic)
- **Light stimulus**: drive an LED (stimulus output → LED cable) and stimulate the photodiode pathway

For background on stimulus modes, see: [Concepts → Stimulus protocols](../user-guide/concepts.md#stimulus-protocols-what-is-built-in-vs-what-the-gui-adds).

---

## **Before you start (recommended setup)**

- Pick one **neuron mode** and keep it fixed during a recipe.
- Start with:
  - injected current = 0 (centre detent / patch clamp neutral)
  - noise = off (unless the recipe is about noise)
  - synapses = off (unless the recipe is about synapses)
- Display:
  - **Vm**
  - **Stimulus** (or the current trace if you route stimulus as current)
  - Optional: **Total input current (Itot)**

!!! tip "Teaching rhythm"
    For each recipe: make students predict the response, then run it, then explain what changed.

---

## **Recipe 1 — Single step (classic current clamp protocol)**

**Use:** threshold finding, adaptation, F–I curves  
**GUI mode:** `Steps`  
**Route:** `Current`

### Settings (suggested)
- Baseline: 1 s
- Step duration: 2–5 s
- Return to baseline: 1 s
- Step amplitude: start small and increase

### What to look for
- Vm depolarisation/hyperpolarisation during the step
- spikes appear once the step crosses threshold
- adaptation: spike rate often slows over time during a long step

---

## **Recipe 2 — Step family (build an F–I curve)**

**Use:** excitability quantification  
**GUI mode:** `Steps`  
**Route:** `Current`

### Settings
Run a sequence of step amplitudes (e.g., 6–10 levels), keeping duration fixed.

### Measure
- spike count or firing rate during each step
- plot firing rate vs step amplitude

---

## **Recipe 3 — Pulse train (frequency vs strength)**

**Use:** recruitment, frequency following, reliability  
**GUI mode:** pulse/square train (or square-like train via your GUI controls)  
**Route:** `Current` (or `Light` for flicker teaching)

### Settings
- Set pulse strength moderate
- Sweep frequency (e.g., low → high)
- Then fix frequency and sweep strength

### What to look for
- some frequencies produce reliable time-locked spiking
- at high frequencies, Vm may integrate or spikes may fail depending on mode

---

## **Recipe 4 — Sine wave (subthreshold resonance)**

**Use:** membrane filtering, resonance intuition  
**GUI mode:** `Sine`  
**Route:** `Current`

### Settings
- Use small amplitude to keep Vm subthreshold
- Sweep frequency manually or run several fixed frequencies

### What to look for
- Vm oscillation amplitude depends on frequency and neuron mode
- some modes show stronger response in certain frequency bands

!!! note
    This is best as a demonstration unless students already know resonance/impedance concepts.

---

## **Recipe 5 — Triangle wave (rate-of-change and threshold crossing)**

**Use:** compare rising vs falling phases; “when does threshold get crossed?”  
**GUI mode:** `Triangle`  
**Route:** `Current`

### Settings
- Moderate amplitude
- Low–moderate frequency

### What to look for
- spikes often cluster near the peaks (depending on mode)
- threshold crossing can differ on rising vs falling ramps

---

## **Recipe 6 — Chirp / ZAP sweep (frequency probing)**

**Use:** resonance, frequency preference, dynamic response  
**GUI mode:** `Chirp` (linear or exponential; amplitude increase variants if available)  
**Route:** `Current`

### Settings
- Keep amplitude subthreshold at first
- Sweep over a wide band (e.g., low → high)

### What to look for
- Vm response changes across the sweep
- some modes show “preferred” frequency ranges with larger Vm deflections

---

## **Recipe 7 — Noise stimulus (variability under controlled conditions)**

**Use:** stochastic spiking, jitter, threshold probability  
**GUI mode:** `Noise`  
**Route:** `Current`

### Settings
- Set a small depolarising bias current so Vm is near threshold
- Increase noise amplitude gradually

### What to look for
- intermittent spikes appear without changing mean input
- spike timing becomes variable
- rate increases with noise amplitude

---

## **Recipe 8 — On-board square stimulus (fast classroom demo)**

**Use:** immediate hands-on demonstration  
**Source:** on-board square stimulus generator  
**Controls:** frequency + strength knobs (board)

### Workflow
1. Keep current injection at zero initially.
2. Increase stimulus strength until Vm deflections are clear.
3. Increase frequency and observe changes in spiking reliability.

### What to look for
- easy “knob-to-trace” intuition
- quick illustration of strength vs frequency effects

---

## **Recipe 9 — Light flicker (sensory-style stimulation)**

**Use:** visual sensory analogue; polarity inversion with Photo-gain  
**Route:** `Light`

### Two common setups
- **Controlled LED**: stimulus output → LED cable → photodiode
- **External LED source**: any modulated light aimed at the photodiode

### Settings
- Start with modest **Photo-gain**
- Use square pulses or a pulse train to deliver flicker
- Flip Photo-gain sign to show excitatory vs inhibitory sensory drive

### What to look for
- same light can depolarise or hyperpolarise depending on gain sign
- photoreceptor dynamics (decay/recovery) shape response to flicker

---

## **Recipe 10 — Synaptic drive bursts (postsynaptic recruitment)**

**Use:** integration, coincidence, E/I balance  
**Source:** presynaptic unit spikes (or emulator auxiliary neuron)

### Workflow
1. Create presynaptic spiking bursts (increase presynaptic drive briefly).
2. Set postsynaptic neuron below threshold.
3. Increase synapse gain until bursts recruit postsynaptic spikes.

### What to look for
- burst summation is more effective than isolated spikes
- inhibition can veto recruitment

---

## **Recipe 11 — “Design your own stimulus” (student capstone)**

**Use:** experimental design thinking  
**Goal:** students build a stimulus to test a hypothesis.

Example hypotheses:
- “This mode adapts strongly, so a long step will slow firing.”
- “Noise increases spike-time jitter but does not strongly change mean Vm.”
- “This neuron responds differently to slow vs fast oscillatory inputs.”

Student checklist:
- write the hypothesis
- choose waveform type
- choose amplitude and timing
- record one dataset
- compute one metric
- interpret results

---

## **Practical tips**

- If you are confused, disable everything except **one** input pathwa
