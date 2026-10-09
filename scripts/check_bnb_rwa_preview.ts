import { parseGuardianResponse } from "../src/bnb/gapGuardian";
import { parseSimulationProofResponse } from "../src/bnb/simulationProof";

const [deploymentUrl, receiver] = process.argv.slice(2);

if (!deploymentUrl || !receiver) {
  throw new Error(
    "Usage: npm run bnb:rwa:preview -- <https-preview-url> <public-BSC-sender>",
  );
}
if (!/^0x[a-fA-F0-9]{40}$/u.test(receiver)) {
  throw new Error("The preview sender must be a public 20-byte EVM address");
}

const baseUrl = new URL(deploymentUrl);
if (
  baseUrl.protocol !== "https:"
  || baseUrl.username
  || baseUrl.password
  || baseUrl.pathname !== "/"
  || baseUrl.search
  || baseUrl.hash
) {
  throw new Error("The preview URL must be a plain HTTPS origin");
}

const request = async (url: URL): Promise<{ response: Response; body: unknown }> => {
  const response = await fetch(url, {
    headers: { Accept: "application/json" },
    redirect: "error",
    signal: AbortSignal.timeout(45_000),
  });
  const body: unknown = await response.json();
  if (!response.ok) {
    const message = typeof body === "object" && body !== null && "message" in body
      && typeof body.message === "string"
      ? body.message
      : `HTTP ${response.status}`;
    throw new Error(`Preview request failed: ${message}`);
  }
  if (!response.headers.get("cache-control")?.includes("no-store")) {
    throw new Error("The preview API response is missing its no-store policy");
  }
  if (response.headers.get("x-content-type-options") !== "nosniff") {
    throw new Error("The preview API response is missing nosniff");
  }
  return { response, body };
};

const comparisonUrl = new URL("/api/bnb/rwa", baseUrl);
comparisonUrl.searchParams.set("operation", "compare");
comparisonUrl.searchParams.set("q", "NVDA");
const comparisonResult = await request(comparisonUrl);
const comparison = parseGuardianResponse(comparisonResult.body);
const selected = comparison.assets.find((asset) => asset.asset.platformId === "ondo");
if (!selected) throw new Error("The deployed comparison did not resolve Ondo NVDAon");

const simulationUrl = new URL("/api/bnb/rwa", baseUrl);
simulationUrl.searchParams.set("operation", "simulate");
simulationUrl.searchParams.set("q", comparison.ticker);
simulationUrl.searchParams.set("token", selected.asset.tokenContractAddress);
simulationUrl.searchParams.set("receiver", receiver);
simulationUrl.searchParams.set("amount", "5.1");
const simulationResult = await request(simulationUrl);
const proof = parseSimulationProofResponse(simulationResult.body);

if (proof.sender !== receiver.toLowerCase()) {
  throw new Error("The deployed simulation changed the requested sender");
}
if (proof.approval.simulation.status !== "SUCCESS") {
  throw new Error("The deployed exact-approval simulation did not succeed");
}
if (proof.verdict !== "BLOCKED" || proof.swap.simulation.status !== "FAILED") {
  throw new Error(
    "Expected the unfunded preview sender to remain blocked at the swap simulation",
  );
}

process.stdout.write(`${JSON.stringify({
  status: "PASS_DEPLOYED_SIMULATION_ONLY_PREVIEW",
  origin: baseUrl.origin,
  chainId: 56,
  ticker: proof.ticker,
  tokenSymbol: proof.asset.tokenSymbol,
  sender: proof.sender,
  approvalStatus: proof.approval.simulation.status,
  swapStatus: proof.swap.simulation.status,
  verdict: proof.verdict,
  reasons: proof.reasons,
  boundary: "NO_LOCAL_CREDENTIAL_NO_WALLET_NO_PRIVATE_KEY_NO_SIGNING_NO_BROADCAST",
}, null, 2)}\n`);
