// SPDX-License-Identifier: GPL-3.0-or-later

import type { SimulationSample } from "../model/types.ts";
import { SPIKELING_PALETTE } from "./theme.ts";

export type TraceAxis = "voltage" | "current";

export type TraceField =
  | "mainVm"
  | "stimulus"
  | "totalCurrent"
  | "synapse1Vm"
  | "synapse1Current"
  | "synapse2Vm"
  | "synapse2Current";

export interface OscilloscopeTrace {
  readonly id: TraceField;
  readonly label: string;
  readonly axis: TraceAxis;
  readonly colour: string;
  readonly colourVariable: string;
  readonly defaultVisible: boolean;
}

/** The order, separate axes and colours match SetPlot in Graph_Emulator.py. */
export const OSCILLOSCOPE_TRACES: readonly OscilloscopeTrace[] = Object.freeze([
  {
    id: "mainVm",
    label: "Membrane potential",
    axis: "voltage",
    colour: SPIKELING_PALETTE.membrane,
    colourVariable: "--spk-membrane",
    defaultVisible: true,
  },
  {
    id: "stimulus",
    label: "Stimulus",
    axis: "current",
    colour: SPIKELING_PALETTE.stimulus,
    colourVariable: "--spk-stimulus",
    defaultVisible: true,
  },
  {
    id: "totalCurrent",
    label: "Input current",
    axis: "current",
    colour: SPIKELING_PALETTE.cell,
    colourVariable: "--spk-cell",
    defaultVisible: true,
  },
  {
    id: "synapse1Vm",
    label: "Synapse 1 Vm",
    axis: "voltage",
    colour: SPIKELING_PALETTE.synapse1Voltage,
    colourVariable: "--spk-syn1-voltage",
    defaultVisible: false,
  },
  {
    id: "synapse1Current",
    label: "Synapse 1 input",
    axis: "current",
    colour: SPIKELING_PALETTE.synapse1Current,
    colourVariable: "--spk-syn1",
    defaultVisible: false,
  },
  {
    id: "synapse2Vm",
    label: "Synapse 2 Vm",
    axis: "voltage",
    colour: SPIKELING_PALETTE.synapse2Voltage,
    colourVariable: "--spk-syn2-voltage",
    defaultVisible: false,
  },
  {
    id: "synapse2Current",
    label: "Synapse 2 input",
    axis: "current",
    colour: SPIKELING_PALETTE.synapse2Current,
    colourVariable: "--spk-syn2",
    defaultVisible: false,
  },
] satisfies ReadonlyArray<{
  readonly id: keyof SimulationSample;
  readonly label: string;
  readonly axis: TraceAxis;
  readonly colour: string;
  readonly colourVariable: string;
  readonly defaultVisible: boolean;
}>);

export function getOscilloscopeTrace(id: TraceField): OscilloscopeTrace {
  const trace = OSCILLOSCOPE_TRACES.find((candidate) => candidate.id === id);
  if (trace === undefined) {
    throw new RangeError("Unknown oscilloscope trace: " + String(id));
  }
  return trace;
}

export function defaultVisibleTraces(): Set<TraceField> {
  return new Set(
    OSCILLOSCOPE_TRACES.filter((trace) => trace.defaultVisible).map(
      (trace) => trace.id,
    ),
  );
}
