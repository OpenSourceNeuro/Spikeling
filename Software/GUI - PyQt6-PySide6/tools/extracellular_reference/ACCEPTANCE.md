# Phase 3B acceptance protocol

Freeze this protocol before generating the exploratory banks. The practical asks
students to distinguish a change on E1 at fixed gain and to estimate how the
E1/E4 range ratio changes. Minimum classroom contrasts are 10 µV peak-to-peak
(ten 1 µV displayed divisions), 0.2 ms signed-lobe width (two 10 kHz rows),
0.2 ms landmark timing, and 0.25 in a dimensionless E1/E4 range ratio (a
quarter of equality). These are design requirements for this proposed lesson,
subject to instructor confirmation. Rank and sign must have uncertainty bands
excluding a tie and zero, respectively. A ratio is unreportable when its
denominator is consistent with zero. Measure true bandwidth and reference
uncertainty separately. For each comparison require 2(U+E) below its minimum
contrast. Use absolute µV at nulls. Report relative whole-profile error
descriptively. Use a separate threshold-margin test and match at most one
detector group per launch in a disclosed timing window.

Development uses the two declared teaching poses and 10 µm / 5 µm grids.
Open validation uses eight octants at radii 36 and 58 µm, a deterministic
stratified diagnostic set and exact faces, edges, mask holes and boundaries.
Compute expected values independently with 96-point Gauss–Legendre quadrature
of each straight segment. Use finer timesteps and a tripled compartment count
to estimate observed model-discretisation error on identical positions. Report
time-only and spatial+time differences separately. Failure to cross, absence of
quiet window edges or additional spikes inside the crop rejects a kernel.

Final sealed acceptance requires a second operator. Give that operator a
frozen bank digest, recipe, thresholds and uncertainty budgets. They privately
select a fresh random seed and commit its SHA-256 before issuing an independent
test run. Stratify by supported octant, clearance-to-mask, distance, local
gradient, low magnitude and sign transition, with translated and rotated
four-contact probes. Keep every failure and negative support check. Release the
seed with signed results. Revise and reseal if tuning uses any of these data.
Open results never count as a sealed pass.

Candidate detector comparison uses identical model events, a causal 300–3000
Hz Phase 2 bandpass, all four contacts, None versus four-contact CAR, and
paired repeat trials with seeded independent and shared Gaussian noise. Use a
noiseless negative control, a 1 µV contact/2 µV shared SD classroom example,
and the 5/5 µV legacy-noise comparison. Report matches, misses and extra
groups, including outside stimulus exposure. Start from −15 µV and also compare
a family of negative thresholds against the noise-only control. Do not
multiply the voltage. Reject if the uncertainty bound overlaps the required
contrast or if threshold, polarity, tail or rights evidence is incomplete.
