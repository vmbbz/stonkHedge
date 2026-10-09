import { describe, expect, it } from "vitest";

import {
  assessReadOnlyQuote,
  parseReadOnlyQuoteResponse,
} from "../src/bnb/readOnlyQuote";

const response = {
  operation: "quote",
  chainId: 56,
  data: {
    ticker: "NVDA",
    companyName: "Nvidia Corp",
    asset: {
      platformId: "ondo",
      binanceChainId: "56",
      tokenContractAddress: "0xa9ee28c80f960b889dfbd1902055218cba016f75",
      tokenSymbol: "NVDAon",
      assetType: 1,
    },
    userWalletAddress: "0x6719e877c05b2d6c28abcea405fc033feef5750f",
    input: { symbol: "USDT", displayAmount: "5.1", rawAmount: "5100000000000000000" },
    routes: [{
      quoteId: "quote1",
      vendorName: "PcsXRfq",
      binanceChainId: "56",
      fromTokenAmount: "5100000000000000000",
      toTokenAmount: "25960000000000000",
      tradeFee: "0.03",
      estimateGasFee: "220000",
      priceImpactPercent: "-0.04",
      router: "USDT--NVDAon",
      fromToken: { tokenContractAddress: "0x55d398326f99059ff775485246999027b3197955", tokenSymbol: "USDT", tokenUnitPrice: "1", decimal: "18", isHoneyPot: false, taxRate: "0" },
      toToken: { tokenContractAddress: "0xa9ee28c80f960b889dfbd1902055218cba016f75", tokenSymbol: "NVDAon", tokenUnitPrice: "192.6", decimal: "18", isHoneyPot: false, taxRate: "0" },
      dexRouterList: [{ dexProtocol: { dexName: "PcsX RFQ", percent: "100.00" }, fromToken: { tokenContractAddress: "0x55d398326f99059ff775485246999027b3197955", tokenSymbol: "USDT" }, fromTokenIndex: "0", toToken: { tokenContractAddress: "0xa9ee28c80f960b889dfbd1902055218cba016f75", tokenSymbol: "NVDAon" }, toTokenIndex: "1" }],
      executionMode: "RFQ",
      approveTarget: "0xc67879f4065d3b9fe1c09ee990b891aa8e3a4c2f",
      isBest: true,
      feeAmount: null,
      feeToken: null,
      actualSwapAmount: null,
    }],
    timestamp: 1_791_550_732_585,
    expiresAt: 1_791_550_752_585,
  },
  requestId: "request-1",
  boundary: "READ_ONLY_QUOTE_NO_BUILD_NO_WALLET_NO_SIGNING_NO_BROADCAST",
};

describe("read-only BSC RWA quote policy", () => {
  it("validates a quote-bound public response and formats exact token output", () => {
    const parsed = parseReadOnlyQuoteResponse(response);
    expect(parsed.routes[0]?.executionMode).toBe("RFQ");
    expect(parsed.routes[0]?.toTokenAmount).toBe("25960000000000000");

    const swap = structuredClone(response);
    swap.data.routes[0]!.executionMode = "SWAP";
    expect(parseReadOnlyQuoteResponse(swap).routes[0]?.executionMode).toBe("SWAP");
  });

  it("reports route count as liquidity evidence and blocks stale quotes", () => {
    const parsed = parseReadOnlyQuoteResponse(response);
    expect(assessReadOnlyQuote(parsed, 1_791_550_740_000)).toMatchObject({
      level: "clear",
      routeCount: 1,
      usableForMs: 12_585,
    });
    expect(assessReadOnlyQuote(parsed, 1_791_550_752_585)).toMatchObject({
      level: "blocked",
      label: "Quote expired",
      usableForMs: 0,
    });
  });

  it("blocks honeypot, material tax, and excessive impact evidence", () => {
    const dangerous = structuredClone(response);
    dangerous.data.routes[0]!.toToken.isHoneyPot = true;
    dangerous.data.routes[0]!.toToken.taxRate = "0.12";
    dangerous.data.routes[0]!.priceImpactPercent = "-1.25";
    const assessment = assessReadOnlyQuote(
      parseReadOnlyQuoteResponse(dangerous),
      1_791_550_740_000,
    );
    expect(assessment.level).toBe("blocked");
    expect(assessment.reasons).toEqual(expect.arrayContaining([
      "Destination token is flagged as a honeypot",
      "Destination token reports 12.00% tax",
      "Absolute price impact is 1.25%",
    ]));
  });

  it("rejects a public response with an execution or identity mismatch", () => {
    const swap = structuredClone(response);
    swap.data.routes[0]!.executionMode = "LIMIT";
    expect(() => parseReadOnlyQuoteResponse(swap)).toThrow("execution mode");

    const wrongChain = structuredClone(response);
    wrongChain.data.routes[0]!.binanceChainId = "1";
    expect(() => parseReadOnlyQuoteResponse(wrongChain)).toThrow("route chain");

    const wrongInputToken = structuredClone(response);
    wrongInputToken.data.routes[0]!.fromToken.tokenContractAddress = "0x02fca66c1d1afb4e2a7884261eb00f63598a7436";
    expect(() => parseReadOnlyQuoteResponse(wrongInputToken)).toThrow("input token binding");

    const wrongBound = structuredClone(response);
    wrongBound.data.input.displayAmount = "5";
    wrongBound.data.input.rawAmount = "5000000000000000000";
    wrongBound.data.routes[0]!.fromTokenAmount = "5000000000000000000";
    expect(() => parseReadOnlyQuoteResponse(wrongBound)).toThrow("input bound");
  });

  it("rejects duplicate quote IDs and ambiguous best-route selection", () => {
    const duplicate = structuredClone(response);
    const duplicateRoute = structuredClone(duplicate.data.routes[0]!);
    duplicateRoute.isBest = false;
    duplicate.data.routes.push(duplicateRoute);
    expect(() => parseReadOnlyQuoteResponse(duplicate)).toThrow("duplicate quote IDs");

    const ambiguous = structuredClone(response);
    const second = structuredClone(ambiguous.data.routes[0]!);
    second.quoteId = "quote2";
    ambiguous.data.routes.push(second);
    expect(() => parseReadOnlyQuoteResponse(ambiguous)).toThrow("best-route cardinality");
  });
});
