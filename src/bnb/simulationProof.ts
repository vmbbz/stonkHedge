export type SimulationVerdict = "CLEAR" | "BLOCKED";
export type SimulationStatus = "SUCCESS" | "FAILED";

export interface PublicSimulationProof {
  ticker: string;
  companyName: string;
  asset: {
    platformId: string;
    tokenContractAddress: string;
    tokenSymbol: string;
  };
  sender: string;
  input: { symbol: "USDT"; displayAmount: "5.1"; rawAmount: "5100000000000000000" };
  route: {
    quoteIdHash: string;
    vendorName: string;
    executionMode: "SWAP";
    expectedOutputRaw: string;
    slippagePercent: "0.5";
  };
  approval: {
    token: string;
    spender: string;
    amount: "5100000000000000000";
    transaction: PublicTransactionEvidence;
    simulation: PublicSimulationSummary;
  };
  swap: {
    transaction: PublicTransactionEvidence & { from: string };
    minimumOutputRaw: string;
    simulation: PublicSimulationSummary;
  };
  verdict: SimulationVerdict;
  reasons: string[];
  timestamp: number;
}

export interface PublicTransactionEvidence {
  from?: string;
  to: string;
  value: string;
  selector: string;
  calldataHash: string;
}

export interface PublicSimulationSummary {
  status: SimulationStatus;
  failReason: string | null;
  balanceChangeCount: number;
  allowanceChangeCount: number;
}

const BOUNDARY = "SIMULATION_ONLY_NO_WALLET_NO_PRIVATE_KEY_NO_SIGNING_NO_BROADCAST";
const BSC_USDT_ADDRESS = "0x55d398326f99059ff775485246999027b3197955";
const ADDRESS_PATTERN = /^0x[a-f0-9]{40}$/u;
const HASH_PATTERN = /^0x[a-f0-9]{64}$/u;
const SELECTOR_PATTERN = /^0x[a-f0-9]{8}$/u;
const INTEGER_PATTERN = /^(?:0|[1-9]\d*)$/u;
const TRANSACTION_FIELDS = new Set(["from", "to", "value", "selector", "calldataHash"]);

function record(value: unknown, label: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`Invalid ${label}`);
  }
  return value as Record<string, unknown>;
}

function text(value: unknown, label: string, maximum = 2_048): string {
  if (
    typeof value !== "string"
    || value.length < 1
    || value.length > maximum
    || /[\u0000-\u001f\u007f]/u.test(value)
  ) {
    throw new Error(`Invalid ${label}`);
  }
  return value;
}

function address(value: unknown, label: string): string {
  const parsed = text(value, label, 42).toLowerCase();
  if (!ADDRESS_PATTERN.test(parsed)) throw new Error(`Invalid ${label}`);
  return parsed;
}

function integer(value: unknown, label: string, positive = false): string {
  const parsed = text(value, label, 100);
  if (!INTEGER_PATTERN.test(parsed) || (positive && BigInt(parsed) <= 0n)) {
    throw new Error(`Invalid ${label}`);
  }
  return parsed;
}

function count(value: unknown, label: string): number {
  if (!Number.isSafeInteger(value) || Number(value) < 0 || Number(value) > 128) {
    throw new Error(`Invalid ${label}`);
  }
  return Number(value);
}

function parseTransaction(value: unknown, label: string, requireFrom: boolean): PublicTransactionEvidence {
  const transaction = record(value, label);
  for (const key of Object.keys(transaction)) {
    if (!TRANSACTION_FIELDS.has(key)) {
      throw new Error(`Invalid executable transaction field ${key}`);
    }
  }
  const selector = text(transaction.selector, `${label} selector`, 10).toLowerCase();
  const calldataHash = text(transaction.calldataHash, `${label} calldata hash`, 66).toLowerCase();
  if (!SELECTOR_PATTERN.test(selector) || !HASH_PATTERN.test(calldataHash)) {
    throw new Error(`Invalid ${label} byte evidence`);
  }
  const parsed: PublicTransactionEvidence = {
    to: address(transaction.to, `${label} destination`),
    value: integer(transaction.value, `${label} value`),
    selector,
    calldataHash,
  };
  if (requireFrom) parsed.from = address(transaction.from, `${label} sender`);
  else if (transaction.from !== undefined) throw new Error(`Invalid executable transaction field from`);
  return parsed;
}

function parseSimulation(value: unknown, label: string): PublicSimulationSummary {
  const simulation = record(value, label);
  const status = simulation.status;
  if (status !== "SUCCESS" && status !== "FAILED") throw new Error(`Invalid ${label} status`);
  const failReason = simulation.failReason === null
    ? null
    : text(simulation.failReason, `${label} failure reason`);
  return {
    status,
    failReason,
    balanceChangeCount: count(simulation.balanceChangeCount, `${label} balance count`),
    allowanceChangeCount: count(simulation.allowanceChangeCount, `${label} allowance count`),
  };
}

export function parseSimulationProofResponse(value: unknown): PublicSimulationProof {
  const envelope = record(value, "simulation response");
  if (envelope.operation !== "simulate" || envelope.chainId !== 56 || envelope.boundary !== BOUNDARY) {
    throw new Error("Invalid simulation response identity");
  }
  const data = record(envelope.data, "simulation proof");
  const asset = record(data.asset, "simulation asset");
  const input = record(data.input, "simulation input");
  const route = record(data.route, "simulation route");
  const approval = record(data.approval, "approval evidence");
  const swap = record(data.swap, "swap evidence");
  const quoteIdHash = text(route.quoteIdHash, "quote ID hash", 66).toLowerCase();
  if (!HASH_PATTERN.test(quoteIdHash)) throw new Error("Invalid quote ID hash");
  const rawAmount = integer(input.rawAmount, "simulation input raw amount", true);
  if (input.symbol !== "USDT" || input.displayAmount !== "5.1" || rawAmount !== "5100000000000000000") {
    throw new Error("Invalid simulation input bound");
  }
  if (route.executionMode !== "SWAP" || route.slippagePercent !== "0.5") {
    throw new Error("Invalid simulation route policy");
  }
  const verdict = data.verdict;
  if (verdict !== "CLEAR" && verdict !== "BLOCKED") throw new Error("Invalid simulation verdict");
  if (!Array.isArray(data.reasons) || data.reasons.length > 16) {
    throw new Error("Invalid simulation reasons");
  }
  const reasons = data.reasons.map((reason, index) => text(reason, `simulation reason ${index}`));
  const approvalSimulation = parseSimulation(approval.simulation, "approval simulation");
  const swapSimulation = parseSimulation(swap.simulation, "swap simulation");
  if (verdict === "CLEAR" && (approvalSimulation.status !== "SUCCESS" || swapSimulation.status !== "SUCCESS" || reasons.length > 0)) {
    throw new Error("Invalid clear simulation verdict");
  }
  if (verdict === "BLOCKED" && reasons.length === 0) throw new Error("Invalid blocked simulation verdict");

  const sender = address(data.sender, "simulation sender");
  const approvalToken = address(approval.token, "approval token");
  const approvalSpender = address(approval.spender, "approval spender");
  const approvalTransaction = parseTransaction(approval.transaction, "approval transaction", false);
  const swapTransaction = parseTransaction(
    swap.transaction,
    "swap transaction",
    true,
  ) as PublicTransactionEvidence & { from: string };
  if (
    approvalToken !== BSC_USDT_ADDRESS
    || approvalTransaction.to !== approvalToken
    || approvalTransaction.value !== "0"
    || approvalTransaction.selector !== "0x095ea7b3"
  ) {
    throw new Error("Invalid approval transaction binding");
  }
  if (swapTransaction.from !== sender || swapTransaction.value !== "0") {
    throw new Error("Invalid swap transaction binding");
  }

  return {
    ticker: text(data.ticker, "simulation ticker", 32),
    companyName: text(data.companyName, "simulation company", 160),
    asset: {
      platformId: text(asset.platformId, "simulation platform", 80),
      tokenContractAddress: address(asset.tokenContractAddress, "simulation token"),
      tokenSymbol: text(asset.tokenSymbol, "simulation token symbol", 32),
    },
    sender,
    input: { symbol: "USDT", displayAmount: "5.1", rawAmount: "5100000000000000000" },
    route: {
      quoteIdHash,
      vendorName: text(route.vendorName, "simulation vendor", 80),
      executionMode: "SWAP",
      expectedOutputRaw: integer(route.expectedOutputRaw, "simulation expected output", true),
      slippagePercent: "0.5",
    },
    approval: {
      token: approvalToken,
      spender: approvalSpender,
      amount: approval.amount === "5100000000000000000"
        ? "5100000000000000000"
        : (() => { throw new Error("Invalid approval amount"); })(),
      transaction: approvalTransaction,
      simulation: approvalSimulation,
    },
    swap: {
      transaction: swapTransaction,
      minimumOutputRaw: integer(swap.minimumOutputRaw, "swap minimum output", true),
      simulation: swapSimulation,
    },
    verdict,
    reasons,
    timestamp: typeof data.timestamp === "number" && Number.isSafeInteger(data.timestamp) && data.timestamp > 0
      ? data.timestamp
      : (() => { throw new Error("Invalid simulation timestamp"); })(),
  };
}
