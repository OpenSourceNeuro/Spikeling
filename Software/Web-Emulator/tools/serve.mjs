// SPDX-License-Identifier: GPL-3.0-or-later

import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { stripTypeScriptTypes } from "node:module";
import { dirname, extname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const PACKAGE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const MIME_TYPES = Object.freeze({
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".ts": "text/javascript; charset=utf-8",
});

/** Serve existing erasable TypeScript as native browser modules without npm. */
export async function readDevelopmentAsset(pathname, root = PACKAGE_ROOT) {
  const requested = pathname === "/" ? "/demo/index.html" : pathname;
  let decoded;
  try {
    decoded = decodeURIComponent(requested);
  } catch {
    return { status: 400, contentType: "text/plain", content: "Invalid URL encoding." };
  }

  const file = resolve(root, "." + decoded);
  if (file !== root && !file.startsWith(root + sep)) {
    return { status: 403, contentType: "text/plain", content: "Access denied." };
  }

  const extension = extname(file);
  const contentType = MIME_TYPES[extension];
  if (contentType === undefined) {
    return { status: 404, contentType: "text/plain", content: "Asset not found." };
  }

  try {
    let content = await readFile(file, "utf8");
    if (extension === ".ts") {
      content = stripTypeScriptTypes(content, { mode: "strip", sourceUrl: decoded });
    }
    return { status: 200, contentType, content };
  } catch (error) {
    if (error?.code === "ENOENT" || error?.code === "EISDIR") {
      return { status: 404, contentType: "text/plain", content: "Asset not found." };
    }
    throw error;
  }
}

export function createDevelopmentServer(root = PACKAGE_ROOT) {
  return createServer(async (request, response) => {
    try {
      const pathname = new URL(request.url ?? "/", "http://localhost").pathname;
      const asset = await readDevelopmentAsset(pathname, root);
      response.writeHead(asset.status, {
        "Content-Type": asset.contentType,
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
      });
      response.end(asset.content);
    } catch {
      response.writeHead(500, { "Content-Type": "text/plain" });
      response.end("Unable to serve the local development asset.");
    }
  });
}

const invokedAsScript =
  process.argv[1] !== undefined &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (invokedAsScript) {
  const port = Number(process.env.SPIKELING_DEV_PORT ?? 4173);
  if (!Number.isInteger(port) || port < 1 || port > 65_535) {
    throw new RangeError("SPIKELING_DEV_PORT must be an integer between 1 and 65535.");
  }

  const server = createDevelopmentServer();
  server.listen(port, "127.0.0.1", () => {
    process.stdout.write("Spikeling oscilloscope preview: http://127.0.0.1:" + port + "/\n");
  });
}
