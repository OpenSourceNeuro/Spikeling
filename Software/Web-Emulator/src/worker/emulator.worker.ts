// SPDX-License-Identifier: GPL-3.0-or-later

import type { MainToWorkerMessage } from "../simulation/protocol.ts";
import { createEmulatorWorkerRuntime } from "./emulator-runtime.ts";

interface BrowserWorkerScope {
  addEventListener(
    type: "message",
    listener: (event: { readonly data: MainToWorkerMessage }) => void,
  ): void;
  postMessage(message: unknown, transfer?: readonly ArrayBuffer[]): void;
}

const scope = globalThis as unknown as BrowserWorkerScope;
const runtime = createEmulatorWorkerRuntime({
  postMessage: (message, transfer) => scope.postMessage(message, transfer),
});

scope.addEventListener("message", (event) => {
  runtime.handleMessage(event.data);
});
