import { createBinanceWeb3ClientFromEnv } from "../server/binanceWeb3";
import {
  assessReadOnlyQuote,
  formatRawTokenAmount,
  parseReadOnlyQuoteResponse,
} from "../src/bnb/readOnlyQuote";

async function main(): Promise<void> {
  const receiver = process.argv[2]?.trim() ?? "";
  const keyword = process.argv[3]?.trim() || "NVDA";
  const amount = process.argv[4]?.trim() || "5.1";
  const platform = process.argv[5]?.trim() || "ondo";
  if (!/^0x[a-fA-F0-9]{40}$/u.test(receiver)) {
    throw new Error(
      "Usage: npm run bnb:rwa:quote -- <public-receiver-0x-address> [ticker] [USDT amount] [platform]",
    );
  }

  const startedAt = Date.now();
  const client = createBinanceWeb3ClientFromEnv();
  const search = await client.searchRwaTokens(keyword);
  const selected = client.filterBscAssets(search.data)
    .flatMap((result) => result.assets)
    .find((asset) => asset.platformId === platform);
  if (!selected) throw new Error(`No ${platform} BSC representation was found for ${keyword}`);

  const quote = await client.quoteRwaFromUsdt({
    keyword,
    tokenContractAddress: selected.tokenContractAddress,
    userWalletAddress: receiver,
    usdtAmount: amount,
  });
  const publicQuote = parseReadOnlyQuoteResponse({
    operation: "quote",
    chainId: 56,
    data: quote,
    requestId: "local-live-acceptance",
    boundary: "READ_ONLY_QUOTE_NO_BUILD_NO_WALLET_NO_SIGNING_NO_BROADCAST",
  });
  const assessment = assessReadOnlyQuote(publicQuote);

  process.stdout.write(`${JSON.stringify({
    status: "PASS_READ_ONLY_AGGREGATOR_QUOTE",
    chainId: 56,
    durationMs: Date.now() - startedAt,
    ticker: quote.ticker,
    platform: quote.asset.platformId,
    tokenSymbol: quote.asset.tokenSymbol,
    tokenContractAddress: quote.asset.tokenContractAddress,
    receiver: quote.userWalletAddress,
    input: quote.input,
    quoteTimestamp: quote.timestamp,
    conservativeExpiry: quote.expiresAt,
    assessment,
    routes: quote.routes.map((route) => ({
      vendorName: route.vendorName,
      executionMode: route.executionMode,
      isBest: route.isBest,
      output: `${formatRawTokenAmount(route.toTokenAmount, route.toToken.decimal)} ${route.toToken.tokenSymbol}`,
      priceImpactPercent: route.priceImpactPercent,
      tradeFeeUsd: route.tradeFee,
      estimateGasFee: route.estimateGasFee,
      approveTarget: route.approveTarget,
      reportedProtocols: route.dexRouterList.map((segment) => ({
        name: segment.dexProtocol.dexName,
        percent: segment.dexProtocol.percent,
      })),
    })),
    liquidityEvidenceBoundary: "ROUTE_AVAILABILITY_AND_REPORTED_IMPACT_NOT_RESERVE_DEPTH",
    boundary: "READ_ONLY_QUOTE_NO_BUILD_NO_WALLET_NO_SIGNING_NO_BROADCAST",
  }, null, 2)}\n`);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : "Unknown Binance Web3 quote error";
  process.stderr.write(`${message}\n`);
  process.exitCode = 1;
});
