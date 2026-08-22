// SPDX-License-Identifier: GPL-3.0-or-later

import { SimulationEngine } from "../simulation/clock.ts";
import type { SimulationScheduler } from "../simulation/clock.ts";
import type {
  MainToWorkerMessage,
  WorkerToMainMessage,
} from "../simulation/protocol.ts";
import { packSamples } from "../simulation/ring-buffer.ts";

export interface EmulatorWorkerRuntimeOptions {
  readonly postMessage: (
    message: WorkerToMainMessage,
    transfer?: readonly ArrayBuffer[],
  ) => void;
  readonly scheduler?: SimulationScheduler;
}

export interface EmulatorWorkerRuntime {
  handleMessage(message: MainToWorkerMessage): void;
  dispose(): void;
}

/** Transport-independent worker core; the entry point only supplies its port. */
export function createEmulatorWorkerRuntime(
  options: EmulatorWorkerRuntimeOptions,
): EmulatorWorkerRuntime {
  let engine: SimulationEngine | undefined;

  function requireEngine(): SimulationEngine {
    if (engine === undefined) {
      throw new Error("Initialise the emulator worker before sending commands.");
    }
    return engine;
  }

  function reportError(error: unknown): void {
    options.postMessage({
      type: "error",
      message: error instanceof Error ? error.message : String(error),
    });
  }

  return {
    handleMessage(message): void {
      try {
        switch (message.type) {
          case "initialise": {
            engine?.dispose();
            engine = new SimulationEngine({
              modelOptions: message.options,
              historyCapacity: message.historyCapacity,
              speedIndex: message.speedIndex,
              maxStepsPerSlice: message.maxStepsPerSlice,
              maxCatchUpTicks: message.maxCatchUpTicks,
              scheduler: options.scheduler,
              onSamples(samples) {
                const packed = packSamples(samples);
                const buffer = packed.buffer as ArrayBuffer;
                options.postMessage(
                  {
                    type: "samples",
                    count: samples.length,
                    firstTimeMs: samples[0].timeMs,
                    lastTimeMs: samples[samples.length - 1].timeMs,
                    buffer,
                  },
                  [buffer],
                );
              },
              onState(snapshot) {
                options.postMessage({ type: "state", snapshot });
              },
              onError: reportError,
            });
            options.postMessage({ type: "ready", snapshot: engine.getSnapshot() });
            break;
          }

          case "start":
            requireEngine().start();
            break;
          case "pause":
            requireEngine().pause();
            break;
          case "stop":
            requireEngine().stop();
            break;
          case "reset":
            requireEngine().reset(message.options);
            break;
          case "set-speed":
            requireEngine().setSpeed(message.index);
            break;
          case "update-controls":
            requireEngine().updateControls(message.patch);
            break;
          case "snapshot":
            options.postMessage({
              type: "snapshot",
              snapshot: requireEngine().getSnapshot(),
            });
            break;
          case "dispose":
            requireEngine().dispose();
            engine = undefined;
            break;
          default:
            throw new TypeError("Unknown emulator-worker command.");
        }
      } catch (error) {
        reportError(error);
      }
    },

    dispose(): void {
      engine?.dispose();
      engine = undefined;
    },
  };
}
