import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import {
  buildPlan,
  canonicalSha256,
  DEFAULT_CHAIN,
  DEFAULT_GENESIS,
  DEFAULT_INPUTS,
  DEFAULT_OUTPUT,
} from "../scripts/prepare_robinhood_two_actor_lifecycle_plan";

const REPOSITORY = resolve(import.meta.dirname, "..");
const SCRIPT = resolve(
  REPOSITORY,
  "scripts/prepare_robinhood_two_actor_lifecycle_plan.ts",
);
const PACKAGE_JSON = resolve(REPOSITORY, "package.json");
const PACKAGE_LOCK = resolve(REPOSITORY, "package-lock.json");

const temporaryDirectories: string[] = [];

afterEach(() => {
  while (temporaryDirectories.length > 0) {
    rmSync(temporaryDirectories.pop()!, { recursive: true, force: true });
  }
});

function committedPlan() {
  return buildPlan({
    genesis: DEFAULT_GENESIS,
    chain: DEFAULT_CHAIN,
    inputs: DEFAULT_INPUTS,
    script: SCRIPT,
    packageJson: PACKAGE_JSON,
    packageLock: PACKAGE_LOCK,
  });
}

function mutateInputs(mutator: (value: any) => void): string {
  const directory = mkdtempSync(join(tmpdir(), "stonkhedge-lifecycle-"));
  temporaryDirectories.push(directory);
  const output = join(directory, "inputs.json");
  const value = JSON.parse(readFileSync(DEFAULT_INPUTS, "utf8"));
  mutator(value);
  writeFileSync(output, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  return output;
}

describe("two-actor lifecycle proposal", () => {
  it("uses published-SDK golden vectors for the exact V4 market and matched call chunk", () => {
    const plan = committedPlan();

    expect(plan.market.poolId).toBe(
      "0xd600fd2ff936078114b72a01d3c6d31d449b7af12c24c82fb61efb7bf9c613ae",
    );
    expect(plan.market.sfpmPoolId).toBe("16897827167146926");
    expect(plan.tokenIds.shortCall).toBe("3797733774652686947289370334126");
    expect(plan.tokenIds.longCall).toBe("3797733779375053430159015547822");
    expect(plan.tokenIds.shortDecoded).toMatchObject({
      poolId: "0x003c087bf9c613ae",
      vegoid: "8",
      tickSpacing: "60",
      legCount: "1",
      legs: [
        {
          asset: "0",
          optionRatio: "1",
          isLong: false,
          tokenType: "0",
          strike: "-69060",
          width: "2",
          tickLower: "-69120",
          tickUpper: "-69000",
        },
      ],
    });
    expect(plan.tokenIds.longDecoded.legs[0].isLong).toBe(true);
  });

  it("is deterministic, hash-bound, nonce-free, and carries no execution authority", () => {
    const first = committedPlan();
    const second = committedPlan();

    expect(first).toEqual(second);
    expect(first.status).toBe(
      "OFFLINE_LIFECYCLE_PROPOSAL_OWNER_ACCEPTANCE_REQUIRED_NO_EXECUTION_AUTHORITY",
    );
    expect(first.planBodySha256).toBe(
      canonicalSha256(
        Object.fromEntries(
          Object.entries(first).filter(([key]) => key !== "planBodySha256"),
        ),
      ),
    );
    expect(Object.values(first.authorization).every((value) => value === false)).toBe(true);
    expect(first.publicExecution.ready).toBe(false);
    expect(first.transactions.every((transaction: any) => transaction.nonce === null)).toBe(true);
    expect(first.transactions.every((transaction: any) => transaction.valueWei !== undefined)).toBe(true);
    expect(first.transactions).toHaveLength(25);
    expect(first.transactions.map((transaction: any) => transaction.ordinal)).toEqual(
      Array.from({ length: 25 }, (_, index) => index),
    );
  });

  it("binds each calldata hash and exact ordered lifecycle phase", () => {
    const plan = committedPlan();
    const labels = plan.transactions.map((transaction: any) => transaction.label);

    expect(labels).toEqual([
      "buyer wraps bounded native ETH for WETH collateral",
      "writer approves exact total PLTR swap budget to Permit2",
      "writer approves exact total WETH swap budget to Permit2",
      "writer grants exact PLTR Permit2 allowance to UniversalRouter",
      "writer grants exact WETH Permit2 allowance to UniversalRouter",
      "writer swaps tiny exact-input PLTR to WETH",
      "writer swaps tiny exact-input WETH to PLTR",
      "writer approves exact PLTR collateral to tracker0",
      "writer deposits exact PLTR collateral",
      "writer approves exact WETH collateral to tracker1",
      "writer deposits exact WETH collateral",
      "buyer approves exact PLTR collateral to tracker0",
      "buyer deposits exact PLTR collateral",
      "buyer approves exact WETH collateral to tracker1",
      "buyer deposits exact WETH collateral",
      "writer opens bounded in-range short call",
      "buyer opens bounded matched long call",
      "writer performs controlled PLTR-to-WETH premium-driving swap",
      "writer performs controlled WETH-to-PLTR premium-driving swap",
      "buyer closes matched long call before writer",
      "writer closes short call after buyer",
      "writer revokes PLTR Permit2 allowance to UniversalRouter",
      "writer revokes WETH Permit2 allowance to UniversalRouter",
      "writer clears PLTR ERC20 allowance to Permit2",
      "writer clears WETH ERC20 allowance to Permit2",
    ]);
    for (const transaction of plan.transactions) {
      expect(transaction.calldata).toMatch(/^0x[0-9a-f]+$/);
      expect(transaction.calldataKeccak256).toMatch(/^0x[0-9a-f]{64}$/);
      expect(transaction.mandatoryPostconditions.length).toBeGreaterThan(0);
    }
    expect(plan.transactionCountsBySender).toEqual({
      "0x04d5a0f57cb2e110fac9703024888cd4562b6d6f": 18,
      "0xca60c8ef6934f8a97c6a503c4e3a46e87f5b08bd": 7,
    });
  });

  it("uses exact bounded allowances and defers state-dependent withdrawals", () => {
    const plan = committedPlan();
    const approvals = plan.transactions.filter((transaction: any) =>
      transaction.decodedIntent.function.startsWith("approve("),
    );

    expect(approvals.every((transaction: any) => transaction.decodedIntent.amount !== undefined)).toBe(true);
    expect(approvals.some((transaction: any) => transaction.decodedIntent.amount === (2n ** 256n - 1n).toString())).toBe(false);
    expect(plan.postCloseContinuation.includedInThisProposal).toBe(false);
    expect(plan.postCloseContinuation.requiredSteps).toContain(
      "generate a new bounded withdrawal-only continuation whose calldata is bound to those post-close values",
    );
    expect(
      plan.transactions.some((transaction: any) =>
        transaction.decodedIntent.function.startsWith("withdraw("),
      ),
    ).toBe(false);
    expect(plan.exposureCaps.option.effectiveLiquidityLimitBps).toBe(2_000);
    expect(plan.transactions[15].decodedIntent.tickAndSpreadLimits).toEqual([
      [-887_272, 887_272, 2_000],
    ]);
    expect(plan.transactions[16].decodedIntent.tickAndSpreadLimits).toEqual([
      [-887_272, 887_272, 2_000],
    ]);
    expect(plan.requiredForkReverts).toEqual([
      "writer option open before collateral deposits",
      "expired UniversalRouter swap deadline",
      "buyer long with zero effective-liquidity tolerance",
      "writer short close while the matched buyer long remains open",
    ]);
  });

  it("committed output is the exact generator result with LF and a final newline", () => {
    expect(JSON.parse(readFileSync(DEFAULT_OUTPUT, "utf8"))).toEqual(committedPlan());
    const bytes = readFileSync(DEFAULT_OUTPUT);
    expect(bytes.includes(Buffer.from("\r\n"))).toBe(false);
    expect(bytes.at(-1)).toBe(10);
  });

  it("rejects same-account roles, unhealthy market identity, and cap overruns", () => {
    const sameActor = mutateInputs((value) => {
      value.actors.buyer.address = value.actors.writer.address;
    });
    expect(() =>
      buildPlan({ genesis: DEFAULT_GENESIS, chain: DEFAULT_CHAIN, inputs: sameActor }),
    ).toThrow("writer and buyer must be distinct accounts");

    const wrongPool = mutateInputs((value) => {
      value.marketState.poolId = `0x${"00".repeat(32)}`;
    });
    expect(() =>
      buildPlan({ genesis: DEFAULT_GENESIS, chain: DEFAULT_CHAIN, inputs: wrongPool }),
    ).toThrow("input snapshot PoolId mismatch");

    const excessiveCap = mutateInputs((value) => {
      value.proposedExposure.writerCollateral.pltrAssets = "4000000000000000000";
    });
    expect(() =>
      buildPlan({ genesis: DEFAULT_GENESIS, chain: DEFAULT_CHAIN, inputs: excessiveCap }),
    ).toThrow("writer PLTR caps exceed the pinned balance");

    const zeroSpreadLimit = mutateInputs((value) => {
      value.proposedExposure.option.effectiveLiquidityLimitBps = 0;
    });
    expect(() =>
      buildPlan({ genesis: DEFAULT_GENESIS, chain: DEFAULT_CHAIN, inputs: zeroSpreadLimit }),
    ).toThrow("effective liquidity limit must be within (0, 90000] bps");
  });

  it("has no network, wallet, signing, or submission primitive", () => {
    const source = readFileSync(SCRIPT, "utf8");
    const importedModules = [...source.matchAll(/from\s+["']([^"']+)["']/g)].map(
      (match) => match[1],
    );

    expect(importedModules).toEqual(
      expect.arrayContaining([
        "node:crypto",
        "node:fs",
        "@panoptic-eng/sdk/v2",
        "../src/protocol/robinhoodV4Swap",
        "viem",
      ]),
    );
    expect(importedModules.some((name) => ["node:http", "node:https", "node:net", "node:child_process"].includes(name))).toBe(false);
    for (const primitive of [
      "fetch(",
      "createPublicClient(",
      "createWalletClient(",
      "privateKeyToAccount(",
      "sendRawTransaction(",
      "sendTransaction(",
      "signTransaction(",
      "writeContract(",
    ]) {
      expect(source).not.toContain(primitive);
    }
  });
});
