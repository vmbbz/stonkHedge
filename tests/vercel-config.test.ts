import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

interface VercelConfig {
  framework?: string;
  functions?: Record<string, Record<string, unknown>>;
  headers?: Array<{
    source: string;
    headers: Array<{ key: string; value: string }>;
  }>;
  env?: unknown;
  builds?: unknown;
  routes?: unknown;
}

const config = JSON.parse(readFileSync(
  resolve(process.cwd(), "vercel.json"),
  "utf8",
)) as VercelConfig;
const packageJson = JSON.parse(readFileSync(
  resolve(process.cwd(), "package.json"),
  "utf8",
)) as { engines?: { node?: string } };

describe("Vercel preview configuration", () => {
  it("uses Vite zero-config functions with enough time for bounded upstream calls", () => {
    expect(config.framework).toBe("vite");
    expect(config.functions?.["api/**/*.ts"]).toMatchObject({
      maxDuration: 60,
      supportsCancellation: true,
    });
    expect(config).not.toHaveProperty("builds");
    expect(config).not.toHaveProperty("routes");
    expect(config).not.toHaveProperty("env");
    expect(packageJson.engines?.node).toBe("22.x");
  });

  it("keeps credentials out of deployment configuration and adds browser safeguards", () => {
    const serialized = JSON.stringify(config);
    expect(serialized).not.toContain("BINANCE_WEB3_API_KEY");
    expect(serialized).not.toContain("BINANCE_WEB3_SECRET_KEY");

    const rootHeaders = config.headers?.find((entry) => entry.source === "/(.*)")?.headers ?? [];
    const headers = new Map(rootHeaders.map(({ key, value }) => [key, value]));
    expect(headers.get("Content-Security-Policy")).toContain("connect-src 'self'");
    expect(headers.get("Content-Security-Policy")).toContain("frame-ancestors 'none'");
    expect(headers.get("Permissions-Policy")).toContain("payment=()");
    expect(headers.get("X-Content-Type-Options")).toBe("nosniff");
    expect(headers.get("X-Frame-Options")).toBe("DENY");
  });
});
