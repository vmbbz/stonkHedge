import { createBinanceWeb3ClientFromEnv } from "../server/binanceWeb3";

async function main(): Promise<void> {
  const keyword = process.argv[2]?.trim() || "NVDA";
  const startedAt = Date.now();
  const client = createBinanceWeb3ClientFromEnv();
  const platforms = await client.getRwaPlatforms();
  const search = await client.searchRwaTokens(keyword);

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
