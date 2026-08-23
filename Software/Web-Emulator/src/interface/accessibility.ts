// SPDX-License-Identifier: GPL-3.0-or-later

/** Desktop trace colours remain unchanged; these lighter variants are for text. */
export const ACCESSIBLE_SPIKELING_PALETTE = Object.freeze({
  background: "#002B36",
  panel: "#073642",
  foreground: "#EEE8D5",
  secondary: "#A3B1B1",
  stimulusText: "#80C9FF",
  cellText: "#B4CA60",
  synapse1Text: "#67D3C7",
  synapse2Text: "#F08AC3",
  warningText: "#E4C36A",
  errorText: "#FF8E8B",
  focus: "#FDF6E3",
});

export const DESKTOP_MINIMUM_WIDTH = 1_025;
export const TABLET_MINIMUM_WIDTH = 768;
export const TABLET_MEDIA_QUERY = "(max-width: 1024px)";
export const MOBILE_MEDIA_QUERY = "(max-width: 767px)";
export const REDUCED_MOTION_MEDIA_QUERY = "(prefers-reduced-motion: reduce)";

export type EmulatorLayout = "desktop" | "tablet" | "mobile";
export type ContrastConformance = "AA" | "AAA";

export interface ContrastOptions {
  readonly level?: ContrastConformance;
  readonly largeText?: boolean;
}

/** WCAG 2.x sRGB relative luminance for a validated six-digit CSS colour. */
export function relativeLuminance(colour: string): number {
  if (!/^#[0-9a-fA-F]{6}$/.test(colour)) {
    throw new RangeError("Accessible colours must use a six-digit hexadecimal value.");
  }
  const components = [1, 3, 5].map((offset) => {
    const value = Number.parseInt(colour.slice(offset, offset + 2), 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * components[0] + 0.7152 * components[1] + 0.0722 * components[2];
}

export function contrastRatio(first: string, second: string): number {
  const left = relativeLuminance(first);
  const right = relativeLuminance(second);
  return (Math.max(left, right) + 0.05) / (Math.min(left, right) + 0.05);
}

export function meetsTextContrast(foreground: string, background: string, options: ContrastOptions = {}): boolean {
  const level = options.level ?? "AA";
  if (level !== "AA" && level !== "AAA") {
    throw new RangeError("Contrast conformance must be WCAG AA or AAA.");
  }
  const minimum = level === "AAA" ? (options.largeText ? 4.5 : 7) : (options.largeText ? 3 : 4.5);
  return contrastRatio(foreground, background) >= minimum;
}

/** Keep responsive boundaries explicit and independently testable. */
export function emulatorLayout(width: number): EmulatorLayout {
  if (!Number.isFinite(width) || width <= 0) {
    throw new RangeError("An emulator viewport width must be a positive finite number.");
  }
  if (width < TABLET_MINIMUM_WIDTH) return "mobile";
  if (width < DESKTOP_MINIMUM_WIDTH) return "tablet";
  return "desktop";
}
