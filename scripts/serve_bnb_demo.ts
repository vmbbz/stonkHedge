import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";

import rwaHandler from "../api/bnb/rwa";

const HOST = "127.0.0.1";
const portArgument = process.argv[2] ?? "3000";
if (!/^\d{1,5}$/u.test(portArgument)) throw new Error("Port must be an integer");
const port = Number(portArgument);
if (port < 1 || port > 65_535) throw new Error("Port must be between 1 and 65535");

const root = process.cwd();
const dist = path.resolve(root, "dist");
const distPrefix = `${dist}${path.sep}`;

try {
  const index = await stat(path.join(dist, "index.html"));
  if (!index.isFile()) throw new Error("dist/index.html is not a file");
} catch {
  throw new Error("Production build not found. Run npm run build before npm run bnb:rwa:demo");
}

const types = new Map([
  [".css", "text/css; charset=utf-8"],
  [".html", "text/html; charset=utf-8"],
  [".ico", "image/x-icon"],
  [".jpg", "image/jpeg"],
  [".jpeg", "image/jpeg"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".map", "application/json; charset=utf-8"],
  [".mp4", "video/mp4"],
  [".png", "image/png"],
  [".svg", "image/svg+xml"],
  [".webp", "image/webp"],
  [".woff2", "font/woff2"],
]);

const setSecurityHeaders = (response: import("node:http").ServerResponse) => {
  response.setHeader(
    "Content-Security-Policy",
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self'; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
  );
  response.setHeader("Cross-Origin-Opener-Policy", "same-origin");
  response.setHeader("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()");
  response.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
  response.setHeader("X-Content-Type-Options", "nosniff");
  response.setHeader("X-Frame-Options", "DENY");
};

const server = createServer(async (request, response) => {
  setSecurityHeaders(response);
  const url = new URL(request.url ?? "/", `http://${HOST}:${port}`);
  if (url.pathname === "/api/bnb/rwa") {
    await rwaHandler(request, response);
    return;
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    response.statusCode = 405;
    response.setHeader("Allow", "GET, HEAD");
    response.end("Method not allowed");
    return;
  }

  let relativePath: string;
  try {
    relativePath = url.pathname === "/" ? "index.html" : decodeURIComponent(url.pathname.slice(1));
  } catch {
    response.statusCode = 400;
    response.end("Invalid path");
    return;
  }
  const filePath = path.resolve(dist, relativePath);
  if (filePath !== dist && !filePath.startsWith(distPrefix)) {
    response.statusCode = 403;
    response.end("Forbidden");
    return;
  }

  try {
    const body = await readFile(filePath);
    response.statusCode = 200;
    response.setHeader("Content-Type", types.get(path.extname(filePath).toLowerCase()) ?? "application/octet-stream");
    response.setHeader("Cache-Control", filePath.endsWith("index.html") ? "no-cache" : "public, max-age=3600");
    response.end(request.method === "HEAD" ? undefined : body);
  } catch {
    response.statusCode = 404;
    response.end("Not found");
  }
});

server.listen(port, HOST, () => {
  process.stdout.write(`StonkHedge local demo ready at http://${HOST}:${port}/\n`);
  process.stdout.write("Boundary: local live API and unsigned simulation; no wallet, signing, or broadcast\n");
});

const shutdown = () => server.close(() => process.exit(0));
process.once("SIGINT", shutdown);
process.once("SIGTERM", shutdown);
