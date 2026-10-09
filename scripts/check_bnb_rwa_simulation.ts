import { createBinanceWeb3ClientFromEnv } from "../server/binanceWeb3";

const [keyword = "NVDA", tokenContractAddress, userWalletAddress] = process.argv.slice(2);

if (!tokenContractAddress || !userWalletAddress) {
  throw new Error(
    "Usage: npm run bnb:rwa:simulate -- <ticker> <BSC RWA token address> <public BSC sender>",
  );
}

const client = createBinanceWeb3ClientFromEnv();
const proof = await client.simulateRwaSwap({
  keyword,
  tokenContractAddress,
  userWalletAddress,
  usdtAmount: "5.1",
});

console.log(JSON.stringify({
  status: "PASS_SIMULATION_ONLY",
  chainId: 56,
  proof,
  boundary: "SIMULATION_ONLY_NO_WALLET_NO_PRIVATE_KEY_NO_SIGNING_NO_BROADCAST",
}, null, 2));
