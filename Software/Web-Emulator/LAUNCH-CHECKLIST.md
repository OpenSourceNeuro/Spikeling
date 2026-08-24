# Spikeling browser emulator — Phase 9 launch checklist

Audit date: 23 August 2026. Scope: authenticated, unpublished WordPress page
1196; active isolated shortcode plugin; existing published pages observed
read-only. This checklist is evidence of QA, not approval to publish.

## Reproducible release gate

Run from `Software/Web-Emulator`:

```sh
npm run qa:integration
npm run verify
```

The integration audit independently checks the three manifest-referenced
SHA-256 content hashes, filenames, byte counts, gzip counts, reproducible
manifest version, pinned worker URL, root-scoped CSS, responsive/accessibility
media queries, dependency-free lockfile, conditional WordPress loading and the
33 desktop-reference scenarios. Its successful structural result never converts
missing real-world evidence into a pass and never grants publication permission.
The Phase 9 audit completed with **354 passing automated tests**, including 32
new integration-QA cases and 100% line, branch and function coverage for the
pure launch-readiness decision engine.

## Scientific and interaction acceptance

| Gate | Evidence | Status |
| --- | --- | --- |
| Desktop scientific parity | 33 pinned desktop-reference scenarios; fixed 0.1 ms timestep; exact model/worker regression suites. | Pass |
| Neuronal behaviour | All 20 desktop neuronal presets present in the main selector and both presynaptic selectors. | Pass |
| Scientific speeds | Six approved positions spanning 250–10,000 wall-clock samples/s; 0.1× default. | Pass |
| Main stimulation | Positive and negative injected-current extrema exercised on the deployed draft. | Pass |
| Stimulus, noise and light | Stimulus frequency/strength, noise, photoreceptor gain and both routing paths exercised on the deployed draft. | Pass |
| Dual synapses | Both synapses active simultaneously; +100 and −100 gains; positive/negative auxiliary currents; independent presets; all auxiliary traces visible. | Pass |
| Transport | Start, pause and live fixed-timestep scientific sampling verified against the real production worker. | Pass |
| Scientific recording | Real production browser recorded 2,550 full-resolution samples; stopping enabled local CSV export. | Pass |
| Custom stimulus and CSV interoperability | Dedicated import/validation and byte-compatible desktop recording regression suites pass. | Pass |
| Maximum-speed and bounded operation | Performance suite verifies 10,000-step scientific parity, 70,000-step bounded runs, catch-up limits and bounded scientific graph frames. | Pass |

## Accessibility, responsiveness and browser matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Accessible names | All 76 focusable or interactive elements on the deployed draft have an accessible label. | Pass |
| Keyboard semantics | Real browser keyboard Enter closes/reopens native panels; `aria-expanded` remains truthful; slider extrema reached by keyboard. | Pass |
| Announcements and landmarks | Semantic status/region/alert roles and polite atomic announcements observed; rapid scientific values are not live-announced. | Pass |
| Contrast and reduced motion | Audited WCAG text palette plus reduced-motion, forced-colours and high-contrast regression coverage. | Pass |
| Desktop layout | Real Chrome desktop viewport approximately 1,363 × 936; no document-width overflow; root remains scoped. | Pass |
| Laptop layout | Automated layout/media-query matrix passes; actual laptop-browser sign-off outstanding. | Pending real browser |
| Tablet layout | Automated 768–1,024 px layout matrix passes; physical/tablet-browser sign-off outstanding. | Pending real device |
| Mobile layout | Automated below-768 px layout and native collapsed-panel matrix passes; physical/mobile-browser sign-off outstanding. | Pending real device |
| Chrome | Authenticated real WordPress draft exercised end to end in Chrome. | Pass |
| Edge | No Edge browser environment was available for this audit. | Pending |
| Firefox | No Firefox browser environment was available for this audit. | Pending |
| Safari | No macOS/iOS Safari environment was available for this audit. | Pending |

Automated responsive checks are valuable regression protection; they do not
constitute a claim that a physical browser or device was actually exercised.

## WordPress, Elementor and published-page isolation

| Gate | Evidence | Status |
| --- | --- | --- |
| Real WordPress/PHP runtime | Active plugin rendered the actual scientific emulator on draft page 1196. | Pass |
| Shortcode and unique root | One isolated shortcode root initialised one production worker without duplicate initialisation. | Pass |
| Production asset integrity | Manifest pins one application, one dedicated worker and one scoped stylesheet; combined compressed payload 50,549 bytes. | Pass |
| Existing-page isolation | Original and redesigned published Spikeling pages contain zero emulator roots and load zero emulator JS/CSS assets. | Pass |
| Site console | No site-origin JavaScript errors observed; an unrelated browser-extension error is excluded. | Pass |
| Elementor storage/frontend contracts | Conditional `_elementor_data` lookup, dynamic shortcode fallback and duplicate-initialisation regressions pass. | Pass |
| Actual Elementor editor | A real editing session was not opened because conversion/auto-save could modify the draft without approval. | Pending |
| Logged-out frontend | An anonymous visitor cannot access an intentionally unpublished draft; verify after an approved staging/public route exists. | Pending |
| Existing original-page headings | The pre-existing published original Spikeling page contains two H1 elements. No published page was changed. | Existing editorial risk |

## Navigation and call-to-action acceptance

The published redesign presently contains exactly two `Try the emulator` buttons.
Both open `https://github.com/OpenSourceNeuro/Spikeling/releases/latest`, which
is the existing desktop-release destination, not the browser emulator.

Their future migration is specified in `wordpress/CTA-INTEGRATION.md`. Both
buttons must receive the same confirmed, publicly accessible HTTPS emulator
permalink only after explicit approval to publish page 1196 and edit the
identified live redesign. Do not link visitors to the authenticated draft
preview. Do not bulk-edit unrelated desktop-download links.

## Mandatory blockers before a production launch

1. Obtain direct, explicit owner approval for the exact production publication,
   approved URL, any existing-page edits and any requested navigation change.
2. Complete actual Edge, Firefox and Safari checks, or obtain a documented
   product-owner exception for unavailable environments.
3. Complete physical laptop/tablet/mobile browser checks, or document an
   explicitly accepted device-coverage exception.
4. Verify the real Elementor editing experience safely, or obtain a documented
   exception if the approved implementation intentionally remains block-only.
5. Verify an anonymous staging/public frontend once an approved route exists.
6. Update exactly two approved CTA links only after the final public emulator
   permalink has passed anonymous verification.
7. Repeat `npm run verify`, check both previously published pages for
   regressions and retain the previous CTA destination for narrowly scoped
   rollback.

**Current release decision: not authorised for publication.** The WordPress
emulator remains an unpublished draft; existing live content and navigation are
unchanged.
