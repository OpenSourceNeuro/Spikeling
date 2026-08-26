# Sources and references

Source codes used throughout the module catalogue resolve here. Repository behaviour governs what Spikeling can teach directly; neuroscience sources govern interpretation and limitations.

## References and source key

**\[T1\]** Izhikevich, E. M. (2007). Dynamical Systems in Neuroscience: The Geometry of Excitability and Bursting. MIT Press. Ch.1 p.1; Ch.2 p.25; Ch.3 p.53; Ch.4 p.89; Ch.5 p.127; Ch.6 p.159; Ch.7 p.215; Ch.8 p.267; Ch.9 p.325; Ch.10 p.385.

**\[T2\]** Kandel, E. R., et al. (2021). Principles of Neural Science (6th ed.). McGraw Hill. Especially Chs.3,5–17 and modality-specific sensory chapters.

**\[T3\]** Bear, M. F., Connors, B. W., & Paradiso, M. A. (2020). Neuroscience: Exploring the Brain, Enhanced 4th ed. Jones & Bartlett. Chs.2–5 and 8–12.

**\[T4\]** Purves, D., et al. (2001). Neuroscience (2nd ed.). Sinauer/NCBI Bookshelf. Part I Chs.2–8; Part II sensory chapters.

**\[T5\]** Dayan, P., & Abbott, L. F. (2001). Theoretical Neuroscience. MIT Press. Ch.1 p.3; Ch.2 p.45; Ch.3 p.87; Ch.4 p.123; Ch.5 p.153; Ch.6 p.195; Ch.7 p.229; Ch.8 p.281; Ch.9 p.331; Ch.10 p.359.

**\[T6\]** Gerstner, W., Kistler, W. M., Naud, R., & Paninski, L. (2014). Neuronal Dynamics. Cambridge University Press; open online edition and exercises.

**\[P1\]** Izhikevich, E. M. (2003). Simple model of spiking neurons. IEEE Transactions on Neural Networks, 14, 1569–1572.

**\[M1\]** Molecular Devices. The Axon Guide: A Guide to Electrophysiology and Biophysics Laboratory Techniques; official current-clamp and voltage-clamp method pages.

**\[R1\]** Zucker, R. S., & Regehr, W. G. (2002). Short-term synaptic plasticity. Annual Review of Physiology, 64, 355–405. doi:10.1146/annurev.physiol.64.092501.114547.

**\[O1\]** Neuromatch Academy. Computational Neuroscience curriculum: model types, model fitting, GLMs, signal processing, biological neuron models, dynamic synapses and dynamical systems. CC BY 4.0.

**\[P2\]** Vogelstein, J. T., et al. (2010). Fast nonnegative deconvolution for spike train inference from population calcium imaging. Journal of Neurophysiology, 104, 3691–3704. doi:10.1152/jn.01073.2009.

**\[O3\]** Suite2p documentation: ROI classification, signal extraction, neuropil correction and spike deconvolution.

**\[P3\]** Gold, C., Henze, D. A., Koch, C., & Buzsáki, G. (2006). On the origin of the extracellular action potential waveform: a modeling study. Journal of Neurophysiology, 95, 3113–3128. doi:10.1152/jn.00979.2005.

**\[P4\]** Harris, K. D., et al. (2000). Accuracy of tetrode spike separation as determined by simultaneous intracellular and extracellular measurements. Journal of Neurophysiology, 84, 401–414. doi:10.1152/jn.2000.84.1.401.

**\[O2\]** SpikeInterface official documentation and Jupyter tutorials: preprocessing, sorting, ground-truth comparison, curation and quality metrics.

**\[O4\]** Open Ephys GUI official documentation: acquisition sampling, filtering, TTL events, common average reference, spike detection and sorting.

**\[O5\]** Neurodata Without Borders official documentation and NWB format specification for intracellular, extracellular, optical and stimulus time series.

**\[O6\]** NC3Rs Experimental Design Assistant: experimental units, variables, controls, randomisation, blinding, sample size and analysis planning.

**\[O7\]** The Turing Way: Guides for Reproducible Research, Research Data Management, Project Design and Communication.

**\[P5\]** Wilkinson, M. D., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. Scientific Data, 3, 160018. doi:10.1038/sdata.2016.18.

**\[R4\]** Calin-Jageman, R. J., & Cumming, G. (2019). Estimation for better inference in neuroscience. eNeuro, 6. PMCID: PMC6709209.

**\[R5\]** Calin-Jageman, R. J. (2018). The new statistics for neuroscience majors: thinking in effect sizes. Journal of Undergraduate Neuroscience Education, 16, E21–E25.

**\[G1\]** OpenSourceNeuro/Spikeling README.md at audited main snapshot: platform scope, physical interfaces, recording, multi-board networks and teaching use.

**\[G2\]** Firmware/Spikeling_V3/Izhikevich_parameters.h: twenty implemented presets and parameter table.

**\[G3\]** Firmware/Spikeling_V3/Core_functions.h and Spikeling_V3.ino: current, noise, photodiode, synapses, stimulus, clamp and Izhikevich update.

**\[G4\]** Software/GUI - PyQt6-PySide6/Graph_Spikeling.py and Page_Spikeling_NeuronInterface.py: live plotting, recording, custom stimulus and timing controls.

**\[G5\]** Firmware/Spikeling_V3/Serial_functions.h and General_settings.h: commands, adjustable update period, packet fields and scales.

**\[G6\]** Software/GUI - PyQt6-PySide6/Graph_Imaging.py: spike detection, calcium/indicator forward model, frame sampling, fluorescence and recording.

**\[G7\]** Software/GUI - PyQt6-PySide6/Graph_ExtraCellular.py: reduced tetrode forward model, geometry, noise, CAR, filtering, detection and ground truth.

**\[G8\]** Software/README.md: GUI pages and dependencies.

**\[G9\]** Documentation/docs/user-guide/recording-and-export.md and Page_Spikeling_DataAnalysis.py: CSV schema, recording practice, plotting and built-in detection/rate workflow.

### Online access points

- [Spikeling source repository](https://github.com/OpenSourceNeuro/Spikeling)
- [Izhikevich, *Dynamical Systems in Neuroscience*](https://direct.mit.edu/books/monograph/2589/Dynamical-Systems-in-NeuroscienceThe-Geometry-of)
- [*Neuronal Dynamics* open online edition](https://neuronaldynamics.epfl.ch/online/)
- [Neuromatch Computational Neuroscience curriculum](https://compneuro.neuromatch.io/)
- [Purves *Neuroscience* on NCBI Bookshelf](https://www.ncbi.nlm.nih.gov/books/NBK10799/toc/)
- [Molecular Devices electrophysiology resources](https://www.moleculardevices.com/applications/patch-clamp-electrophysiology)
- [Suite2p documentation](https://suite2p.readthedocs.io/)
- [SpikeInterface documentation](https://spikeinterface.readthedocs.io/)
- [Open Ephys GUI documentation](https://open-ephys.github.io/gui-docs/)
- [Neurodata Without Borders](https://nwb.org/)
- [NC3Rs Experimental Design Assistant](https://eda.nc3rs.org.uk/)
- [The Turing Way](https://book.the-turing-way.org/)
