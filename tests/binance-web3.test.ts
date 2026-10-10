import { describe, expect, it, vi } from "vitest";

import {
  BSC_USDT_ADDRESS,
  BinanceWeb3Error,
  buildSignedGetRequest,
  createBinanceWeb3Client,
  normalizeBoundedUsdtAmount,
} from "../server/binanceWeb3";

const timestamp = "2026-10-09T08:30:00.000Z";

describe("Binance Web3 server-only client", () => {
  it("signs the exact raw request path including /build", () => {
    const request = buildSignedGetRequest(
      { apiKey: "api-key", secretKey: "top-secret" },
      {
        apiPath: "/api/v1/dex/market/rwa/search",
        query: [
          ["keyword", "NVIDIA Corp"],
          ["platformId", "ondo"],
        ],
        timestamp,
        nonce: "nonce-1",
      },
    );

    expect(request.requestPath).toBe(
      "/build/api/v1/dex/market/rwa/search?keyword=NVIDIA%20Corp&platformId=ondo",
    );
    expect(request.url).toBe(
      "https://web3.binance.com/build/api/v1/dex/market/rwa/search?keyword=NVIDIA%20Corp&platformId=ondo",
    );
    expect(request.headers).toMatchObject({
      "X-OC-APIKEY": "api-key",
      "X-OC-TIMESTAMP": timestamp,
      "X-OC-NONCE": "nonce-1",
      "X-OC-SIGN": "xBCnLIow/Qnjm0OBkecWLUlzv1b8xw504cP/PPGSmdM=",
    });
  });

  it("validates platform data and never sends credentials in the URL", async () => {
    let requestedUrl = "";
    const fetchMock = vi.fn(async (input: string | URL | Request) => {
      requestedUrl = String(input);
      return new Response(
        JSON.stringify({
          code: 0,
          msg: "success",
          data: [
            {
              platformId: "ondo",
              tickerCount: 264,
              chainDistribution: [{ binanceChainId: "56", tokenCount: 264 }],
              website: "https://ondo.finance",
              logoUrl: null,
            },
          ],
          timestamp: 1_791_532_800_000,
          success: true,
        }),
        { status: 200 },
      );
    });
    const client = createBinanceWeb3Client({
      apiKey: "api-key",
      secretKey: "top-secret",
      fetchImplementation: fetchMock,
      now: () => new Date(timestamp),
      nonce: () => "nonce-1",
    });

    const result = await client.getRwaPlatforms();
    expect(result.data[0]?.chainDistribution[0]).toEqual({
      binanceChainId: "56",
      tokenCount: 264,
    });
    expect(requestedUrl).not.toContain("api-key");
    expect(requestedUrl).not.toContain("top-secret");
  });

  it("filters ticker results to BSC without changing the upstream identity", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({
          code: 0,
          msg: "success",
          data: [
            {
              ticker: "NVDA",
              companyName: "NVIDIA Corporation",
              assets: [
                {
                  platformId: "ondo",
                  binanceChainId: "56",
                  tokenContractAddress: "0xa9ee28c80f960b889dfbd1902055218cba016f75",
                  tokenSymbol: "NVDAon",
                  assetType: 1,
                },
                {
                  platformId: "xstocks",
                  binanceChainId: "CT_501",
                  tokenContractAddress: "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",
                  tokenSymbol: "NVDAX",
                  assetType: 1,
                },
              ],
            },
          ],
          timestamp: 1_791_532_800_000,
          success: true,
        }),
        { status: 200 },
      ),
    );
    const client = createBinanceWeb3Client({
      apiKey: "api-key",
      secretKey: "top-secret",
      fetchImplementation: fetchMock,
      now: () => new Date(timestamp),
      nonce: () => "nonce-1",
    });

    const result = await client.searchRwaTokens("NVDA");
    const bsc = client.filterBscAssets(result.data);
    expect(bsc).toHaveLength(1);
    expect(bsc[0]?.assets).toHaveLength(1);
    expect(bsc[0]?.assets[0]?.binanceChainId).toBe("56");
    expect(bsc[0]?.assets[0]?.tokenContractAddress).toBe(
      "0xa9ee28c80f960b889dfbd1902055218cba016f75",
    );
  });

  it("rejects upstream errors without exposing either credential", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({
          code: 40102,
          msg: "Invalid signature",
          data: null,
          timestamp: 1_791_532_800_000,
          success: false,
        }),
        { status: 401 },
      ),
    );
    const client = createBinanceWeb3Client({
      apiKey: "api-key-sensitive",
      secretKey: "secret-sensitive",
      fetchImplementation: fetchMock,
      now: () => new Date(timestamp),
      nonce: () => "nonce-1",
    });

    await expect(client.getRwaPlatforms()).rejects.toMatchObject({
      name: "BinanceWeb3Error",
      kind: "upstream",
      status: 401,
      code: 40102,
    });
    try {
      await client.getRwaPlatforms();
    } catch (error) {
      expect(error).toBeInstanceOf(BinanceWeb3Error);
      expect(String(error)).not.toContain("api-key-sensitive");
      expect(String(error)).not.toContain("secret-sensitive");
    }
  });

  it("rejects empty, oversized, and control-character search terms", async () => {
    const client = createBinanceWeb3Client({
      apiKey: "api-key",
      secretKey: "top-secret",
      fetchImplementation: vi.fn(),
    });

    await expect(client.searchRwaTokens(" ")).rejects.toThrow("1 to 80 characters");
    await expect(client.searchRwaTokens("x".repeat(81))).rejects.toThrow("1 to 80 characters");
    await expect(client.searchRwaTokens("NV\nDA")).rejects.toThrow("control characters");
  });

  it("binds a comparison to matching BSC price, profile, and market identities", async () => {
    const ondo = "0xa9ee28c80f960b889dfbd1902055218cba016f75";
    const bstock = "0x02fca66c1d1afb4e2a7884261eb00f63598a7436";
    const envelope = (data: unknown) => JSON.stringify({
      code: 0,
      msg: "success",
      data,
      timestamp: 1_791_550_732_585,
      success: true,
    });
    const profile = (address: string, platformId: string) => ({
      binanceChainId: "56",
      tokenContractAddress: address,
      platformId,
      underlyingTicker: "NVDA",
      underlyingFullName: "Nvidia Corp",
      assetType: 1,
      tokenToShareRatio: "1",
      protections: {
        dailyAttestationReport: { supported: true, url: "https://example.com/report.pdf" },
      },
      companyInfo: { website: "https://nvidia.com", industry: "Technology" },
    });
    const market = (address: string, platformId: string) => ({
      binanceChainId: "56",
      tokenContractAddress: address,
      platformId,
      assetType: 1,
      statusInfo: {
        openState: true,
        marketStatus: "regular",
        reasonCode: null,
        reasonMsg: null,
        nextOpenTime: null,
        nextCloseTime: 1_791_600_000_000,
      },
      marketData: {
        referencePrice: "192.50",
        high52W: "200",
        low52W: "80",
        volumeShares24H: "1000000",
        avgDailyVolume1Y: "900000",
        totalShares: "24000000000",
        marketCap: "4600000000000",
        turnoverRate: "1.2",
        amplitude: "2.5",
        peRatioTTM: "50",
        pbRatio: "45",
        dividendYield: "0.02",
        latestDividend: "0.01",
      },
    });
    const fetchMock = vi.fn(async (input: string | URL | Request) => {
      const url = new URL(String(input));
      const path = url.pathname;
      if (path.endsWith("/search")) {
        return new Response(envelope([{
          ticker: "NVDA",
          companyName: "Nvidia Corp",
          assets: [
            { platformId: "ondo", binanceChainId: "56", tokenContractAddress: ondo, tokenSymbol: "NVDAon", assetType: 1 },
            { platformId: "bstock", binanceChainId: "56", tokenContractAddress: bstock, tokenSymbol: "NVDAB", assetType: 1 },
          ],
        }]));
      }
      if (path.endsWith("/price")) {
        expect(url.searchParams.get("tokenContractAddresses")).toBe(`${ondo},${bstock}`);
        return new Response(envelope([
          { binanceChainId: "56", tokenContractAddress: ondo, platformId: "ondo", tokenPrice: "192.90", referencePrice: "192.50", tokenPriceUpdatedAt: 1_791_550_700_000 },
          { binanceChainId: "56", tokenContractAddress: bstock, platformId: "bstock", tokenPrice: "193.10", referencePrice: "192.50", tokenPriceUpdatedAt: 1_791_550_700_000 },
        ]));
      }
      const address = url.searchParams.get("tokenContractAddress") ?? "";
      const platformId = address === ondo ? "ondo" : "bstock";
      if (path.endsWith("/underlying-profile")) {
        return new Response(envelope(profile(address, platformId)));
      }
      if (path.endsWith("/underlying-market")) {
        return new Response(envelope(market(address, platformId)));
      }
      return new Response("not found", { status: 404 });
    });
    const client = createBinanceWeb3Client({
      apiKey: "api-key",
      secretKey: "top-secret",
      fetchImplementation: fetchMock,
      now: () => new Date(timestamp),
      nonce: () => "nonce-1",
    });

    const result = await client.compareRwaTicker("NVDA");
    expect(result.ticker).toBe("NVDA");
    expect(result.assets.map((item) => item.asset.tokenSymbol)).toEqual(["NVDAon", "NVDAB"]);
    expect(result.assets[0]?.profile.protections.dailyAttestationReport?.supported).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(6);
  });

  it("accepts the observed offhours status without treating it as regular hours", async () => {
    const address = "0xa9ee28c80f960b889dfbd1902055218cba016f75";
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({
          code: 0,
          msg: "success",
          data: {
            binanceChainId: "56",
            tokenContractAddress: address,
            platformId: "ondo",
            assetType: 1,
            statusInfo: {
              openState: true,
              marketStatus: "offhours",
              reasonCode: "TRADING",
              reasonMsg: null,
              nextOpenTime: 1_791_763_500_000,
              nextCloseTime: 1_791_762_900_000,
            },
            marketData: {
              referencePrice: "192.50",
              high52W: null,
              low52W: null,
              volumeShares24H: null,
              avgDailyVolume1Y: null,
              totalShares: null,
              marketCap: null,
              turnoverRate: null,
              amplitude: null,
              peRatioTTM: null,
              pbRatio: null,
              dividendYield: null,
              latestDividend: null,
            },
          },
          timestamp: 1_791_632_943_037,
          success: true,
        }),
        { status: 200 },
      ),
    );
    const client = createBinanceWeb3Client({
      apiKey: "api-key",
      secretKey: "top-secret",
      fetchImplementation: fetchMock,
      now: () => new Date(timestamp),
      nonce: () => "nonce-1",
    });

    const result = await client.getRwaUnderlyingMarket(address);
    expect(result.data.statusInfo).toMatchObject({
      openState: true,
      marketStatus: "offhours",
      reasonCode: "TRADING",
    });
  });

  it("normalizes only the exact 5.10 USDT buffered quote input", () => {
    expect(normalizeBoundedUsdtAmount("5.100000000000000000")).toEqual({
      displayAmount: "5.1",
      rawAmount: "5100000000000000000",
    });
    expect(() => normalizeBoundedUsdtAmount("5.099999999999999999")).toThrow("exactly 5.10");
    expect(() => normalizeBoundedUsdtAmount("5.100000000000000001")).toThrow("exactly 5.10");
    expect(() => normalizeBoundedUsdtAmount("1e18")).toThrow("decimal USDT amount");
  });

  it("parses and identity-binds an observed RWA SWAP quote without building a transaction", async () => {
    const ondo = "0xa9ee28c80f960b889dfbd1902055218cba016f75";
    const wallet = "0x6719e877c05b2d6c28abcea405fc033feef5750f";
    const envelope = (data: unknown, responseTimestamp = 1_791_550_732_585) => JSON.stringify({
      code: 0,
      msg: "success",
      data,
      timestamp: responseTimestamp,
      success: true,
    });
    const fetchMock = vi.fn(async (input: string | URL | Request) => {
      const url = new URL(String(input));
      if (url.pathname.endsWith("/search")) {
        return new Response(envelope([{
          ticker: "NVDA",
          companyName: "Nvidia Corp",
          assets: [{
            platformId: "ondo",
            binanceChainId: "56",
            tokenContractAddress: ondo,
            tokenSymbol: "NVDAon",
            assetType: 1,
          }],
        }]));
      }
      expect(url.pathname).toContain("/aggregator/quote");
      expect(url.searchParams.get("binanceChainId")).toBe("56");
      expect(url.searchParams.get("amount")).toBe("5100000000000000000");
      expect(url.searchParams.get("fromTokenAddress")?.toLowerCase()).toBe(BSC_USDT_ADDRESS);
      expect(url.searchParams.get("toTokenAddress")?.toLowerCase()).toBe(ondo);
      expect(url.searchParams.get("userWalletAddress")?.toLowerCase()).toBe(wallet);
      return new Response(envelope([{
        quoteId: "a1b2c3d4e5f64a8b9c0d1e2f3a4b5c6d",
        vendorName: "PcsXRfq",
        binanceChainId: "56",
        fromTokenAmount: "5100000000000000000",
        toTokenAmount: "5192000000000000",
        tradeFee: "0.03",
        estimateGasFee: "220000",
        priceImpactPercent: "-0.04",
        router: `${BSC_USDT_ADDRESS}--${ondo}`,
        fromToken: {
          tokenContractAddress: BSC_USDT_ADDRESS,
          tokenSymbol: "USDT",
          tokenUnitPrice: "1",
          decimal: "18",
          isHoneyPot: false,
          taxRate: "0",
        },
        toToken: {
          tokenContractAddress: ondo,
          tokenSymbol: "NVDAon",
          tokenUnitPrice: "192.6",
          decimal: "18",
          isHoneyPot: false,
          taxRate: "0",
        },
        dexRouterList: [{
          dexProtocol: { dexName: "PcsX RFQ", percent: "100.00" },
          fromToken: { tokenContractAddress: BSC_USDT_ADDRESS, tokenSymbol: "USDT" },
          fromTokenIndex: "0",
          toToken: { tokenContractAddress: ondo, tokenSymbol: "NVDAon" },
          toTokenIndex: "1",
        }],
        executionMode: "SWAP",
        approveTarget: "0xc67879f4065d3b9fe1c09ee990b891aa8e3a4c2f",
        isBest: true,
        feeAmount: null,
        feeToken: null,
        actualSwapAmount: null,
      }]));
    });
    const client = createBinanceWeb3Client({
      apiKey: "api-key",
      secretKey: "top-secret",
      fetchImplementation: fetchMock,
      now: () => new Date(timestamp),
      nonce: () => "nonce-1",
    });

    const quote = await client.quoteRwaFromUsdt({
      keyword: "NVDA",
      tokenContractAddress: ondo,
      userWalletAddress: wallet,
      usdtAmount: "5.1",
    });
    expect(quote.asset.tokenSymbol).toBe("NVDAon");
    expect(quote.input).toEqual({ symbol: "USDT", displayAmount: "5.1", rawAmount: "5100000000000000000" });
    expect(quote.routes).toHaveLength(1);
    expect(quote.routes[0]).toMatchObject({ executionMode: "SWAP", vendorName: "PcsXRfq", isBest: true });
    expect(quote.expiresAt).toBe(1_791_550_752_585);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("rejects arbitrary contracts and route identity drift before exposure to the browser", async () => {
    const ondo = "0xa9ee28c80f960b889dfbd1902055218cba016f75";
    const other = "0x02fca66c1d1afb4e2a7884261eb00f63598a7436";
    const wallet = "0x6719e877c05b2d6c28abcea405fc033feef5750f";
    const envelope = (data: unknown) => new Response(JSON.stringify({
      code: 0,
      msg: "success",
      data,
      timestamp: 1_791_550_732_585,
      success: true,
    }));
    const search = [{
      ticker: "NVDA",
      companyName: "Nvidia Corp",
      assets: [{ platformId: "ondo", binanceChainId: "56", tokenContractAddress: ondo, tokenSymbol: "NVDAon", assetType: 1 }],
    }];
    const client = createBinanceWeb3Client({
      apiKey: "api-key",
      secretKey: "top-secret",
      fetchImplementation: vi.fn(async () => envelope(search)),
    });
    await expect(client.quoteRwaFromUsdt({
      keyword: "NVDA",
      tokenContractAddress: other,
      userWalletAddress: wallet,
      usdtAmount: "5.1",
    })).rejects.toMatchObject({ kind: "not_found" });

    const driftClient = createBinanceWeb3Client({
      apiKey: "api-key",
      secretKey: "top-secret",
      fetchImplementation: vi.fn(async (input: string | URL | Request) => {
        const url = new URL(String(input));
        if (url.pathname.endsWith("/search")) return envelope(search);
        return envelope([{
          quoteId: "quote1",
          vendorName: "PcsXRfq",
          binanceChainId: "56",
          fromTokenAmount: "5100000000000000000",
          toTokenAmount: "1",
          tradeFee: null,
          estimateGasFee: null,
          priceImpactPercent: null,
          router: `${BSC_USDT_ADDRESS}--${other}`,
          fromToken: { tokenContractAddress: BSC_USDT_ADDRESS, tokenSymbol: "USDT", tokenUnitPrice: "1", decimal: "18", isHoneyPot: false, taxRate: "0" },
          toToken: { tokenContractAddress: other, tokenSymbol: "NVDAB", tokenUnitPrice: "1", decimal: "18", isHoneyPot: false, taxRate: "0" },
          dexRouterList: [],
          executionMode: "RFQ",
          approveTarget: null,
          isBest: true,
          feeAmount: null,
          feeToken: null,
          actualSwapAmount: null,
        }]);
      }),
    });
    await expect(driftClient.quoteRwaFromUsdt({
      keyword: "NVDA",
      tokenContractAddress: ondo,
      userWalletAddress: wallet,
      usdtAmount: "5.1",
    })).rejects.toThrow("mismatched quote to-token identity");
  });
});
