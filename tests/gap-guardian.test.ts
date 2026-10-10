import { describe, expect, it } from "vitest";

import {
  assessGuardianAsset,
  issuerGapBps,
  normalizedPerSharePrice,
  parseGuardianResponse,
  type GuardianAsset,
} from "../src/bnb/gapGuardian";

const asset = (overrides: Partial<GuardianAsset> = {}): GuardianAsset => ({
  asset: {
    platformId: "ondo",
    tokenContractAddress: "0xa9ee28c80f960b889dfbd1902055218cba016f75",
    tokenSymbol: "NVDAon",
  },
  price: {
    tokenPrice: "200",
    referencePrice: "100",
    tokenPriceUpdatedAt: 1_000_000,
  },
  profile: {
    tokenToShareRatio: "2",
    protections: {},
  },
  market: {
    statusInfo: {
      openState: true,
      marketStatus: "regular",
      reasonCode: null,
      reasonMsg: null,
      nextOpenTime: null,
      nextCloseTime: 2_000_000,
    },
    marketData: {
      referencePrice: "100",
      volumeShares24H: "1000",
      marketCap: "1000000",
    },
  },
  ...overrides,
});

describe("Gap Guardian policy", () => {
  it("normalizes token prices by the token-to-share ratio", () => {
    expect(normalizedPerSharePrice(asset())).toBe(100);
    expect(issuerGapBps([asset(), asset({
      price: { tokenPrice: "204", referencePrice: "102", tokenPriceUpdatedAt: 1_000_000 },
    })])).toBeCloseTo(198.0198, 3);
  });

  it("blocks issuer or market pauses before weaker warnings", () => {
    const paused = asset({
      market: {
        statusInfo: {
          openState: false,
          marketStatus: "pause",
          reasonCode: "ASSET_PAUSED",
          reasonMsg: "stock_split",
          nextOpenTime: null,
          nextCloseTime: null,
        },
        marketData: {
          referencePrice: "100",
          volumeShares24H: "1000",
          marketCap: "1000000",
        },
      },
    });
    expect(assessGuardianAsset(paused, 1_100_000)).toEqual({
      level: "blocked",
      label: "Do not act",
      reasons: ["stock_split"],
      priceAgeMs: 100_000,
    });
  });

  it("treats stale data and closed sessions as warnings, not fabricated halts", () => {
    const closed = asset({
      market: {
        statusInfo: {
          openState: false,
          marketStatus: "closed",
          reasonCode: "MARKET_CLOSED",
          reasonMsg: "Weekend or Holiday",
          nextOpenTime: 9_000_000,
          nextCloseTime: null,
        },
        marketData: {
          referencePrice: "100",
          volumeShares24H: "1000",
          marketCap: "1000000",
        },
      },
    });
    const result = assessGuardianAsset(closed, 2_000_001);
    expect(result.level).toBe("watch");
    expect(result.reasons).toContain("Token price is more than 15 minutes old");
    expect(result.reasons).toContain("Underlying session is closed");
  });

  it("treats the observed offhours state as a review warning", () => {
    const offhours = asset({
      market: {
        statusInfo: {
          openState: true,
          marketStatus: "offhours",
          reasonCode: "TRADING",
          reasonMsg: null,
          nextOpenTime: 9_000_000,
          nextCloseTime: 8_000_000,
        },
        marketData: {
          referencePrice: "100",
          volumeShares24H: "1000",
          marketCap: "1000000",
        },
      },
    });

    const result = assessGuardianAsset(offhours, 1_100_000);
    expect(result.level).toBe("watch");
    expect(result.reasons).toContain("Underlying session is offhours");
  });

  it("rejects an unbound or malformed public response", () => {
    expect(() => parseGuardianResponse({ operation: "search", chainId: 56 })).toThrow(
      "Invalid comparison identity",
    );
  });
});
