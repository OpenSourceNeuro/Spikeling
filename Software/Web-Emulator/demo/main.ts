// SPDX-License-Identifier: GPL-3.0-or-later

import {
  DESKTOP_STEPS_PER_UPDATE,
  EmulatorSource,
  SpikelingMainControls,
  SpikelingOscilloscope,
  SpikelingRecorder,
  SpikelingRecordingControls,
  SpikelingSynapseControls,
  getSimulationSpeed,
} from "../src/index.ts";

function requiredElement<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (element === null) {
    throw new Error("Missing local-preview element: " + id);
  }
  return element as T;
}

const host = requiredElement<HTMLElement>("oscilloscope");
const controlsHost = requiredElement<HTMLElement>("controls");
const recordingHost = requiredElement<HTMLElement>("recording");
const synapsesHost = requiredElement<HTMLElement>("synapses");
const speed = requiredElement<HTMLSelectElement>("speed");
const error = requiredElement<HTMLElement>("error");

for (const [index] of DESKTOP_STEPS_PER_UPDATE.entries()) {
  const setting = getSimulationSpeed(index);
  const option = document.createElement("option");
  option.value = String(index);
  option.textContent = setting.realtimeMultiplier + "× real time";
  option.selected = index === 2;
  speed.append(option);
}

const source = new EmulatorSource({
  speedIndex: 2,
  simulation: {
    seed: 123456,
  },
});

const oscilloscope = new SpikelingOscilloscope(host, source);
const recorder = new SpikelingRecorder(source);
const recording = new SpikelingRecordingControls(recordingHost, recorder);
const controls = new SpikelingMainControls(controlsHost, source, {
  devicePixelRatio: () => window.devicePixelRatio,
});
const synapses = new SpikelingSynapseControls(synapsesHost, source, {
  oscilloscope,
});
source.subscribeErrors((failure) => {
  error.textContent = failure.message;
});

requiredElement<HTMLButtonElement>("start").addEventListener("click", () => source.start());
requiredElement<HTMLButtonElement>("pause").addEventListener("click", () => source.pause());
requiredElement<HTMLButtonElement>("stop").addEventListener("click", () => source.stop());
requiredElement<HTMLButtonElement>("reset").addEventListener("click", () => source.reset());
speed.addEventListener("change", () => source.setSpeed(Number(speed.value)));

window.addEventListener("pagehide", () => {
  oscilloscope.dispose();
  controls.dispose();
  recording.dispose();
  recorder.dispose();
  synapses.dispose();
  void source.disconnect();
});

try {
  await source.connect();
} catch (failure) {
  error.textContent =
    failure instanceof Error ? failure.message : "Unable to initialise the emulator worker.";
}
