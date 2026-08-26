# Development status and validation gates

The architecture identifies what should be developed first and which empirical checks must precede release. Inclusion in the catalogue does not mean that a student handout, notebook, dataset or answer key is already available.

## Initial development shortlist

| **Order** | **Module** | **Why it should be developed early**                                                    |
|-----------|------------|-----------------------------------------------------------------------------------------|
| 1         | FND-01     | Immediate accessibility; establishes physical engagement and common vocabulary.         |
| 2         | FND-02     | Prevents category errors across every later module.                                     |
| 3         | FND-04     | Creates the variable/unit discipline required for acquisition and notebooks.            |
| 4         | EPH-04     | Mandatory gateway for trustworthy temporal analysis.                                    |
| 5         | EPH-01     | Core experimental logic of command versus response.                                     |
| 6         | NPH-02     | Simple, visible and scientifically central polarity experiment.                         |
| 7         | NPH-03     | Introduces protocol-dependent threshold, measurement and uncertainty.                   |
| 8         | MET-01     | Turns exploration into scientific questioning early.                                    |
| 9         | MET-02     | Makes later feature extraction reproducible.                                            |
| 10        | MET-03     | Provides the protocol-design backbone for the library.                                  |
| 11        | DAT-01     | Standardises import, metadata and timebase before analysis.                             |
| 12        | DAT-02     | Establishes QC before automated measurements.                                           |
| 13        | DAT-03     | Reusable event-detection foundation for most quantitative strands.                      |
| 14        | DAT-04     | Introduces core spike-train summaries after timing validation.                          |
| 15        | STA-01     | Prevents pseudoreplication and makes variability visible.                               |
| 16        | STA-02     | Adds uncertainty and supports threshold, sensory and fitting modules.                   |
| 17        | SYN-01     | Uses a distinctive Spikeling capability and leads naturally to networks.                |
| 18        | SYN-02     | Directly demonstrates functional excitation/inhibition with explicit biological limits. |
| 19        | SEN-01     | Adds sensory input, outreach value and cross-domain flexibility.                        |
| 20        | CMP-01     | Connects hardware behaviour to the defining model equations.                            |

### Recommended development order and validation gates

> 1\. Wave A — common foundations: FND-01, FND-02, FND-04, MET-01 and MET-02.
>
> 2\. Gate 1 — platform timing/QC: empirically validate EPH-04 and define the metadata standard before finalising any timing-dependent values.
>
> 3\. Wave B — core experiments: EPH-01, NPH-02, NPH-03, SYN-01, SYN-02 and SEN-01.
>
> 4\. Wave C — analysis spine: DAT-01, DAT-02, DAT-03, DAT-04, STA-01 and STA-02.
>
> 5\. Wave D — computation and integration: CMP-01 plus the first network, imaging and extracellular bridge modules once their active parameters and timing are validated.
>
> 6\. Gate 2 — cross-board and simulation validation: measure network delays, confirm imaging preset application, and establish timestamped extracellular reference datasets before advanced modules are released.

### Three initial course bundles from the shortlist

| **Bundle**                             | **Modules**                                                            | **Purpose**                                                                                            |
|----------------------------------------|------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| A. First neurophysiology practical     | FND-01 → FND-04 → EPH-01 → NPH-02 → NPH-03 → DAT-02                    | A three- to four-hour first practical centred on manipulation, current clamp, threshold and QC.        |
| B. Experimental data pathway           | FND-02 → EPH-04 → MET-01/02/03 → DAT-01/02/03/04 → STA-01/02           | A one- to two-day methods course from question and timing validation to uncertainty.                   |
| C. Synapses, sensation and computation | SYN-01 → SYN-02 → SEN-01 → CMP-01, with FND-01/FND-04 as prerequisites | A half- or full-day bundle showcasing distinctive physical inputs, functional E/I and model equations. |

### Template for later full module development

| **Section**                      | **Required content**                                                                                             |
|----------------------------------|------------------------------------------------------------------------------------------------------------------|
| 1\. Version and validation       | Target board/firmware/GUI version; validation date; timing certificate; known limitations.                       |
| 2\. Teaching intent              | Concept statement, audience, prerequisites, duration, context and module relationship code.                      |
| 3\. Outcomes and evidence        | Observable learning outcomes and the learner artefact that demonstrates each.                                    |
| 4\. Instructor preparation       | Hardware setup, software environment, files, safety, pilot checks and fallback dataset.                          |
| 5\. Student activity             | Prediction, configuration, protocol execution, acquisition, analysis, interpretation and limitation.             |
| 6\. Data specification           | Variables, units, sample interval, metadata, file naming and expected QC checks.                                 |
| 7\. Analysis notebook            | Minimal scaffold, visible assumptions, tests, figures and reproducibility information.                           |
| 8\. Assessment                   | Short evidence-based questions, artefact criteria and misconception checks; model answers maintained separately. |
| 9\. Differentiation              | Lower-level, standard and advanced variants; outreach adaptation; accessibility considerations.                  |
| 10\. Sources and claims          | Textbook sections, methods sources, implementation references and explicit prohibited overclaims.                |
| 11\. Empirical validation record | Tested settings/ranges, failure modes, board-to-board variation and instructor troubleshooting.                  |
| 12\. Reuse connections           | Inputs inherited from earlier modules and outputs exported to later modules/course bundles.                      |
