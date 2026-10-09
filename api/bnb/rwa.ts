import { randomUUID } from "node:crypto";
import type { IncomingMessage, ServerResponse } from "node:http";

import {
  BinanceWeb3Error,
  createBinanceWeb3ClientFromEnv,
} from "../../server/binanceWeb3";

const WINDOW_MS = 60_000;
const REQUESTS_PER_WINDOW = 30;
const requestWindows = new Map<string, { count: number; resetAt: number }>();

interface PublicError {
  error: string;
  message: string;
  requestId: string;
}

function sendJson(
  response: ServerResponse,
  status: number,
  body: unknown,
): void {
  response.statusCode = status;
  response.setHeader("Content-Type", "application/json; charset=utf-8");
  response.setHeader("Cache-Control", "private, no-store, max-age=0");
  response.setHeader("X-Content-Type-Options", "nosniff");
  response.end(JSON.stringify(body));
}

function getClientIdentifier(request: IncomingMessage): string {
  const forwarded = request.headers["x-forwarded-for"];
  if (typeof forwarded === "string") return forwarded.split(",")[0]?.trim() || "unknown";
  if (Array.isArray(forwarded)) return forwarded[0] ?? "unknown";
  return request.socket.remoteAddress ?? "unknown";
}

function consumeRateLimit(identifier: string, now = Date.now()): boolean {
  if (requestWindows.size > 1_000) {
    for (const [key, value] of requestWindows) {
      if (value.resetAt <= now) requestWindows.delete(key);
    }
  }
  const current = requestWindows.get(identifier);
  if (!current || current.resetAt <= now) {
    requestWindows.set(identifier, { count: 1, resetAt: now + WINDOW_MS });
    return true;
  }
  if (current.count >= REQUESTS_PER_WINDOW) return false;
  current.count += 1;
  return true;
}

function publicError(error: unknown, requestId: string): { status: number; body: PublicError } {
  if (error instanceof BinanceWeb3Error) {
    if (error.kind === "not_found") {
      return {
        status: 404,
        body: {
          error: "RWA_NOT_FOUND",
          message: error.message,
          requestId,
        },
      };
    }
    if (error.kind === "configuration") {
      const missingCredentials = error.message.includes("not configured");
      return {
        status: missingCredentials ? 503 : 400,
        body: {
          error: missingCredentials ? "BINANCE_WEB3_NOT_CONFIGURED" : "INVALID_REQUEST",
          message: error.message,
          requestId,
        },
      };
    }
    return {
      status: error.kind === "timeout" ? 504 : 502,
      body: {
        error: error.kind === "timeout" ? "UPSTREAM_TIMEOUT" : "UPSTREAM_ERROR",
        message:
          error.kind === "timeout"
            ? "The Binance Web3 request timed out"
            : `Binance Web3 could not complete the request${error.code === undefined ? "" : ` (code ${error.code})`}`,
        requestId,
      },
    };
  }
  return {
    status: 500,
    body: {
      error: "INTERNAL_ERROR",
      message: "The RWA request could not be completed",
      requestId,
    },
  };
}

export default async function handler(
  request: IncomingMessage,
  response: ServerResponse,
): Promise<void> {
  const requestId = randomUUID();
  if (request.method !== "GET") {
    response.setHeader("Allow", "GET");
    sendJson(response, 405, {
      error: "METHOD_NOT_ALLOWED",
      message: "Only GET is supported",
      requestId,
    });
    return;
  }

  if (!consumeRateLimit(getClientIdentifier(request))) {
    response.setHeader("Retry-After", "60");
    sendJson(response, 429, {
      error: "RATE_LIMITED",
      message: "Too many RWA requests; retry after one minute",
      requestId,
    });
    return;
  }

  try {
    const url = new URL(request.url ?? "/", "https://stonkhedge.invalid");
    const operation = url.searchParams.get("operation") ?? "platforms";
    const platform = url.searchParams.get("platform") ?? undefined;
    const client = createBinanceWeb3ClientFromEnv();

    if (operation === "platforms") {
      const result = await client.getRwaPlatforms(platform);
      sendJson(response, 200, {
        operation,
        chainId: 56,
        ...result,
        requestId,
      });
      return;
    }

    if (operation === "search") {
      const keyword = url.searchParams.get("q") ?? "";
      const result = await client.searchRwaTokens(keyword, platform);
      sendJson(response, 200, {
        operation,
        chainId: 56,
        data: client.filterBscAssets(result.data),
        timestamp: result.timestamp,
        requestId,
      });
      return;
    }

    if (operation === "compare") {
      const keyword = url.searchParams.get("q") ?? "";
      const comparison = await client.compareRwaTicker(keyword);
      sendJson(response, 200, {
        operation,
        chainId: 56,
        data: comparison,
        timestamp: Date.now(),
        requestId,
        boundary: "READ_ONLY_NO_WALLET_NO_SIGNING_NO_BROADCAST",
      });
      return;
    }

    if (operation === "quote") {
      const quote = await client.quoteRwaFromUsdt({
        keyword: url.searchParams.get("q") ?? "",
        tokenContractAddress: url.searchParams.get("token") ?? "",
        userWalletAddress: url.searchParams.get("receiver") ?? "",
        usdtAmount: url.searchParams.get("amount") ?? "",
      });
      sendJson(response, 200, {
        operation,
        chainId: 56,
        data: quote,
        requestId,
        boundary: "READ_ONLY_QUOTE_NO_BUILD_NO_WALLET_NO_SIGNING_NO_BROADCAST",
      });
      return;
    }

    sendJson(response, 400, {
      error: "INVALID_OPERATION",
      message: "operation must be platforms, search, compare, or quote",
      requestId,
    });
  } catch (error) {
    const mapped = publicError(error, requestId);
    sendJson(response, mapped.status, mapped.body);
  }
}
