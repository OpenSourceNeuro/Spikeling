// SPDX-License-Identifier: GPL-3.0-or-later

/** Palette values are pinned to the existing desktop Parameters_Settings.py. */
export const SPIKELING_PALETTE = Object.freeze({
  backgroundDeep: "#001E26",
  background: "#002B36",
  panel: "#073642",
  muted: "#586E75",
  secondary: "#93A1A1",
  text: "#BECDCD",
  light: "#FDF6E3",
  membrane: "#DC322F",
  cell: "#859900",
  stimulus: "#268BD2",
  synapse1Voltage: "#CB4B16",
  synapse1Current: "#2AA198",
  synapse2Voltage: "#B58900",
  synapse2Current: "#D33682",
});

export interface OscilloscopeTheme {
  readonly background: string;
  readonly panel: string;
  readonly grid: string;
  readonly muted: string;
  readonly text: string;
}

export const DEFAULT_OSCILLOSCOPE_THEME: OscilloscopeTheme = Object.freeze({
  background: SPIKELING_PALETTE.backgroundDeep,
  panel: SPIKELING_PALETTE.background,
  grid: SPIKELING_PALETTE.panel,
  muted: SPIKELING_PALETTE.secondary,
  text: SPIKELING_PALETTE.text,
});
