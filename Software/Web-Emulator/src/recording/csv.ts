// SPDX-License-Identifier: GPL-3.0-or-later

import { TIMESTEP_MS } from "../model/izhikevich.ts";
import type { SimulationSample } from "../model/types.ts";

/** Exact names and order emitted by the desktop Graph_Emulator.SavePlotData. */
export const DESKTOP_RECORDING_COLUMNS = [
  { header: "Time (ms)", field: "timeMs" },
  { header: "Spikeling Vm (mV)", field: "mainVm" },
  { header: "Stimulus (%)", field: "stimulus" },
  { header: "Total Current Input (a.u.)", field: "totalCurrent" },
  { header: "Synapse 1 Vm (mV)", field: "synapse1Vm" },
  { header: "Synapse 1 Input (a.u.)", field: "synapse1Current" },
  { header: "Synapse 2 Vm (mV)", field: "synapse2Vm" },
  { header: "Synapse 2 Input (a.u.)", field: "synapse2Current" },
  { header: "Trigger", field: "trigger" },
] as const satisfies ReadonlyArray<{ header: string; field: keyof SimulationSample }>;

export const RECORDING_SAMPLE_RATE_HZ = 1_000 / TIMESTEP_MS;
export const DEFAULT_RECORDING_MAX_SAMPLES = 250_000;
export const MAX_RECORDING_FILE_BYTES = 64 * 1_024 * 1_024;

export type RecordingField = (typeof DESKTOP_RECORDING_COLUMNS)[number]["field"];
export type RecordingSample = Pick<SimulationSample, RecordingField>;
export type RecordingErrorCode =
  | "file-type"
  | "file-size"
  | "empty-file"
  | "malformed-csv"
  | "invalid-header"
  | "duplicate-column"
  | "empty-samples"
  | "invalid-sample"
  | "invalid-trigger"
  | "invalid-timestamp"
  | "sample-interval"
  | "sample-limit";

export class RecordingError extends Error {
  readonly code: RecordingErrorCode;
  readonly line: number | undefined;

  constructor(code: RecordingErrorCode, message: string, line?: number) {
    super(message);
    this.name = "RecordingError";
    this.code = code;
    this.line = line;
  }
}

export interface RecordingCsvOptions {
  readonly maxBytes?: number;
  readonly maxSamples?: number;
}

export interface ParsedRecording {
  readonly samples: readonly RecordingSample[];
  readonly sampleIntervalMs: number;
  readonly durationMs: number;
}

export interface LocalRecordingFile {
  readonly name: string;
  readonly size: number;
  text(): Promise<string>;
}

const NUMBER_PATTERN = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;

export function recordingLimit(value: number | undefined, fallback: number, name: string): number {
  const limit = value ?? fallback;
  if (!Number.isSafeInteger(limit) || limit < 1) {
    throw new RangeError(name + " must be a positive safe integer.");
  }
  return limit;
}

function readRows(content: string, visit: (fields: string[], line: number) => void): void {
  let fields: string[] = [];
  let field = "";
  let line = 1;
  let rowLine = 1;
  let quoted = false;
  let closed = false;

  function finish(): void {
    fields.push(field.trim());
    if (fields.some((value) => value.length > 0)) {
      visit(fields, rowLine);
    }
    fields = [];
    field = "";
    closed = false;
  }

  for (let index = 0; index < content.length; index += 1) {
    const character = content[index];
    if (quoted) {
      if (character === '"') {
        if (content[index + 1] === '"') {
          field += '"';
          index += 1;
        } else {
          quoted = false;
          closed = true;
        }
      } else {
        if (character === "\n") line += 1;
        field += character;
      }
      continue;
    }
    if (character === '"') {
      if (field.trim().length > 0 || closed) {
        throw new RecordingError("malformed-csv", "Unexpected quotation mark in recording CSV.", line);
      }
      field = "";
      quoted = true;
    } else if (character === ",") {
      fields.push(field.trim());
      field = "";
      closed = false;
    } else if (character === "\n" || character === "\r") {
      finish();
      if (character === "\r" && content[index + 1] === "\n") index += 1;
      line += 1;
      rowLine = line;
    } else if (closed && !/\s/.test(character)) {
      throw new RecordingError("malformed-csv", "Unexpected text after a quoted recording field.", line);
    } else if (!closed) {
      field += character;
    }
  }

  if (quoted) {
    throw new RecordingError("malformed-csv", "Unterminated quoted field in recording CSV.", rowLine);
  }
  if (field.length > 0 || fields.length > 0 || closed) finish();
}

function numeric(value: string, line: number, header: string): number {
  if (!NUMBER_PATTERN.test(value)) {
    throw new RecordingError("invalid-sample", header + " must contain a finite number.", line);
  }
  const number = Number(value);
  if (!Number.isFinite(number)) {
    throw new RecordingError("invalid-sample", header + " must contain a finite number.", line);
  }
  return number;
}

/** Parse source-pinned desktop files without accepting invented or missing signals. */
export function parseRecordingCsv(content: string, options: RecordingCsvOptions = {}): ParsedRecording {
  const maxBytes = recordingLimit(options.maxBytes, MAX_RECORDING_FILE_BYTES, "Recording file-size limit");
  const maxSamples = recordingLimit(options.maxSamples, DEFAULT_RECORDING_MAX_SAMPLES, "Recording sample limit");
  if (new TextEncoder().encode(content).byteLength > maxBytes) {
    throw new RecordingError("file-size", "Recording CSV exceeds its configured file-size limit.");
  }
  if (content.trim().length === 0) {
    throw new RecordingError("empty-file", "Recording CSV is empty.");
  }

  const samples: RecordingSample[] = [];
  let indices: number[] | undefined;
  readRows(content.replace(/^\uFEFF/, ""), (fields, line) => {
    if (indices === undefined) {
      if (new Set(fields).size !== fields.length) {
        throw new RecordingError("duplicate-column", "Recording CSV contains duplicate column names.", line);
      }
      const expected = DESKTOP_RECORDING_COLUMNS.map((column) => column.header);
      if (fields.length !== expected.length || fields.some((header) => !expected.includes(header as typeof expected[number]))) {
        throw new RecordingError("invalid-header", "Recording CSV must contain all nine exact desktop signal columns.", line);
      }
      indices = expected.map((header) => fields.indexOf(header));
      return;
    }

    if (fields.length !== DESKTOP_RECORDING_COLUMNS.length) {
      throw new RecordingError("malformed-csv", "Recording CSV row has an incorrect number of columns.", line);
    }
    if (samples.length >= maxSamples) {
      throw new RecordingError("sample-limit", "Recording CSV exceeds its configured sample limit.", line);
    }
    const values = DESKTOP_RECORDING_COLUMNS.map((column, index) => numeric(fields[indices![index]], line, column.header));
    const timeMs = values[0];
    if (timeMs < 0) {
      throw new RecordingError("invalid-timestamp", "Recording timestamps must be non-negative.", line);
    }
    if (samples.length > 0 && Math.abs(timeMs - samples[samples.length - 1].timeMs - TIMESTEP_MS) > 1e-8) {
      throw new RecordingError("sample-interval", "Recording samples must be exactly 0.1 ms apart.", line);
    }
    const trigger = values[8];
    if (trigger !== 0 && trigger !== 1) {
      throw new RecordingError("invalid-trigger", "Recording trigger values must be zero or one.", line);
    }
    samples.push({
      timeMs,
      mainVm: values[1],
      stimulus: values[2],
      totalCurrent: values[3],
      synapse1Vm: values[4],
      synapse1Current: values[5],
      synapse2Vm: values[6],
      synapse2Current: values[7],
      trigger,
    });
  });

  if (indices === undefined) {
    throw new RecordingError("empty-file", "Recording CSV has no header row.");
  }
  if (samples.length === 0) {
    throw new RecordingError("empty-samples", "Recording CSV contains no scientific samples.");
  }
  return { samples, sampleIntervalMs: TIMESTEP_MS, durationMs: samples.length * TIMESTEP_MS };
}

export async function parseRecordingFile(file: LocalRecordingFile, options: RecordingCsvOptions = {}): Promise<ParsedRecording> {
  if (!/\.csv$/i.test(file.name)) {
    throw new RecordingError("file-type", "Select a recording with a .csv extension.");
  }
  const maxBytes = recordingLimit(options.maxBytes, MAX_RECORDING_FILE_BYTES, "Recording file-size limit");
  if (!Number.isSafeInteger(file.size) || file.size < 0 || file.size > maxBytes) {
    throw new RecordingError("file-size", "Recording CSV exceeds its configured file-size limit.");
  }
  return parseRecordingCsv(await file.text(), options);
}

/** ECMAScript's shortest Float64 representation round-trips without rounding. */
export function serialiseRecordingCsv(samples: readonly RecordingSample[]): string {
  if (samples.length === 0) {
    throw new RecordingError("empty-samples", "There are no recorded scientific samples to export.");
  }
  const lines = [DESKTOP_RECORDING_COLUMNS.map((column) => column.header).join(",")];
  for (const sample of samples) {
    const fields = DESKTOP_RECORDING_COLUMNS.map((column) => {
      const value = sample[column.field];
      if (!Number.isFinite(value)) {
        throw new RecordingError("invalid-sample", column.header + " must contain a finite number.");
      }
      if (column.field === "trigger" && value !== 0 && value !== 1) {
        throw new RecordingError("invalid-trigger", "Recording trigger values must be zero or one.");
      }
      return String(value);
    });
    lines.push(fields.join(","));
  }
  return lines.join("\n") + "\n";
}
