import { createHmac } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import {
  buildSignedPostRequest,
  createBinanceWeb3Client,
  decodeExactErc20Approval,
  parseTransactionSimulation,
} from "../server/binanceWeb3";
import { parseSimulationProofResponse } from "../src/bnb/simulationProof";

const timestamp = "2026-10-09T12:00:00.000Z";
const owner = "0x6719e877c05b2d6c28abcea405fc033feef5750f";
const token = "0x55d398326f99059ff775485246999027b3197955";
const spender = "0xc67879f4065d3b9fe1c09ee990b891aa8e3a4c2f";
const amount = "5100000000000000000";
const approvalData = `0x095ea7b3${spender.slice(2).padStart(64, "0")}${BigInt(amount).toString(16).padStart(64, "0")}`;

describe("BNB simulation-only transaction compiler", () => {
  it("signs the exact POST body bytes and sends no credential in the URL or body", () => {
    const body = JSON.stringify({
      binanceChainId: "56",
      evmTx: { from: owner, to: token, value: "0", data: approvalData },
    });
    const request = buildSignedPostRequest(
      { apiKey: "api-key", secretKey: "top-secret" },
      {
        apiPath: "/api/v1/dex/pre-transaction/simulate",
        body,
        timestamp,
        nonce: "nonce-2",
      },
    );
    const expected = createHmac("sha256", "top-secret")
      .update(`${timestamp}POST/build/api/v1/dex/pre-transaction/simulate${body}`, "utf8")
      .digest("base64");

    expect(request.requestPath).toBe("/build/api/v1/dex/pre-transaction/simulate");
    expect(request.body).toBe(body);
    expect(request.headers).toMatchObject({
      "Content-Type": "application/json",
      "X-OC-APIKEY": "api-key",
      "X-OC-NONCE": "nonce-2",
      "X-OC-SIGN": expected,
    });
    expect(`${request.url}${request.body}`).not.toContain("top-secret");
  });

  it("decodes an exact bounded ERC-20 approval and rejects malformed or inflated calldata", () => {
    expect(decodeExactErc20Approval(approvalData)).toEqual({
      functionName: "approve",
      spender,
      amount,
    });
    expect(() => decodeExactErc20Approval(`0xa9059cbb${approvalData.slice(10)}`)).toThrow(
      "approve selector",
    );
    expect(() => decodeExactErc20Approval(`${approvalData}00`)).toThrow("approve calldata length");

    const unlimited = `0x095ea7b3${spender.slice(2).padStart(64, "0")}${"f".repeat(64)}`;
    expect(decodeExactErc20Approval(unlimited).amount).not.toBe(amount);
  });

  it("strictly parses successful and failed simulation state evidence", () => {
    const success = parseTransactionSimulation({
      status: "SUCCESS",
      failReason: "",
      balanceChanges: [],
      allowanceChanges: [{
        tokenAddress: token,
        owner,
        spender,
        preAmount: "0",
        postAmount: amount,
      }],
    });
    expect(success).toMatchObject({ failReason: null });
    expect(success.allowanceChanges[0]).toMatchObject({ owner, spender, postAmount: amount });

    const failed = parseTransactionSimulation({
      status: "FAILED",
      failReason: "execution reverted: ERC20InsufficientBalance",
      balanceChanges: [],
      allowanceChanges: [],
    });
    expect(failed).toMatchObject({
      status: "FAILED",
      failReason: "execution reverted: ERC20InsufficientBalance",
    });

    expect(() => parseTransactionSimulation({
      status: "UNKNOWN",
      failReason: null,
      balanceChanges: [],
      allowanceChanges: [],
    })).toThrow("simulation status");
  });

  it("accepts only a non-executable public proof envelope", () => {
    const proof = {
      operation: "simulate",
      chainId: 56,
      data: {
        ticker: "NVDA",
        companyName: "Nvidia Corp",
        asset: {
          platformId: "ondo",
          tokenContractAddress: "0xa9ee28c80f960b889dfbd1902055218cba016f75",
          tokenSymbol: "NVDAon",
        },
        sender: owner,
        input: { symbol: "USDT", displayAmount: "5.1", rawAmount: amount },
        route: {
          quoteIdHash: `0x${"11".repeat(32)}`,
          vendorName: "LiquidMesh",
          executionMode: "SWAP",
          expectedOutputRaw: "22000000000000000",
          slippagePercent: "0.5",
        },
        approval: {
          token,
          spender,
          amount,
          transaction: { to: token, value: "0", selector: "0x095ea7b3", calldataHash: `0x${"22".repeat(32)}` },
          simulation: { status: "SUCCESS", failReason: null, balanceChangeCount: 0, allowanceChangeCount: 1 },
        },
        swap: {
          transaction: { from: owner, to: spender, value: "0", selector: "0x12aa3caf", calldataHash: `0x${"33".repeat(32)}` },
          minimumOutputRaw: "21890000000000000",
          simulation: { status: "FAILED", failReason: "ERC20InsufficientBalance", balanceChangeCount: 0, allowanceChangeCount: 0 },
        },
        verdict: "BLOCKED",
        reasons: ["Swap simulation failed"],
        timestamp: 1_791_550_732_585,
      },
      requestId: "request-1",
      boundary: "SIMULATION_ONLY_NO_WALLET_NO_PRIVATE_KEY_NO_SIGNING_NO_BROADCAST",
    };

    expect(parseSimulationProofResponse(proof)).toMatchObject({ verdict: "BLOCKED" });
    const executable = structuredClone(proof) as typeof proof & { data: { swap: { transaction: { data?: string } } } };
    executable.data.swap.transaction.data = approvalData;
    expect(() => parseSimulationProofResponse(executable)).toThrow("executable transaction field");

    const changedSender = structuredClone(proof);
    changedSender.data.swap.transaction.from = "0x1111111111111111111111111111111111111111";
    expect(() => parseSimulationProofResponse(changedSender)).toThrow("swap transaction binding");

    const changedApproval = structuredClone(proof);
    changedApproval.data.approval.transaction.selector = "0xa9059cbb";
    expect(() => parseSimulationProofResponse(changedApproval)).toThrow("approval transaction binding");
  });

  it("keeps every simulation surface free of signing and broadcast primitives", () => {
    const sources = [
      "server/binanceWeb3.ts",
      "api/bnb/rwa.ts",
      "scripts/check_bnb_rwa_simulation.ts",
      "src/bnb/simulationProof.ts",
      "src/main.ts",
    ].map((path) => readFileSync(resolve(process.cwd(), path), "utf8")).join("\n");

    expect(sources).not.toContain("eth_sendRawTransaction");
    expect(sources).not.toContain("/pre-transaction/broadcast");
    expect(sources).not.toContain("privateKeyToAccount");
    expect(sources).not.toContain("createWalletClient");
    expect(sources).not.toContain("signTransaction");
  });

  it("records only non-executable live acceptance evidence", () => {
    const evidence = JSON.parse(readFileSync(resolve(
      process.cwd(),
      "manifests/testing/bnb-gap-guardian-unsigned-simulation-2026-10-09.json",
    ), "utf8")) as {
      boundary: string;
      observations: Array<Record<string, unknown>>;
    };
    const serialized = JSON.stringify(evidence);

    expect(evidence.boundary).toBe(
      "SIMULATION_ONLY_NO_WALLET_NO_PRIVATE_KEY_NO_SIGNING_NO_BROADCAST",
    );
    expect(evidence.observations).toHaveLength(2);
    expect(evidence.observations.map((item) => item.verdict)).toEqual(["BLOCKED", "BLOCKED"]);
    expect(serialized).not.toMatch(/"(?:data|calldata|quoteId|privateKey)"\s*:/u);
  });

  it("binds one fresh quote to an exact approval, swap, and two unsigned simulations", async () => {
    const rwaToken = "0xa9ee28c80f960b889dfbd1902055218cba016f75";
    const swapRouter = "0x1111111254eeb25477b68fb85ed929f73a960582";
    const swapData = "0x12aa3caf00";
    const envelope = (data: unknown, upstreamTimestamp = 1_791_550_732_585) =>
      new Response(JSON.stringify({ code: 0, msg: "success", data, timestamp: upstreamTimestamp, success: true }));
    const tokenShape = (address: string, symbol: string) => ({
      tokenContractAddress: address,
      tokenSymbol: symbol,
      tokenUnitPrice: symbol === "USDT" ? "1" : "192.6",
      decimal: "18",
      isHoneyPot: false,
      taxRate: "0",
    });
    const routeSegments = [{
      dexProtocol: { dexName: "Pancakeswap V4", percent: "100" },
      fromToken: { tokenContractAddress: token, tokenSymbol: "USDT" },
      fromTokenIndex: "0",
      toToken: { tokenContractAddress: rwaToken, tokenSymbol: "NVDAon" },
      toTokenIndex: "1",
    }];
    const fetchMock = async (input: string | URL | Request, init?: RequestInit) => {
      const url = new URL(String(input));
      if (url.pathname.endsWith("/search")) {
        return envelope([{ ticker: "NVDA", companyName: "Nvidia Corp", assets: [{
          platformId: "ondo",
          binanceChainId: "56",
          tokenContractAddress: rwaToken,
          tokenSymbol: "NVDAon",
          assetType: 1,
        }] }]);
      }
      if (url.pathname.endsWith("/quote")) {
        return envelope([{
          quoteId: "quote-bound-1",
          vendorName: "LiquidMesh",
          binanceChainId: "56",
          fromTokenAmount: amount,
          toTokenAmount: "22000000000000000",
          tradeFee: "0.03",
          estimateGasFee: "220000",
          priceImpactPercent: "-0.01",
          router: `${token}--${rwaToken}`,
          fromToken: tokenShape(token, "USDT"),
          toToken: tokenShape(rwaToken, "NVDAon"),
          dexRouterList: routeSegments,
          executionMode: "SWAP",
          approveTarget: spender,
          isBest: true,
          feeAmount: null,
          feeToken: null,
          actualSwapAmount: null,
        }]);
      }
      if (url.pathname.endsWith("/approve-transaction")) {
        expect(url.searchParams.get("approveAmount")).toBe(amount);
        expect(url.searchParams.get("vendor")).toBe("LiquidMesh");
        return envelope([{ data: approvalData, dexContractAddress: spender, gasLimit: "50000", gasPrice: "100000000" }]);
      }
      if (url.pathname.endsWith("/swap")) {
        expect(url.searchParams.get("quoteId")).toBe("quote-bound-1");
        expect(url.searchParams.get("slippagePercent")).toBe("0.5");
        expect(url.searchParams.get("approveTransaction")).toBe("false");
        return envelope({
          routerResult: {
            binanceChainId: "56",
            vendorName: "LiquidMesh",
            fromTokenAmount: amount,
            toTokenAmount: "22000000000000000",
            tradeFee: "0.03",
            estimateGasFee: "220000",
            router: `${token}--${rwaToken}`,
            priceImpactPercent: "-0.01",
            dexRouterList: routeSegments,
            fromToken: tokenShape(token, "USDT"),
            toToken: tokenShape(rwaToken, "NVDAon"),
            feeAmount: null,
            feeToken: null,
            actualSwapAmount: null,
          },
          tx: {
            from: owner,
            to: swapRouter,
            data: swapData,
            value: "0",
            gas: "300000",
            gasPrice: "100000000",
            maxPriorityFeePerGas: "0",
            minReceiveAmount: "21890000000000000",
            slippagePercent: "0.5",
          },
          executionMode: "SWAP",
          rfq: null,
        });
      }
      if (url.pathname.endsWith("/simulate")) {
        expect(init?.method).toBe("POST");
        const body = JSON.parse(String(init?.body)) as { evmTx: { data: string } };
        if (body.evmTx.data === approvalData) {
          return envelope({
            status: "SUCCESS",
            failReason: null,
            balanceChanges: [],
            allowanceChanges: [{ tokenAddress: token, owner, spender, preAmount: "0", postAmount: amount }],
          });
        }
        expect(body.evmTx.data).toBe(swapData);
        return envelope({
          status: "FAILED",
          failReason: "execution reverted: ERC20InsufficientBalance",
          balanceChanges: [],
          allowanceChanges: [],
        });
      }
      return new Response("not found", { status: 404 });
    };
    const client = createBinanceWeb3Client({
      apiKey: "api-key",
      secretKey: "top-secret",
      fetchImplementation: fetchMock,
      now: () => new Date(timestamp),
      nonce: () => "nonce",
    });

    const proof = await client.simulateRwaSwap({
      keyword: "NVDA",
      tokenContractAddress: rwaToken,
      userWalletAddress: owner,
      usdtAmount: "5.1",
    });
    expect(proof).toMatchObject({
      sender: owner,
      verdict: "BLOCKED",
      approval: { amount, spender, simulation: { status: "SUCCESS" } },
      swap: { simulation: { status: "FAILED" } },
    });
    expect(JSON.stringify(proof)).not.toContain(approvalData);
    expect(JSON.stringify(proof)).not.toContain(swapData);
  });
});
