# **Roadmap**

This roadmap outlines planned improvements for Spikeling. It is aspirational and may change based on classroom feedback, contributor availability, and hardware supply constraints.

## **Guiding priorities**

1. **Teaching reliability**: predictable experiments, robust setup, fewer “mystery failures”.
2. **Clarity and documentation**: reduce load for first-time users and instructors.
3. **Reproducible data**: stable export formats and versioning across firmware/GUI.
4. **Extensibility**: make it easy to add stimuli, models, and multi-unit experiments.

## **Near-term (next 1–2 releases)**

- **Documentation polish**
  - Complete Quickstart and the canonical “First experiment” workflow.
  - Add troubleshooting decision trees for common classroom issues.
- **GUI usability**
  - Improve responsiveness during long sessions (buffering/decimation best practices).
  - Presets for common lab protocols (steps, ramps, pulse trains, noise).
- **Firmware robustness**
  - Clear version handshake between GUI ↔ firmware.
  - More explicit error reporting for streaming and configuration.

## **Mid-term**

- **Experiment library**
  - A curated set of patch-clamp-style labs with expected outcomes and analysis notebooks.
  - A stimulus “recipe book” tied to learning objectives.
- **Multi-unit workflows**
  - Document and standardize wiring/topologies for simple networks (2–N devices).
  - Sync/trigger guidance for multi-device recordings.
- **Imaging simulation**
  - Better parameter documentation and example datasets.
  - Suggested teaching modules that bridge Vm ↔ calcium ↔ fluorescence interpretation.

## **Long-term**

- **Packaging and distribution**
  - Simplified installers for major platforms.
  - Fully versioned documentation with archived releases for reproducibility.
- **Hardware ecosystem**
  - Clear support policy for board revisions.
  - Optional accessory ecosystem (mounting/enclosures, classroom wiring kits).
- **Community scaling**
  - Contributor pathways for educators (lab handouts, rubrics, translations).
  - Governance practices for reviewing and merging contributions.

## **Help wanted**

Contributions are welcome in the following areas:

- Writing and testing **teaching labs** (protocol + expected result + analysis)
- Improving **GUI performance and polish**
- Documenting **hardware assembly** with photos and checkpoints
- Expanding **data analysis notebooks** (spike features, F–I curves, imaging metrics)
- Translation/localization of key pages

See **Community → How to contribute** for contribution workflow and style guidance.
