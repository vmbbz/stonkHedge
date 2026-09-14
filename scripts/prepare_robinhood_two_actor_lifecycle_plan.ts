#!/usr/bin/env node
/**
 * Build the deterministic, unsigned PLTR/WETH two-actor lifecycle proposal.
 *
 * This is deliberately an offline design tool. It reads committed public
 * manifests, uses the published Panoptic SDK for TokenId and Universal Router
 * encoding, and writes inspection-only calldata. It has no RPC, keystore,
 * private-key, signing, transaction-submission, or broadcast capability.
 */

import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import {
  createTokenIdBuilder,
  decodeTokenId,
  encodeV4PoolId,
} from "@panoptic-eng/sdk/v2";
import {
  encodeFunctionData,
  keccak256,
  type Address,
  type Hex,
} from "viem";

import {
  buildRobinhoodV4ExactInputSingleCalldata,
  ROBINHOOD_UNIVERSAL_ROUTER,
  ROBINHOOD_UNIVERSAL_ROUTER_RUNTIME_HASH,
  ROBINHOOD_V4_PERIPHERY_SOURCE_COMMIT,
} from "../src/protocol/robinhoodV4Swap";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const REPOSITORY = resolve(dirname(SCRIPT_PATH), "..");

export const DEFAULT_GENESIS = resolve(
  REPOSITORY,
  "manifests/markets/robinhood-testnet-pltr-weth-public-genesis-2026-09-11.json",
);
export const DEFAULT_CHAIN = resolve(
  REPOSITORY,
  "manifests/chains/robinhood-testnet-46630.json",
);
export const DEFAULT_INPUTS = resolve(
  REPOSITORY,
  "manifests/markets/robinhood-testnet-pltr-weth-lifecycle-inputs-2026-09-14.json",
);
export const DEFAULT_OUTPUT = resolve(
  REPOSITORY,
  "manifests/markets/robinhood-testnet-pltr-weth-lifecycle-proposal-2026-09-14.json",
);

const ZERO_ADDRESS = "0x0000000000000000000000000000000000000000" as Address;
const MIN_TICK = -887_272;
const MAX_TICK = 887_272;

const erc20Abi = [
  {
    type: "function",
    name: "approve",
    stateMutability: "nonpayable",
    inputs: [
      { name: "spender", type: "address" },
      { name: "amount", type: "uint256" },
    ],
    outputs: [{ name: "", type: "bool" }],
  },
] as const;

const wethAbi = [
  {
    type: "function",
    name: "deposit",
    stateMutability: "payable",
    inputs: [],
    outputs: [],
  },
] as const;

const permit2Abi = [
  {
    type: "function",
    name: "approve",
    stateMutability: "nonpayable",
    inputs: [
      { name: "token", type: "address" },
      { name: "spender", type: "address" },
      { name: "amount", type: "uint160" },
      { name: "expiration", type: "uint48" },
    ],
    outputs: [],
  },
] as const;

const collateralTrackerAbi = [
  {
    type: "function",
    name: "deposit",
    stateMutability: "payable",
    inputs: [
      { name: "assets", type: "uint256" },
      { name: "receiver", type: "address" },
    ],
    outputs: [{ name: "shares", type: "uint256" }],
  },
] as const;

const panopticPoolAbi = [
  {
    type: "function",
    name: "dispatch",
    stateMutability: "nonpayable",
    inputs: [
      { name: "positionIdList", type: "uint256[]" },
      { name: "finalPositionIdList", type: "uint256[]" },
      { name: "positionSizes", type: "uint128[]" },
      { name: "tickAndSpreadLimits", type: "int24[3][]" },
      { name: "usePremiaAsCollateral", type: "bool" },
      { name: "builderCode", type: "uint256" },
    ],
    outputs: [],
  },
] as const;

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
type JsonObject = { [key: string]: any };

export interface PlanPaths {
  genesis: string;
  chain: string;
  inputs: string;
  script?: string;
  packageJson?: string;
  packageLock?: string;
  swapAdapter?: string;
}

interface TransactionIntent {
  ordinal: number;
  phase: string;
  sender: Address;
  nonce: null;
  label: string;
  to: Address;
  valueWei: string;
  calldata: Hex;
  calldataKeccak256: Hex;
  decodedIntent: JsonObject;
  mandatoryPostconditions: string[];
}

function readJson(path: string): JsonObject {
  return JSON.parse(readFileSync(path, "utf8")) as JsonObject;
}

export function fileSha256(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function sortJson(value: Json): Json {
  if (Array.isArray(value)) return value.map(sortJson);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, child]) => [key, sortJson(child)]),
    );
  }
  return value;
}

function jsonSafe(value: unknown): Json {
  if (typeof value === "bigint") return value.toString();
  if (Array.isArray(value)) return value.map(jsonSafe);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, child]) => [key, jsonSafe(child)]),
    );
  }
  return value as Json;
}

export function canonicalSha256(value: Json): string {
  return createHash("sha256")
    .update(JSON.stringify(sortJson(value)))
    .digest("hex");
}

function address(value: unknown, label: string): Address {
  if (typeof value !== "string" || !/^0x[0-9a-fA-F]{40}$/.test(value)) {
    throw new Error(`${label} must be a 20-byte hex address`);
  }
  return value.toLowerCase() as Address;
}

function integer(value: unknown, label: string): bigint {
  try {
    const parsed = BigInt(value as string | number | bigint);
    if (parsed < 0n) throw new Error();
    return parsed;
  } catch {
    throw new Error(`${label} must be a non-negative integer`);
  }
}

function equal(left: unknown, right: unknown, label: string): void {
  if (String(left).toLowerCase() !== String(right).toLowerCase()) {
    throw new Error(`${label} mismatch: ${String(left)} != ${String(right)}`);
  }
}

function transaction(
  ordinal: number,
  phase: string,
  sender: Address,
  label: string,
  to: Address,
  calldata: Hex,
  decodedIntent: JsonObject,
  mandatoryPostconditions: string[],
  value = 0n,
): TransactionIntent {
  return {
    ordinal,
    phase,
    sender,
    nonce: null,
    label,
    to,
    valueWei: value.toString(),
    calldata,
    calldataKeccak256: keccak256(calldata),
    decodedIntent,
    mandatoryPostconditions,
  };
}

function approveErc20(spender: Address, amount: bigint): Hex {
  return encodeFunctionData({
    abi: erc20Abi,
    functionName: "approve",
    args: [spender, amount],
  });
}

function approvePermit2(
  token: Address,
  spender: Address,
  amount: bigint,
  expiration: bigint,
): Hex {
  return encodeFunctionData({
    abi: permit2Abi,
    functionName: "approve",
    args: [token, spender, amount, Number(expiration)],
  });
}

function depositCollateral(assets: bigint, receiver: Address): Hex {
  return encodeFunctionData({
    abi: collateralTrackerAbi,
    functionName: "deposit",
    args: [assets, receiver],
  });
}

function dispatch(
  tokenId: bigint,
  finalPositionIds: bigint[],
  positionSize: bigint,
  effectiveLiquidityLimitBps: number,
  usePremiaAsCollateral: boolean,
  builderCode: bigint,
): Hex {
  return encodeFunctionData({
    abi: panopticPoolAbi,
    functionName: "dispatch",
    args: [
      [tokenId],
      finalPositionIds,
      [positionSize],
      [[MIN_TICK, MAX_TICK, effectiveLiquidityLimitBps]],
      usePremiaAsCollateral,
      builderCode,
    ],
  });
}

function relativePath(path: string): string {
  return relative(REPOSITORY, resolve(path)).replaceAll("\\", "/");
}

export function buildPlan(paths: PlanPaths): JsonObject {
  const genesis = readJson(paths.genesis);
  const chain = readJson(paths.chain);
  const inputs = readJson(paths.inputs);
  const packageJsonPath = paths.packageJson ?? resolve(REPOSITORY, "package.json");
  const packageLockPath = paths.packageLock ?? resolve(REPOSITORY, "package-lock.json");
  const scriptPath = paths.script ?? SCRIPT_PATH;
  const swapAdapterPath =
    paths.swapAdapter ?? resolve(REPOSITORY, "src/protocol/robinhoodV4Swap.ts");
  const packageJson = readJson(packageJsonPath);

  equal(genesis.network.chainId, 46630, "genesis chain ID");
  equal(chain.network.chainId, 46630, "chain manifest chain ID");
  equal(inputs.network.chainId, 46630, "input snapshot chain ID");
  equal(
    inputs.marketState.poolId,
    genesis.market.poolId,
    "input snapshot PoolId",
  );
  equal(
    inputs.marketState.sfpmPoolId,
    genesis.registeredMarket.sfpmPoolId,
    "input snapshot SFPM pool ID",
  );
  equal(
    inputs.marketState.activeLiquidity,
    genesis.market.liquidityPosition.liquidity,
    "input snapshot active liquidity",
  );
  if (
    inputs.marketState.registryPaused !== false ||
    inputs.marketState.stockTokenPaused !== false ||
    inputs.marketState.stockMultiplierEffectiveAt !== "0" ||
    inputs.marketState.stockUiMultiplier !== "1000000000000000000"
  ) {
    throw new Error("Stock Token health is not eligible for lifecycle planning");
  }

  const pltr = address(genesis.market.asset.address, "PLTR");
  const weth = address(genesis.market.quoteAsset.address, "WETH");
  const pool = address(genesis.registeredMarket.panopticPool.address, "PanopticPool");
  const tracker0 = address(
    genesis.registeredMarket.collateralTracker0.address,
    "PLTR CollateralTracker",
  );
  const tracker1 = address(
    genesis.registeredMarket.collateralTracker1.address,
    "WETH CollateralTracker",
  );
  const permit2 = address(chain.infrastructure.permit2.address, "Permit2");
  const router = address(
    chain.infrastructure.universalRouter.address,
    "UniversalRouter",
  );
  equal(router, ROBINHOOD_UNIVERSAL_ROUTER, "Robinhood UniversalRouter address");
  equal(
    chain.infrastructure.universalRouter.runtimeCodeHash,
    ROBINHOOD_UNIVERSAL_ROUTER_RUNTIME_HASH,
    "Robinhood UniversalRouter runtime hash",
  );
  const stateView = address(chain.infrastructure.stateView.address, "StateView");
  const stockRegistry = address(
    chain.sharedStockInfrastructure.registryAndBeacon,
    "Stock registry",
  );
  const deployer = address(chain.deployer.address, "shared deployer");
  const writer = address(inputs.actors.writer.address, "writer");
  const buyer = address(inputs.actors.buyer.address, "buyer");
  if (writer === buyer) throw new Error("writer and buyer must be distinct accounts");
  if (buyer === deployer) {
    throw new Error("buyer must be a third unprivileged account, not the shared deployer");
  }
  if (!String(inputs.actors.buyer.role).toUpperCase().includes("UNPRIVILEGED")) {
    throw new Error("buyer role must be explicitly classified as unprivileged");
  }
  if (inputs.roleRisk.accepted !== false) {
    throw new Error("privileged buyer risk acceptance must remain false");
  }
  if (inputs.actors.writer.openLegs !== 0 || inputs.actors.buyer.openLegs !== 0) {
    throw new Error("both actors must begin with zero open legs");
  }
  if (
    inputs.actors.writer.collateralTracker0Shares !== "0" ||
    inputs.actors.writer.collateralTracker1Shares !== "0" ||
    inputs.actors.buyer.collateralTracker0Shares !== "0" ||
    inputs.actors.buyer.collateralTracker1Shares !== "0"
  ) {
    throw new Error("both actors must begin with zero collateral shares");
  }
  for (const [role, actor] of Object.entries(inputs.actors) as [string, JsonObject][]) {
    const allowances = actor.initialAllowances;
    if (!allowances) {
      throw new Error(`${role} snapshot must include initial allowance evidence`);
    }
    for (const name of [
      "pltrToPermit2",
      "wethToPermit2",
      "pltrToTracker0",
      "wethToTracker1",
    ]) {
      if (integer(allowances[name], `${role} ${name}`) !== 0n) {
        throw new Error(`${role} initial ERC20 allowances must be zero`);
      }
    }
    for (const name of ["pltrPermit2ToRouter", "wethPermit2ToRouter"]) {
      if (!Array.isArray(allowances[name]) || allowances[name].length !== 3) {
        throw new Error(`${role} ${name} snapshot is malformed`);
      }
      if (integer(allowances[name][0], `${role} ${name} amount`) !== 0n) {
        throw new Error(`${role} initial Permit2 allowance amounts must be zero`);
      }
    }
  }

  const poolKey = {
    currency0: address(genesis.market.poolKey.currency0, "currency0"),
    currency1: address(genesis.market.poolKey.currency1, "currency1"),
    fee: BigInt(genesis.market.poolKey.fee),
    tickSpacing: BigInt(genesis.market.poolKey.tickSpacing),
    hooks: address(genesis.market.poolKey.hooks, "hooks"),
  };
  if (poolKey.currency0 !== pltr || poolKey.currency1 !== weth) {
    throw new Error("the lifecycle proposal requires PLTR as currency0 and WETH as currency1");
  }
  if (poolKey.fee !== 3000n || poolKey.tickSpacing !== 60n || poolKey.hooks !== ZERO_ADDRESS) {
    throw new Error("the lifecycle proposal requires the exact fee-3000, spacing-60, no-hook PoolKey");
  }

  const derivedSfpmPoolId = encodeV4PoolId(
    genesis.market.poolId as Hex,
    poolKey.tickSpacing,
    BigInt(genesis.registeredMarket.riskEngineVegoid),
  );
  equal(derivedSfpmPoolId, inputs.marketState.sfpmPoolId, "published SDK SFPM pool ID");

  const option = inputs.proposedExposure.option;
  const shortTokenId = createTokenIdBuilder(derivedSfpmPoolId)
    .addCall({
      asset: BigInt(option.asset),
      optionRatio: BigInt(option.optionRatio),
      isLong: false,
      riskPartner: BigInt(option.riskPartner),
      strike: BigInt(option.strike),
      width: BigInt(option.width),
    })
    .build();
  const longTokenId = createTokenIdBuilder(derivedSfpmPoolId)
    .addCall({
      asset: BigInt(option.asset),
      optionRatio: BigInt(option.optionRatio),
      isLong: true,
      riskPartner: BigInt(option.riskPartner),
      strike: BigInt(option.strike),
      width: BigInt(option.width),
    })
    .build();
  const decodedShort = decodeTokenId(shortTokenId);
  const decodedLong = decodeTokenId(longTokenId);
  equal(decodedShort.poolId, `0x${derivedSfpmPoolId.toString(16).padStart(16, "0")}`, "short TokenId pool ID");
  equal(decodedLong.poolId, decodedShort.poolId, "matched long TokenId pool ID");
  equal(decodedShort.legs[0]?.tickLower, option.tickLower, "short lower tick");
  equal(decodedShort.legs[0]?.tickUpper, option.tickUpper, "short upper tick");
  equal(decodedLong.legs[0]?.tickLower, option.tickLower, "long lower tick");
  equal(decodedLong.legs[0]?.tickUpper, option.tickUpper, "long upper tick");

  const writerCollateralPltr = integer(
    inputs.proposedExposure.writerCollateral.pltrAssets,
    "writer PLTR collateral",
  );
  const writerCollateralWeth = integer(
    inputs.proposedExposure.writerCollateral.wethAssets,
    "writer WETH collateral",
  );
  const buyerCollateralPltr = integer(
    inputs.proposedExposure.buyerCollateral.pltrAssets,
    "buyer PLTR collateral",
  );
  const buyerCollateralWeth = integer(
    inputs.proposedExposure.buyerCollateral.wethAssets,
    "buyer WETH collateral",
  );
  const wrapNative = integer(
    inputs.proposedExposure.buyerWrapNativeWei,
    "buyer native wrap",
  );
  const pltrSwapTotal = integer(
    inputs.proposedExposure.writerSwapBudget.pltrTotalInput,
    "writer PLTR swap total",
  );
  const wethSwapTotal = integer(
    inputs.proposedExposure.writerSwapBudget.wethTotalInput,
    "writer WETH swap total",
  );
  const perPltrSwap = integer(
    inputs.proposedExposure.writerSwapBudget.perSwapPltrInput,
    "PLTR per swap",
  );
  const perWethSwap = integer(
    inputs.proposedExposure.writerSwapBudget.perSwapWethInput,
    "WETH per swap",
  );
  if (perPltrSwap * 2n !== pltrSwapTotal || perWethSwap * 2n !== wethSwapTotal) {
    throw new Error("swap totals must equal the two planned exact-input swaps per asset");
  }
  const minWethOut = integer(
    inputs.proposedExposure.writerSwapBudget.minimumWethOutputPerPltrSwap,
    "minimum WETH output",
  );
  const minPltrOut = integer(
    inputs.proposedExposure.writerSwapBudget.minimumPltrOutputPerWethSwap,
    "minimum PLTR output",
  );
  const expiry = integer(inputs.proposedExposure.rehearsalOnlyExpiry.unix, "rehearsal expiry");
  const shortSize = integer(option.writerShortSize, "writer short size");
  const longSize = integer(option.buyerLongSize, "buyer long size");
  const effectiveLiquidityLimitBps = Number(
    integer(option.effectiveLiquidityLimitBps, "effective liquidity limit"),
  );
  const usePremia = Boolean(option.usePremiaAsCollateral);
  const builderCode = integer(option.builderCode, "builder code");

  if (effectiveLiquidityLimitBps <= 0 || effectiveLiquidityLimitBps > 90_000) {
    throw new Error("effective liquidity limit must be within (0, 90000] bps");
  }

  if (writerCollateralPltr + pltrSwapTotal > integer(inputs.actors.writer.pltrBalance, "writer PLTR balance")) {
    throw new Error("writer PLTR caps exceed the pinned balance");
  }
  if (writerCollateralWeth + wethSwapTotal > integer(inputs.actors.writer.wethBalance, "writer WETH balance")) {
    throw new Error("writer WETH caps exceed the pinned balance");
  }
  if (buyerCollateralPltr > integer(inputs.actors.buyer.pltrBalance, "buyer PLTR balance")) {
    throw new Error("buyer PLTR cap exceeds the pinned balance");
  }
  if (buyerCollateralWeth > wrapNative) {
    throw new Error("buyer WETH collateral exceeds the proposed native wrap");
  }
  const buyerNativeAfterWrap = integer(inputs.actors.buyer.nativeBalanceWei, "buyer native balance") - wrapNative;
  if (buyerNativeAfterWrap < integer(inputs.proposedExposure.nativeReserveFloorsBeforeGas.buyerAfterWrap, "buyer native reserve")) {
    throw new Error("buyer native reserve would fall below the proposal floor");
  }
  if (integer(inputs.actors.writer.nativeBalanceWei, "writer native balance") < integer(inputs.proposedExposure.nativeReserveFloorsBeforeGas.writer, "writer native reserve")) {
    throw new Error("writer native reserve is below the proposal floor");
  }

  const transactions: TransactionIntent[] = [];
  const add = (
    phase: string,
    sender: Address,
    label: string,
    to: Address,
    calldata: Hex,
    decodedIntent: JsonObject,
    mandatoryPostconditions: string[],
    value = 0n,
  ): void => {
    transactions.push(
      transaction(
        transactions.length,
        phase,
        sender,
        label,
        to,
        calldata,
        decodedIntent,
        mandatoryPostconditions,
        value,
      ),
    );
  };

  add(
    "BUYER_FUNDING",
    buyer,
    "buyer wraps bounded native ETH for WETH collateral",
    weth,
    encodeFunctionData({ abi: wethAbi, functionName: "deposit" }),
    { function: "deposit()", wrapNativeWei: wrapNative.toString() },
    ["buyer WETH increases by exactly valueWei", "buyer native reserve remains above the frozen floor"],
    wrapNative,
  );

  add(
    "WRITER_SWAP_PERMISSIONS",
    writer,
    "writer approves exact total PLTR swap budget to Permit2",
    pltr,
    approveErc20(permit2, pltrSwapTotal),
    { function: "approve(address,uint256)", spender: permit2, amount: pltrSwapTotal.toString() },
    ["PLTR ERC20 allowance equals the exact total swap budget and no more"],
  );
  add(
    "WRITER_SWAP_PERMISSIONS",
    writer,
    "writer approves exact total WETH swap budget to Permit2",
    weth,
    approveErc20(permit2, wethSwapTotal),
    { function: "approve(address,uint256)", spender: permit2, amount: wethSwapTotal.toString() },
    ["WETH ERC20 allowance equals the exact total swap budget and no more"],
  );
  add(
    "WRITER_SWAP_PERMISSIONS",
    writer,
    "writer grants exact PLTR Permit2 allowance to UniversalRouter",
    permit2,
    approvePermit2(pltr, router, pltrSwapTotal, expiry),
    {
      function: "approve(address,address,uint160,uint48)",
      token: pltr,
      spender: router,
      amount: pltrSwapTotal.toString(),
      expiration: expiry.toString(),
    },
    ["Permit2 PLTR allowance equals the exact total budget and rehearsal-only expiry"],
  );
  add(
    "WRITER_SWAP_PERMISSIONS",
    writer,
    "writer grants exact WETH Permit2 allowance to UniversalRouter",
    permit2,
    approvePermit2(weth, router, wethSwapTotal, expiry),
    {
      function: "approve(address,address,uint160,uint48)",
      token: weth,
      spender: router,
      amount: wethSwapTotal.toString(),
      expiration: expiry.toString(),
    },
    ["Permit2 WETH allowance equals the exact total budget and rehearsal-only expiry"],
  );

  const addSwap = (
    phase: string,
    zeroForOne: boolean,
    amountIn: bigint,
    minimumOut: bigint,
    label: string,
  ): void => {
    const tokenIn = zeroForOne ? pltr : weth;
    const tokenOut = zeroForOne ? weth : pltr;
    const swap = buildRobinhoodV4ExactInputSingleCalldata({
      poolKey,
      zeroForOne,
      amountIn,
      amountOutMinimum: minimumOut,
      deadline: expiry,
      minHopPriceX36: 0n,
    });
    add(
      phase,
      writer,
      label,
      router,
      swap.data,
      {
        function: "execute(bytes,bytes[],uint256)",
        route: "UNISWAP_V4_EXACT_INPUT_SINGLE",
        poolId: genesis.market.poolId,
        zeroForOne,
        tokenIn,
        tokenOut,
        amountIn: amountIn.toString(),
        amountOutMinimum: minimumOut.toString(),
        minHopPriceX36: "0",
        deadline: expiry.toString(),
      },
      [
        "receipt contains the exact PoolId swap event",
        "input spend does not exceed amountIn",
        "output received is at least amountOutMinimum",
        "tick and sqrtPrice move in the expected direction",
      ],
      swap.value,
    );
  };

  addSwap("BIDIRECTIONAL_BASELINE", true, perPltrSwap, minWethOut, "writer swaps tiny exact-input PLTR to WETH");
  addSwap("BIDIRECTIONAL_BASELINE", false, perWethSwap, minPltrOut, "writer swaps tiny exact-input WETH to PLTR");

  const addCollateralPair = (
    sender: Address,
    role: "writer" | "buyer",
    pltrAssets: bigint,
    wethAssets: bigint,
  ): void => {
    add(
      "BOUNDED_COLLATERAL",
      sender,
      `${role} approves exact PLTR collateral to tracker0`,
      pltr,
      approveErc20(tracker0, pltrAssets),
      { function: "approve(address,uint256)", spender: tracker0, amount: pltrAssets.toString() },
      ["PLTR allowance to tracker0 equals the next deposit and no more"],
    );
    add(
      "BOUNDED_COLLATERAL",
      sender,
      `${role} deposits exact PLTR collateral`,
      tracker0,
      depositCollateral(pltrAssets, sender),
      { function: "deposit(uint256,address)", assets: pltrAssets.toString(), receiver: sender },
      ["tracker0 shares and assets increase by previewDeposit/asset deltas", "PLTR allowance to tracker0 is zero after transferFrom"],
    );
    add(
      "BOUNDED_COLLATERAL",
      sender,
      `${role} approves exact WETH collateral to tracker1`,
      weth,
      approveErc20(tracker1, wethAssets),
      { function: "approve(address,uint256)", spender: tracker1, amount: wethAssets.toString() },
      ["WETH allowance to tracker1 equals the next deposit and no more"],
    );
    add(
      "BOUNDED_COLLATERAL",
      sender,
      `${role} deposits exact WETH collateral`,
      tracker1,
      depositCollateral(wethAssets, sender),
      { function: "deposit(uint256,address)", assets: wethAssets.toString(), receiver: sender },
      ["tracker1 shares and assets increase by previewDeposit/asset deltas", "WETH allowance to tracker1 is zero after transferFrom"],
    );
  };

  addCollateralPair(writer, "writer", writerCollateralPltr, writerCollateralWeth);
  addCollateralPair(buyer, "buyer", buyerCollateralPltr, buyerCollateralWeth);

  add(
    "MATCHED_OPTION_OPEN",
    writer,
    "writer opens bounded in-range short call",
    pool,
    dispatch(
      shortTokenId,
      [shortTokenId],
      shortSize,
      effectiveLiquidityLimitBps,
      usePremia,
      builderCode,
    ),
    {
      function: "dispatch(uint256[],uint256[],uint128[],int24[3][],bool,uint256)",
      operation: "OPEN_SHORT_CALL",
      tokenId: shortTokenId.toString(),
      finalPositionIdList: [shortTokenId.toString()],
      positionSize: shortSize.toString(),
      tickAndSpreadLimits: [[MIN_TICK, MAX_TICK, effectiveLiquidityLimitBps]],
      usePremiaAsCollateral: usePremia,
      builderCode: builderCode.toString(),
    },
    ["writer owns exactly one leg with the planned TokenId and size", "writer remains solvent at every verifier tick"],
  );
  add(
    "MATCHED_OPTION_OPEN",
    buyer,
    "buyer opens bounded matched long call",
    pool,
    dispatch(
      longTokenId,
      [longTokenId],
      longSize,
      effectiveLiquidityLimitBps,
      usePremia,
      builderCode,
    ),
    {
      function: "dispatch(uint256[],uint256[],uint128[],int24[3][],bool,uint256)",
      operation: "OPEN_LONG_CALL",
      tokenId: longTokenId.toString(),
      finalPositionIdList: [longTokenId.toString()],
      positionSize: longSize.toString(),
      tickAndSpreadLimits: [[MIN_TICK, MAX_TICK, effectiveLiquidityLimitBps]],
      usePremiaAsCollateral: usePremia,
      builderCode: builderCode.toString(),
    },
    ["buyer owns exactly one leg with the matched chunk and planned size", "buyer and writer remain solvent"],
  );

  addSwap("PREMIUM_OBSERVATION", true, perPltrSwap, minWethOut, "writer performs controlled PLTR-to-WETH premium-driving swap");
  addSwap("PREMIUM_OBSERVATION", false, perWethSwap, minPltrOut, "writer performs controlled WETH-to-PLTR premium-driving swap");

  add(
    "ORDERED_CLOSE",
    buyer,
    "buyer closes matched long call before writer",
    pool,
    dispatch(
      longTokenId,
      [],
      0n,
      effectiveLiquidityLimitBps,
      usePremia,
      builderCode,
    ),
    {
      function: "dispatch(uint256[],uint256[],uint128[],int24[3][],bool,uint256)",
      operation: "CLOSE_LONG_CALL",
      tokenId: longTokenId.toString(),
      finalPositionIdList: [],
      positionSize: "0",
    },
    ["buyer has zero open legs", "premium and collateral deltas reconcile", "writer remains solvent before its close"],
  );
  add(
    "ORDERED_CLOSE",
    writer,
    "writer closes short call after buyer",
    pool,
    dispatch(
      shortTokenId,
      [],
      0n,
      effectiveLiquidityLimitBps,
      usePremia,
      builderCode,
    ),
    {
      function: "dispatch(uint256[],uint256[],uint128[],int24[3][],bool,uint256)",
      operation: "CLOSE_SHORT_CALL",
      tokenId: shortTokenId.toString(),
      finalPositionIdList: [],
      positionSize: "0",
    },
    ["writer has zero open legs", "SFPM balances and premium deltas reconcile", "both actors become eligible for standard maxWithdraw"],
  );

  add(
    "SWAP_PERMISSION_CLEANUP",
    writer,
    "writer revokes PLTR Permit2 allowance to UniversalRouter",
    permit2,
    approvePermit2(pltr, router, 0n, 0n),
    { function: "approve(address,address,uint160,uint48)", token: pltr, spender: router, amount: "0", expiration: "0" },
    ["Permit2 PLTR allowance amount is zero"],
  );
  add(
    "SWAP_PERMISSION_CLEANUP",
    writer,
    "writer revokes WETH Permit2 allowance to UniversalRouter",
    permit2,
    approvePermit2(weth, router, 0n, 0n),
    { function: "approve(address,address,uint160,uint48)", token: weth, spender: router, amount: "0", expiration: "0" },
    ["Permit2 WETH allowance amount is zero"],
  );
  add(
    "SWAP_PERMISSION_CLEANUP",
    writer,
    "writer clears PLTR ERC20 allowance to Permit2",
    pltr,
    approveErc20(permit2, 0n),
    { function: "approve(address,uint256)", spender: permit2, amount: "0" },
    ["PLTR ERC20 allowance to Permit2 is zero"],
  );
  add(
    "SWAP_PERMISSION_CLEANUP",
    writer,
    "writer clears WETH ERC20 allowance to Permit2",
    weth,
    approveErc20(permit2, 0n),
    { function: "approve(address,uint256)", spender: permit2, amount: "0" },
    ["WETH ERC20 allowance to Permit2 is zero"],
  );

  const nonceCounts = transactions.reduce<Record<string, number>>((counts, item) => {
    counts[item.sender] = (counts[item.sender] ?? 0) + 1;
    return counts;
  }, {});

  const planBody = {
    schemaVersion: 1,
    status: "OFFLINE_LIFECYCLE_PROPOSAL_OWNER_ACCEPTANCE_REQUIRED_NO_EXECUTION_AUTHORITY",
    mode: "PUBLISHED_SDK_TOKEN_IDS_RUNTIME_BOUND_ROBINHOOD_SWAP_ENCODING_NO_RPC_NO_KEYS_NO_SIGNING_NO_BROADCAST",
    classification: inputs.classification,
    warning: "This proposal uses valueless testnet assets and a synthetic mechanism-test price. It is not a live equity quote, issuer endorsement, audit, mainnet readiness statement, or transaction authorization.",
    network: inputs.network,
    sourceBindings: {
      genesisManifest: relativePath(paths.genesis),
      genesisManifestSha256: fileSha256(paths.genesis),
      chainManifest: relativePath(paths.chain),
      chainManifestSha256: fileSha256(paths.chain),
      lifecycleInputs: relativePath(paths.inputs),
      lifecycleInputsSha256: fileSha256(paths.inputs),
      planner: relativePath(scriptPath),
      plannerSha256: fileSha256(scriptPath),
      robinhoodSwapAdapter: relativePath(swapAdapterPath),
      robinhoodSwapAdapterSha256: fileSha256(swapAdapterPath),
      packageLock: relativePath(packageLockPath),
      packageLockSha256: fileSha256(packageLockPath),
      panopticSdkVersion: packageJson.devDependencies["@panoptic-eng/sdk"],
      viemVersion: packageJson.devDependencies.viem,
      robinhoodUniversalRouterRuntimeHash: ROBINHOOD_UNIVERSAL_ROUTER_RUNTIME_HASH,
      robinhoodV4PeripherySourceCommit: ROBINHOOD_V4_PERIPHERY_SOURCE_COMMIT,
      coreDeploymentSourceCommit: "f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d",
      localLifecycleProofCommit: "cfaf42c29b5c59304540e2a31e24daee4d977797",
    },
    market: {
      symbol: "PLTR/WETH",
      pltr,
      weth,
      poolKey: genesis.market.poolKey,
      poolId: genesis.market.poolId,
      sfpmPoolId: derivedSfpmPoolId.toString(),
      panopticPool: pool,
      collateralTracker0: tracker0,
      collateralTracker1: tracker1,
      permit2,
      universalRouter: router,
      stateView,
      stockRegistry,
      referenceTick: inputs.marketState.currentTick,
      referenceTwapTick: inputs.marketState.twapTick,
      referenceActiveLiquidity: inputs.marketState.activeLiquidity,
    },
    roles: {
      writer: { ...inputs.actors.writer, address: writer },
      buyer: { ...inputs.actors.buyer, address: buyer },
      privilegedBuyerRisk: inputs.roleRisk,
    },
    exposureCaps: inputs.proposedExposure,
    tokenIds: {
      encoding: "PUBLISHED_@panoptic-eng/sdk_V4_POOL_ID_AND_SINGLE_CALL_LEG",
      shortCall: shortTokenId.toString(),
      longCall: longTokenId.toString(),
      shortDecoded: jsonSafe(decodedShort),
      longDecoded: jsonSafe(decodedLong),
      matchedChunk: {
        asset: option.asset,
        tokenType: option.tokenType,
        strike: option.strike,
        width: option.width,
        tickLower: option.tickLower,
        tickUpper: option.tickUpper,
      },
    },
    transactionCount: transactions.length,
    transactionCountsBySender: nonceCounts,
    transactions,
    postCloseContinuation: {
      includedInThisProposal: false,
      reason: "Exact recoverable assets are state-dependent after premium settlement and both closes.",
      requiredSteps: [
        "reconcile both actors at the canonical close block",
        "read maxWithdraw, assetsOf, balances, shares, and every remaining allowance",
        "generate a new bounded withdrawal-only continuation whose calldata is bound to those post-close values",
        "withdraw recoverable collateral one transaction at a time",
        "verify zero open legs, bounded residuals, and zero temporary allowances",
      ],
      authorizationRule: "The withdrawal continuation requires its own exact simulation, review, and hash-bound authorization.",
    },
    negativeRehearsalCases: [
      "wrong chain ID or PoolId",
      "runtime or immutable-wiring drift",
      "paused or blocked Stock Token actor",
      "changed UI multiplier state",
      "same writer and buyer address",
      "actor balance below a frozen cap or native reserve floor",
      "allowance above the exact proposal cap",
      "expired swap deadline or Permit2 expiry",
      "swap output below the proposal minimum",
      "TokenId pool, token orientation, strike, width, or long/short bit mismatch",
      "unexpected position list, leg count, premium, solvency, receipt event, or post-state",
    ],
    requiredForkReverts: [
      "writer option open before collateral deposits",
      "expired UniversalRouter swap deadline",
      "buyer long with zero effective-liquidity tolerance",
      "writer short close while the matched buyer long remains open",
    ],
    authorization: inputs.authorization,
    publicExecution: {
      ready: false,
      blockingReasons: [
        "the owner has not accepted the exact roles and exposure caps",
        "all nonces are deliberately null",
        "the deadline and Permit2 expiry are rehearsal-only",
        "an exact-head positive replay and required negative cases are not yet attached",
        "no lifecycle verifier, one-step operator, authorization manifest, signing path, or broadcast authority exists",
      ],
    },
    nextGate: "EXACT_HEAD_FORK_REHEARSAL_THEN_OWNER_REVIEW_OF_ROLES_AND_EXPOSURE",
  } as JsonObject;

  return {
    ...planBody,
    planBodySha256: canonicalSha256(planBody as Json),
  };
}

function parseArguments(argv: string[]): { paths: PlanPaths; output: string } {
  const values: Record<string, string> = {};
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flag?.startsWith("--") || value === undefined) {
      throw new Error("arguments must be --flag value pairs");
    }
    values[flag] = value;
  }
  const allowed = new Set(["--genesis", "--chain", "--inputs", "--output"]);
  for (const flag of Object.keys(values)) {
    if (!allowed.has(flag)) throw new Error(`unsupported argument: ${flag}`);
  }
  return {
    paths: {
      genesis: resolve(values["--genesis"] ?? DEFAULT_GENESIS),
      chain: resolve(values["--chain"] ?? DEFAULT_CHAIN),
      inputs: resolve(values["--inputs"] ?? DEFAULT_INPUTS),
    },
    output: resolve(values["--output"] ?? DEFAULT_OUTPUT),
  };
}

function main(): void {
  const { paths, output } = parseArguments(process.argv.slice(2));
  const plan = buildPlan(paths);
  writeFileSync(output, `${JSON.stringify(plan, null, 2)}\n`, "utf8");
  process.stdout.write(
    `${JSON.stringify(
      {
        status: plan.status,
        output: relativePath(output),
        planBodySha256: plan.planBodySha256,
        transactionCount: plan.transactionCount,
        signing: false,
        publicBroadcast: false,
        nextGate: plan.nextGate,
      },
      null,
      2,
    )}\n`,
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main();
}
