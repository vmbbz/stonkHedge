import { createBinanceWeb3ClientFromEnv } from "../server/binanceWeb3";
import {
  assessGuardianAsset,
  issuerGapBps,
  parseGuardianResponse,
} from "../src/bnb/gapGuardian";

async function main(): Promise<void> {
  const keyword = process.argv[2]?.trim() || "NVDA";
  const startedAt = Date.now();
  const client = createBinanceWeb3ClientFromEnv();
  const platforms = await client.getRwaPlatforms();
  const search = await client.searchRwaTokens(keyword);
  const comparison = await client.compareRwaTicker(keyword);
  const publicComparison = parseGuardianResponse({
    operation: "compare",
    chainId: 56,
    data: comparison,
  });
  const gapBps = issuerGapBps(publicComparison.assets);

  process.stdout.write(
    `${JSON.stringify(
      {
        status: "PASS_READ_ONLY",
        chainId: 56,
        keyword,
        durationMs: Date.now() - startedAt,
        platformTimestamp: platforms.timestamp,
        platforms: platforms.data.map((platform) => ({
          platformId: platform.platformId,
          tickerCount: platform.tickerCount,
          bscTokenCount:
            platform.chainDistribution.find((chain) => chain.binanceChainId === "56")
              ?.tokenCount ?? 0,
        })),
        searchTimestamp: search.timestamp,
        bscResults: client.filterBscAssets(search.data),
        comparison: {
          ticker: comparison.ticker,
          companyName: comparison.companyName,
          representations: comparison.assets.map(({ asset, price, profile, market }) => ({
            platformId: asset.platformId,
            tokenSymbol: asset.tokenSymbol,
            tokenContractAddress: asset.tokenContractAddress,
            tokenPrice: price.tokenPrice,
            reportedReferencePrice: price.referencePrice,
            tokenToShareRatio: profile.tokenToShareRatio,
            tokenPriceUpdatedAt: price.tokenPriceUpdatedAt,
            marketStatus: market.statusInfo.marketStatus,
            openState: market.statusInfo.openState,
            reasonCode: market.statusInfo.reasonCode,
            supportedProtections: Object.entries(profile.protections)
              .filter(([, protection]) => protection.supported)
              .map(([name]) => name),
          })),
          timestamps: comparison.timestamps,
          issuerNormalizedGapBps: gapBps,
          guardianSignals: publicComparison.assets.map((asset) => ({
            tokenSymbol: asset.asset.tokenSymbol,
            ...assessGuardianAsset(asset, Date.now(), gapBps),
          })),
        },
        boundary: "READ_ONLY_NO_WALLET_NO_SIGNING_NO_BROADCAST",
      },
      null,
      2,
    )}\n`,
  );
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : "Unknown Binance Web3 error";
  process.stderr.write(`${message}\n`);
  process.exitCode = 1;
});
