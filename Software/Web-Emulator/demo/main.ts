// SPDX-License-Identifier: GPL-3.0-or-later

import {
  EmulatorSource,
  SpikelingEmulator,
} from "../src/index.ts";

const host = document.getElementById("emulator");
if (host === null) {
  throw new Error("Missing local-preview emulator mount.");
}

const source = new EmulatorSource({
  speedIndex: 2,
  simulation: {
    seed: 123456,
  },
});

const emulator = new SpikelingEmulator(host, source, {
  oscilloscope: { devicePixelRatio: () => window.devicePixelRatio },
  controls: { devicePixelRatio: () => window.devicePixelRatio },
});

window.addEventListener("pagehide", () => {
  emulator.dispose();
  void source.disconnect();
});

await source.connect();
