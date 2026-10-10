import chainManifest from "../../manifests/chains/robinhood-testnet-46630.json";
import deploymentManifest from "../../manifests/deployments/robinhood-testnet-direct-public-progress-2026-09-09.json";
import genesisManifest from "../../manifests/markets/robinhood-testnet-pltr-weth-public-genesis-2026-09-11.json";
import lifecyclePlan from "../../manifests/markets/robinhood-testnet-pltr-weth-lifecycle-continuation-candidate-2026-09-19.json";
import lifecyclePreflight from "../../manifests/markets/robinhood-testnet-pltr-weth-lifecycle-continuation-preflight-2026-09-19.json";
import lifecycleProgress from "../../manifests/markets/robinhood-testnet-pltr-weth-lifecycle-continuation-public-progress-2026-09-19.json";
import lifecycleIndex17 from "../../manifests/markets/robinhood-testnet-pltr-weth-lifecycle-index-17-reconciliation-2026-10-10.json";
import progressJson from "../../content/progress.json";
import type {
  ArchitectureNode,
  ContractRecord,
  Metric,
  ProgressContent,
  TransactionRecord,
} from "./model";

export const explorerBase = "https://explorer.testnet.chain.robinhood.com";
export const repositoryBase = "https://github.com/vmbbz/stonkHedge/blob/main";

const progressBase = progressJson as ProgressContent;

const sharedNames = [
  "FactoryNFT data slice 0",
  "FactoryNFT data slice 1",
  "FactoryNFT data slice 2",
  "FactoryNFT data slice 3",
  "FactoryNFT data slice 4",
  "FactoryNFT data slice 5",
  "FactoryNFT data slice 6",
  "PanopticMath",
  "InteractionHelper",
  "CollateralTrackerV2 reference",
  "PanopticGuardian",
  "BuilderFactory",
  "RiskEngine",
  "SemiFungiblePositionManagerV4",
  "PanopticPoolV2 reference",
  "PanopticFactoryV4",
] as const;

const sharedIds = [
  "metadata-0",
  "metadata-1",
  "metadata-2",
  "metadata-3",
  "metadata-4",
  "metadata-5",
  "metadata-6",
  "panoptic-math",
  "interaction-helper",
  "collateral-reference",
  "panoptic-guardian",
  "builder-factory",
  "risk-engine",
  "sfpm-v4",
  "pool-reference",
  "panoptic-factory",
] as const;

const sharedRoles = [
  "Immutable FactoryNFT metadata segment 1 of 7",
  "Immutable FactoryNFT metadata segment 2 of 7",
  "Immutable FactoryNFT metadata segment 3 of 7",
  "Immutable FactoryNFT metadata segment 4 of 7",
  "Immutable FactoryNFT metadata segment 5 of 7",
  "Immutable FactoryNFT metadata segment 6 of 7",
  "Immutable FactoryNFT metadata segment 7 of 7",
  "Shared options and liquidity mathematics",
  "Shared protocol interaction helpers",
  "Clone implementation for asset-specific collateral vaults",
  "Emergency authority and treasury boundary",
  "Guardian-owned builder allow-list factory",
  "Solvency configuration and market risk parameters",
  "Maps multi-leg Panoptic positions onto Uniswap V4",
  "Clone implementation for each options market",
  "Creates and registers each Panoptic market graph",
] as const;

const sharedReasons = [
  "Metadata pointers must be fixed before constructing the factory.",
  "Metadata slices are deployed consecutively to preserve the address plan.",
  "Metadata slices are deployed consecutively to preserve the address plan.",
  "Metadata slices are deployed consecutively to preserve the address plan.",
  "Metadata slices are deployed consecutively to preserve the address plan.",
  "Metadata slices are deployed consecutively to preserve the address plan.",
  "Completes the immutable seven-pointer metadata set.",
  "Shared linked library must exist before dependent initcode.",
  "Shared interaction dependency must exist before references and factory.",
  "The factory needs this clone implementation to create market trackers.",
  "Establishes guardian-admin and treasurer authority before dependants.",
  "Must follow Guardian because Guardian owns it; RiskEngine consumes it.",
  "Binds Guardian, BuilderFactory, buffers, and vegoid before pool creation.",
  "Connects Panoptic positions to the qualified V4 PoolManager.",
  "The market clone implementation binds SFPM and risk dependencies.",
  "Last: its constructor consumes metadata, references, and shared contracts.",
] as const;

type SharedTransaction = (typeof deploymentManifest.transactions)[number];

const sharedTransactions: TransactionRecord[] = deploymentManifest.transactions.map(
  (transaction: SharedTransaction, index: number) => ({
    id: `shared-${index}`,
    phase: "shared",
    index,
    nonce: transaction.nonce,
    label: sharedNames[index] ?? transaction.label,
    hash: transaction.transactionHash,
    blockNumber: transaction.blockNumber,
    toOrCreated: transaction.createdAddress,
    reason: sharedReasons[index] ?? "Required by the frozen direct-CREATE plan.",
    signedByProject: true,
  }),
);

const genesisReasons = [
  "Create WETH before any quote-asset permission or liquidity action.",
  "Permit2 needs an exact ERC-20 PLTR allowance before it can transfer PLTR.",
  "Permit2 needs an exact ERC-20 WETH allowance before it can transfer WETH.",
  "PositionManager needs a bounded second-layer PLTR permission.",
  "Refresh the aging PLTR permission under the newly authorized deadline.",
  "Complete the bounded second-layer WETH permission.",
  "The exact PoolKey must be initialized before it can receive liquidity.",
  "Positive bounded liquidity is required before market registration checks.",
  "Remove the temporary second-layer PLTR permission after the mint.",
  "Remove the temporary second-layer WETH permission after the mint.",
  "Close the first-layer PLTR authorization path.",
  "Close the first-layer WETH path; all temporary allowances are now zero.",
  "Last: register only after initialization, liquidity, and permission cleanup.",
] as const;

type GenesisTransaction = (typeof genesisManifest.completedTransactions)[number];

const genesisTransactions: TransactionRecord[] = genesisManifest.completedTransactions.map(
  (transaction: GenesisTransaction, index: number) => ({
    id: `genesis-${index}`,
    phase: "genesis",
    index,
    nonce: transaction.nonce,
    label: transaction.label,
    hash: transaction.transactionHash,
    blockNumber: transaction.blockNumber,
    toOrCreated: transaction.to,
    reason: genesisReasons[index] ?? "Bound to the accepted genesis sequence.",
    signedByProject: true,
  }),
);

const lifecycleReason = (phase: string) => {
  const reasons: Record<string, string> = {
    BUYER_FUNDING: "Fund the ordinary buyer with the exact bounded WETH collateral amount before any market interaction.",
    WRITER_SWAP_PERMISSIONS: "Establish the exact two-layer token permission required by the bounded baseline swaps.",
    WRITER_SWAP_PERMISSION_REFRESH: "Refresh only the existing Permit2 expiry after the original human-review window became too short.",
    BIDIRECTIONAL_BASELINE: "Exercise the live V4 route with a capped exact input and calldata-bound minimum output.",
    WRITER_REMAINING_SWAP_PERMISSION_REFRESH: "Renew only the unspent router allowance preserved by the canonical receipt prefix.",
    BOUNDED_COLLATERAL: "Move the exact authorized test collateral through its approval and tracker-deposit boundary.",
  };
  return reasons[phase] ?? "Advance one hash-bound lifecycle transition and stop for receipt and state verification.";
};

type LifecyclePlanTransaction = (typeof lifecyclePlan.transactions)[number];

const lifecycleTransactionAt = (index: number): LifecyclePlanTransaction => {
  const transaction = lifecyclePlan.transactions.find((candidate) => candidate.ordinal === index);
  if (!transaction) throw new Error(`Missing lifecycle transaction ${index}`);
  return transaction;
};

const lifecyclePrefixTransactions: TransactionRecord[] = lifecyclePreflight.evidencePrefix.map((evidence) => {
  const transaction = lifecycleTransactionAt(evidence.transactionIndex);
  return {
    id: `lifecycle-${evidence.transactionIndex}`,
    phase: "lifecycle",
    index: evidence.transactionIndex,
    nonce: evidence.nonce,
    label: transaction.label,
    hash: evidence.transactionHash,
    blockNumber: evidence.receiptBlock,
    toOrCreated: transaction.to,
    reason: lifecycleReason(transaction.phase),
    signedByProject: true,
  };
});

const lifecycleContinuationTransactions: TransactionRecord[] = lifecycleProgress.completedTransactions.map((evidence) => {
  const transaction = lifecycleTransactionAt(evidence.index);
  return {
    id: `lifecycle-${evidence.index}`,
    phase: "lifecycle",
    index: evidence.index,
    nonce: evidence.nonce,
    label: evidence.label,
    hash: evidence.transactionHash,
    blockNumber: evidence.blockNumber,
    toOrCreated: evidence.to,
    reason: lifecycleReason(transaction.phase),
    signedByProject: true,
  };
});

const lifecycleIndex17Transaction: TransactionRecord = {
  id: `lifecycle-${lifecycleIndex17.transaction.ordinal}`,
  phase: "lifecycle",
  index: lifecycleIndex17.transaction.ordinal,
  nonce: lifecycleIndex17.transaction.nonce,
  label: lifecycleIndex17.transaction.label,
  hash: lifecycleIndex17.receipt.transactionHash,
  blockNumber: lifecycleIndex17.receipt.blockNumber,
  toOrCreated: lifecycleIndex17.transaction.to,
  reason: lifecycleReason(lifecycleTransactionAt(lifecycleIndex17.transaction.ordinal).phase),
  signedByProject: true,
};

const lifecycleTransactions = [
  ...lifecyclePrefixTransactions,
  ...lifecycleContinuationTransactions,
  lifecycleIndex17Transaction,
].sort((left, right) => left.index - right.index);

const fundingTransactions: TransactionRecord[] = [
  {
    id: "funding-deployer",
    phase: "funding",
    index: 0,
    label: "Robinhood faucet distribution to deployer",
    hash: "0x4ad5005f8f19e454a2a4b0bbe111f3f5ead57a15b146023f87000b3c18e47d98",
    blockNumber: 115750101,
    toOrCreated: "0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD",
    reason: "Funded the deployment account with valueless test assets.",
    signedByProject: false,
  },
  {
    id: "funding-actor",
    phase: "funding",
    index: 1,
    label: "Robinhood faucet distribution to second actor",
    hash: "0xc9a5d901ddb0bd2d109fda652029550ec96b280433e9fb18e385da7c18a169b9",
    blockNumber: 116017132,
    toOrCreated: genesisManifest.actor,
    reason: "Funded the independent actor role with valueless test assets.",
    signedByProject: false,
  },
];

export const transactions: TransactionRecord[] = [
  ...fundingTransactions,
  ...sharedTransactions,
  ...genesisTransactions,
  ...lifecycleTransactions,
];

const latestLifecycleTransaction = lifecycleIndex17Transaction;
const nextLifecycleTransaction = lifecyclePlan.transactions.find(
  (transaction) => transaction.ordinal === lifecycleIndex17.nextUnexecutedIndex,
);

const lifecycleCheckpoint = (nextIndex: number) => {
  if (nextIndex <= 10) return {
    headline: "Bounded swaps in progress.",
    summary: "The permission and baseline-swap prefix is advancing under receipt-by-receipt verification.",
  };
  if (nextIndex <= 14) return {
    headline: "Writer collateral in progress.",
    summary: "The writer's exact PLTR and WETH collateral path is advancing through the two trackers.",
  };
  if (nextIndex <= 18) return {
    headline: "Writer funded. Buyer collateral next.",
    summary: "Both writer collateral deposits are live; the next gated phase establishes the buyer's bounded collateral.",
  };
  if (nextIndex <= 20) return {
    headline: "Collateral live. Matched positions next.",
    summary: "Both actors are funded; the lifecycle is advancing into the bounded matched short/long option pair.",
  };
  if (nextIndex <= 22) return {
    headline: "Matched positions live. Premium test next.",
    summary: "The bounded option pair is open; controlled swaps and premium/solvency observations are next.",
  };
  if (nextIndex <= 24) return {
    headline: "Premium observed. Ordered close next.",
    summary: "The mechanism observation has run; the buyer-first then writer close sequence remains gated.",
  };
  if (nextIndex <= 28) return {
    headline: "Positions closed. Cleanup next.",
    summary: "Both option legs are closed; only exact Permit2 and ERC-20 permission cleanup remains.",
  };
  return {
    headline: "Public lifecycle complete.",
    summary: "All plan-bound lifecycle calls have canonical receipts and reconciled terminal state.",
  };
};

const checkpoint = lifecycleCheckpoint(lifecycleIndex17.nextUnexecutedIndex);

export const lifecycleFacts = {
  completedCalls: lifecycleTransactions.length,
  completedThrough: lifecycleIndex17.completedThroughTransactionIndex,
  totalCalls: lifecyclePlan.transactionCount,
  remainingCalls: lifecycleIndex17.remainingTransactionCount,
  nextUnexecutedIndex: lifecycleIndex17.nextUnexecutedIndex,
  nextLabel: nextLifecycleTransaction?.label ?? "No remaining plan-bound transaction",
  nextRequiredAction: `${lifecycleIndex17.nextUnexecutedAction}; fresh plan clocks, simulation, and authorization are required`,
  latestBlock: lifecycleIndex17.receipt.blockNumber,
  latestTimestampUtc: lifecycleIndex17.receipt.blockTimestamp,
  writerNonce: lifecycleIndex17.freshPostState.writerNonce,
  buyerNonce: lifecycleIndex17.freshPostState.buyerNonce,
  headline: checkpoint.headline,
  checkpointSummary: checkpoint.summary,
};

export const progress: ProgressContent = {
  ...progressBase,
  entries: progressBase.entries.map((entry) => entry.id === "two-actor-lifecycle" ? {
    ...entry,
    summary: `The hash-bound public lifecycle is verified through index ${lifecycleFacts.completedThrough}: ${lifecycleFacts.completedCalls}/${lifecycleFacts.totalCalls} calls are canonical. ${lifecycleFacts.checkpointSummary} Next: ${lifecycleFacts.nextLabel}.`,
    outcomes: [
      `${lifecycleFacts.completedCalls}/${lifecycleFacts.totalCalls} public lifecycle calls have canonical receipts and reconciled post-state`,
      "Every public call is bound to its plan, receipt, exact post-state, and both actors' nonce stream",
      `${lifecycleFacts.remainingCalls} plan-bound calls remain unexecuted; fresh authorization is required before ${lifecycleFacts.nextLabel}`,
    ],
    transactionRefs: lifecycleTransactions.map((transaction) => transaction.id),
    evidence: [
      `Verified public prefix 0..${lifecycleFacts.completedThrough}`,
      `Latest reconciled block ${lifecycleFacts.latestBlock}`,
      `Writer nonce ${lifecycleFacts.writerNonce} · buyer nonce ${lifecycleFacts.buyerNonce}`,
      "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH",
    ],
  } : entry),
};

const sharedContracts: ContractRecord[] = deploymentManifest.transactions.map(
  (transaction: SharedTransaction, index: number) => ({
    id: sharedIds[index] ?? `shared-contract-${index}`,
    name: sharedNames[index] ?? transaction.label,
    address: transaction.createdAddress,
    role: sharedRoles[index] ?? "Shared Panoptic deployment",
    provenance: "stonkhedge",
    layer: index < 7 ? "Factory metadata" : "Shared Panoptic",
    transactionId: `shared-${index}`,
    blockNumber: transaction.blockNumber,
    detail: `${transaction.runtimeBytes.toLocaleString()} runtime bytes · ${transaction.runtimeCodeHash}`,
  }),
);

const stockTokens = chainManifest.stockTokens.map((token) => ({
  id: `stock-${token.symbol.toLowerCase()}`,
  name: `${token.symbol} Stock Token`,
  address: token.address,
  role: token.symbol === "PLTR" ? "Base asset in the first test market" : "Qualified faucet-distributed test asset",
  provenance: "external" as const,
  layer: "Robinhood test assets",
  detail: "Transferable test token subject to external issuer controls",
}));

const externalContracts: ContractRecord[] = [
  {
    id: "stock-registry",
    name: "Stock registry / beacon",
    address: chainManifest.sharedStockInfrastructure.registryAndBeacon,
    role: "Shared policy registry and implementation beacon",
    provenance: "external",
    layer: "Robinhood test assets",
  },
  {
    id: "stock-implementation",
    name: "Stock Token implementation",
    address: chainManifest.sharedStockInfrastructure.implementation,
    role: "Shared implementation behind the Stock Token proxies",
    provenance: "external",
    layer: "Robinhood test assets",
  },
  ...stockTokens,
  {
    id: "testnet-weth",
    name: "Testnet WETH",
    address: chainManifest.quoteAssets.weth.address,
    role: "Wrapped native quote asset",
    provenance: "external",
    layer: "Robinhood test assets",
  },
  ...Object.entries(chainManifest.infrastructure).map(([key, value]) => ({
    id: key === "poolManager" ? "v4-pool-manager" : key === "positionManager" ? "v4-position-manager" : key.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`),
    name: key.replace(/([A-Z])/g, " $1").replace(/^./, (letter) => letter.toUpperCase()),
    address: value.address,
    role: key === "poolManager" ? "Owns Uniswap V4 pool state" : key === "positionManager" ? "Mints and manages V4 liquidity NFTs" : "Qualified candidate V4 periphery",
    provenance: "external" as const,
    layer: "Candidate Uniswap V4",
  })),
];

const registered = genesisManifest.registeredMarket;
const marketContracts: ContractRecord[] = [
  {
    id: "market-panoptic-pool",
    name: "PLTR/WETH PanopticPool",
    address: registered.panopticPool.address,
    role: "Market-level perpetual-options engine",
    provenance: "market",
    layer: "PLTR/WETH market",
    transactionId: "genesis-12",
    blockNumber: genesisManifest.completedTransactions[12].blockNumber,
    detail: `SFPM pool ID ${registered.panopticPool.poolId}`,
  },
  {
    id: "market-tracker-pltr",
    name: "PLTR CollateralTracker",
    address: registered.collateralTracker0.address,
    role: "PLTR-side collateral accounting clone",
    provenance: "market",
    layer: "PLTR/WETH market",
    transactionId: "genesis-12",
    blockNumber: genesisManifest.completedTransactions[12].blockNumber,
  },
  {
    id: "market-tracker-weth",
    name: "WETH CollateralTracker",
    address: registered.collateralTracker1.address,
    role: "WETH-side collateral accounting clone",
    provenance: "market",
    layer: "PLTR/WETH market",
    transactionId: "genesis-12",
    blockNumber: genesisManifest.completedTransactions[12].blockNumber,
  },
];

export const contracts: ContractRecord[] = [
  ...sharedContracts,
  ...marketContracts,
  ...externalContracts,
];

export const metrics: Metric[] = [
  { value: "19", label: "StonkHedge deployments", note: "16 shared + 3 market clones" },
  { value: String(transactions.filter((transaction) => transaction.signedByProject).length), label: "Project-signed transactions", note: "Deployment + genesis + public lifecycle" },
  { value: `${lifecycleFacts.completedCalls}/${lifecycleFacts.totalCalls}`, label: "Lifecycle calls verified", note: `Canonical public prefix through index ${lifecycleFacts.completedThrough}` },
  { value: "2", label: "Writer collateral deposits", note: "Bounded PLTR + WETH mechanism-test assets" },
];

export const architectureNodes: ArchitectureNode[] = [
  { id: "assets", label: "Robinhood\ntest assets", layer: "external", position: [-4.5, 1.6, 0], connections: ["v4"] },
  { id: "v4", contractId: "v4-pool-manager", label: "Uniswap V4\nPoolManager", layer: "external", position: [-2.2, 0, 0], connections: ["sfpm", "liquidity"] },
  { id: "guardian", contractId: "panoptic-guardian", label: "Guardian +\nRiskEngine", layer: "shared", position: [0.2, 2.2, 0], connections: ["factory", "market"] },
  { id: "sfpm", contractId: "sfpm-v4", label: "SFPM V4", layer: "shared", position: [0.1, -1.8, 0], connections: ["market"] },
  { id: "factory", contractId: "panoptic-factory", label: "Panoptic\nFactory V4", layer: "shared", position: [2.4, 1.2, 0], connections: ["market"] },
  { id: "liquidity", label: "PLTR / WETH\nLP NFT 3903", layer: "market", position: [-1.6, -3.8, 0], connections: ["market"] },
  { id: "market", contractId: "market-panoptic-pool", label: "PanopticPool +\n2 Trackers", layer: "market", position: [4.5, -0.7, 0], connections: ["lifecycle"] },
  { id: "lifecycle", label: `Public lifecycle\n${lifecycleFacts.completedCalls} / ${lifecycleFacts.totalCalls}`, layer: "market", position: [6.2, 2.2, 0], connections: ["next"] },
  { id: "next", label: `Next unexecuted\nindex ${lifecycleFacts.nextUnexecutedIndex}`, layer: "next", position: [7.5, -1.4, 0], connections: [] },
];

export const terminalFacts = {
  status: lifecycleIndex17.status,
  referenceBlock: lifecycleFacts.latestBlock,
  referenceTimestamp: lifecycleFacts.latestTimestampUtc,
  poolId: genesisManifest.market.poolId,
  lpNft: genesisManifest.market.liquidityPosition.tokenId,
  liquidity: genesisManifest.market.liquidityPosition.liquidity,
  sfpmPoolId: genesisManifest.registeredMarket.sfpmPoolId,
  finalTransaction: latestLifecycleTransaction.hash,
  nextGate: lifecycleFacts.nextRequiredAction,
};
