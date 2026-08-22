// SPDX-License-Identifier: GPL-3.0-or-later

import type {
  ControlsPatch,
  InitialisationMode,
  SimulationControls,
  SimulationOptions,
} from "../model/types.ts";
import type { SimulationSpeed } from "./speed.ts";

/** Custom random-source functions cannot cross a browser worker boundary. */
export type TransferableSimulationOptions = Omit<SimulationOptions, "randomSource">;

export type SimulationLifecycle = "idle" | "running" | "paused" | "stopped";

export interface EngineSnapshot {
  readonly lifecycle: SimulationLifecycle;
  readonly speed: SimulationSpeed;
  readonly stepIndex: number;
  readonly retainedSamples: number;
  readonly historyCapacity: number;
  readonly historyBytes: number;
  readonly pendingSteps: number;
  readonly droppedSteps: number;
  readonly controls: SimulationControls;
}

export type MainToWorkerMessage =
  | {
      readonly type: "initialise";
      readonly options?: TransferableSimulationOptions;
      readonly historyCapacity?: number;
      readonly speedIndex?: number;
      readonly maxStepsPerSlice?: number;
      readonly maxCatchUpTicks?: number;
    }
  | { readonly type: "start" }
  | { readonly type: "pause" }
  | { readonly type: "stop" }
  | {
      readonly type: "reset";
      readonly options?: { readonly seed?: number; readonly initialisation?: InitialisationMode };
    }
  | { readonly type: "set-speed"; readonly index: number }
  | { readonly type: "update-controls"; readonly patch: ControlsPatch }
  | { readonly type: "snapshot" }
  | { readonly type: "dispose" };

export type WorkerToMainMessage =
  | { readonly type: "ready"; readonly snapshot: EngineSnapshot }
  | { readonly type: "state"; readonly snapshot: EngineSnapshot }
  | { readonly type: "snapshot"; readonly snapshot: EngineSnapshot }
  | {
      readonly type: "samples";
      readonly count: number;
      readonly firstTimeMs: number;
      readonly lastTimeMs: number;
      readonly buffer: ArrayBuffer;
    }
  | { readonly type: "error"; readonly message: string };
