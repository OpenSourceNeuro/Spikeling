// SPDX-License-Identifier: GPL-3.0-or-later

import { parentPort } from "node:worker_threads";

import type { MainToWorkerMessage, WorkerToMainMessage } from "../../src/index.ts";

if (parentPort === null) {
  throw new Error("The Node worker adapter requires a parent port.");
}

const port = parentPort;
const listeners = new Set<
  (event: { readonly data: MainToWorkerMessage }) => void
>();
const browserScope = globalThis as unknown as {
  addEventListener: (
    type: "message",
    listener: (event: { readonly data: MainToWorkerMessage }) => void,
  ) => void;
  postMessage: (message: WorkerToMainMessage, transfer?: readonly ArrayBuffer[]) => void;
};

browserScope.addEventListener = (_type, listener) => listeners.add(listener);
browserScope.postMessage = (message, transfer) =>
  port.postMessage(message, transfer ?? []);

// Exercise the production browser-worker entry point in a genuine Node thread.
await import("../../src/worker/emulator.worker.ts");
port.on("message", (message: MainToWorkerMessage) => {
  for (const listener of listeners) {
    listener({ data: message });
  }
});
