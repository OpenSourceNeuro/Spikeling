# - Kd_uM and hill_n: equilibrium binding parameters (typically purified-protein titrations).
# - dff_max: intrinsic saturation amplitude, defined as (F_sat - F_apo)/F_apo = (Fmax/Fmin - 1).
# - tau_rise_ms / tau_decay_ms: “effective” imaging kinetics knobs for your real-time simulator.
#   For some indicators (notably red GECIs), very long “decays” reported in some cell assays
#   largely reflect cellular Ca2+ clearance, not intrinsic indicator off-kinetics.

GECI = {
    # Educational default
    "Generic"  : dict(Kd_uM=0.200, hill_n=2.0, Ind_tau_rise_ms=50.0,  Ind_tau_decay_ms=300.0,  dff_max=20.0),

    # Green GECIs
    # Affinity/cooperativity are well-documented; dynamic range varies by construct/assay.
    "GCaMP2"   : dict(Kd_uM=0.146, hill_n=3.8, Ind_tau_rise_ms=150.0, Ind_tau_decay_ms=1200.0, dff_max=3.9),

    # For GCaMP6 variants: keep your commonly-used Kd/Hill defaults for now,
    # but recognize these are assay-dependent (temperature, Mg2+, buffer, etc.).
    # Rise-time ranges in neurons are described in Chen et al. (2013).
    "GCaMP6s"  : dict(Kd_uM=0.144, hill_n=3.0, Ind_tau_rise_ms=125.0, Ind_tau_decay_ms=580.0,  dff_max=60.0),
    "GCaMP6m"  : dict(Kd_uM=0.167, hill_n=3.0, Ind_tau_rise_ms=90.0,  Ind_tau_decay_ms=220.0,  dff_max=55.0),
    "GCaMP6f"  : dict(Kd_uM=0.375, hill_n=3.0, Ind_tau_rise_ms=60.0,  Ind_tau_decay_ms=140.0,  dff_max=50.0),

    # Red GECIs (corrected to match purified-protein binding + dynamic range measurements;
    # and using imaging-relevant fast off-kinetics measured in neural tissue where available)
    "R-GECO1"  : dict(Kd_uM=0.480, hill_n=2.0, Ind_tau_rise_ms=200.0, Ind_tau_decay_ms=1500.0, dff_max=30.0),

    "jRGECO1a" : dict(Kd_uM=0.161, hill_n=1.8, Ind_tau_rise_ms=200.0, Ind_tau_decay_ms=314.0,  dff_max=13.0),
    "jRCaMP1a" : dict(Kd_uM=0.141, hill_n=1.5, Ind_tau_rise_ms=200.0, Ind_tau_decay_ms=327.0,  dff_max=6.0),

    # Optional additions (widely used “fast-decay” red variants from the same characterization set)
    "f-RGECO1" : dict(Kd_uM=1.200, hill_n=3.0, Ind_tau_rise_ms=120.0, Ind_tau_decay_ms=83.0,   dff_max=9.0),
    "f-RGECO2" : dict(Kd_uM=1.300, hill_n=5.8, Ind_tau_rise_ms=120.0, Ind_tau_decay_ms=77.0,   dff_max=13.0),
    "f-RCaMP1" : dict(Kd_uM=0.520, hill_n=2.3, Ind_tau_rise_ms=150.0, Ind_tau_decay_ms=211.0,  dff_max=5.0),
    "f-RCaMP2" : dict(Kd_uM=0.785, hill_n=3.5, Ind_tau_rise_ms=150.0, Ind_tau_decay_ms=140.0,  dff_max=5.0),
}
