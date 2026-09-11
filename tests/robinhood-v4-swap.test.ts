import { buildV4SwapExecuteCalldata as buildPublishedSdkSwap } from "@panoptic-eng/sdk/uniswap";
import {
  decodeAbiParameters,
  decodeFunctionData,
  keccak256,
  type Address,
} from "viem";
import { describe, expect, it } from "vitest";

import {
  buildRobinhoodV4ExactInputSingleCalldata,
  ROBINHOOD_UNIVERSAL_ROUTER,
  ROBINHOOD_UNIVERSAL_ROUTER_RUNTIME_HASH,
  ROBINHOOD_V4_PERIPHERY_SOURCE_COMMIT,
} from "../src/protocol/robinhoodV4Swap";

const poolKey = {
  currency0: "0x1fbe1a0e43594b3455993b5de5fd0a7a266298d0" as Address,
  currency1: "0x33e4191705c386532ba27cbf171db86919200b94" as Address,
  fee: 3000n,
  tickSpacing: 60n,
  hooks: "0x0000000000000000000000000000000000000000" as Address,
};

const executeAbi = [
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

const poolKeyComponents = [
  { name: "currency0", type: "address" },
  { name: "currency1", type: "address" },
  { name: "fee", type: "uint24" },
  { name: "tickSpacing", type: "int24" },
  { name: "hooks", type: "address" },
] as const;

describe("Robinhood Universal Router exact-input adapter", () => {
  it("binds the exact observed runtime and pinned v4-periphery source", () => {
    expect(ROBINHOOD_UNIVERSAL_ROUTER).toBe(
      "0x8876789976decbfcbbbe364623c63652db8c0904",
    );
    expect(ROBINHOOD_UNIVERSAL_ROUTER_RUNTIME_HASH).toBe(
      "0xfdd90802f39ce5fc8bac4c2f1b3ac7bac530fd17ff46b0630f1bd00f1e14082f",
    );
    expect(ROBINHOOD_V4_PERIPHERY_SOURCE_COMMIT).toBe(
      "3779387e5d296f39df543d23524b050f89a62917",
    );
  });

  it("encodes the later six-field single-hop tuple and stable calldata hash", () => {
    const result = buildRobinhoodV4ExactInputSingleCalldata({
      poolKey,
      zeroForOne: true,
      amountIn: 1_000_000_000_000_000n,
      amountOutMinimum: 800_000_000_000n,
      minHopPriceX36: 0n,
      deadline: 1_790_000_000n,
    });
    const decodedExecute = decodeFunctionData({ abi: executeAbi, data: result.data });
    expect(decodedExecute.functionName).toBe("execute");
    const [commands, inputs, deadline] = decodedExecute.args;
    expect(commands).toBe("0x10");
    expect(deadline).toBe(1_790_000_000n);
    expect(result.value).toBe(0n);

    const [actions, params] = decodeAbiParameters(
      [
        { name: "actions", type: "bytes" },
        { name: "params", type: "bytes[]" },
      ],
      inputs[0],
    );
    expect(actions).toBe("0x060c0f");
    expect(params).toHaveLength(3);

    const [swap] = decodeAbiParameters(
      [
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
      ],
      params[0],
    );
    expect(swap).toMatchObject({
      zeroForOne: true,
      amountIn: 1_000_000_000_000_000n,
      amountOutMinimum: 800_000_000_000n,
      minHopPriceX36: 0n,
      hookData: "0x",
    });
    expect(swap.poolKey.currency0.toLowerCase()).toBe(poolKey.currency0);
    expect(swap.poolKey.currency1.toLowerCase()).toBe(poolKey.currency1);
    expect(swap.poolKey).toMatchObject({
      fee: 3000,
      tickSpacing: 60,
      hooks: poolKey.hooks,
    });
    expect(keccak256(result.data)).toBe(
      "0x141ca9e939a9037d7fa14d20187642d30eec0867d43e9321d620d96eb7bedb87",
    );
  });

  it("does not silently reuse the incompatible five-field SDK swap payload", () => {
    const robinhood = buildRobinhoodV4ExactInputSingleCalldata({
      poolKey,
      zeroForOne: true,
      amountIn: 1_000_000_000_000_000n,
      amountOutMinimum: 800_000_000_000n,
      deadline: 1_790_000_000n,
    });
    const published = buildPublishedSdkSwap({
      poolKey,
      zeroForOne: true,
      amountIn: 1_000_000_000_000_000n,
      amountOutMinimum: 800_000_000_000n,
      tokenIn: poolKey.currency0,
      tokenOut: poolKey.currency1,
      deadline: 1_790_000_000n,
    });

    expect(robinhood.data).not.toBe(published.data);
    expect(keccak256(robinhood.data)).not.toBe(keccak256(published.data));
  });

  it("rejects values outside uint128", () => {
    expect(() =>
      buildRobinhoodV4ExactInputSingleCalldata({
        poolKey,
        zeroForOne: true,
        amountIn: 1n << 128n,
        amountOutMinimum: 0n,
        deadline: 1_790_000_000n,
      }),
    ).toThrow("amountIn must fit uint128");
  });
});
