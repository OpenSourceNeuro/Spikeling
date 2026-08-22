// SPDX-License-Identifier: GPL-3.0-or-later

import type {
  ControlsPatch,
  InitialisationMode,
  SimulationSample,
} from "../model/types.ts";
import type { EngineSnapshot } from "../simulation/protocol.ts";

export type SampleListener = (samples: readonly SimulationSample[]) => void;
export type StateListener = (snapshot: EngineSnapshot) => void;
export type ErrorListener = (error: Error) => void;
export type Unsubscribe = () => void;

/** Future hardware and emulator sources share one UI-independent boundary. */
export interface DataSource {
  readonly kind: "emulator" | "hardware";
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  start(): void;
  pause(): void;
  stop(): void;
  reset(options?: { readonly seed?: number; readonly initialisation?: InitialisationMode }): void;
  setSpeed(index: number): void;
  updateControls(patch: ControlsPatch): void;
  requestSnapshot(): void;
  subscribe(listener: SampleListener): Unsubscribe;
  subscribeState(listener: StateListener): Unsubscribe;
  subscribeErrors(listener: ErrorListener): Unsubscribe;
  latest(count?: number): SimulationSample[];
}
