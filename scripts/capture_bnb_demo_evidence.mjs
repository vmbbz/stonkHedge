import { existsSync } from "node:fs";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";

const DEFAULT_RECEIVER = "0x6719E877C05b2d6c28aBceA405fC033FEeF5750f";
const DEFAULT_OUTPUT = "docs/hackathons/evidence/2026-10-10";
const DEFAULT_URL = "http://127.0.0.1:3000/";
const TIMEOUT_MS = 45_000;

const [, , baseUrlArgument = DEFAULT_URL, outputArgument = DEFAULT_OUTPUT, receiver = DEFAULT_RECEIVER] = process.argv;
const baseUrl = new URL(baseUrlArgument);
if (!new Set(["127.0.0.1", "localhost"]).has(baseUrl.hostname) || baseUrl.protocol !== "http:") {
  throw new Error("Evidence capture accepts only a local HTTP server");
}
if (!/^0x[a-fA-F0-9]{40}$/u.test(receiver)) {
  throw new Error("Receiver must be a public EVM address");
}

const outputDirectory = path.resolve(outputArgument);
await mkdir(outputDirectory, { recursive: true });

const browserCandidates = [
  process.env.STONKHEDGE_BROWSER_PATH,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
].filter(Boolean);
const browserPath = browserCandidates.find((candidate) => existsSync(candidate));
if (!browserPath) throw new Error("Chrome or Edge was not found; set STONKHEDGE_BROWSER_PATH");

const reservePort = () => new Promise((resolve, reject) => {
  const server = net.createServer();
  server.unref();
  server.once("error", reject);
  server.listen(0, "127.0.0.1", () => {
    const address = server.address();
    if (!address || typeof address === "string") {
      server.close();
      reject(new Error("Could not reserve a DevTools port"));
      return;
    }
    const { port } = address;
    server.close((error) => error ? reject(error) : resolve(port));
  });
});

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

const waitForJson = async (url, timeoutMs = TIMEOUT_MS) => {
  const deadline = Date.now() + timeoutMs;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return response.json();
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await sleep(100);
  }
  throw new Error(`Timed out waiting for ${url}: ${lastError instanceof Error ? lastError.message : "unknown error"}`);
};

const port = await reservePort();
const profileDirectory = await mkdtemp(path.join(os.tmpdir(), "stonkhedge-evidence-"));
const browser = spawn(browserPath, [
  "--headless=new",
  "--disable-gpu",
  "--disable-background-networking",
  "--disable-component-update",
  "--disable-default-apps",
  "--disable-extensions",
  "--disable-sync",
  "--hide-scrollbars",
  "--no-first-run",
  `--remote-debugging-port=${port}`,
  `--user-data-dir=${profileDirectory}`,
  "about:blank",
], { stdio: "ignore", windowsHide: true });

let socket;
let nextId = 1;
const pending = new Map();

const closeBrowser = async () => {
  const waitForExit = () => new Promise((resolve) => {
    if (browser.exitCode !== null) {
      resolve(true);
      return;
    }
    const timeout = setTimeout(() => resolve(false), 3_000);
    browser.once("exit", () => {
      clearTimeout(timeout);
      resolve(true);
    });
  });
  if (socket?.readyState === WebSocket.OPEN) {
    try {
      await send("Browser.close");
    } catch {
      socket.close();
    }
  }
  if (!await waitForExit() && browser.exitCode === null) {
    browser.kill();
    await waitForExit();
  }
  try {
    await rm(profileDirectory, {
      recursive: true,
      force: true,
      maxRetries: 10,
      retryDelay: 200,
    });
  } catch (error) {
    process.stderr.write(`Temporary browser profile cleanup warning: ${error instanceof Error ? error.message : String(error)}\n`);
  }
};

const connect = (url) => new Promise((resolve, reject) => {
  socket = new WebSocket(url);
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(String(event.data));
    if (!message.id) return;
    const request = pending.get(message.id);
    if (!request) return;
    pending.delete(message.id);
    if (message.error) request.reject(new Error(`${request.method}: ${message.error.message}`));
    else request.resolve(message.result);
  });
});

const send = (method, params = {}) => new Promise((resolve, reject) => {
  const id = nextId++;
  pending.set(id, { method, resolve, reject });
  socket.send(JSON.stringify({ id, method, params }));
});

const evaluate = async (expression) => {
  const result = await send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.exception?.description ?? "Browser evaluation failed");
  }
  return result.result.value;
};

const waitFor = async (expression, label, timeoutMs = TIMEOUT_MS) => {
  const deadline = Date.now() + timeoutMs;
  let lastValue;
  while (Date.now() < deadline) {
    lastValue = await evaluate(expression);
    if (lastValue) return lastValue;
    await sleep(150);
  }
  const visibleError = await evaluate(`document.querySelector(".guardian-error")?.textContent?.trim() ?? null`);
  throw new Error(`Timed out waiting for ${label}${visibleError ? `: ${visibleError}` : ` (last value: ${lastValue})`}`);
};

const setViewport = (width, height, mobile = false) => send("Emulation.setDeviceMetricsOverride", {
  width,
  height,
  deviceScaleFactor: 1,
  mobile,
});

const documentClip = async (startSelector, endSelector, width, maximumHeight = 2_400) => {
  const clip = await evaluate(`(() => {
    const start = document.querySelector(${JSON.stringify(startSelector)});
    const end = document.querySelector(${JSON.stringify(endSelector)});
    if (!(start instanceof HTMLElement) || !(end instanceof HTMLElement)) return null;
    const first = start.getBoundingClientRect();
    const last = end.getBoundingClientRect();
    const top = Math.max(0, window.scrollY + first.top - 18);
    const bottom = window.scrollY + last.bottom + 18;
    return { x: 0, y: top, width: ${width}, height: Math.min(${maximumHeight}, bottom - top), scale: 1 };
  })()`);
  if (!clip || clip.height <= 0) throw new Error(`Could not calculate screenshot clip ${startSelector}..${endSelector}`);
  return clip;
};

const screenshot = async (fileName, startSelector, endSelector, width, maximumHeight) => {
  const clip = await documentClip(startSelector, endSelector, width, maximumHeight);
  const result = await send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: true,
    clip,
  });
  await writeFile(path.join(outputDirectory, fileName), Buffer.from(result.data, "base64"));
};

try {
  await waitForJson(`http://127.0.0.1:${port}/json/version`);
  const targets = await waitForJson(`http://127.0.0.1:${port}/json/list`);
  const pageTarget = targets.find((target) => target.type === "page" && target.webSocketDebuggerUrl);
  if (!pageTarget) throw new Error("Headless browser did not expose a page target");
  await connect(pageTarget.webSocketDebuggerUrl);
  await send("Page.enable");
  await send("Runtime.enable");
  await setViewport(1_440, 1_200);
  await send("Page.navigate", { url: baseUrl.href });
  await waitFor(`document.readyState === "complete"`, "document load");
  await waitFor(`document.querySelectorAll(".guardian-grid .guardian-card").length >= 2`, "two live issuer cards");

  await screenshot("01-live-comparison-desktop.png", ".guardian-heading", ".guardian-grid", 1_440, 2_200);

  await evaluate(`(() => {
    const input = document.querySelector("#guardian-quote-receiver");
    if (!(input instanceof HTMLInputElement)) return false;
    input.value = ${JSON.stringify(receiver)};
    input.dispatchEvent(new Event("input", { bubbles: true }));
    const button = document.querySelector("#guardian-quote-form button[type='submit']");
    if (!(button instanceof HTMLButtonElement) || button.disabled) return false;
    button.click();
    return true;
  })()`);
  await waitFor(`document.querySelector("#guardian-quote-result .quote-card") !== null`, "bounded quote card");
  await screenshot("02-live-quote-desktop.png", "#guardian-quote-form", "#guardian-quote-result", 1_440, 1_900);

  await evaluate(`(() => {
    const button = document.querySelector("#guardian-quote-result .simulation-button");
    if (!(button instanceof HTMLButtonElement) || button.disabled) return false;
    button.click();
    return true;
  })()`);
  await waitFor(`document.querySelector("#guardian-simulation-result .simulation-card") !== null`, "simulation proof", 60_000);
  await screenshot("03-live-simulation-desktop.png", "#guardian-quote-result", "#guardian-simulation-result", 1_440, 2_200);

  const publicSummary = await evaluate(`(() => {
    const summary = document.querySelector(".guardian-summary")?.textContent?.replace(/\\s+/gu, " ").trim() ?? null;
    const quote = document.querySelector(".quote-card")?.textContent?.replace(/\\s+/gu, " ").trim() ?? null;
    const simulation = document.querySelector(".simulation-card")?.textContent?.replace(/\\s+/gu, " ").trim() ?? null;
    return { summary, quote, simulation };
  })()`);

  await setViewport(390, 900, true);
  await evaluate(`window.dispatchEvent(new Event("resize")); true`);
  await sleep(300);
  await waitFor(`document.querySelectorAll(".guardian-grid .guardian-card").length >= 2`, "two mobile issuer cards");
  await screenshot("04-live-comparison-mobile.png", ".guardian-heading", ".guardian-grid", 390, 2_400);

  const manifest = {
    status: "PASS_PUBLIC_BROWSER_EVIDENCE",
    capturedAt: new Date().toISOString(),
    source: baseUrl.href,
    receiver,
    browser: path.basename(browserPath),
    files: [
      "01-live-comparison-desktop.png",
      "02-live-quote-desktop.png",
      "03-live-simulation-desktop.png",
      "04-live-comparison-mobile.png",
    ],
    publicSummary,
    boundary: "LIVE_API_UNSIGNED_SIMULATION_NO_WALLET_NO_SIGNING_NO_BROADCAST",
  };
  await writeFile(path.join(outputDirectory, "capture-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify(manifest, null, 2)}\n`);
} finally {
  await closeBrowser();
}
