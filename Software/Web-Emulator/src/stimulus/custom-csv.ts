// SPDX-License-Identifier: GPL-3.0-or-later

import { TIMESTEP_MS } from "../model/izhikevich.ts";

export const MAX_CUSTOM_STIMULUS_BYTES = 8 * 1_024 * 1_024;
export const MAX_CUSTOM_STIMULUS_SAMPLES = 250_000;
export const REQUIRED_STIMULUS_COLUMN = "Stim";

const TIME_COLUMN_NAMES = ["Time (ms)", "timeMs", "time_ms"] as const;
const NUMERIC_FIELD = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;

export type CustomStimulusErrorCode =
  | "file-type"
  | "file-size"
  | "empty-file"
  | "malformed-csv"
  | "missing-stim-column"
  | "duplicate-column"
  | "empty-samples"
  | "invalid-sample"
  | "sample-limit"
  | "invalid-timestamp"
  | "sample-interval";

export class CustomStimulusError extends Error {
  readonly code: CustomStimulusErrorCode;
  readonly line: number | undefined;

  constructor(code: CustomStimulusErrorCode, message: string, line?: number) {
    super(message);
    this.name = "CustomStimulusError";
    this.code = code;
    this.line = line;
  }
}

export interface CustomStimulusOptions {
  readonly maxBytes?: number;
  readonly maxSamples?: number;
}

export interface ParsedCustomStimulus {
  readonly samples: readonly number[];
  readonly sampleIntervalMs: number;
  readonly durationMs: number;
  readonly minimum: number;
  readonly maximum: number;
  readonly hasTriggerColumn: boolean;
  readonly hasTimeColumn: boolean;
}

export interface LocalStimulusFile {
  readonly name: string;
  readonly size: number;
  text(): Promise<string>;
}

interface CsvRow {
  readonly line: number;
  readonly fields: string[];
}

function positiveLimit(value: number | undefined, fallback: number, name: string): number {
  const limit = value ?? fallback;
  if (!Number.isSafeInteger(limit) || limit < 1) {
    throw new RangeError(name + " must be a positive safe integer.");
  }
  return limit;
}

function readCsvRows(content: string): CsvRow[] {
  const rows: CsvRow[] = [];
  let fields: string[] = [];
  let field = "";
  let line = 1;
  let rowLine = 1;
  let quoted = false;
  let closedQuote = false;

  function finishRow(): void {
    fields.push(field.trim());
    if (fields.some((value) => value.length > 0)) {
      rows.push({ line: rowLine, fields });
    }
    fields = [];
    field = "";
    closedQuote = false;
  }

  for (let index = 0; index < content.length; index += 1) {
    const character = content[index];

    if (quoted) {
      if (character === '"' && content[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
        closedQuote = true;
      } else {
        if (character === "\n") {
          line += 1;
        }
        field += character;
      }
      continue;
    }

    if (character === '"') {
      if (field.trim().length > 0 || closedQuote) {
        throw new CustomStimulusError("malformed-csv", "Unexpected quote in CSV data.", line);
      }
      field = "";
      quoted = true;
      continue;
    }

    if (closedQuote && character !== "," && character !== "\n" && character !== "\r") {
      if (character.trim().length > 0) {
        throw new CustomStimulusError("malformed-csv", "Unexpected text after a quoted CSV field.", line);
      }
      continue;
    }

    if (character === ",") {
      fields.push(field.trim());
      field = "";
      closedQuote = false;
    } else if (character === "\n" || character === "\r") {
      if (character === "\r" && content[index + 1] === "\n") {
        index += 1;
      }
      finishRow();
      line += 1;
      rowLine = line;
    } else {
      field += character;
    }
  }

  if (quoted) {
    throw new CustomStimulusError("malformed-csv", "The CSV contains an unterminated quoted field.", line);
  }
  if (field.length > 0 || fields.length > 0 || closedQuote) {
    finishRow();
  }

  return rows;
}

function numericField(value: string, code: "invalid-sample" | "invalid-timestamp", line: number): number {
  if (!NUMERIC_FIELD.test(value)) {
    throw new CustomStimulusError(
      code,
      (code === "invalid-sample" ? "Stimulus value" : "Timestamp") +
        " on line " +
        line +
        " must be a finite decimal number.",
      line,
    );
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    throw new CustomStimulusError(code, "Numeric CSV value is not finite on line " + line + ".", line);
  }
  return parsed;
}

/** Parse the desktop's exact Stim[,Trigger] format entirely in local memory. */
export function parseCustomStimulusCsv(
  content: string,
  options: CustomStimulusOptions = {},
): ParsedCustomStimulus {
  const maxBytes = positiveLimit(options.maxBytes, MAX_CUSTOM_STIMULUS_BYTES, "CSV byte limit");
  const maxSamples = positiveLimit(options.maxSamples, MAX_CUSTOM_STIMULUS_SAMPLES, "CSV sample limit");
  const bytes = new TextEncoder().encode(content).byteLength;
  if (bytes > maxBytes) {
    throw new CustomStimulusError("file-size", "The stimulus CSV exceeds the allowed " + maxBytes + " bytes.");
  }

  const cleaned = content.replace(/^\uFEFF/, "");
  if (cleaned.trim().length === 0) {
    throw new CustomStimulusError("empty-file", "The stimulus CSV is empty.");
  }

  const rows = readCsvRows(cleaned);
  if (rows.length === 0) {
    throw new CustomStimulusError("empty-file", "The stimulus CSV contains no readable rows.");
  }

  const header = rows[0].fields;
  const stimulusIndices = header.flatMap((name, index) =>
    name === REQUIRED_STIMULUS_COLUMN ? [index] : [],
  );
  if (stimulusIndices.length === 0) {
    throw new CustomStimulusError("missing-stim-column", 'The CSV must contain an exact "Stim" column.', rows[0].line);
  }
  if (stimulusIndices.length > 1) {
    throw new CustomStimulusError("duplicate-column", 'The CSV contains more than one "Stim" column.', rows[0].line);
  }

  const timeIndices = header.flatMap((name, index) =>
    TIME_COLUMN_NAMES.includes(name as (typeof TIME_COLUMN_NAMES)[number]) ? [index] : [],
  );
  if (timeIndices.length > 1) {
    throw new CustomStimulusError("duplicate-column", "The CSV contains ambiguous timestamp columns.", rows[0].line);
  }

  const samples: number[] = [];
  let minimum = Number.POSITIVE_INFINITY;
  let maximum = Number.NEGATIVE_INFINITY;
  let previousTime: number | undefined;

  for (const row of rows.slice(1)) {
    if (row.fields.length !== header.length) {
      throw new CustomStimulusError("malformed-csv", "CSV row " + row.line + " has an unexpected number of columns.", row.line);
    }
    if (samples.length >= maxSamples) {
      throw new CustomStimulusError("sample-limit", "The stimulus CSV exceeds " + maxSamples + " samples.", row.line);
    }

    const sample = numericField(row.fields[stimulusIndices[0]], "invalid-sample", row.line);
    if (timeIndices.length === 1) {
      const timestamp = numericField(row.fields[timeIndices[0]], "invalid-timestamp", row.line);
      if (
        previousTime !== undefined &&
        Math.abs(timestamp - previousTime - TIMESTEP_MS) > 1e-8
      ) {
        throw new CustomStimulusError(
          "sample-interval",
          "Timestamp spacing on line " + row.line + " must match the 0.1 ms simulation timestep.",
          row.line,
        );
      }
      previousTime = timestamp;
    }

    samples.push(sample);
    minimum = Math.min(minimum, sample);
    maximum = Math.max(maximum, sample);
  }

  if (samples.length === 0) {
    throw new CustomStimulusError("empty-samples", 'The "Stim" column contains no samples.', rows[0].line);
  }

  return {
    samples,
    sampleIntervalMs: TIMESTEP_MS,
    durationMs: samples.length * TIMESTEP_MS,
    minimum,
    maximum,
    hasTriggerColumn: header.includes("Trigger"),
    hasTimeColumn: timeIndices.length === 1,
  };
}

export async function parseCustomStimulusFile(
  file: LocalStimulusFile,
  options: CustomStimulusOptions = {},
): Promise<ParsedCustomStimulus> {
  if (!/\.csv$/i.test(file.name)) {
    throw new CustomStimulusError("file-type", "A custom stimulus must be a .csv file.");
  }
  const maxBytes = positiveLimit(options.maxBytes, MAX_CUSTOM_STIMULUS_BYTES, "CSV byte limit");
  if (!Number.isFinite(file.size) || file.size < 0 || file.size > maxBytes) {
    throw new CustomStimulusError("file-size", "The stimulus file exceeds the allowed " + maxBytes + " bytes.");
  }
  return parseCustomStimulusCsv(await file.text(), options);
}
