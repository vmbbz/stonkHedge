import { createHash, createHmac, randomUUID } from "node:crypto";

const DEFAULT_BASE_URL = "https://web3.binance.com/build";
const DEFAULT_TIMEOUT_MS = 8_000;
const MAX_TIMEOUT_MS = 30_000;
const BSC_CHAIN_ID = "56";
const ADDRESS_PATTERN = /^0x[a-fA-F0-9]{40}$/;
const INTEGER_STRING_PATTERN = /^(?:0|[1-9]\d*)$/u;
const QUOTE_IDENTIFIER_PATTERN = /^[A-Za-z0-9_-]{1,128}$/u;
const USDT_DECIMALS = 18;
const MIN_USDT_QUOTE_RAW = 5_100_000_000_000_000_000n;
const MAX_USDT_QUOTE_RAW = 5_100_000_000_000_000_000n;
const PUBLIC_QUOTE_LIFETIME_MS = 20_000;

export const BSC_USDT_ADDRESS = "0x55d398326f99059ff775485246999027b3197955";

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

export interface SignedPostRequest extends SignedGetRequest {
  body: string;
}

export interface ExactErc20Approval {
  functionName: "approve";
  spender: string;
  amount: string;
}

export interface EvmTransactionPayload {
  from: string;
  to: string;
  value: string;
  data: string;
}

export interface TransactionBalanceChange {
  contractAddress: string;
  tokenType: string;
  change: string;
  owner: string;
}

export interface TransactionAllowanceChange {
  tokenAddress: string;
  owner: string;
  spender: string;
  preAmount: string;
  postAmount: string;
}

export interface TransactionSimulation {
  status: "SUCCESS" | "FAILED";
  failReason: string | null;
  balanceChanges: TransactionBalanceChange[];
  allowanceChanges: TransactionAllowanceChange[];
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

export interface RwaTokenPrice {
  binanceChainId: string;
  tokenContractAddress: string;
  platformId: string;
  tokenPrice: string;
  referencePrice: string;
  tokenPriceUpdatedAt: number;
}

export interface RwaProtection {
  supported: boolean;
  url: string | null;
}

export interface RwaUnderlyingProfile {
  binanceChainId: string;
  tokenContractAddress: string;
  platformId: string;
  underlyingTicker: string;
  underlyingFullName: string;
  assetType: RwaAssetType;
  tokenToShareRatio: string;
  protections: Record<string, RwaProtection>;
  companyInfo: {
    website: string | null;
    industry: string | null;
  } | null;
}

export type RwaMarketStatus =
  | "premarket"
  | "regular"
  | "postmarket"
  | "overnight"
  | "offhours"
  | "closed"
  | "pause";

export type RwaReasonCode =
  | "TRADING"
  | "MARKET_CLOSED"
  | "MARKET_PAUSED"
  | "MARKET_MAINTENANCE"
  | "ASSET_PAUSED"
  | "ASSET_LIMITED"
  | "UNSUPPORTED";

export interface RwaStatusInfo {
  openState: boolean;
  marketStatus: RwaMarketStatus | null;
  reasonCode: RwaReasonCode | null;
  reasonMsg: string | null;
  nextOpenTime: number | null;
  nextCloseTime: number | null;
}

export interface RwaMarketData {
  referencePrice: string | null;
  high52W: string | null;
  low52W: string | null;
  volumeShares24H: string | null;
  avgDailyVolume1Y: string | null;
  totalShares: string | null;
  marketCap: string | null;
  turnoverRate: string | null;
  amplitude: string | null;
  peRatioTTM: string | null;
  pbRatio: string | null;
  dividendYield: string | null;
  latestDividend: string | null;
}

export interface RwaUnderlyingMarket {
  binanceChainId: string;
  tokenContractAddress: string;
  platformId: string;
  assetType: RwaAssetType;
  statusInfo: RwaStatusInfo;
  marketData: RwaMarketData;
}

export interface RwaComparisonAsset {
  asset: RwaAsset;
  price: RwaTokenPrice;
  profile: RwaUnderlyingProfile;
  market: RwaUnderlyingMarket;
}

export interface RwaComparison {
  ticker: string;
  companyName: string;
  assets: RwaComparisonAsset[];
  timestamps: {
    search: number;
    price: number;
    profiles: number[];
    markets: number[];
  };
}

export interface AggregatorQuoteToken {
  tokenContractAddress: string;
  tokenSymbol: string;
  tokenUnitPrice: string;
  decimal: string;
  isHoneyPot: boolean;
  taxRate: string;
}

export interface AggregatorQuoteRouteSegment {
  dexProtocol: {
    dexName: string;
    percent: string;
  };
  fromToken: {
    tokenContractAddress: string;
    tokenSymbol: string;
  };
  fromTokenIndex: string;
  toToken: {
    tokenContractAddress: string;
    tokenSymbol: string;
  };
  toTokenIndex: string;
}

export interface AggregatorQuoteRoute {
  quoteId: string;
  vendorName: string;
  binanceChainId: string;
  fromTokenAmount: string;
  toTokenAmount: string;
  tradeFee: string | null;
  estimateGasFee: string | null;
  priceImpactPercent: string | null;
  router: string;
  fromToken: AggregatorQuoteToken;
  toToken: AggregatorQuoteToken;
  dexRouterList: AggregatorQuoteRouteSegment[];
  executionMode: "RFQ" | "SWAP";
  approveTarget: string | null;
  isBest: boolean;
  feeAmount: string | null;
  feeToken: string | null;
  actualSwapAmount: string | null;
}

export interface RwaReadOnlyQuote {
  ticker: string;
  companyName: string;
  asset: RwaAsset;
  userWalletAddress: string;
  input: {
    symbol: "USDT";
    displayAmount: string;
    rawAmount: string;
  };
  routes: AggregatorQuoteRoute[];
  timestamp: number;
  expiresAt: number;
}

export interface AggregatorApprovalTransaction {
  data: string;
  dexContractAddress: string;
  gasLimit: string;
  gasPrice: string;
  decoded: ExactErc20Approval;
}

export interface AggregatorSwapTransaction extends EvmTransactionPayload {
  gas: string;
  gasPrice: string;
  maxPriorityFeePerGas: string;
  minReceiveAmount: string;
  slippagePercent: string;
  signatureData: string[];
}

export interface AggregatorSwapBuild {
  routerResult: {
    binanceChainId: string;
    vendorName: string;
    fromTokenAmount: string;
    toTokenAmount: string;
    tradeFee: string | null;
    estimateGasFee: string | null;
    router: string;
    priceImpactPercent: string;
    dexRouterList: AggregatorQuoteRouteSegment[];
    fromToken: AggregatorQuoteToken;
    toToken: AggregatorQuoteToken;
    feeAmount: string | null;
    feeToken: string | null;
    actualSwapAmount: string | null;
  };
  tx: AggregatorSwapTransaction;
  executionMode: "SWAP" | "RFQ";
}

export interface PublicTransactionEvidence {
  from?: string;
  to: string;
  value: string;
  selector: string;
  calldataHash: string;
}

export interface PublicSimulationSummary {
  status: "SUCCESS" | "FAILED";
  failReason: string | null;
  balanceChangeCount: number;
  allowanceChangeCount: number;
}

export interface RwaSimulationProof {
  ticker: string;
  companyName: string;
  asset: {
    platformId: string;
    tokenContractAddress: string;
    tokenSymbol: string;
  };
  sender: string;
  input: { symbol: "USDT"; displayAmount: string; rawAmount: string };
  route: {
    quoteIdHash: string;
    vendorName: string;
    executionMode: "SWAP";
    expectedOutputRaw: string;
    slippagePercent: "0.5";
  };
  approval: {
    token: string;
    spender: string;
    amount: string;
    transaction: PublicTransactionEvidence;
    simulation: PublicSimulationSummary;
  };
  swap: {
    transaction: PublicTransactionEvidence & { from: string };
    minimumOutputRaw: string;
    simulation: PublicSimulationSummary;
  };
  verdict: "CLEAR" | "BLOCKED";
  reasons: string[];
  timestamp: number;
}

export interface TimestampedResult<T> {
  data: T;
  timestamp: number;
}

export class BinanceWeb3Error extends Error {
  readonly kind: "configuration" | "not_found" | "upstream" | "schema" | "timeout";
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

export function buildSignedPostRequest(
  credentials: BinanceWeb3Credentials,
  options: {
    apiPath: string;
    body: string;
    timestamp: string;
    nonce: string;
    baseUrl?: string;
  },
): SignedPostRequest {
  const apiKey = requireNonEmpty(credentials.apiKey, "Binance Web3 API key");
  const secretKey = requireNonEmpty(credentials.secretKey, "Binance Web3 secret key");
  assertApiPath(options.apiPath);
  if (!options.body || options.body.length > 100_000) {
    throw new BinanceWeb3Error("Binance Web3 POST body is invalid", {
      kind: "configuration",
    });
  }
  const baseUrl = normalizeBaseUrl(options.baseUrl ?? DEFAULT_BASE_URL);
  const requestPath = `/build${options.apiPath}`;
  const preHash = `${options.timestamp}POST${requestPath}${options.body}`;
  const signature = createHmac("sha256", secretKey)
    .update(preHash, "utf8")
    .digest("base64");

  return {
    url: `${baseUrl}${options.apiPath}`,
    requestPath,
    timestamp: options.timestamp,
    body: options.body,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
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

function optionalNullableString(value: unknown, path: string): string | null {
  if (value === undefined || value === null) return null;
  return requireString(value, path);
}

function requireBoolean(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return value;
}

function requireInteger(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value)) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return value;
}

function requireNullableInteger(value: unknown, path: string): number | null {
  if (value === null) return null;
  return requireInteger(value, path);
}

function requireDecimalString(value: unknown, path: string, positive = false): string {
  const decimal = requireString(value, path);
  const numeric = Number(decimal);
  if (!/^-?(?:0|[1-9]\d*)(?:\.\d+)?$/u.test(decimal) || !Number.isFinite(numeric)) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  if (positive && numeric <= 0) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return decimal;
}

function requireNullableDecimalString(value: unknown, path: string): string | null {
  if (value === null) return null;
  return requireDecimalString(value, path);
}

function requireIntegerString(value: unknown, path: string, positive = false): string {
  const integer = requireString(value, path);
  if (!INTEGER_STRING_PATTERN.test(integer) || (positive && BigInt(integer) <= 0n)) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return integer;
}

function requireNullableIntegerString(value: unknown, path: string): string | null {
  if (value === null) return null;
  return requireIntegerString(value, path);
}

function requireAssetType(value: unknown, path: string): RwaAssetType {
  const assetType = requireInteger(value, path);
  if (assetType !== 1 && assetType !== 2 && assetType !== 3) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return assetType;
}

function requireBscAddress(value: unknown, path: string): string {
  const address = requireString(value, path);
  if (!ADDRESS_PATTERN.test(address)) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return address.toLowerCase();
}

function requireHexData(value: unknown, path: string, minimumBytes = 4): string {
  const data = requireString(value, path).toLowerCase();
  const payload = data.slice(2);
  if (
    !data.startsWith("0x")
    || payload.length < minimumBytes * 2
    || payload.length % 2 !== 0
    || !/^[a-f0-9]+$/u.test(payload)
  ) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return data;
}

function sha256Hex(value: string): string {
  return `0x${createHash("sha256").update(value, "utf8").digest("hex")}`;
}

function sha256Calldata(value: string): string {
  return `0x${createHash("sha256").update(Buffer.from(value.slice(2), "hex")).digest("hex")}`;
}

export function decodeExactErc20Approval(value: string): ExactErc20Approval {
  const data = requireHexData(value, "approve calldata");
  if (data.length !== 2 + 8 + 64 + 64) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid approve calldata length", {
      kind: "schema",
    });
  }
  if (!data.startsWith("0x095ea7b3")) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid approve selector", {
      kind: "schema",
    });
  }
  const spenderWord = data.slice(10, 74);
  if (!/^0{24}[a-f0-9]{40}$/u.test(spenderWord)) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid approve spender encoding", {
      kind: "schema",
    });
  }
  return {
    functionName: "approve",
    spender: `0x${spenderWord.slice(24)}`,
    amount: BigInt(`0x${data.slice(74)}`).toString(),
  };
}

export function parseTransactionSimulation(value: unknown): TransactionSimulation {
  if (!isRecord(value)) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid simulation data", {
      kind: "schema",
    });
  }
  const status = requireString(value.status, "simulation status");
  if (status !== "SUCCESS" && status !== "FAILED") {
    throw new BinanceWeb3Error("Binance Web3 response has invalid simulation status", {
      kind: "schema",
    });
  }
  const failReason = value.failReason === null || value.failReason === ""
    ? null
    : requireShortString(value.failReason, "simulation failure reason", 2_048);
  const balanceChanges = requireArray(value.balanceChanges, "simulation balance changes");
  const allowanceChanges = requireArray(value.allowanceChanges, "simulation allowance changes");
  if (balanceChanges.length > 128 || allowanceChanges.length > 128) {
    throw new BinanceWeb3Error("Binance Web3 simulation change set exceeds the safety limit", {
      kind: "schema",
    });
  }
  return {
    status,
    failReason,
    balanceChanges: balanceChanges.map((candidate, index) => {
      if (!isRecord(candidate)) {
        throw new BinanceWeb3Error(`Binance Web3 response has invalid balance change ${index}`, {
          kind: "schema",
        });
      }
      const contractAddress = candidate.contractAddress === ""
        ? ""
        : requireBscAddress(candidate.contractAddress, `balance change ${index} token`);
      const change = requireString(candidate.change, `balance change ${index} amount`);
      if (!/^-?(?:0|[1-9]\d*)$/u.test(change)) {
        throw new BinanceWeb3Error(`Binance Web3 response has invalid balance change ${index} amount`, {
          kind: "schema",
        });
      }
      return {
        contractAddress,
        tokenType: requireShortString(candidate.tokenType, `balance change ${index} type`, 32),
        change,
        owner: requireBscAddress(candidate.owner, `balance change ${index} owner`),
      };
    }),
    allowanceChanges: allowanceChanges.map((candidate, index) => {
      if (!isRecord(candidate)) {
        throw new BinanceWeb3Error(`Binance Web3 response has invalid allowance change ${index}`, {
          kind: "schema",
        });
      }
      return {
        tokenAddress: requireBscAddress(candidate.tokenAddress, `allowance change ${index} token`),
        owner: requireBscAddress(candidate.owner, `allowance change ${index} owner`),
        spender: requireBscAddress(candidate.spender, `allowance change ${index} spender`),
        preAmount: requireIntegerString(candidate.preAmount, `allowance change ${index} pre amount`),
        postAmount: requireIntegerString(candidate.postAmount, `allowance change ${index} post amount`),
      };
    }),
  };
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
        const assetType = requireAssetType(
          asset.assetType,
          `result ${index} asset ${assetIndex} assetType`,
        );
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

function parseTokenPrices(value: unknown): RwaTokenPrice[] {
  return requireArray(value, "price data").map((candidate, index) => {
    if (!isRecord(candidate)) {
      throw new BinanceWeb3Error(`Binance Web3 response has invalid price ${index}`, {
        kind: "schema",
      });
    }
    const binanceChainId = requireString(candidate.binanceChainId, `price ${index} binanceChainId`);
    if (binanceChainId !== BSC_CHAIN_ID) {
      throw new BinanceWeb3Error(`Binance Web3 response has invalid price ${index} chain`, {
        kind: "schema",
      });
    }
    return {
      binanceChainId,
      tokenContractAddress: requireBscAddress(
        candidate.tokenContractAddress,
        `price ${index} tokenContractAddress`,
      ),
      platformId: requireString(candidate.platformId, `price ${index} platformId`),
      tokenPrice: requireDecimalString(candidate.tokenPrice, `price ${index} tokenPrice`, true),
      referencePrice: requireDecimalString(
        candidate.referencePrice,
        `price ${index} referencePrice`,
        true,
      ),
      tokenPriceUpdatedAt: requireInteger(
        candidate.tokenPriceUpdatedAt,
        `price ${index} tokenPriceUpdatedAt`,
      ),
    };
  });
}

function parseProtections(value: unknown): Record<string, RwaProtection> {
  if (!isRecord(value)) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid protections", {
      kind: "schema",
    });
  }
  return Object.fromEntries(
    Object.entries(value).map(([key, candidate]) => {
      if (!isRecord(candidate)) {
        throw new BinanceWeb3Error(`Binance Web3 response has invalid protection ${key}`, {
          kind: "schema",
        });
      }
      return [
        key,
        {
          supported: requireBoolean(candidate.supported, `protection ${key} supported`),
          url: requireNullableString(candidate.url, `protection ${key} url`),
        },
      ];
    }),
  );
}

function parseUnderlyingProfile(value: unknown): RwaUnderlyingProfile {
  if (!isRecord(value)) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid underlying profile", {
      kind: "schema",
    });
  }
  const binanceChainId = requireString(value.binanceChainId, "profile binanceChainId");
  if (binanceChainId !== BSC_CHAIN_ID) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid profile chain", {
      kind: "schema",
    });
  }
  let companyInfo: RwaUnderlyingProfile["companyInfo"] = null;
  if (value.companyInfo !== null) {
    if (!isRecord(value.companyInfo)) {
      throw new BinanceWeb3Error("Binance Web3 response has invalid profile companyInfo", {
        kind: "schema",
      });
    }
    companyInfo = {
      website: optionalNullableString(value.companyInfo.website, "profile companyInfo website"),
      industry: optionalNullableString(value.companyInfo.industry, "profile companyInfo industry"),
    };
  }
  return {
    binanceChainId,
    tokenContractAddress: requireBscAddress(
      value.tokenContractAddress,
      "profile tokenContractAddress",
    ),
    platformId: requireString(value.platformId, "profile platformId"),
    underlyingTicker: requireString(value.underlyingTicker, "profile underlyingTicker"),
    underlyingFullName: requireString(value.underlyingFullName, "profile underlyingFullName"),
    assetType: requireAssetType(value.assetType, "profile assetType"),
    tokenToShareRatio: requireDecimalString(
      value.tokenToShareRatio,
      "profile tokenToShareRatio",
      true,
    ),
    protections: parseProtections(value.protections),
    companyInfo,
  };
}

const MARKET_STATUSES = new Set<RwaMarketStatus>([
  "premarket",
  "regular",
  "postmarket",
  "overnight",
  "offhours",
  "closed",
  "pause",
]);
const REASON_CODES = new Set<RwaReasonCode>([
  "TRADING",
  "MARKET_CLOSED",
  "MARKET_PAUSED",
  "MARKET_MAINTENANCE",
  "ASSET_PAUSED",
  "ASSET_LIMITED",
  "UNSUPPORTED",
]);

function parseStatusInfo(value: unknown): RwaStatusInfo {
  if (!isRecord(value)) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid statusInfo", {
      kind: "schema",
    });
  }
  const marketStatus = requireNullableString(value.marketStatus, "statusInfo marketStatus");
  if (marketStatus !== null && !MARKET_STATUSES.has(marketStatus as RwaMarketStatus)) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid statusInfo marketStatus", {
      kind: "schema",
    });
  }
  const reasonCode = requireNullableString(value.reasonCode, "statusInfo reasonCode");
  if (reasonCode !== null && !REASON_CODES.has(reasonCode as RwaReasonCode)) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid statusInfo reasonCode", {
      kind: "schema",
    });
  }
  return {
    openState: requireBoolean(value.openState, "statusInfo openState"),
    marketStatus: marketStatus as RwaMarketStatus | null,
    reasonCode: reasonCode as RwaReasonCode | null,
    reasonMsg: requireNullableString(value.reasonMsg, "statusInfo reasonMsg"),
    nextOpenTime: requireNullableInteger(value.nextOpenTime, "statusInfo nextOpenTime"),
    nextCloseTime: requireNullableInteger(value.nextCloseTime, "statusInfo nextCloseTime"),
  };
}

function parseMarketData(value: unknown): RwaMarketData {
  if (!isRecord(value)) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid marketData", {
      kind: "schema",
    });
  }
  return {
    referencePrice: requireNullableDecimalString(value.referencePrice, "marketData referencePrice"),
    high52W: requireNullableDecimalString(value.high52W, "marketData high52W"),
    low52W: requireNullableDecimalString(value.low52W, "marketData low52W"),
    volumeShares24H: requireNullableDecimalString(value.volumeShares24H, "marketData volumeShares24H"),
    avgDailyVolume1Y: requireNullableDecimalString(value.avgDailyVolume1Y, "marketData avgDailyVolume1Y"),
    totalShares: requireNullableDecimalString(value.totalShares, "marketData totalShares"),
    marketCap: requireNullableDecimalString(value.marketCap, "marketData marketCap"),
    turnoverRate: requireNullableDecimalString(value.turnoverRate, "marketData turnoverRate"),
    amplitude: requireNullableDecimalString(value.amplitude, "marketData amplitude"),
    peRatioTTM: requireNullableDecimalString(value.peRatioTTM, "marketData peRatioTTM"),
    pbRatio: requireNullableDecimalString(value.pbRatio, "marketData pbRatio"),
    dividendYield: requireNullableDecimalString(value.dividendYield, "marketData dividendYield"),
    latestDividend: requireNullableDecimalString(value.latestDividend, "marketData latestDividend"),
  };
}

function parseUnderlyingMarket(value: unknown): RwaUnderlyingMarket {
  if (!isRecord(value)) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid underlying market", {
      kind: "schema",
    });
  }
  const binanceChainId = requireString(value.binanceChainId, "market binanceChainId");
  if (binanceChainId !== BSC_CHAIN_ID) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid market chain", {
      kind: "schema",
    });
  }
  return {
    binanceChainId,
    tokenContractAddress: requireBscAddress(value.tokenContractAddress, "market tokenContractAddress"),
    platformId: requireString(value.platformId, "market platformId"),
    assetType: requireAssetType(value.assetType, "market assetType"),
    statusInfo: parseStatusInfo(value.statusInfo),
    marketData: parseMarketData(value.marketData),
  };
}

function requireShortString(value: unknown, path: string, maximumLength: number): string {
  const text = requireString(value, path);
  if (text.length > maximumLength || /[\u0000-\u001f\u007f]/u.test(text)) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return text;
}

function requireRate(value: unknown, path: string, maximum: number): string {
  const rate = requireDecimalString(value, path);
  const numeric = Number(rate);
  if (numeric < 0 || numeric > maximum) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, {
      kind: "schema",
    });
  }
  return rate;
}

function parseQuoteToken(value: unknown, path: string): AggregatorQuoteToken {
  if (!isRecord(value)) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, { kind: "schema" });
  }
  const decimals = requireIntegerString(value.decimal, `${path} decimal`);
  if (BigInt(decimals) > 255n) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path} decimal`, {
      kind: "schema",
    });
  }
  return {
    tokenContractAddress: requireBscAddress(value.tokenContractAddress, `${path} address`),
    tokenSymbol: requireShortString(value.tokenSymbol, `${path} symbol`, 32),
    tokenUnitPrice: requireDecimalString(value.tokenUnitPrice, `${path} unit price`, true),
    decimal: decimals,
    isHoneyPot: requireBoolean(value.isHoneyPot, `${path} honeypot flag`),
    taxRate: requireRate(value.taxRate, `${path} tax rate`, 1),
  };
}

function parseQuoteRouteToken(
  value: unknown,
  path: string,
): AggregatorQuoteRouteSegment["fromToken"] {
  if (!isRecord(value)) {
    throw new BinanceWeb3Error(`Binance Web3 response has invalid ${path}`, { kind: "schema" });
  }
  return {
    tokenContractAddress: requireBscAddress(value.tokenContractAddress, `${path} address`),
    tokenSymbol: requireShortString(value.tokenSymbol, `${path} symbol`, 32),
  };
}

function parseQuoteSegments(value: unknown, routeIndex: number): AggregatorQuoteRouteSegment[] {
  const segments = requireArray(value, `quote ${routeIndex} route list`);
  if (segments.length > 32) {
    throw new BinanceWeb3Error("Binance Web3 quote route exceeds the segment safety limit", {
      kind: "schema",
    });
  }
  return segments.map((candidate, segmentIndex) => {
    if (!isRecord(candidate) || !isRecord(candidate.dexProtocol)) {
      throw new BinanceWeb3Error(
        `Binance Web3 response has invalid quote ${routeIndex} segment ${segmentIndex}`,
        { kind: "schema" },
      );
    }
    return {
      dexProtocol: {
        dexName: requireShortString(
          candidate.dexProtocol.dexName,
          `quote ${routeIndex} segment ${segmentIndex} DEX name`,
          80,
        ),
        percent: requireRate(
          candidate.dexProtocol.percent,
          `quote ${routeIndex} segment ${segmentIndex} percent`,
          100,
        ),
      },
      fromToken: parseQuoteRouteToken(
        candidate.fromToken,
        `quote ${routeIndex} segment ${segmentIndex} from token`,
      ),
      fromTokenIndex: requireIntegerString(
        candidate.fromTokenIndex,
        `quote ${routeIndex} segment ${segmentIndex} from index`,
      ),
      toToken: parseQuoteRouteToken(
        candidate.toToken,
        `quote ${routeIndex} segment ${segmentIndex} to token`,
      ),
      toTokenIndex: requireIntegerString(
        candidate.toTokenIndex,
        `quote ${routeIndex} segment ${segmentIndex} to index`,
      ),
    };
  });
}

function parseAggregatorQuoteRoutes(value: unknown): AggregatorQuoteRoute[] {
  const candidates = requireArray(value, "quote data");
  if (candidates.length < 1 || candidates.length > 8) {
    throw new BinanceWeb3Error("Binance Web3 quote requires 1 to 8 routes", {
      kind: candidates.length === 0 ? "not_found" : "schema",
    });
  }
  const quoteIds = new Set<string>();
  const routes = candidates.map((candidate, index): AggregatorQuoteRoute => {
    if (!isRecord(candidate)) {
      throw new BinanceWeb3Error(`Binance Web3 response has invalid quote ${index}`, {
        kind: "schema",
      });
    }
    const quoteId = requireShortString(candidate.quoteId, `quote ${index} ID`, 128);
    if (!QUOTE_IDENTIFIER_PATTERN.test(quoteId) || quoteIds.has(quoteId)) {
      throw new BinanceWeb3Error(`Binance Web3 response has invalid quote ${index} ID`, {
        kind: "schema",
      });
    }
    quoteIds.add(quoteId);
    const executionMode = requireString(candidate.executionMode, `quote ${index} execution mode`);
    if (executionMode !== "RFQ" && executionMode !== "SWAP") {
      throw new BinanceWeb3Error(
        `Binance Web3 response has invalid quote ${index} execution mode ${JSON.stringify(executionMode)}`,
        {
          kind: "schema",
        },
      );
    }
    const approveTarget = candidate.approveTarget === null
      ? null
      : requireBscAddress(candidate.approveTarget, `quote ${index} approve target`);
    const feeToken = candidate.feeToken === null
      ? null
      : requireBscAddress(candidate.feeToken, `quote ${index} fee token`);
    return {
      quoteId,
      vendorName: requireShortString(candidate.vendorName, `quote ${index} vendor`, 80),
      binanceChainId: requireString(candidate.binanceChainId, `quote ${index} chain`),
      fromTokenAmount: requireIntegerString(candidate.fromTokenAmount, `quote ${index} input`, true),
      toTokenAmount: requireIntegerString(candidate.toTokenAmount, `quote ${index} output`, true),
      tradeFee: candidate.tradeFee === null
        ? null
        : requireDecimalString(candidate.tradeFee, `quote ${index} trade fee`),
      estimateGasFee: requireNullableIntegerString(candidate.estimateGasFee, `quote ${index} gas estimate`),
      priceImpactPercent: candidate.priceImpactPercent === null
        ? null
        : requireDecimalString(candidate.priceImpactPercent, `quote ${index} price impact`),
      router: requireShortString(candidate.router, `quote ${index} router`, 2_048),
      fromToken: parseQuoteToken(candidate.fromToken, `quote ${index} from token`),
      toToken: parseQuoteToken(candidate.toToken, `quote ${index} to token`),
      dexRouterList: parseQuoteSegments(candidate.dexRouterList, index),
      executionMode,
      approveTarget,
      isBest: requireBoolean(candidate.isBest, `quote ${index} best flag`),
      feeAmount: requireNullableIntegerString(candidate.feeAmount, `quote ${index} fee amount`),
      feeToken,
      actualSwapAmount: requireNullableIntegerString(
        candidate.actualSwapAmount,
        `quote ${index} actual swap amount`,
      ),
    };
  });
  if (routes.filter((route) => route.isBest).length !== 1) {
    throw new BinanceWeb3Error("Binance Web3 quote response must identify exactly one best route", {
      kind: "schema",
    });
  }
  return routes;
}

function parseApprovalTransactions(value: unknown): AggregatorApprovalTransaction[] {
  const candidates = requireArray(value, "approval transaction data");
  if (candidates.length !== 1) {
    throw new BinanceWeb3Error("Binance Web3 must return exactly one approval transaction", {
      kind: "schema",
    });
  }
  return candidates.map((candidate, index) => {
    if (!isRecord(candidate)) {
      throw new BinanceWeb3Error(`Binance Web3 response has invalid approval ${index}`, {
        kind: "schema",
      });
    }
    const data = requireHexData(candidate.data, `approval ${index} calldata`);
    return {
      data,
      dexContractAddress: requireBscAddress(
        candidate.dexContractAddress,
        `approval ${index} spender`,
      ),
      gasLimit: requireIntegerString(candidate.gasLimit, `approval ${index} gas limit`, true),
      gasPrice: requireIntegerString(candidate.gasPrice, `approval ${index} gas price`, true),
      decoded: decodeExactErc20Approval(data),
    };
  });
}

function parseSwapBuild(value: unknown): AggregatorSwapBuild {
  if (!isRecord(value) || !isRecord(value.routerResult) || !isRecord(value.tx)) {
    throw new BinanceWeb3Error("Binance Web3 response has invalid swap transaction data", {
      kind: "schema",
    });
  }
  const result = value.routerResult;
  const tx = value.tx;
  const executionMode = requireString(value.executionMode, "swap execution mode");
  if (executionMode !== "SWAP" && executionMode !== "RFQ") {
    throw new BinanceWeb3Error("Binance Web3 response has invalid swap execution mode", {
      kind: "schema",
    });
  }
  const signatureData = tx.signatureData === undefined || tx.signatureData === null
    ? []
    : requireArray(tx.signatureData, "swap signature data");
  if (signatureData.length > 16) {
    throw new BinanceWeb3Error("Binance Web3 swap signature data exceeds the safety limit", {
      kind: "schema",
    });
  }
  return {
    routerResult: {
      binanceChainId: requireString(result.binanceChainId, "swap chain"),
      vendorName: requireShortString(result.vendorName, "swap vendor", 80),
      fromTokenAmount: requireIntegerString(result.fromTokenAmount, "swap input", true),
      toTokenAmount: requireIntegerString(result.toTokenAmount, "swap output", true),
      tradeFee: result.tradeFee === null
        ? null
        : requireDecimalString(result.tradeFee, "swap trade fee"),
      estimateGasFee: requireNullableIntegerString(result.estimateGasFee, "swap gas estimate"),
      router: requireShortString(result.router, "swap router", 2_048),
      priceImpactPercent: requireDecimalString(result.priceImpactPercent, "swap price impact"),
      dexRouterList: parseQuoteSegments(result.dexRouterList, 0),
      fromToken: parseQuoteToken(result.fromToken, "swap from token"),
      toToken: parseQuoteToken(result.toToken, "swap to token"),
      feeAmount: requireNullableIntegerString(result.feeAmount, "swap fee amount"),
      feeToken: result.feeToken === null
        ? null
        : requireBscAddress(result.feeToken, "swap fee token"),
      actualSwapAmount: requireNullableIntegerString(result.actualSwapAmount, "swap actual amount"),
    },
    tx: {
      from: requireBscAddress(tx.from, "swap transaction sender"),
      to: requireBscAddress(tx.to, "swap transaction destination"),
      data: requireHexData(tx.data, "swap transaction calldata"),
      value: requireIntegerString(tx.value, "swap transaction value"),
      gas: requireIntegerString(tx.gas, "swap transaction gas", true),
      gasPrice: requireIntegerString(tx.gasPrice, "swap transaction gas price", true),
      maxPriorityFeePerGas: requireIntegerString(
        tx.maxPriorityFeePerGas,
        "swap transaction priority fee",
      ),
      minReceiveAmount: requireIntegerString(
        tx.minReceiveAmount,
        "swap minimum receive amount",
        true,
      ),
      slippagePercent: requireRate(tx.slippagePercent, "swap slippage", 100),
      signatureData: signatureData.map((item, index) =>
        requireShortString(item, `swap signature data ${index}`, 8_192)),
    },
    executionMode,
  };
}

function simulationSummary(simulation: TransactionSimulation): PublicSimulationSummary {
  return {
    status: simulation.status,
    failReason: simulation.failReason,
    balanceChangeCount: simulation.balanceChanges.length,
    allowanceChangeCount: simulation.allowanceChanges.length,
  };
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

function normalizeBscAddress(value: string): string {
  const address = value.trim().toLowerCase();
  if (!ADDRESS_PATTERN.test(address)) {
    throw new BinanceWeb3Error("RWA token contract address must be a valid EVM address", {
      kind: "configuration",
    });
  }
  return address;
}

function normalizeWalletAddress(value: string): string {
  const address = value.trim().toLowerCase();
  if (!ADDRESS_PATTERN.test(address)) {
    throw new BinanceWeb3Error("Quote receiver must be a valid EVM address", {
      kind: "configuration",
    });
  }
  return address;
}

export function normalizeBoundedUsdtAmount(value: string): {
  displayAmount: string;
  rawAmount: string;
} {
  const amount = value.trim();
  const match = /^(0|[1-9]\d*)(?:\.(\d{1,18}))?$/u.exec(amount);
  if (!match) {
    throw new BinanceWeb3Error("Quote input must be a plain decimal USDT amount", {
      kind: "configuration",
    });
  }
  const whole = match[1] ?? "0";
  const fraction = match[2] ?? "";
  const rawAmount = BigInt(whole) * 10n ** BigInt(USDT_DECIMALS)
    + BigInt(fraction.padEnd(USDT_DECIMALS, "0") || "0");
  if (rawAmount < MIN_USDT_QUOTE_RAW || rawAmount > MAX_USDT_QUOTE_RAW) {
    throw new BinanceWeb3Error("Quote input must be exactly 5.10 USDT", {
      kind: "configuration",
    });
  }
  const normalizedFraction = fraction.replace(/0+$/u, "");
  return {
    displayAmount: `${BigInt(whole)}${normalizedFraction ? `.${normalizedFraction}` : ""}`,
    rawAmount: rawAmount.toString(),
  };
}

function normalizeBscAddresses(values: readonly string[]): string[] {
  const addresses = [...new Set(values.map(normalizeBscAddress))];
  if (addresses.length < 1 || addresses.length > 100) {
    throw new BinanceWeb3Error("RWA price query requires 1 to 100 unique addresses", {
      kind: "configuration",
    });
  }
  return addresses;
}

function assertMatchingIdentity(
  asset: RwaAsset,
  value: { binanceChainId: string; tokenContractAddress: string; platformId: string },
  label: string,
): void {
  if (
    value.binanceChainId !== BSC_CHAIN_ID ||
    value.tokenContractAddress.toLowerCase() !== asset.tokenContractAddress.toLowerCase() ||
    value.platformId !== asset.platformId
  ) {
    throw new BinanceWeb3Error(`Binance Web3 returned mismatched ${label} identity`, {
      kind: "schema",
    });
  }
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

  async function post<T>(
    apiPath: string,
    body: unknown,
    parseData: (value: unknown) => T,
  ): Promise<TimestampedResult<T>> {
    const bodyText = JSON.stringify(body);
    const signed = buildSignedPostRequest(credentials, {
      apiPath,
      body: bodyText,
      timestamp: now().toISOString(),
      nonce: nonce(),
      baseUrl,
    });

    let response: Response;
    try {
      response = await fetchImplementation(signed.url, {
        method: "POST",
        headers: signed.headers,
        body: signed.body,
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

    async getRwaTokenPrices(
      tokenContractAddresses: readonly string[],
    ): Promise<TimestampedResult<RwaTokenPrice[]>> {
      const addresses = normalizeBscAddresses(tokenContractAddresses);
      return get(
        "/api/v1/dex/market/rwa/price",
        [
          ["binanceChainId", BSC_CHAIN_ID],
          ["tokenContractAddresses", addresses.join(",")],
        ],
        parseTokenPrices,
      );
    },

    async getRwaUnderlyingProfile(
      tokenContractAddress: string,
    ): Promise<TimestampedResult<RwaUnderlyingProfile>> {
      return get(
        "/api/v1/dex/market/rwa/underlying-profile",
        [
          ["binanceChainId", BSC_CHAIN_ID],
          ["tokenContractAddress", normalizeBscAddress(tokenContractAddress)],
        ],
        parseUnderlyingProfile,
      );
    },

    async getRwaUnderlyingMarket(
      tokenContractAddress: string,
    ): Promise<TimestampedResult<RwaUnderlyingMarket>> {
      return get(
        "/api/v1/dex/market/rwa/underlying-market",
        [
          ["binanceChainId", BSC_CHAIN_ID],
          ["tokenContractAddress", normalizeBscAddress(tokenContractAddress)],
        ],
        parseUnderlyingMarket,
      );
    },

    async getAggregatorQuote(input: {
      amount: string;
      fromTokenAddress: string;
      toTokenAddress: string;
      userWalletAddress: string;
    }): Promise<TimestampedResult<AggregatorQuoteRoute[]>> {
      const amount = requireIntegerString(input.amount, "quote input amount", true);
      const fromTokenAddress = normalizeBscAddress(input.fromTokenAddress);
      const toTokenAddress = normalizeBscAddress(input.toTokenAddress);
      if (fromTokenAddress === toTokenAddress) {
        throw new BinanceWeb3Error("Quote input and output tokens must differ", {
          kind: "configuration",
        });
      }
      return get(
        "/api/v1/dex/aggregator/quote",
        [
          ["binanceChainId", BSC_CHAIN_ID],
          ["amount", amount],
          ["fromTokenAddress", fromTokenAddress],
          ["toTokenAddress", toTokenAddress],
          ["userWalletAddress", normalizeWalletAddress(input.userWalletAddress)],
        ],
        parseAggregatorQuoteRoutes,
      );
    },

    async getApproveTransaction(input: {
      tokenContractAddress: string;
      approveAmount: string;
      vendorName: string;
      expectedSpender: string;
    }): Promise<TimestampedResult<AggregatorApprovalTransaction>> {
      const tokenContractAddress = normalizeBscAddress(input.tokenContractAddress);
      const approveAmount = requireIntegerString(input.approveAmount, "approval amount", true);
      const vendorName = requireShortString(input.vendorName, "approval vendor", 80);
      const expectedSpender = normalizeBscAddress(input.expectedSpender);
      const result = await get(
        "/api/v1/dex/aggregator/approve-transaction",
        [
          ["binanceChainId", BSC_CHAIN_ID],
          ["tokenContractAddress", tokenContractAddress],
          ["approveAmount", approveAmount],
          ["vendor", vendorName],
        ],
        parseApprovalTransactions,
      );
      const approval = result.data[0];
      if (
        !approval
        || approval.dexContractAddress !== expectedSpender
        || approval.decoded.spender !== expectedSpender
        || approval.decoded.amount !== approveAmount
      ) {
        throw new BinanceWeb3Error("Binance Web3 returned mismatched approval intent", {
          kind: "schema",
        });
      }
      return { data: approval, timestamp: result.timestamp };
    },

    async buildSwapTransaction(input: {
      amount: string;
      fromTokenAddress: string;
      toTokenAddress: string;
      userWalletAddress: string;
      quoteId: string;
      vendorName: string;
      expectedOutputAmount: string;
      slippagePercent: "0.5";
    }): Promise<TimestampedResult<AggregatorSwapBuild>> {
      const amount = requireIntegerString(input.amount, "swap input amount", true);
      const fromTokenAddress = normalizeBscAddress(input.fromTokenAddress);
      const toTokenAddress = normalizeBscAddress(input.toTokenAddress);
      const userWalletAddress = normalizeWalletAddress(input.userWalletAddress);
      const quoteId = requireShortString(input.quoteId, "swap quote ID", 128);
      if (!QUOTE_IDENTIFIER_PATTERN.test(quoteId)) {
        throw new BinanceWeb3Error("Swap quote ID is invalid", { kind: "configuration" });
      }
      const vendorName = requireShortString(input.vendorName, "swap vendor", 80);
      const expectedOutputAmount = requireIntegerString(
        input.expectedOutputAmount,
        "expected swap output",
        true,
      );
      const result = await get(
        "/api/v1/dex/aggregator/swap",
        [
          ["binanceChainId", BSC_CHAIN_ID],
          ["amount", amount],
          ["fromTokenAddress", fromTokenAddress],
          ["toTokenAddress", toTokenAddress],
          ["userWalletAddress", userWalletAddress],
          ["quoteId", quoteId],
          ["slippagePercent", input.slippagePercent],
          ["approveTransaction", "false"],
        ],
        parseSwapBuild,
      );
      const swap = result.data;
      if (swap.executionMode !== "SWAP") {
        throw new BinanceWeb3Error(
          "The selected route requires RFQ signing and cannot enter unsigned simulation",
          { kind: "configuration" },
        );
      }
      if (
        swap.routerResult.binanceChainId !== BSC_CHAIN_ID
        || swap.routerResult.vendorName !== vendorName
        || swap.routerResult.fromTokenAmount !== amount
        || swap.routerResult.toTokenAmount !== expectedOutputAmount
        || swap.routerResult.fromToken.tokenContractAddress !== fromTokenAddress
        || swap.routerResult.toToken.tokenContractAddress !== toTokenAddress
        || swap.tx.from !== userWalletAddress
        || swap.tx.value !== "0"
        || swap.tx.slippagePercent !== input.slippagePercent
        || BigInt(swap.tx.minReceiveAmount) > BigInt(expectedOutputAmount)
      ) {
        throw new BinanceWeb3Error("Binance Web3 returned mismatched swap intent", {
          kind: "schema",
        });
      }
      return result;
    },

    async simulateEvmTransaction(
      transaction: EvmTransactionPayload,
    ): Promise<TimestampedResult<TransactionSimulation>> {
      const evmTx: EvmTransactionPayload = {
        from: normalizeWalletAddress(transaction.from),
        to: normalizeBscAddress(transaction.to),
        value: requireIntegerString(transaction.value, "simulation transaction value"),
        data: requireHexData(transaction.data, "simulation transaction calldata"),
      };
      return post(
        "/api/v1/dex/pre-transaction/simulate",
        { binanceChainId: BSC_CHAIN_ID, evmTx },
        parseTransactionSimulation,
      );
    },

    async quoteRwaFromUsdt(input: {
      keyword: string;
      tokenContractAddress: string;
      userWalletAddress: string;
      usdtAmount: string;
    }): Promise<RwaReadOnlyQuote> {
      const targetAddress = normalizeBscAddress(input.tokenContractAddress);
      const userWalletAddress = normalizeWalletAddress(input.userWalletAddress);
      const normalizedAmount = normalizeBoundedUsdtAmount(input.usdtAmount);
      const search = await this.searchRwaTokens(input.keyword);
      const result = this.filterBscAssets(search.data).find((candidate) =>
        candidate.assets.some(
          (asset) => asset.tokenContractAddress.toLowerCase() === targetAddress,
        ),
      );
      const asset = result?.assets.find(
        (candidate) => candidate.tokenContractAddress.toLowerCase() === targetAddress,
      );
      if (!result || !asset) {
        throw new BinanceWeb3Error(
          "The requested quote token is not a Binance-discovered BSC RWA representation",
          { kind: "not_found" },
        );
      }

      const quote = await this.getAggregatorQuote({
        amount: normalizedAmount.rawAmount,
        fromTokenAddress: BSC_USDT_ADDRESS,
        toTokenAddress: targetAddress,
        userWalletAddress,
      });
      for (const route of quote.data) {
        if (route.binanceChainId !== BSC_CHAIN_ID) {
          throw new BinanceWeb3Error("Binance Web3 returned mismatched quote chain identity", {
            kind: "schema",
          });
        }
        if (route.fromTokenAmount !== normalizedAmount.rawAmount) {
          throw new BinanceWeb3Error("Binance Web3 returned mismatched quote input amount", {
            kind: "schema",
          });
        }
        if (route.fromToken.tokenContractAddress !== BSC_USDT_ADDRESS) {
          throw new BinanceWeb3Error("Binance Web3 returned mismatched quote from-token identity", {
            kind: "schema",
          });
        }
        if (route.toToken.tokenContractAddress !== targetAddress) {
          throw new BinanceWeb3Error("Binance Web3 returned mismatched quote to-token identity", {
            kind: "schema",
          });
        }
      }

      return {
        ticker: result.ticker,
        companyName: result.companyName,
        asset,
        userWalletAddress,
        input: {
          symbol: "USDT",
          ...normalizedAmount,
        },
        routes: quote.data,
        timestamp: quote.timestamp,
        expiresAt: quote.timestamp + PUBLIC_QUOTE_LIFETIME_MS,
      };
    },

    async simulateRwaSwap(input: {
      keyword: string;
      tokenContractAddress: string;
      userWalletAddress: string;
      usdtAmount: string;
    }): Promise<RwaSimulationProof> {
      const quote = await this.quoteRwaFromUsdt(input);
      const route = quote.routes.find((candidate) => candidate.isBest);
      if (!route) {
        throw new BinanceWeb3Error("The quote has no unique best route", { kind: "schema" });
      }
      if (route.executionMode !== "SWAP") {
        throw new BinanceWeb3Error(
          "The best route requires RFQ signing and cannot enter unsigned simulation",
          { kind: "configuration" },
        );
      }
      if (!route.approveTarget) {
        throw new BinanceWeb3Error(
          "The exact ERC-20 approval target was not reported for this route",
          { kind: "schema" },
        );
      }

      const approval = await this.getApproveTransaction({
        tokenContractAddress: BSC_USDT_ADDRESS,
        approveAmount: quote.input.rawAmount,
        vendorName: route.vendorName,
        expectedSpender: route.approveTarget,
      });
      const swap = await this.buildSwapTransaction({
        amount: quote.input.rawAmount,
        fromTokenAddress: BSC_USDT_ADDRESS,
        toTokenAddress: quote.asset.tokenContractAddress,
        userWalletAddress: quote.userWalletAddress,
        quoteId: route.quoteId,
        vendorName: route.vendorName,
        expectedOutputAmount: route.toTokenAmount,
        slippagePercent: "0.5",
      });
      const approvalTransaction: EvmTransactionPayload = {
        from: quote.userWalletAddress,
        to: BSC_USDT_ADDRESS,
        value: "0",
        data: approval.data.data,
      };
      const [approvalSimulation, swapSimulation] = await Promise.all([
        this.simulateEvmTransaction(approvalTransaction),
        this.simulateEvmTransaction(swap.data.tx),
      ]);

      for (const change of approvalSimulation.data.allowanceChanges) {
        if (
          change.tokenAddress !== BSC_USDT_ADDRESS
          || change.owner !== quote.userWalletAddress
          || change.spender !== route.approveTarget
          || change.postAmount !== quote.input.rawAmount
        ) {
          throw new BinanceWeb3Error(
            "Binance Web3 returned an approval simulation with mismatched allowance state",
            { kind: "schema" },
          );
        }
      }
      if (
        approvalSimulation.data.status === "SUCCESS"
        && approvalSimulation.data.allowanceChanges.length !== 1
      ) {
        throw new BinanceWeb3Error(
          "Binance Web3 approval simulation omitted the exact allowance change",
          { kind: "schema" },
        );
      }

      const reasons: string[] = [];
      if (approvalSimulation.data.status !== "SUCCESS") {
        reasons.push(
          `Approval simulation failed${approvalSimulation.data.failReason ? `: ${approvalSimulation.data.failReason}` : ""}`,
        );
      }
      if (swapSimulation.data.status !== "SUCCESS") {
        reasons.push(
          `Swap simulation failed${swapSimulation.data.failReason ? `: ${swapSimulation.data.failReason}` : ""}`,
        );
      }
      if (approvalSimulation.data.status === "SUCCESS" && approvalSimulation.data.failReason) {
        reasons.push(`Approval simulator reported a failure reason: ${approvalSimulation.data.failReason}`);
      }
      if (swapSimulation.data.status === "SUCCESS" && swapSimulation.data.failReason) {
        reasons.push(`Swap simulator reported a failure reason: ${swapSimulation.data.failReason}`);
      }

      return {
        ticker: quote.ticker,
        companyName: quote.companyName,
        asset: {
          platformId: quote.asset.platformId,
          tokenContractAddress: quote.asset.tokenContractAddress.toLowerCase(),
          tokenSymbol: quote.asset.tokenSymbol,
        },
        sender: quote.userWalletAddress,
        input: quote.input,
        route: {
          quoteIdHash: sha256Hex(route.quoteId),
          vendorName: route.vendorName,
          executionMode: "SWAP",
          expectedOutputRaw: route.toTokenAmount,
          slippagePercent: "0.5",
        },
        approval: {
          token: BSC_USDT_ADDRESS,
          spender: route.approveTarget,
          amount: quote.input.rawAmount,
          transaction: {
            to: BSC_USDT_ADDRESS,
            value: "0",
            selector: approval.data.data.slice(0, 10),
            calldataHash: sha256Calldata(approval.data.data),
          },
          simulation: simulationSummary(approvalSimulation.data),
        },
        swap: {
          transaction: {
            from: swap.data.tx.from,
            to: swap.data.tx.to,
            value: swap.data.tx.value,
            selector: swap.data.tx.data.slice(0, 10),
            calldataHash: sha256Calldata(swap.data.tx.data),
          },
          minimumOutputRaw: swap.data.tx.minReceiveAmount,
          simulation: simulationSummary(swapSimulation.data),
        },
        verdict: reasons.length === 0 ? "CLEAR" : "BLOCKED",
        reasons,
        timestamp: Math.max(
          quote.timestamp,
          approval.timestamp,
          swap.timestamp,
          approvalSimulation.timestamp,
          swapSimulation.timestamp,
        ),
      };
    },

    async compareRwaTicker(keyword: string): Promise<RwaComparison> {
      const search = await this.searchRwaTokens(keyword);
      const bscResults = this.filterBscAssets(search.data);
      const exact = bscResults.find(
        (candidate) => candidate.ticker.toLowerCase() === keyword.trim().toLowerCase(),
      );
      const result = exact ?? bscResults[0];
      if (!result) {
        throw new BinanceWeb3Error("No supported BSC tokenized-stock representation was found", {
          kind: "not_found",
        });
      }

      const seen = new Set<string>();
      const assets = result.assets.filter((asset) => {
        const address = asset.tokenContractAddress.toLowerCase();
        if (seen.has(address)) return false;
        seen.add(address);
        return true;
      });
      if (assets.length > 8) {
        throw new BinanceWeb3Error("RWA comparison fan-out exceeds the eight-asset safety limit", {
          kind: "schema",
        });
      }

      const [prices, profiles, markets] = await Promise.all([
        this.getRwaTokenPrices(assets.map((asset) => asset.tokenContractAddress)),
        Promise.all(assets.map((asset) => this.getRwaUnderlyingProfile(asset.tokenContractAddress))),
        Promise.all(assets.map((asset) => this.getRwaUnderlyingMarket(asset.tokenContractAddress))),
      ]);
      const pricesByAddress = new Map(
        prices.data.map((price) => [price.tokenContractAddress.toLowerCase(), price]),
      );
      const comparisonAssets = assets.map((asset, index): RwaComparisonAsset => {
        const price = pricesByAddress.get(asset.tokenContractAddress.toLowerCase());
        const profile = profiles[index]?.data;
        const market = markets[index]?.data;
        if (!price || !profile || !market) {
          throw new BinanceWeb3Error("Binance Web3 returned incomplete comparison data", {
            kind: "schema",
          });
        }
        assertMatchingIdentity(asset, price, "price");
        assertMatchingIdentity(asset, profile, "profile");
        assertMatchingIdentity(asset, market, "market");
        return { asset, price, profile, market };
      });

      return {
        ticker: result.ticker,
        companyName: result.companyName,
        assets: comparisonAssets,
        timestamps: {
          search: search.timestamp,
          price: prices.timestamp,
          profiles: profiles.map((profile) => profile.timestamp),
          markets: markets.map((market) => market.timestamp),
        },
      };
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
