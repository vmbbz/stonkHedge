import { createHmac, randomUUID } from "node:crypto";

const DEFAULT_BASE_URL = "https://web3.binance.com/build";
const DEFAULT_TIMEOUT_MS = 8_000;
const MAX_TIMEOUT_MS = 30_000;
const BSC_CHAIN_ID = "56";
const ADDRESS_PATTERN = /^0x[a-fA-F0-9]{40}$/;

type QueryEntry = readonly [key: string, value: string];
type FetchImplementation = typeof fetch;

interface BinanceEnvelope {
  code: unknown;
  msg: unknown;
  data: unknown;
  timestamp: unknown;
  success: unknown;
}

export interface BinanceWeb3Credentials {
  apiKey: string;
  secretKey: string;
}

export interface BinanceWeb3ClientOptions extends BinanceWeb3Credentials {
  baseUrl?: string;
  timeoutMs?: number;
  fetchImplementation?: FetchImplementation;
  now?: () => Date;
  nonce?: () => string;
}

export interface SignedGetRequest {
  url: string;
  requestPath: string;
  timestamp: string;
  headers: Readonly<Record<string, string>>;
}

export interface RwaChainDistribution {
  binanceChainId: string;
  tokenCount: number;
}

export interface RwaPlatform {
  platformId: string;
  tickerCount: number;
  chainDistribution: RwaChainDistribution[];
  website: string | null;
  logoUrl: string | null;
}

export type RwaAssetType = 1 | 2 | 3;

export interface RwaAsset {
  platformId: string;
  binanceChainId: string;
  tokenContractAddress: string;
  tokenSymbol: string;
  assetType: RwaAssetType;
}

export interface RwaSearchResult {
  ticker: string;
  companyName: string;
  assets: RwaAsset[];
}

export interface TimestampedResult<T> {
  data: T;
  timestamp: number;
}

export class BinanceWeb3Error extends Error {
  readonly kind: "configuration" | "upstream" | "schema" | "timeout";
  readonly status?: number;
  readonly code?: number;

  constructor(
    message: string,
    options: {
      kind: BinanceWeb3Error["kind"];
      status?: number;
      code?: number;
      cause?: unknown;
    },
  ) {
    super(message, { cause: options.cause });
    this.name = "BinanceWeb3Error";
    this.kind = options.kind;
    this.status = options.status;
    this.code = options.code;
  }
}

function requireNonEmpty(value: string, label: string): string {
  const normalized = value.trim();
  if (!normalized) {
    throw new BinanceWeb3Error(`${label} is not configured`, {
      kind: "configuration",
    });
  }
  return normalized;
}

function normalizeBaseUrl(value: string): string {
  const normalized = value.replace(/\/+$/, "");
  const parsed = new URL(normalized);
  if (parsed.protocol !== "https:") {
    throw new BinanceWeb3Error("Binance Web3 base URL must use HTTPS", {
      kind: "configuration",
    });
  }
  if (!parsed.pathname.endsWith("/build")) {
    throw new BinanceWeb3Error("Binance Web3 base URL must end with /build", {
      kind: "configuration",
    });
  }
  return normalized;
}

function normalizeTimeout(value: number): number {
  if (!Number.isSafeInteger(value) || value < 1 || value > MAX_TIMEOUT_MS) {
    throw new BinanceWeb3Error(
      `Binance Web3 timeout must be an integer between 1 and ${MAX_TIMEOUT_MS}`,
      { kind: "configuration" },
    );
  }
  return value;
}

function encodeQuery(entries: readonly QueryEntry[]): string {
  return entries
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join("&");
}

function assertApiPath(apiPath: string): void {
  if (!apiPath.startsWith("/api/v1/") || apiPath.includes("?") || apiPath.includes("#")) {
    throw new BinanceWeb3Error("Binance Web3 API path is invalid", {
      kind: "configuration",
    });
  }
}

export function buildSignedGetRequest(
  credentials: BinanceWeb3Credentials,
  options: {
    apiPath: string;
    query?: readonly QueryEntry[];
    timestamp: string;
    nonce: string;
    baseUrl?: string;
  },
): SignedGetRequest {
  const apiKey = requireNonEmpty(credentials.apiKey, "Binance Web3 API key");
  const secretKey = requireNonEmpty(credentials.secretKey, "Binance Web3 secret key");
  assertApiPath(options.apiPath);

  const baseUrl = normalizeBaseUrl(options.baseUrl ?? DEFAULT_BASE_URL);
  const query = encodeQuery(options.query ?? []);
  const pathWithQuery = query ? `${options.apiPath}?${query}` : options.apiPath;
  const requestPath = `/build${pathWithQuery}`;
  const preHash = `${options.timestamp}GET${requestPath}`;
  const signature = createHmac("sha256", secretKey)
    .update(preHash, "utf8")
    .digest("base64");

  return {
    url: `${baseUrl}${pathWithQuery}`,
    requestPath,
    timestamp: options.timestamp,
    headers: {
      Accept: "application/json",
      "X-OC-APIKEY": apiKey,
      "X-OC-TIMESTAMP": options.timestamp,
      "X-OC-SIGN": signature,
      "X-OC-RECV-WINDOW": "5000",
      "X-OC-NONCE": requireNonEmpty(options.nonce, "Binance Web3 request nonce"),
    },
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseEnvelope(value: unknown): BinanceEnvelope {
  if (!isRecord(value)) {
    throw new BinanceWeb3Error("Binance Web3 returned a non-object response", {
      kind: "schema",
    });
  }
  return {
    code: value.code,
    msg: value.msg,
    data: value.data,
    timestamp: value.timestamp,
    success: value.success,
  };
}

function requireString(value: unknown, path: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return value;
}

function requireNullableString(value: unknown, path: string): string | null {
  if (value === null) return null;
  return requireString(value, path);
}

function requireInteger(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value)) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return value;
}

function requireArray(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value)) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return value;
}

function parseTimestamp(value: unknown): number {
  const timestamp = requireInteger(value, "timestamp");
  if (timestamp <= 0) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid timestamp", {
      kind: "schema",
    });
  }
  return timestamp;
}

function parsePlatforms(value: unknown): RwaPlatform[] {
  return requireArray(value, "platform data").map((candidate, index) => {
    if (!isRecord(candidate)) {
      throw new BinanceWeb3Error(`Binance Web3 response has invalid platform ${index}`, {
        kind: "schema",
      });
    }
    const chainDistribution = requireArray(
      candidate.chainDistribution,
      `platform ${index} chainDistribution`,
    ).map((chain, chainIndex) => {
      if (!isRecord(chain)) {
        throw new BinanceWeb3Error(
          `Binance Web3 response has invalid platform ${index} chain ${chainIndex}`,
          { kind: "schema" },
        );
      }
      return {
        binanceChainId: requireString(
          chain.binanceChainId,
          `platform ${index} chain ${chainIndex} binanceChainId`,
        ),
        tokenCount: requireInteger(
          chain.tokenCount,
          `platform ${index} chain ${chainIndex} tokenCount`,
        ),
      };
    });

    return {
      platformId: requireString(candidate.platformId, `platform ${index} platformId`),
      tickerCount: requireInteger(candidate.tickerCount, `platform ${index} tickerCount`),
      chainDistribution,
      website: requireNullableString(candidate.website, `platform ${index} website`),
      logoUrl: requireNullableString(candidate.logoUrl, `platform ${index} logoUrl`),
    };
  });
}

function parseSearchResults(value: unknown): RwaSearchResult[] {
  return requireArray(value, "search data").map((candidate, index) => {
    if (!isRecord(candidate)) {
      throw new BinanceWeb3Error(`Binance Web3 response has invalid result ${index}`, {
        kind: "schema",
      });
    }

    const assets = requireArray(candidate.assets, `result ${index} assets`).map(
      (asset, assetIndex): RwaAsset => {
        if (!isRecord(asset)) {
          throw new BinanceWeb3Error(
            `Binance Web3 response has invalid result ${index} asset ${assetIndex}`,
            { kind: "schema" },
          );
        }
        const binanceChainId = requireString(
          asset.binanceChainId,
          `result ${index} asset ${assetIndex} binanceChainId`,
        );
        const tokenContractAddress = requireString(
          asset.tokenContractAddress,
          `result ${index} asset ${assetIndex} tokenContractAddress`,
        );
        if (binanceChainId === BSC_CHAIN_ID && !ADDRESS_PATTERN.test(tokenContractAddress)) {
          throw new BinanceWeb3Error(
            `Binance Web3 response has invalid result ${index} asset ${assetIndex} BSC address`,
            { kind: "schema" },
          );
        }
        const assetType = requireInteger(
          asset.assetType,
          `result ${index} asset ${assetIndex} assetType`,
        );
        if (assetType !== 1 && assetType !== 2 && assetType !== 3) {
          throw new BinanceWeb3Error(
            `Binance Web3 response has invalid result ${index} asset ${assetIndex} type`,
            { kind: "schema" },
          );
        }
        return {
          platformId: requireString(
            asset.platformId,
            `result ${index} asset ${assetIndex} platformId`,
          ),
          binanceChainId,
          tokenContractAddress,
          tokenSymbol: requireString(
            asset.tokenSymbol,
            `result ${index} asset ${assetIndex} tokenSymbol`,
          ),
          assetType,
        };
      },
    );

    return {
      ticker: requireString(candidate.ticker, `result ${index} ticker`),
      companyName: requireString(candidate.companyName, `result ${index} companyName`),
      assets,
    };
  });
}

function normalizeKeyword(value: string): string {
  const keyword = value.trim();
  if (keyword.length < 1 || keyword.length > 80 || /[\u0000-\u001f\u007f]/u.test(keyword)) {
    throw new BinanceWeb3Error(
      "RWA search keyword must contain 1 to 80 characters and no control characters",
      { kind: "configuration" },
    );
  }
  return keyword;
}

function normalizePlatform(value: string | undefined): "ondo" | "bstock" | undefined {
  if (value === undefined) return undefined;
  if (value !== "ondo" && value !== "bstock") {
    throw new BinanceWeb3Error("RWA platform must be ondo or bstock", {
      kind: "configuration",
    });
  }
  return value;
}

export function createBinanceWeb3Client(options: BinanceWeb3ClientOptions) {
  const credentials = {
    apiKey: requireNonEmpty(options.apiKey, "Binance Web3 API key"),
    secretKey: requireNonEmpty(options.secretKey, "Binance Web3 secret key"),
  };
  const baseUrl = normalizeBaseUrl(options.baseUrl ?? DEFAULT_BASE_URL);
  const timeoutMs = normalizeTimeout(options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
  const fetchImplementation = options.fetchImplementation ?? fetch;
  const now = options.now ?? (() => new Date());
  const nonce = options.nonce ?? randomUUID;

  async function get<T>(
    apiPath: string,
    query: readonly QueryEntry[],
    parseData: (value: unknown) => T,
  ): Promise<TimestampedResult<T>> {
    const signed = buildSignedGetRequest(credentials, {
      apiPath,
      query,
      timestamp: now().toISOString(),
      nonce: nonce(),
      baseUrl,
    });

    let response: Response;
    try {
      response = await fetchImplementation(signed.url, {
        method: "GET",
        headers: signed.headers,
        redirect: "error",
        signal: AbortSignal.timeout(timeoutMs),
      });
    } catch (error) {
      const timedOut = error instanceof DOMException && error.name === "TimeoutError";
      throw new BinanceWeb3Error(
        timedOut ? "Binance Web3 request timed out" : "Binance Web3 request failed",
        { kind: timedOut ? "timeout" : "upstream", cause: error },
      );
    }

    let decoded: unknown;
    try {
      decoded = await response.json();
    } catch (error) {
      throw new BinanceWeb3Error("Binance Web3 returned invalid JSON", {
        kind: "schema",
        status: response.status,
        cause: error,
      });
    }

    const envelope = parseEnvelope(decoded);
    const code = typeof envelope.code === "number" ? envelope.code : undefined;
    const message = typeof envelope.msg === "string" ? envelope.msg : "Upstream request failed";
    if (!response.ok || code !== 0 || envelope.success !== true) {
      throw new BinanceWeb3Error(`Binance Web3 rejected the request: ${message}`, {
        kind: "upstream",
        status: response.status,
        code,
      });
    }

    return {
      data: parseData(envelope.data),
      timestamp: parseTimestamp(envelope.timestamp),
    };
  }

  return {
    async getRwaPlatforms(platform?: string): Promise<TimestampedResult<RwaPlatform[]>> {
      const normalizedPlatform = normalizePlatform(platform);
      return get(
        "/api/v1/dex/market/rwa/platforms",
        normalizedPlatform ? [["platformId", normalizedPlatform]] : [],
        parsePlatforms,
      );
    },

    async searchRwaTokens(
      keyword: string,
      platform?: string,
    ): Promise<TimestampedResult<RwaSearchResult[]>> {
      const normalizedPlatform = normalizePlatform(platform);
      const query: QueryEntry[] = [["keyword", normalizeKeyword(keyword)]];
      if (normalizedPlatform) query.push(["platformId", normalizedPlatform]);
      return get("/api/v1/dex/market/rwa/search", query, parseSearchResults);
    },

    filterBscAssets(results: readonly RwaSearchResult[]): RwaSearchResult[] {
      return results
        .map((result) => ({
          ...result,
          assets: result.assets.filter((asset) => asset.binanceChainId === BSC_CHAIN_ID),
        }))
        .filter((result) => result.assets.length > 0);
    },
  };
}

export function createBinanceWeb3ClientFromEnv(
  environment: NodeJS.ProcessEnv = process.env,
) {
  const timeoutValue = environment.BINANCE_WEB3_TIMEOUT_MS;
  const timeoutMs = timeoutValue === undefined ? undefined : Number(timeoutValue);
  return createBinanceWeb3Client({
    apiKey: environment.BINANCE_WEB3_API_KEY ?? "",
    secretKey: environment.BINANCE_WEB3_SECRET_KEY ?? "",
    baseUrl: environment.BINANCE_WEB3_BASE_URL,
    timeoutMs,
  });
}
