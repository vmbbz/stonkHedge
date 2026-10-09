export type QuoteLevel = "clear" | "watch" | "blocked";

export interface ReadOnlyQuoteToken {
  tokenContractAddress: string;
  tokenSymbol: string;
  tokenUnitPrice: string;
  decimal: string;
  isHoneyPot: boolean;
  taxRate: string;
}

export interface ReadOnlyQuoteSegment {
  dexProtocol: { dexName: string; percent: string };
  fromToken: { tokenContractAddress: string; tokenSymbol: string };
  fromTokenIndex: string;
  toToken: { tokenContractAddress: string; tokenSymbol: string };
  toTokenIndex: string;
}

export interface ReadOnlyQuoteRoute {
  quoteId: string;
  vendorName: string;
  binanceChainId: "56";
  fromTokenAmount: string;
  toTokenAmount: string;
  tradeFee: string | null;
  estimateGasFee: string | null;
  priceImpactPercent: string | null;
  router: string;
  fromToken: ReadOnlyQuoteToken;
  toToken: ReadOnlyQuoteToken;
  dexRouterList: ReadOnlyQuoteSegment[];
  executionMode: "RFQ" | "SWAP";
  approveTarget: string | null;
  isBest: boolean;
  feeAmount: string | null;
  feeToken: string | null;
  actualSwapAmount: string | null;
}

export interface ReadOnlyQuote {
  ticker: string;
  companyName: string;
  asset: {
    platformId: string;
    binanceChainId: "56";
    tokenContractAddress: string;
    tokenSymbol: string;
    assetType: 1 | 2 | 3;
  };
  userWalletAddress: string;
  input: { symbol: "USDT"; displayAmount: string; rawAmount: string };
  routes: ReadOnlyQuoteRoute[];
  timestamp: number;
  expiresAt: number;
}

export interface QuoteAssessment {
  level: QuoteLevel;
  label: string;
  reasons: string[];
  routeCount: number;
  usableForMs: number;
}

const ADDRESS_PATTERN = /^0x[a-f0-9]{40}$/u;
const INTEGER_PATTERN = /^(?:0|[1-9]\d*)$/u;
const DECIMAL_PATTERN = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/u;
const BSC_USDT_ADDRESS = "0x55d398326f99059ff775485246999027b3197955";
const EXACT_USDT_INPUT_RAW = "5100000000000000000";
const BOUNDARY = "READ_ONLY_QUOTE_NO_BUILD_NO_WALLET_NO_SIGNING_NO_BROADCAST";

function record(value: unknown, label: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`Invalid ${label}`);
  }
  return value as Record<string, unknown>;
}

function text(value: unknown, label: string, maximum = 2_048): string {
  if (
    typeof value !== "string"
    || value.length < 1
    || value.length > maximum
    || /[\u0000-\u001f\u007f]/u.test(value)
  ) {
    throw new Error(`Invalid ${label}`);
  }
  return value;
}

function integer(value: unknown, label: string, positive = false): string {
  const parsed = text(value, label, 100);
  if (!INTEGER_PATTERN.test(parsed) || (positive && BigInt(parsed) <= 0n)) {
    throw new Error(`Invalid ${label}`);
  }
  return parsed;
}

function nullableInteger(value: unknown, label: string): string | null {
  if (value === null) return null;
  return integer(value, label);
}

function decimal(value: unknown, label: string): string {
  const parsed = text(value, label, 100);
  if (!DECIMAL_PATTERN.test(parsed) || !Number.isFinite(Number(parsed))) {
    throw new Error(`Invalid ${label}`);
  }
  return parsed;
}

function nullableDecimal(value: unknown, label: string): string | null {
  if (value === null) return null;
  return decimal(value, label);
}

function address(value: unknown, label: string): string {
  const parsed = text(value, label, 42).toLowerCase();
  if (!ADDRESS_PATTERN.test(parsed)) throw new Error(`Invalid ${label}`);
  return parsed;
}

function numberValue(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value <= 0) {
    throw new Error(`Invalid ${label}`);
  }
  return value;
}

function booleanValue(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") throw new Error(`Invalid ${label}`);
  return value;
}

function parseToken(value: unknown, label: string): ReadOnlyQuoteToken {
  const token = record(value, label);
  const decimals = integer(token.decimal, `${label} decimals`);
  const taxRate = decimal(token.taxRate, `${label} tax rate`);
  if (BigInt(decimals) > 255n || Number(taxRate) < 0 || Number(taxRate) > 1) {
    throw new Error(`Invalid ${label} economics`);
  }
  return {
    tokenContractAddress: address(token.tokenContractAddress, `${label} address`),
    tokenSymbol: text(token.tokenSymbol, `${label} symbol`, 32),
    tokenUnitPrice: decimal(token.tokenUnitPrice, `${label} unit price`),
    decimal: decimals,
    isHoneyPot: booleanValue(token.isHoneyPot, `${label} honeypot flag`),
    taxRate,
  };
}

function parseSegmentToken(value: unknown, label: string): ReadOnlyQuoteSegment["fromToken"] {
  const token = record(value, label);
  return {
    tokenContractAddress: address(token.tokenContractAddress, `${label} address`),
    tokenSymbol: text(token.tokenSymbol, `${label} symbol`, 32),
  };
}

function parseSegment(value: unknown, routeIndex: number, segmentIndex: number): ReadOnlyQuoteSegment {
  const segment = record(value, `route ${routeIndex} segment ${segmentIndex}`);
  const protocol = record(segment.dexProtocol, `route ${routeIndex} segment ${segmentIndex} protocol`);
  return {
    dexProtocol: {
      dexName: text(protocol.dexName, `route ${routeIndex} segment ${segmentIndex} DEX`, 80),
      percent: decimal(protocol.percent, `route ${routeIndex} segment ${segmentIndex} percent`),
    },
    fromToken: parseSegmentToken(segment.fromToken, `route ${routeIndex} segment ${segmentIndex} from token`),
    fromTokenIndex: integer(segment.fromTokenIndex, `route ${routeIndex} segment ${segmentIndex} from index`),
    toToken: parseSegmentToken(segment.toToken, `route ${routeIndex} segment ${segmentIndex} to token`),
    toTokenIndex: integer(segment.toTokenIndex, `route ${routeIndex} segment ${segmentIndex} to index`),
  };
}

function parseRoute(value: unknown, index: number): ReadOnlyQuoteRoute {
  const route = record(value, `route ${index}`);
  if (route.binanceChainId !== "56") throw new Error(`Invalid route chain ${index}`);
  if (route.executionMode !== "RFQ" && route.executionMode !== "SWAP") {
    throw new Error(`Invalid route execution mode ${index}`);
  }
  if (!Array.isArray(route.dexRouterList) || route.dexRouterList.length > 32) {
    throw new Error(`Invalid route segments ${index}`);
  }
  return {
    quoteId: text(route.quoteId, `route ${index} quote ID`, 128),
    vendorName: text(route.vendorName, `route ${index} vendor`, 80),
    binanceChainId: "56",
    fromTokenAmount: integer(route.fromTokenAmount, `route ${index} input`, true),
    toTokenAmount: integer(route.toTokenAmount, `route ${index} output`, true),
    tradeFee: nullableDecimal(route.tradeFee, `route ${index} trade fee`),
    estimateGasFee: nullableInteger(route.estimateGasFee, `route ${index} gas estimate`),
    priceImpactPercent: nullableDecimal(route.priceImpactPercent, `route ${index} price impact`),
    router: text(route.router, `route ${index} router`),
    fromToken: parseToken(route.fromToken, `route ${index} from token`),
    toToken: parseToken(route.toToken, `route ${index} to token`),
    dexRouterList: route.dexRouterList.map((segment, segmentIndex) =>
      parseSegment(segment, index, segmentIndex)),
    executionMode: route.executionMode,
    approveTarget: route.approveTarget === null
      ? null
      : address(route.approveTarget, `route ${index} approve target`),
    isBest: booleanValue(route.isBest, `route ${index} best flag`),
    feeAmount: nullableInteger(route.feeAmount, `route ${index} fee amount`),
    feeToken: route.feeToken === null ? null : address(route.feeToken, `route ${index} fee token`),
    actualSwapAmount: nullableInteger(route.actualSwapAmount, `route ${index} actual swap amount`),
  };
}

export function parseReadOnlyQuoteResponse(value: unknown): ReadOnlyQuote {
  const envelope = record(value, "quote response");
  if (envelope.operation !== "quote" || envelope.chainId !== 56 || envelope.boundary !== BOUNDARY) {
    throw new Error("Invalid quote response identity");
  }
  const data = record(envelope.data, "quote data");
  const asset = record(data.asset, "quote asset");
  const input = record(data.input, "quote input");
  if (asset.binanceChainId !== "56" || input.symbol !== "USDT") {
    throw new Error("Invalid quote asset or input identity");
  }
  if (!Array.isArray(data.routes) || data.routes.length < 1 || data.routes.length > 8) {
    throw new Error("Invalid quote routes");
  }
  const parsedAsset: ReadOnlyQuote["asset"] = {
    platformId: text(asset.platformId, "quote platform", 80),
    binanceChainId: "56",
    tokenContractAddress: address(asset.tokenContractAddress, "quote token address"),
    tokenSymbol: text(asset.tokenSymbol, "quote token symbol", 32),
    assetType: asset.assetType === 1 || asset.assetType === 2 || asset.assetType === 3
      ? asset.assetType
      : (() => { throw new Error("Invalid quote asset type"); })(),
  };
  const routes = data.routes.map(parseRoute);
  const rawAmount = integer(input.rawAmount, "quote raw input", true);
  const displayAmount = decimal(input.displayAmount, "quote display input");
  if (rawAmount !== EXACT_USDT_INPUT_RAW || Number(displayAmount) !== 5.1) {
    throw new Error("Invalid quote input bound");
  }
  if (routes.filter((route) => route.isBest).length !== 1) {
    throw new Error("Invalid quote best-route cardinality");
  }
  if (new Set(routes.map((route) => route.quoteId)).size !== routes.length) {
    throw new Error("Invalid duplicate quote IDs");
  }
  for (const route of routes) {
    if (route.fromTokenAmount !== rawAmount) throw new Error("Invalid quote route input binding");
    if (route.fromToken.tokenContractAddress !== BSC_USDT_ADDRESS) {
      throw new Error("Invalid quote route input token binding");
    }
    if (route.toToken.tokenContractAddress !== parsedAsset.tokenContractAddress) {
      throw new Error("Invalid quote route token binding");
    }
  }
  const timestamp = numberValue(data.timestamp, "quote timestamp");
  const expiresAt = numberValue(data.expiresAt, "quote expiry");
  if (expiresAt <= timestamp || expiresAt - timestamp > 30_000) {
    throw new Error("Invalid quote expiry window");
  }
  return {
    ticker: text(data.ticker, "quote ticker", 32),
    companyName: text(data.companyName, "quote company", 160),
    asset: parsedAsset,
    userWalletAddress: address(data.userWalletAddress, "quote receiver"),
    input: {
      symbol: "USDT",
      displayAmount,
      rawAmount,
    },
    routes,
    timestamp,
    expiresAt,
  };
}

export function assessReadOnlyQuote(quote: ReadOnlyQuote, now = Date.now()): QuoteAssessment {
  const usableForMs = Math.max(0, quote.expiresAt - now);
  const best = quote.routes.find((route) => route.isBest) ?? quote.routes[0];
  const reasons: string[] = [];
  if (usableForMs === 0) {
    return { level: "blocked", label: "Quote expired", reasons: ["Refresh before relying on this route"], routeCount: quote.routes.length, usableForMs };
  }
  if (!best) {
    return { level: "blocked", label: "No route", reasons: ["No quote vendor returned a route"], routeCount: 0, usableForMs };
  }
  if (best.fromToken.isHoneyPot) reasons.push("Input token is flagged as a honeypot");
  if (best.toToken.isHoneyPot) reasons.push("Destination token is flagged as a honeypot");
  const inputTax = Number(best.fromToken.taxRate);
  const outputTax = Number(best.toToken.taxRate);
  if (inputTax > 0.1) reasons.push(`Input token reports ${(inputTax * 100).toFixed(2)}% tax`);
  if (outputTax > 0.1) reasons.push(`Destination token reports ${(outputTax * 100).toFixed(2)}% tax`);
  const impact = best.priceImpactPercent === null ? null : Math.abs(Number(best.priceImpactPercent));
  if (impact !== null && impact > 1) reasons.push(`Absolute price impact is ${impact.toFixed(2)}%`);
  if (reasons.length > 0) {
    return { level: "blocked", label: "Quote blocked", reasons, routeCount: quote.routes.length, usableForMs };
  }
  const warnings: string[] = [];
  if (usableForMs <= 5_000) warnings.push("Quote is inside its final five-second safety margin");
  if (impact === null) warnings.push("Vendor did not report price impact");
  else if (impact > 0.5) warnings.push(`Price impact is ${impact.toFixed(2)}%`);
  if (best.dexRouterList.length === 0) warnings.push("Vendor did not report route segments");
  return warnings.length > 0
    ? { level: "watch", label: "Review quote", reasons: warnings, routeCount: quote.routes.length, usableForMs }
    : { level: "clear", label: "Read-only quote clear", reasons: [`Fresh bounded ${best.executionMode} route returned`], routeCount: quote.routes.length, usableForMs };
}

export function formatRawTokenAmount(rawAmount: string, decimals: string, maximumFraction = 8): string {
  const places = Number(decimals);
  if (!Number.isSafeInteger(places) || places < 0 || places > 255 || !INTEGER_PATTERN.test(rawAmount)) {
    throw new Error("Invalid token amount");
  }
  const padded = rawAmount.padStart(places + 1, "0");
  const whole = places === 0 ? padded : padded.slice(0, -places);
  const fraction = places === 0 ? "" : padded.slice(-places).slice(0, maximumFraction).replace(/0+$/u, "");
  return `${whole}${fraction ? `.${fraction}` : ""}`;
}
