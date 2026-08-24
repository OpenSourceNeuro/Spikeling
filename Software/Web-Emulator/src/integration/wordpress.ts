// SPDX-License-Identifier: GPL-3.0-or-later

import type { DataSource } from "../data-source/DataSource.ts";
import { EmulatorSource } from "../data-source/EmulatorSource.ts";
import { SpikelingEmulator } from "../interface/emulator.ts";
import type { EmulatorInterfaceOptions } from "../interface/emulator.ts";
import { DEFAULT_RECORDING_MAX_SAMPLES } from "../recording/csv.ts";
import { DEFAULT_SPEED_INDEX, DESKTOP_STEPS_PER_UPDATE } from "../simulation/speed.ts";

export const WORDPRESS_EMULATOR_SELECTOR = "[data-spikeling-emulator]";
export const DEFAULT_WORDPRESS_SEED = 123_456;
export const MAX_WORDPRESS_RECORDING_SAMPLES = 1_000_000;

export interface WordPressConfiguration {
  readonly speedIndex: number;
  readonly seed: number;
  readonly maxSamples: number;
}

export interface WordPressMountedEmulator {
  readonly host: HTMLElement;
  readonly source: DataSource;
  readonly emulator: SpikelingEmulator;
  readonly configuration: WordPressConfiguration;
  dispose(): Promise<void>;
}

export interface WordPressObserver {
  observe(target: Node, options: MutationObserverInit): void;
  disconnect(): void;
}

export interface WordPressIntegrationOptions {
  readonly sourceFactory?: (configuration: WordPressConfiguration) => DataSource;
  readonly interfaceOptions?: EmulatorInterfaceOptions;
  readonly observerFactory?: (callback: () => void) => WordPressObserver;
  readonly eventTarget?: Pick<Window, "addEventListener" | "removeEventListener">;
}

export interface WordPressIntegrationController {
  scan(): void;
  dispose(): Promise<void>;
}

const mountedRoots = new WeakMap<HTMLElement, Promise<WordPressMountedEmulator>>();
const activeDocuments = new WeakMap<Document, WordPressIntegrationController>();

function integerAttribute(value: string | undefined, fallback: number, minimum: number, maximum: number, name: string): number {
  if (value === undefined || value === "") return fallback;
  if (!/^\d+$/.test(value)) throw new RangeError(name + " must be a positive integer.");
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new RangeError(name + " must be between " + minimum + " and " + maximum + ".");
  }
  return parsed;
}

/** Read only the safely bounded attributes emitted by the WordPress shortcode. */
export function parseWordPressConfiguration(host: HTMLElement): WordPressConfiguration {
  return {
    speedIndex: integerAttribute(host.dataset.spikelingSpeed, DEFAULT_SPEED_INDEX, 0,
      DESKTOP_STEPS_PER_UPDATE.length - 1, "Simulation speed"),
    seed: integerAttribute(host.dataset.spikelingSeed, DEFAULT_WORDPRESS_SEED, 1,
      0xffff_ffff, "Simulation random seed"),
    maxSamples: integerAttribute(host.dataset.spikelingMaxSamples, DEFAULT_RECORDING_MAX_SAMPLES, 1,
      MAX_WORDPRESS_RECORDING_SAMPLES, "Scientific recording capacity"),
  };
}

function reportFailure(host: HTMLElement, failure: unknown): void {
  host.dataset.spikelingState = "error";
  const alert = host.ownerDocument.createElement("p");
  alert.className = "osn-spikeling-emulator__error";
  alert.setAttribute("role", "alert");
  alert.textContent = failure instanceof Error ? failure.message : "Unable to initialise the neuronal emulator.";
  host.append(alert);
}

/** Idempotent per root even when Elementor and DOM observers initialise together. */
export function mountWordPressEmulator(
  host: HTMLElement,
  options: WordPressIntegrationOptions = {},
): Promise<WordPressMountedEmulator> {
  const existing = mountedRoots.get(host);
  if (existing !== undefined) return existing;

  let configuration: WordPressConfiguration;
  try {
    configuration = parseWordPressConfiguration(host);
  } catch (failure) {
    reportFailure(host, failure);
    return Promise.reject(failure);
  }

  host.dataset.spikelingState = "mounting";
  let source: DataSource;
  let emulator: SpikelingEmulator;
  try {
    source = options.sourceFactory?.(configuration) ?? new EmulatorSource({
      speedIndex: configuration.speedIndex,
      simulation: {
        seed: configuration.seed,
        controls: {
          main: { noiseLevel: 5 },
          synapse1: { noiseLevel: 5, gain: 10 },
          synapse2: { noiseLevel: 5, gain: -10 },
          stimulus: { strength: 10 },
        },
      },
    });
    emulator = new SpikelingEmulator(host, source, {
      ...options.interfaceOptions,
      recorder: { ...options.interfaceOptions?.recorder, maxSamples: configuration.maxSamples },
    });
  } catch (failure) {
    reportFailure(host, failure);
    return Promise.reject(failure);
  }

  let disposed = false;
  const connection = Promise.resolve()
    .then(() => source.connect())
    .then(() => {
      host.dataset.spikelingState = "ready";
      return {
        host,
        source,
        emulator,
        configuration,
        async dispose(): Promise<void> {
          if (disposed) return;
          disposed = true;
          emulator.dispose();
          await source.disconnect();
          host.dataset.spikelingState = "disposed";
          mountedRoots.delete(host);
        },
      } satisfies WordPressMountedEmulator;
    })
    .catch(async (failure: unknown) => {
      emulator.dispose();
      try {
        await source.disconnect();
      } catch {
        // Preserve the original connection failure after best-effort cleanup.
      }
      mountedRoots.delete(host);
      reportFailure(host, failure);
      throw failure;
    });
  mountedRoots.set(host, connection);
  return connection;
}

/** Conditional root discovery supports Elementor-rendered and later-added shortcodes. */
export function initialiseWordPressEmulators(
  owner: Document,
  options: WordPressIntegrationOptions = {},
): WordPressIntegrationController {
  const previous = activeDocuments.get(owner);
  if (previous !== undefined) return previous;

  const connections = new Set<Promise<WordPressMountedEmulator>>();
  let disposed = false;
  let observer: WordPressObserver | undefined;
  const target = options.eventTarget ?? owner.defaultView ?? undefined;

  function scan(): void {
    if (disposed) return;
    for (const element of owner.querySelectorAll<HTMLElement>(WORDPRESS_EMULATOR_SELECTOR)) {
      const pending = mountWordPressEmulator(element, options);
      if (!connections.has(pending)) {
        connections.add(pending);
        void pending.catch(() => {});
      }
    }
  }

  function begin(): void {
    scan();
    const factory = options.observerFactory
      ?? (typeof MutationObserver === "undefined" ? undefined : (callback: () => void) => new MutationObserver(callback));
    if (factory !== undefined && owner.body !== null) {
      observer = factory(scan);
      observer.observe(owner.body, { childList: true, subtree: true });
    }
  }

  async function dispose(): Promise<void> {
    if (disposed) return;
    disposed = true;
    observer?.disconnect();
    owner.removeEventListener("DOMContentLoaded", begin);
    target?.removeEventListener("pagehide", handlePageHide);
    target?.removeEventListener("elementor/frontend/init", scan);
    const completed = await Promise.allSettled(connections);
    await Promise.all(completed
      .filter((result): result is PromiseFulfilledResult<WordPressMountedEmulator> => result.status === "fulfilled")
      .map((result) => result.value.dispose()));
    connections.clear();
    activeDocuments.delete(owner);
  }

  function handlePageHide(): void { void dispose(); }
  const controller = { scan, dispose };
  activeDocuments.set(owner, controller);
  target?.addEventListener("pagehide", handlePageHide);
  target?.addEventListener("elementor/frontend/init", scan);

  if (owner.readyState === "loading") owner.addEventListener("DOMContentLoaded", begin, { once: true });
  else begin();
  return controller;
}
