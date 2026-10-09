export type GuardianLevel = "clear" | "watch" | "blocked";

export interface GuardianAsset {
  asset: {
    platformId: string;
    tokenContractAddress: string;
    tokenSymbol: string;
  };
  price: {
    tokenPrice: string;
    referencePrice: string;
    tokenPriceUpdatedAt: number;
  };
  profile: {
    tokenToShareRatio: string;
    protections: Record<string, { supported: boolean; url: string | null }>;
  };
  market: {
    statusInfo: {
      openState: boolean;
      marketStatus: string | null;
      reasonCode: string | null;
      reasonMsg: string | null;
      nextOpenTime: number | null;
      nextCloseTime: number | null;
    };
    marketData: {
      referencePrice: string | null;
      volumeShares24H: string | null;
      marketCap: string | null;
    };
  };
}

export interface GuardianComparison {
  ticker: string;
  companyName: string;
  assets: GuardianAsset[];
  timestamps: {
    search: number;
    price: number;
    profiles: number[];
    markets: number[];
  };
}

export interface GuardianAssessment {
  level: GuardianLevel;
  label: string;
  reasons: string[];
  priceAgeMs: number;
}

const DECIMAL_PATTERN = /^(?:0|[1-9]\d*)(?:\.\d+)?$/u;
const PAUSE_REASONS = new Set([
  "MARKET_PAUSED",
  "MARKET_MAINTENANCE",
  "ASSET_PAUSED",
  "ASSET_LIMITED",
  "UNSUPPORTED",
]);

function asRecord(value: unknown, label: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`Invalid ${label}`);
  }
  return value as Record<string, unknown>;
}

function asString(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0) throw new Error(`Invalid ${label}`);
  return value;
}

function asNullableString(value: unknown, label: string): string | null {
  if (value === null) return null;
  return asString(value, label);
}

function asNumber(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value)) throw new Error(`Invalid ${label}`);
  return value;
}

function asNullableNumber(value: unknown, label: string): number | null {
  if (value === null) return null;
  return asNumber(value, label);
}

function asBoolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") throw new Error(`Invalid ${label}`);
  return value;
}

function asDecimal(value: unknown, label: string): string {
  const decimal = asString(value, label);
  if (!DECIMAL_PATTERN.test(decimal) || !Number.isFinite(Number(decimal))) {
    throw new Error(`Invalid ${label}`);
  }
  return decimal;
}

function asNullableDecimal(value: unknown, label: string): string | null {
  if (value === null) return null;
  return asDecimal(value, label);
}

function parseProtections(value: unknown): GuardianAsset["profile"]["protections"] {
  const protections = asRecord(value, "protections");
  return Object.fromEntries(
    Object.entries(protections).map(([key, raw]) => {
      const protection = asRecord(raw, `protection ${key}`);
      return [
        key,
        {
          supported: asBoolean(protection.supported, `protection ${key} support`),
          url: asNullableString(protection.url, `protection ${key} URL`),
        },
      ];
    }),
  );
}

function parseAsset(value: unknown, index: number): GuardianAsset {
  const candidate = asRecord(value, `asset ${index}`);
  const asset = asRecord(candidate.asset, `asset ${index} identity`);
  const price = asRecord(candidate.price, `asset ${index} price`);
  const profile = asRecord(candidate.profile, `asset ${index} profile`);
  const market = asRecord(candidate.market, `asset ${index} market`);
  const status = asRecord(market.statusInfo, `asset ${index} status`);
  const marketData = asRecord(market.marketData, `asset ${index} market data`);
  return {
    asset: {
      platformId: asString(asset.platformId, `asset ${index} platform`),
      tokenContractAddress: asString(asset.tokenContractAddress, `asset ${index} address`),
      tokenSymbol: asString(asset.tokenSymbol, `asset ${index} symbol`),
    },
    price: {
      tokenPrice: asDecimal(price.tokenPrice, `asset ${index} token price`),
      referencePrice: asDecimal(price.referencePrice, `asset ${index} reference price`),
      tokenPriceUpdatedAt: asNumber(price.tokenPriceUpdatedAt, `asset ${index} price timestamp`),
    },
    profile: {
      tokenToShareRatio: asDecimal(profile.tokenToShareRatio, `asset ${index} ratio`),
      protections: parseProtections(profile.protections),
    },
    market: {
      statusInfo: {
        openState: asBoolean(status.openState, `asset ${index} open state`),
        marketStatus: asNullableString(status.marketStatus, `asset ${index} market status`),
        reasonCode: asNullableString(status.reasonCode, `asset ${index} reason code`),
        reasonMsg: asNullableString(status.reasonMsg, `asset ${index} reason`),
        nextOpenTime: asNullableNumber(status.nextOpenTime, `asset ${index} next open`),
        nextCloseTime: asNullableNumber(status.nextCloseTime, `asset ${index} next close`),
      },
      marketData: {
        referencePrice: asNullableDecimal(marketData.referencePrice, `asset ${index} market reference`),
        volumeShares24H: asNullableDecimal(marketData.volumeShares24H, `asset ${index} volume`),
        marketCap: asNullableDecimal(marketData.marketCap, `asset ${index} market cap`),
      },
    },
  };
}

export function parseGuardianResponse(value: unknown): GuardianComparison {
  const envelope = asRecord(value, "comparison response");
  if (envelope.operation !== "compare" || envelope.chainId !== 56) {
    throw new Error("Invalid comparison identity");
  }
  const data = asRecord(envelope.data, "comparison data");
  const assets = Array.isArray(data.assets) ? data.assets.map(parseAsset) : null;
  if (!assets || assets.length === 0) throw new Error("No comparison assets returned");
  const timestamps = asRecord(data.timestamps, "comparison timestamps");
  const profiles = Array.isArray(timestamps.profiles)
    ? timestamps.profiles.map((item, index) => asNumber(item, `profile timestamp ${index}`))
    : null;
  const markets = Array.isArray(timestamps.markets)
    ? timestamps.markets.map((item, index) => asNumber(item, `market timestamp ${index}`))
    : null;
  if (!profiles || !markets || profiles.length !== assets.length || markets.length !== assets.length) {
    throw new Error("Invalid comparison timestamp vector");
  }
  return {
    ticker: asString(data.ticker, "ticker"),
    companyName: asString(data.companyName, "company name"),
    assets,
    timestamps: {
      search: asNumber(timestamps.search, "search timestamp"),
      price: asNumber(timestamps.price, "price timestamp"),
      profiles,
      markets,
    },
  };
}

function decimalNumber(value: string, label: string): number {
  if (!DECIMAL_PATTERN.test(value)) throw new Error(`Invalid ${label}`);
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) throw new Error(`Invalid ${label}`);
  return parsed;
}

export function normalizedPerSharePrice(asset: GuardianAsset): number {
  const tokenPrice = decimalNumber(asset.price.tokenPrice, "token price");
  const ratio = decimalNumber(asset.profile.tokenToShareRatio, "token-to-share ratio");
  if (ratio <= 0) throw new Error("Token-to-share ratio must be positive");
  return tokenPrice / ratio;
}

export function issuerGapBps(assets: readonly GuardianAsset[]): number | null {
  if (assets.length < 2) return null;
  const values = assets.map(normalizedPerSharePrice);
  const low = Math.min(...values);
  const high = Math.max(...values);
  const midpoint = (low + high) / 2;
  return midpoint === 0 ? 0 : ((high - low) / midpoint) * 10_000;
}

export function assessGuardianAsset(
  asset: GuardianAsset,
  now = Date.now(),
  crossIssuerGapBps: number | null = null,
): GuardianAssessment {
  const reasons: string[] = [];
  const priceAgeMs = Math.max(0, now - asset.price.tokenPriceUpdatedAt);
  const reasonCode = asset.market.statusInfo.reasonCode;
  if (reasonCode && PAUSE_REASONS.has(reasonCode)) {
    reasons.push(asset.market.statusInfo.reasonMsg ?? reasonCode.replaceAll("_", " "));
    return { level: "blocked", label: "Do not act", reasons, priceAgeMs };
  }
  if (priceAgeMs > 15 * 60_000) reasons.push("Token price is more than 15 minutes old");
  if (!asset.market.statusInfo.openState || asset.market.statusInfo.marketStatus !== "regular") {
    reasons.push(
      asset.market.statusInfo.marketStatus === null
        ? "Underlying session label is unreported"
        : `Underlying session is ${asset.market.statusInfo.marketStatus}`,
    );
  }
  if (crossIssuerGapBps !== null && crossIssuerGapBps > 100) {
    reasons.push(`Issuer-normalized gap is ${crossIssuerGapBps.toFixed(1)} bps`);
  }
  return reasons.length
    ? { level: "watch", label: "Review conditions", reasons, priceAgeMs }
    : { level: "clear", label: "Read-only signal clear", reasons: ["No configured warning fired"], priceAgeMs };
}
