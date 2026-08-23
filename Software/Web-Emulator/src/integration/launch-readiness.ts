// SPDX-License-Identifier: GPL-3.0-or-later

import { DESKTOP_STEPS_PER_UPDATE } from "../simulation/speed.ts";

/** Release decisions must distinguish real browser evidence from emulation. */
export const REQUIRED_RELEASE_BROWSERS = ["Chrome", "Edge", "Firefox", "Safari"] as const;
export const REQUIRED_RELEASE_VIEWPORTS = [
  "large-desktop", "laptop", "tablet", "mobile",
] as const;
export const EXPECTED_EMULATOR_CTA_COUNT = 2;
export const EXISTING_DESKTOP_RELEASE_URL =
  "https://github.com/OpenSourceNeuro/Spikeling/releases/latest";
export const APPROVED_WEBSITE_ORIGIN = "https://www.opensourceneuro.com";

export type ReleaseBrowser = typeof REQUIRED_RELEASE_BROWSERS[number];
export type ReleaseViewport = typeof REQUIRED_RELEASE_VIEWPORTS[number];
export type LaunchGateStatus = "pass" | "pending" | "blocked";
export type CoverageEvidence = "browser" | "automated" | "missing";

export interface CoverageEntry {
  readonly name: string;
  readonly evidence: CoverageEvidence;
  readonly status: LaunchGateStatus;
}

export interface SpikelingCallToAction {
  readonly label: string;
  readonly href: string;
}

export interface LaunchEvidence {
  readonly capturedAt: string;
  readonly pageId: number;
  readonly pageStatus: "draft" | "private" | "published";
  readonly pluginActive: boolean;
  readonly desktopReferenceScenarios: number;
  readonly neuronPresetCount: number;
  readonly speedCount: number;
  readonly verifiedBrowsers: readonly ReleaseBrowser[];
  readonly realViewports: readonly ReleaseViewport[];
  readonly automatedViewports: readonly ReleaseViewport[];
  readonly elementorEditorVerified: boolean;
  readonly anonymousFrontendVerified: boolean;
  readonly noSiteConsoleErrors: boolean;
  readonly assetIsolationVerified: boolean;
  readonly ctas: readonly SpikelingCallToAction[];
  readonly finalPublicUrl: string | null;
  readonly publishingApproved: boolean;
}

export interface LaunchGate {
  readonly id: string;
  readonly status: LaunchGateStatus;
  readonly detail: string;
}

export interface LaunchReadiness {
  readonly status: LaunchGateStatus;
  readonly publishAllowed: boolean;
  readonly browsers: readonly CoverageEntry[];
  readonly viewports: readonly CoverageEntry[];
  readonly gates: readonly LaunchGate[];
}

function coverage(
  required: readonly string[],
  browserEvidence: readonly string[],
  automatedEvidence: readonly string[] = [],
): CoverageEntry[] {
  for (const value of [...browserEvidence, ...automatedEvidence]) {
    if (!required.includes(value)) {
      throw new RangeError("Unknown launch-matrix entry: " + value);
    }
  }

  return required.map((name) => {
    const evidence: CoverageEvidence = browserEvidence.includes(name)
      ? "browser"
      : automatedEvidence.includes(name)
        ? "automated"
        : "missing";
    return { name, evidence, status: evidence === "browser" ? "pass" : "pending" };
  });
}

export function assessBrowserCoverage(observed: readonly ReleaseBrowser[]): CoverageEntry[] {
  return coverage(REQUIRED_RELEASE_BROWSERS, observed);
}

export function assessViewportCoverage(
  observed: readonly ReleaseViewport[],
  automated: readonly ReleaseViewport[] = [],
): CoverageEntry[] {
  return coverage(REQUIRED_RELEASE_VIEWPORTS, observed, automated);
}

function publicEmulatorUrl(value: string): URL | undefined {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return undefined;
  }

  if (url.origin !== APPROVED_WEBSITE_ORIGIN || url.pathname === "/"
    || url.search || url.hash || url.username || url.password) {
    return undefined;
  }
  return url;
}

export function assessEmulatorCallsToAction(
  links: readonly SpikelingCallToAction[],
  finalPublicUrl: string | null = null,
): LaunchGate {
  const candidates = links.filter((link) => /try\s+(?:the\s+)?(?:browser\s+)?emulator/i.test(link.label));
  if (candidates.length !== EXPECTED_EMULATOR_CTA_COUNT) {
    return {
      id: "spikeling-ctas",
      status: "blocked",
      detail: "Expected exactly " + EXPECTED_EMULATOR_CTA_COUNT
        + " emulator calls to action; found " + candidates.length + ".",
    };
  }

  if (finalPublicUrl !== null && publicEmulatorUrl(finalPublicUrl) === undefined) {
    return {
      id: "spikeling-ctas",
      status: "blocked",
      detail: "The final emulator destination must be a confirmed, public HTTPS Open Source Neuro permalink.",
    };
  }

  if (candidates.every((link) => link.href === EXISTING_DESKTOP_RELEASE_URL)) {
    return {
      id: "spikeling-ctas",
      status: "pending",
      detail: "Both published buttons still open the desktop release; update only after explicit publication approval.",
    };
  }

  if (finalPublicUrl !== null && candidates.every((link) => link.href === finalPublicUrl)) {
    return {
      id: "spikeling-ctas",
      status: "pass",
      detail: "Both emulator buttons use the confirmed public Open Source Neuro permalink.",
    };
  }

  return {
    id: "spikeling-ctas",
    status: "blocked",
    detail: "Emulator buttons contain mixed, draft-preview or unapproved destinations.",
  };
}

function matrixGate(id: string, entries: readonly CoverageEntry[], noun: string): LaunchGate {
  const missing = entries.filter((entry) => entry.status !== "pass");
  return missing.length === 0
    ? { id, status: "pass", detail: "All required " + noun + " have real browser evidence." }
    : {
      id,
      status: "pending",
      detail: "Real-browser evidence remains outstanding for "
        + missing.map((entry) => entry.name).join(", ") + ".",
    };
}

/** Pure release assessment: no site changes, network calls or approval inference. */
export function assessLaunchReadiness(evidence: LaunchEvidence): LaunchReadiness {
  const browsers = assessBrowserCoverage(evidence.verifiedBrowsers);
  const viewports = assessViewportCoverage(evidence.realViewports, evidence.automatedViewports);
  const prematurePublication = evidence.pageStatus === "published" && !evidence.publishingApproved;
  const scenariosValid = evidence.desktopReferenceScenarios >= 33
    && evidence.neuronPresetCount === 20
    && evidence.speedCount === DESKTOP_STEPS_PER_UPDATE.length;

  const gates: LaunchGate[] = [
    {
      id: "editorial-safety",
      status: prematurePublication ? "blocked" : "pass",
      detail: prematurePublication
        ? "The emulator page became public without explicit approval."
        : "Page " + evidence.pageId + " remains in its authorised " + evidence.pageStatus + " state.",
    },
    {
      id: "wordpress-plugin",
      status: evidence.pluginActive ? "pass" : "blocked",
      detail: evidence.pluginActive ? "The isolated emulator plugin is active." : "The emulator plugin is not active.",
    },
    {
      id: "scientific-regressions",
      status: scenariosValid ? "pass" : "blocked",
      detail: evidence.desktopReferenceScenarios + " desktop-reference scenarios; "
        + evidence.neuronPresetCount + " presets; " + evidence.speedCount + " speeds.",
    },
    matrixGate("browser-matrix", browsers, "browsers"),
    matrixGate("responsive-matrix", viewports, "viewport classes"),
    {
      id: "elementor-editor",
      status: evidence.elementorEditorVerified ? "pass" : "pending",
      detail: evidence.elementorEditorVerified
        ? "The real Elementor editor was verified."
        : "Real Elementor-editor verification remains outstanding; static integration contracts pass.",
    },
    {
      id: "anonymous-frontend",
      status: evidence.anonymousFrontendVerified ? "pass" : "pending",
      detail: evidence.anonymousFrontendVerified
        ? "The anonymous public or authorised staging frontend was verified."
        : "An anonymous frontend cannot be verified while the emulator page is an unpublished draft.",
    },
    {
      id: "site-console",
      status: evidence.noSiteConsoleErrors ? "pass" : "blocked",
      detail: evidence.noSiteConsoleErrors
        ? "No site-origin JavaScript errors were observed."
        : "Site-origin JavaScript errors require investigation.",
    },
    {
      id: "asset-isolation",
      status: evidence.assetIsolationVerified ? "pass" : "blocked",
      detail: evidence.assetIsolationVerified
        ? "Existing published pages load no emulator JavaScript, worker or stylesheet."
        : "Emulator assets leaked onto an unrelated published page.",
    },
    assessEmulatorCallsToAction(evidence.ctas, evidence.finalPublicUrl),
    {
      id: "publication-approval",
      status: evidence.publishingApproved ? "pass" : "blocked",
      detail: evidence.publishingApproved
        ? "The owner explicitly authorised the specific production publication."
        : "Publishing, production navigation and existing-page changes require separate explicit owner approval.",
    },
  ];

  const status: LaunchGateStatus = gates.some((gate) => gate.status === "blocked")
    ? "blocked"
    : gates.some((gate) => gate.status === "pending")
      ? "pending"
      : "pass";
  return { status, publishAllowed: status === "pass", browsers, viewports, gates };
}
