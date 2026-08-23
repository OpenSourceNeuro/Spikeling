// SPDX-License-Identifier: GPL-3.0-or-later

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { stripTypeScriptTypes } from "node:module";
import { dirname, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const DEFAULT_WORDPRESS_ASSET_DIRECTORY = resolve(ROOT, "wordpress/spikeling-emulator/assets");
export const PRODUCTION_STYLE_SOURCES = Object.freeze([
  "src/styles/oscilloscope.css",
  "src/styles/controls.css",
  "src/styles/synapses.css",
  "src/styles/recording.css",
  "src/styles/emulator.css",
  "src/styles/wordpress.css",
]);

const IMPORT_PATTERN = /^([\t ]*)import\s*\{([\s\S]*?)\}\s*from\s*(["'])(\.[^"']+)\3\s*;?/gm;
const EXPORT_PATTERN = /^export\s+(?:(async)\s+)?(const|let|var|function|class)\s+([A-Za-z_$][\w$]*)/gm;
const LICENCE = "/*! SPDX-License-Identifier: GPL-3.0-or-later | Open Source Neuro Spikeling */";

function digest(content) {
  return createHash("sha256").update(content).digest("hex");
}

function assetDetails(file, content) {
  return {
    file,
    bytes: Buffer.byteLength(content),
    gzipBytes: gzipSync(content, { level: 9 }).byteLength,
    sha256: digest(content),
  };
}

function safeModulePath(specifier, importer) {
  if (!specifier.startsWith(".")) {
    throw new Error("Production modules may import only local source files.");
  }
  const file = resolve(dirname(importer), specifier);
  if (!file.startsWith(ROOT + sep) || !file.endsWith(".ts")) {
    throw new Error("Production module resolved outside the TypeScript package.");
  }
  return file;
}

function importBindings(bindings) {
  return bindings.split(",").map((binding) => binding.trim()).filter(Boolean).map((binding) => {
    const parts = binding.split(/\s+as\s+/);
    if (parts.length > 2 || parts.some((part) => !/^[A-Za-z_$][\w$]*$/.test(part))) {
      throw new Error("Unsupported production import binding: " + binding);
    }
    return parts.length === 1 ? parts[0] : parts[0] + ": " + parts[1];
  }).join(", ");
}

/** Small, auditable bundler for the project's existing named-import ESM subset. */
export async function bundleProductionEntry(entry, { workerFilename } = {}) {
  const modules = new Map();

  async function visit(file) {
    const id = relative(ROOT, file).split(sep).join("/");
    if (modules.has(id)) return id;
    modules.set(id, "");
    const original = await readFile(file, "utf8");
    let code = stripTypeScriptTypes(original, { mode: "strip" });
    const imports = [...code.matchAll(IMPORT_PATTERN)];
    for (const found of imports) {
      const dependency = safeModulePath(found[4], file);
      await visit(dependency);
    }
    code = code.replace(IMPORT_PATTERN, (_full, indent, bindings, _quote, specifier) => {
      const dependency = relative(ROOT, safeModulePath(specifier, file)).split(sep).join("/");
      return indent + "const { " + importBindings(bindings) + " } = __spkRequire(" + JSON.stringify(dependency) + ");";
    });

    if (workerFilename !== undefined) {
      code = code.replaceAll('"../worker/emulator.worker.ts"', JSON.stringify("./" + workerFilename));
    }

    const exported = [];
    code = code.replace(EXPORT_PATTERN, (_full, asynchronous, kind, name) => {
      exported.push(name);
      return (asynchronous === undefined ? "" : "async ") + kind + " " + name;
    });
    const assignments = exported.map((name) => "__spkExports." + name + " = " + name + ";").join("\n");
    modules.set(id, code + "\n" + assignments + "\n");
    return id;
  }

  const start = await visit(resolve(ROOT, entry));
  const definitions = [...modules.entries()].map(([id, code]) =>
    JSON.stringify(id) + ": function (__spkExports, __spkRequire) {\n" + code + "\n}",
  ).join(",\n");
  return LICENCE + "\n"
    + "const __spkModules = {\n" + definitions + "\n};\n"
    + "const __spkCache = Object.create(null);\n"
    + "function __spkRequire(id) {\n"
    + "  if (__spkCache[id] !== undefined) return __spkCache[id];\n"
    + "  if (__spkModules[id] === undefined) throw new Error('Missing Spikeling production module: ' + id);\n"
    + "  const exports = Object.create(null);\n"
    + "  __spkCache[id] = exports;\n"
    + "  __spkModules[id](exports, __spkRequire);\n"
    + "  return exports;\n"
    + "}\n"
    + "__spkRequire(" + JSON.stringify(start) + ");\n";
}

export async function buildProductionAssets({ outputDirectory = DEFAULT_WORDPRESS_ASSET_DIRECTORY } = {}) {
  const worker = await bundleProductionEntry("src/worker/emulator.worker.ts");
  const workerFilename = "spikeling-worker." + digest(worker).slice(0, 12) + ".js";
  const application = await bundleProductionEntry("src/integration/wordpress-entry.ts", { workerFilename });
  const applicationFilename = "spikeling-emulator." + digest(application).slice(0, 12) + ".js";

  const styleSections = await Promise.all(PRODUCTION_STYLE_SOURCES.map(async (path) =>
    "/* Source: " + path + " */\n" + await readFile(resolve(ROOT, path), "utf8"),
  ));
  const stylesheet = LICENCE + "\n" + styleSections.join("\n");
  const stylesheetFilename = "spikeling-emulator." + digest(stylesheet).slice(0, 12) + ".css";
  const version = digest(application + "\n" + worker + "\n" + stylesheet).slice(0, 16);
  const manifest = {
    version,
    application: assetDetails(applicationFilename, application),
    worker: assetDetails(workerFilename, worker),
    stylesheet: assetDetails(stylesheetFilename, stylesheet),
    sourceStylesheets: PRODUCTION_STYLE_SOURCES,
    licence: "GPL-3.0-or-later",
  };

  await mkdir(outputDirectory, { recursive: true });
  await Promise.all([
    writeFile(resolve(outputDirectory, workerFilename), worker, "utf8"),
    writeFile(resolve(outputDirectory, applicationFilename), application, "utf8"),
    writeFile(resolve(outputDirectory, stylesheetFilename), stylesheet, "utf8"),
    writeFile(resolve(outputDirectory, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n", "utf8"),
  ]);

  return manifest;
}

const invokedDirectly = process.argv[1] !== undefined
  && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  const manifest = await buildProductionAssets();
  process.stdout.write("Built reproducible WordPress assets " + manifest.version + "\n");
  for (const [name, asset] of Object.entries(manifest)) {
    if (asset !== null && typeof asset === "object" && "file" in asset) {
      process.stdout.write("  " + name + ": " + asset.file + " (" + asset.bytes
        + " bytes; " + asset.gzipBytes + " bytes gzip)\n");
    }
  }
}
