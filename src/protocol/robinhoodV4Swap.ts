/**
 * Exact-input single-hop encoder for Robinhood's deployed Uniswap Universal Router.
 *
 * The deployed runtime uses the later V4 router tuple that inserts
 * `minHopPriceX36` between `amountOutMinimum` and `hookData`. The published
 * `@panoptic-eng/sdk@1.0.49` swap helper still emits the earlier five-field
 * tuple, so it cannot be used for this specific runtime. TokenId construction
 * continues to use the published Panoptic SDK.
 */

import {
  encodeAbiParameters,
  encodeFunctionData,
  encodePacked,
  type Address,
  type Hex,
} from "viem";

export const ROBINHOOD_UNIVERSAL_ROUTER =
  "0x8876789976decbfcbbbe364623c63652db8c0904" as Address;
export const ROBINHOOD_UNIVERSAL_ROUTER_RUNTIME_HASH =
  "0xfdd90802f39ce5fc8bac4c2f1b3ac7bac530fd17ff46b0630f1bd00f1e14082f" as Hex;
export const ROBINHOOD_V4_PERIPHERY_SOURCE_COMMIT =
  "3779387e5d296f39df543d23524b050f89a62917";

export const V4_SWAP = 0x10;
export const SWAP_EXACT_IN_SINGLE = 0x06;
export const SETTLE_ALL = 0x0c;
export const TAKE_ALL = 0x0f;

const UINT128_MAX = (1n << 128n) - 1n;

const poolKeyComponents = [
  { name: "currency0", type: "address" },
  { name: "currency1", type: "address" },
  { name: "fee", type: "uint24" },
  { name: "tickSpacing", type: "int24" },
  { name: "hooks", type: "address" },
] as const;

const routerExactInputSingleParamsAbi = [
  {
    type: "tuple",
    components: [
      { name: "poolKey", type: "tuple", components: poolKeyComponents },
      { name: "zeroForOne", type: "bool" },
      { name: "amountIn", type: "uint128" },
      { name: "amountOutMinimum", type: "uint128" },
      { name: "minHopPriceX36", type: "uint256" },
      { name: "hookData", type: "bytes" },
    ],
  },
] as const;

const currencyAmountAbi = [
  { name: "currency", type: "address" },
  { name: "amount", type: "uint256" },
] as const;

const universalRouterAbi = [
  {
    type: "function",
    name: "execute",
    stateMutability: "payable",
    inputs: [
      { name: "commands", type: "bytes" },
      { name: "inputs", type: "bytes[]" },
      { name: "deadline", type: "uint256" },
    ],
    outputs: [],
  },
] as const;

export interface RobinhoodPoolKey {
  currency0: Address;
  currency1: Address;
  fee: bigint;
  tickSpacing: bigint;
  hooks: Address;
}

export interface BuildRobinhoodV4SwapArgs {
  poolKey: RobinhoodPoolKey;
  zeroForOne: boolean;
  amountIn: bigint;
  amountOutMinimum: bigint;
  deadline: bigint;
  minHopPriceX36?: bigint;
  hookData?: Hex;
}

function assertUint128(value: bigint, label: string): void {
  if (value < 0n || value > UINT128_MAX) {
    throw new RangeError(`${label} must fit uint128`);
  }
}

/** Encode the six-field single-hop tuple used by the observed Robinhood runtime. */
export function buildRobinhoodV4ExactInputSingleCalldata(
  args: BuildRobinhoodV4SwapArgs,
): { data: Hex; value: bigint } {
  const {
    poolKey,
    zeroForOne,
    amountIn,
    amountOutMinimum,
    deadline,
    minHopPriceX36 = 0n,
    hookData = "0x",
  } = args;
  assertUint128(amountIn, "amountIn");
  assertUint128(amountOutMinimum, "amountOutMinimum");
  if (deadline < 0n || minHopPriceX36 < 0n) {
    throw new RangeError("deadline and minHopPriceX36 must be non-negative");
  }

  const inputCurrency = zeroForOne ? poolKey.currency0 : poolKey.currency1;
  const outputCurrency = zeroForOne ? poolKey.currency1 : poolKey.currency0;
  const swapParam = encodeAbiParameters(routerExactInputSingleParamsAbi, [
    {
      poolKey: {
        currency0: poolKey.currency0,
        currency1: poolKey.currency1,
        fee: Number(poolKey.fee),
        tickSpacing: Number(poolKey.tickSpacing),
        hooks: poolKey.hooks,
      },
      zeroForOne,
      amountIn,
      amountOutMinimum,
      minHopPriceX36,
      hookData,
    },
  ]);
  const settleParam = encodeAbiParameters(currencyAmountAbi, [inputCurrency, amountIn]);
  const takeParam = encodeAbiParameters(currencyAmountAbi, [outputCurrency, amountOutMinimum]);
  const actions = encodePacked(
    ["uint8", "uint8", "uint8"],
    [SWAP_EXACT_IN_SINGLE, SETTLE_ALL, TAKE_ALL],
  );
  const v4Input = encodeAbiParameters(
    [
      { name: "actions", type: "bytes" },
      { name: "params", type: "bytes[]" },
    ],
    [actions, [swapParam, settleParam, takeParam]],
  );
  const commands = encodePacked(["uint8"], [V4_SWAP]);
  return {
    data: encodeFunctionData({
      abi: universalRouterAbi,
      functionName: "execute",
      args: [commands, [v4Input], deadline],
    }),
    value: 0n,
  };
}
