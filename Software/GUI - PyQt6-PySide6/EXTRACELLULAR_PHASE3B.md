# Phase 3B reference-bank preparation and calibration dossier

**Promotion decision — no bank approved.** Hay 139653 / cell1 / biophys3 produced
a spatially variable signal and measurable pose contrasts. The tested stimulus
also produced a second spike, and the first-spike window ended with substantial
residual voltage. Release rights and a genuinely sealed acceptance run remain
open. An Allen all-active candidate was identified and deferred. Phase 3C has
no approved biological input from this work.

## Baseline and scope

The isolated `feature/extracellular-phase-3b` worktree starts at the verified
Phase 2 commit `5ee6f64`. Its parent `7da50cf` matched the advertised remote
`dev_max` at inspection. This was run on a Linux workspace. The user's
Windows checkout and hardware were not available from this environment.
The bank module is independent of Qt, only loads when called, and has no
live acquisition caller. Production Scope, recording schemas, Phase 2
processing and detector, and firmware were outside the implementation scope.

## Cell and licence dossier

| Candidate | Characterisation and source | Rights and disposition |
|---|---|---|
| Hay et al. rat L5b pyramidal cell, ModelDB 139653 | Commit `50a4aab3ce5c295ad16a134c5d9261b7cc3fbe58`, `cell1.asc`, `L5PCbiophys3.hoc`, original template and MOD files. Per-file hashes in the saved manifests. The upstream clone is reproducible and retained separately. | The ModelDB tree has no repository licence file. The Open Source Brain port at `a813a88af8eb77fc59ef70bb3e5aef6397e682f7` identifies MIT terms for its own software and separately specifies citation conditions for its NEURON directory. The article is CC BY. Confirm applicability to the exact ModelDB archive, the imported morphology and individual mechanisms and commercial distribution of derived voltages with the rights holders before release. Cite Hay, Hill, Schürmann, Markram and Segev and the ModelDB accession. Provisional. |
| Allen model 497233117 | All-active Pvalb-IRES-Cre;Ai14-177452.03.01.01, mouse specimen 469610831, reconstruction 491120251, fit file ID 517649254. Verify morphological and electrophysiological characterisation against the specimen before simulation. An aspiny class label requires evidence beyond the Cre line. | Allen Institute site terms permit noncommercial use subject to attribution and other conditions. Commercial redistribution requires written permission unless separate applicable model-specific terms grant it. Exact downloaded input hashes and model notices are pending because this candidate was screened from metadata only. Deferred, no waveform generated. |

Sources — [Hay publication](https://doi.org/10.1371/journal.pcbi.1002107),
[ModelDB 139653](https://modeldb.science/139653),
[ModelDB archive](https://github.com/ModelDBRepository/139653),
[Open Source Brain licence](https://github.com/OpenSourceBrain/L5bPyrCellHayEtAl2011/blob/a813a88af8eb77fc59ef70bb3e5aef6397e682f7/LICENSE),
[Allen model record](https://api.brain-map.org/api/v2/data/NeuronalModel/497233117.json),
[Allen terms](https://alleninstitute.org/legal/terms-of-use).
LFPy/LFPyKit are GPL software and MEArec declares MIT for its software.
Those tool licences do not settle the cellular inputs. The toolchain is offline.
[NEURON documentation](https://www.neuronsimulator.org/en/latest/install/install_instructions.html),
[LFPyKit](https://github.com/LFPy/LFPykit), [MEArec](https://github.com/SpikeInterface/MEArec).

## Direct reference and event alignment

Compiled the original Hay NMODL mechanisms with NEURON 9.0.1 and GCC 14.2.
Python 3.12, NumPy 2.3.2, SciPy 1.16.1, LFPyKit
`b729bc650fa060e3e86048e12344cd3fe8524250`. Original `L5PCtemplate`
sets the compartment discretisation and replaces the traced axon with two
30 µm stubs. The forward calculation embeds those stubs along local −Y;
that geometry is an explicit modelling assumption. The axonal recording
is the midpoint of the first stub. Its 0 mV crossing followed the soma by
0.022 ms at dt 0.0125 ms. A threshold timing comparison at two locations
does not locate the initiation site. Model axes retain the original
Neurolucida orientation and are centred at soma(0.5).

Initial Vm −80 mV, 34 °C, fixed step, 350 ms settling before recording, soma
Exp2Syn at 360 ms with 0.1/0.6 ms rise/decay, E=0 mV. At 0.07 and 0.08 µS
the soma did not cross 0 mV. At 0.09 µS the first two somatic crossings were
361.15537 and 371.82069 ms at dt 0.0125 ms. Larger tested stimuli also elicited
two crossings. The first spike can be evaluated in isolation over the
chosen crop. The input protocol has not demonstrated an isolated full response.
Use total outward `i_membrane_` in nA including capacitive and synaptic
currents. Exp2Syn passes current through the model membrane and avoids a
separate injected-electrode return. The synapse contributes to the selected
voltage window. A repeated fine run and independently rebuilt 5 µm bank
matched the original files byte for byte in the pinned Linux environment. Worst net membrane-current imbalance was 2.1×10⁻¹³ nA in the
fine run. Temporal convergence tests used dt 0.025, 0.0125 and 0.00625 ms;
the last run with dt 0.0125 ms and triple nseg probes spatial discretisation
with original channel density carried to the subdivided compartments. It
yielded 1,926 segment traces versus 642. This bounds observed differences
only and is not a proof of asymptotic convergence.

At each valid position compute line-source attenuation in an infinite,
homogeneous and isotropic conductor (0.30 S/m, point contacts, infinity
reference). Project outward currents to signed mV via LFPyKit and multiply
by 1,000 exactly once. Subtract the mean current trace baseline from −8 to
−6 ms, apply a sixth-order 4 kHz zero-phase Butterworth SOS filter to the
high-rate currents, then linearly sample at 10 kHz against a sub-sample
upward somatic crossing. Linearity makes this equivalent to applying the
same processing to the signed field. No contact-dependent time shift or
amplitude normalisation. The common crop is −3 to +7 ms inclusive, 101
samples. For a causal generator the 30-row stored landmark would follow
the launch by 3 ms; kernel index zero starts at the launch. At 5 µm, the
maximum initial voltage was 0.000164 µV, but the ending voltage reached
7.82 µV. Overlaying a zero tail would introduce a discontinuity. This fails
the release kernel criterion. Changing σ scales every unreferenced signal
by 0.30/σ and can move crossings without changing the ideal relative
contact voltages. No range of σ is biologically calibrated here.

## Field and lookup

`SpatialBank(directory, allow_provisional=False)` accepts a version-1 manifest
and six checksummed, bounded NPY assets. The manifest identifies units,
provenance, rights, grid, calibration and status. Axes and time are little-endian
float64, waveform nodes little-endian float32 `[ix,iy,iz,it]`, validity
one boolean per cell. Lookup is float64 and returns `[time,E1–E4]`.
Interior faces choose the positive-side cell; the upper bound uses the final
cell. No interpolation across a masked stencil. The exclusion envelope
contains the original pt3d centreline and radii by adding its maximum chord
deviation. A cube cell is kept only if its centre clears the envelope by at
least 5 µm plus the half diagonal. This certifies clearance relative to the
chosen geometric envelope, not the physical validity of the conductor model.
Grid values outside all valid stencils are placeholders inaccessible by lookup.

The source transform is `(contacts - soma) @ R_s` for contact rows.
Feed it E1–E4 world coordinates from Tetrode Geometry, after applying the probe
transform once. Bank instance and exact resulting coordinates scope a bounded
16-pose cache. A rejected pose names the source, contact and local position.
The returned waveform is a copy. `manifest_sha256`, `id`, `time_ms` and
`landmark_index` are the Phase 3C metadata seam. The future generator can
snapshot a returned kernel at each launch and flush at segment boundaries.
The hand-calculated integer launch fixture covers overlapping and simultaneous
events, a pose transition with an old-pose tail, a reset that discards a
pending tail and multiple block schedules. No new event semantics are
introduced here. Continue to read existing recordings without a bank.

## Reproduce locally

From the GUI directory, install app test requirements and pytest. Use Linux
or WSL for the offline mechanism build. Set BLAS threads to one during the
calibration benchmark. The commands use pinned upstream trees and a local
directory for the unapproved results. The Hay files and derived arrays are not
included in the distribution. Preserve the resulting high-resolution NPZ
files and manifests privately when confirming a recipe.

```bash
python -m pip install neuron==9.0.1 numpy==2.3.2 scipy==1.16.1
git clone https://github.com/ModelDBRepository/139653.git /tmp/spikeling-hay
git -C /tmp/spikeling-hay checkout 50a4aab3ce5c295ad16a134c5d9261b7cc3fbe58
(cd /tmp/spikeling-hay && CC=gcc CXX=g++ nrnivmodl mod)
git clone https://github.com/LFPy/LFPykit.git /tmp/spikeling-lfpykit
git -C /tmp/spikeling-lfpykit checkout b729bc650fa060e3e86048e12344cd3fe8524250
export PYTHONPATH="$PWD:/tmp/spikeling-lfpykit/lfpykit"
export OPENBLAS_NUM_THREADS=1
python tools/extracellular_reference/simulate_hay.py /tmp/spikeling-hay /tmp/ref-coarse.npz --dt .025
python tools/extracellular_reference/simulate_hay.py /tmp/spikeling-hay /tmp/ref-fine.npz --dt .0125
python tools/extracellular_reference/simulate_hay.py /tmp/spikeling-hay /tmp/ref-finer.npz --dt .00625
python tools/extracellular_reference/simulate_hay.py /tmp/spikeling-hay /tmp/ref-refined.npz --dt .0125 --refine
python tools/extracellular_reference/build_bank.py /tmp/ref-fine.npz /tmp/hay-5-v1 --step 5
python tools/extracellular_reference/build_bank.py /tmp/ref-fine.npz /tmp/hay-10-v2 --step 10
python tools/extracellular_reference/calibrate.py /tmp/hay-5-v1 /tmp/ref-fine.npz /tmp/ref-finer.npz /tmp/ref-refined.npz /tmp/results-5.json
python tools/extracellular_reference/calibrate.py /tmp/hay-10-v2 /tmp/ref-fine.npz /tmp/ref-finer.npz /tmp/ref-refined.npz /tmp/results-10.json
```

Windows regression from the Phase 3B worktree:

```powershell
Set-Location '.\Software\GUI - PyQt6-PySide6'
python -m pip install -r requirements.txt pytest
python -m pytest -q tests/test_extracellular_spatial_bank.py
python -m pytest -q
```

## Open validation and uncertainty

Both final grids use the same baseline run with 642 compartments and
dt 0.0125 ms. They contain 747 of 1,728 valid cells (10 µm) and 8,410 of 13,824
(5 µm). At eligible positions independent 96-point Gauss–Legendre evaluation
of the finite line sources agreed with the LFPyKit direct path to within
2.3×10⁻¹³ µV. Float32 conversion over every stored valid node contributed at
most 0.000015 µV. The estimated time and space refinements can be orders of
magnitude larger. See the full per-stratum relative and absolute distributions
in `tools/extracellular_reference/results/` and the frozen acceptance protocol
in `tools/extracellular_reference/ACCEPTANCE.md`.

| Grid | Stratum | Supported / tested | Median / p95 / maximum absolute error (µV) |
|---|---|---:|---:|
| 10 µm | Near | 3/8 | 0.161 / 0.371 / 0.394 |
| 10 µm | Far | 5/8 | 0.0103 / 0.0361 / 0.0402 |
| 10 µm | Interior | 14/48 | 0.0827 / 0.494 / 0.556 |
| 10 µm | Faces and edges | 2/5 | 0.326 / 0.620 / 0.653 |
| 5 µm | Near | 6/8 | 0.174 / 1.125 / 1.407 |
| 5 µm | Far | 6/8 | 0.00131 / 0.0112 / 0.0128 |
| 5 µm | Interior | 26/48 | 0.0123 / 0.0824 / 0.122 |
| 5 µm | Faces and edges | 2/5 | 0.00000105 / 0.00000180 / 0.00000189 |

The grids admit different points, especially near the morphology. A larger
worst-case near error at 5 µm does not establish poorer interpolation at
the same points. At the shared pose C, maximum whole-waveform error fell
from 6.20 to 1.54 µV. At D it fell from 1.47 to 0.45 µV. The original
two candidate poses A and B were rejected by both grids at E1. A 15° rotation
in pose E was supported on the 5 µm grid only. The complete open experiment
is reproducible and exposed. No separately witnessed sealed test was run.
An independent operator must seal fresh conditions after the bank, model and
acceptance criteria have been frozen. Near-field biological validity and
low-voltage or polarity-transition strata require further evidence.

## Candidate practical and detector diagnostics

Use 25 µm adjacent-contact spacing. Hold model, event protocol and probe
orientation fixed. Translate the probe centre from C=(0,25,20) to D=(30,25,20)
in model µm. Compare unreferenced E1 peak-to-peak amplitude and E1/E4
peak-to-peak ratio. At equal vertical scale, predict that E1 dominates at C,
then E4 dominates at D. Use the same causal 300–3000 Hz Phase 2 filtering
and negative threshold only for the **separate detection comparison**. The
waveform metrics below describe broadband before that filter. The waveform
lesson is a candidate exercise until release gates close.

| Observable, 5 µm grid | C | D |
|---|---:|---:|
| Unreferenced E1 range (µV) | 262.54 | 104.44 |
| Unreferenced E4 range (µV) | 105.46 | 124.84 |
| Unreferenced E1/E4 range ratio | 2.489 | 0.837 |
| Unreferenced E1 peak (µV) | −206.43 | −80.78 |
| Unreferenced E1 dominant-lobe width (ms, row count) | 0.3 | 0.3 |
| Unreferenced E1 dominant peak time (ms from landmark) | +0.1 | +0.1 |
| CAR E1 range (µV) | 130.39 | 28.58 |
| CAR E2 dominant peak (µV) | +16.39 | +29.92 |
| CAR E3 dominant peak (µV) | +63.35 | +25.97 |
| CAR differential energy fraction | 22.61% | 15.57% |

E2 and E3 had negative dominant peaks before CAR. CAR changes polarity
and amplitude because it subtracts a shared time-varying field. The rotated
pose E retained 10.28% of its pre-CAR energy. The analytic regression field
also verifies exact cancellation for four identical traces.

The nominal amplitude and ratio changes are 158.10 µV and 1.65.
For E1 range use metric-specific E=1.92 µV across C and D (bank versus
direct). The maximum observed U across the spatial-plus-time and finer-time
comparisons is 1.72 µV. For the E1/E4 ratio E≈0.015 and observed U≈0.032.
These observed metric-specific budgets give 2(U+E)≈7.28 µV and 0.094, below
preregistered minima 10 µV and 0.25. These are exploratory comparisons
under a fixed cell and conductor. A conservative uniform bound from the
pose trace error gives U=4.55 and E=1.54 µV per sample, so the range error
budget from that bound is 4(U+E)=24.36 µV and does not clear 10 µV. A
biological uncertainty bound is unavailable. At 10 kHz, 0.1 ms row
quantisation affects widths. E3 at D changed from 0.4 ms in the direct
trace to 0.5 ms in the bank. E1 width and timing show no teaching contrast
at these poses. Do not offer them as decisive measurements.

Each noise condition used 12 seeded runs, nine synthetic launches per run,
one per 70 ms, and the same Phase 2 detector. A group within −1/+2 ms of the
rendered landmark occupied one event window. Only one counts as a match.
Further groups in that window and groups outside windows are reported
separately. Noise-only windows are controls, with no source event in them.
Hum was disabled. This is an offline rehearsal with inserted kernels, with
no synthetic event inferred from its neighbouring broadband samples.

| 5 µm, −15 µV, 1/2 µV contact/shared SD | Matched windows / 108 | Extra groups in window | Groups outside windows |
|---|---:|---:|---:|
| C, None | 108 | 258 | 15 |
| C, four-contact CAR | 108 | 214 | 0 |
| D, None | 108 | 108 | 3 |
| D, four-contact CAR | 108 | 0 | 0 |
| E, four-contact CAR | 97 | 0 | 0 |
| Noise only, None or four-contact CAR | 0 | 0 | 0 |

At C, 216 extra groups persisted without noise, so the signal/processing
combination alone can split individual events. At D with CAR and 5/5 µV
noise, there were 103/108 matched windows, 20 extra groups in windows and
one outside. At −4 µV with no CAR and 1/2 µV noise the noise-only control had
groups in 58/108 windows and 1,322 groups outside them. At −15 µV and 5/5 µV
with no CAR the noise-only control still occupied 24 windows and produced
554 out-of-window groups. For D with CAR, the strongest filtered trough was E4 at −16.95 µV,
only 1.95 µV beyond the −15 µV threshold. For rotated pose E, the
strongest was E3 at −15.88 µV, a 0.88 µV margin. That explains why
uncertainty and noise matter even when the raw peak is much larger.
Use neither the raw group count nor occupancy
without a control to infer the firing count. For this teaching contrast
use waveform metrics and treat the detector’s dependence on geometry and
reference as something to measure. These are model-based results with no
arbitrary voltage gain.

## Packaging and runtime feasibility

Measured on Linux x86-64, Intel Xeon Platinum 8370C, from the same candidate
files and one BLAS thread. Verified load includes hashing, shape checks,
read-only mapping and finite-value checks. First process load can benefit
from OS cache; physical cold disk was not measured. ZIP sizes are offline
deflate estimates, not measured installer increments.

| Grid | Unpacked / deflated | Verified first load | Median uncached 1 / 4 / 12 queries | Calibration process peak RSS |
|---|---:|---:|---:|---:|
| 10 µm | 0.90 / 0.57 MB | 7.3 ms | 0.231 / 0.854 / 2.624 ms | 335 MiB |
| 5 µm | 6.33 / 4.49 MB | 12.4 ms | 0.181 / 0.962 / 2.748 ms | 340 MiB |

Peak RSS includes the offline currents and independent forward validation.
A second process measured 12.0 ms for the verified 5 µm load and a rise in
peak RSS from 49.3 to 55.9 MiB after loading and preparing poses. A
200-trial benchmark exercised the real pose API for three source transforms
per trial with varying rotations, giving 2.04 ms median and 3.98 ms p95.
Lookup timings are numerical work outside the live loop. The Windows
classroom computer, packaged loader and full runtime overhead remain
unmeasured. Masks do not compress the uncompressed waveform array.

## Files and remaining release work

- `tools/extracellular_reference/` contains the pinned simulator, bank
  builder, independent numerical validation and detector experiments,
  acceptance protocol, and manifests/measurements of both candidate grids.
- `spikeling_gui/features/extracellular/spatial_bank.py` implements the
  strict format reader and signed four-contact lookup.
- `tests/test_extracellular_spatial_bank.py` and its fixture directory
  verify loading, corruption, geometry, sign, reference and launch expectations.
- `resources/extracellular/banks/README.md` documents the release asset
  location. Only original analytic fixture arrays are included, under tests.

For Hay, resolve the derivative distribution rights, find an isolated response
with a quiet tail, check the sensitivity to axon embedding and conductor/contact
assumptions, and run the sealed comparison with the intended classroom recipe.
Keep 497233117 as a second candidate pending model-specific rights, or select
an identified, explicitly redistributable all-active morphology with a markedly
different arbor. Phase 3C can consume the existing loader API after approval.
It should keep evidence and landmark indices separate, preserve each launch’s
pose across a settings change, and preserve stored broadband independence.

## Regression and installation

Linux full suite ran offscreen using Python 3.12, the repository requirements
and pytest 9.0.1. It yielded **224 passed, 4 skipped and 37 subtests passed**.
The four skips were external tutorial installer integration tests. The final
focused bank suite, including the independent analytical line integral test
added after full-suite collection, yielded **13 passed**. Windows interactive,
hardware and installer checks remain unexecuted.

Use an isolated worktree from the already validated Phase 2 checkout. In
PowerShell, run from the root of that checkout. If `git log -1` does not show
your Phase 2 integration commit, locate it before running these commands.

```powershell
git status --short --branch
git log -1 --oneline
git worktree add -b feature/extracellular-phase-3b '..\Spikeling-Phase3B' HEAD
Set-Location '..\Spikeling-Phase3B'
$patch = Join-Path $env:USERPROFILE 'Downloads\Spikeling_Extracellular_Phase_3B.patch'
git apply --check --index $patch
if ($LASTEXITCODE -eq 0) { git am --3way $patch }
git log -1 --oneline
```

This patch adds the offline implementation and analytic fixture. Generate
the provisional biological assets locally through the reproduction commands
above. The classroom bank approval decision is separate from Git integration.
