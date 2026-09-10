import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { contracts, progress, transactions } from "../src/data/protocol";

const addressPattern = /^0x[a-fA-F0-9]{40}$/;
const transactionPattern = /^0x[a-fA-F0-9]{64}$/;
const commitPattern = /^[a-f0-9]{7,40}$/;

describe("build-in-public content", () => {
  it("keeps entry IDs unique and uses known statuses", () => {
    const ids = progress.entries.map((entry) => entry.id);
    expect(new Set(ids).size).toBe(ids.length);
    progress.entries.forEach((entry) => {
      expect(["complete", "in-progress", "next"]).toContain(entry.status);
    });
  });

  it("binds every editorial reference to generated canonical data", () => {
    const contractIds = new Set(contracts.map((contract) => contract.id));
    const transactionIds = new Set(transactions.map((transaction) => transaction.id));
    progress.entries.forEach((entry) => {
      entry.contractRefs.forEach((id) => expect(contractIds.has(id), `${entry.id} contract ${id}`).toBe(true));
      entry.transactionRefs.forEach((id) => expect(transactionIds.has(id), `${entry.id} transaction ${id}`).toBe(true));
      entry.commits.forEach((commit) => expect(commit).toMatch(commitPattern));
    });
  });

  it("contains no duplicate contract or transaction identities", () => {
    expect(new Set(contracts.map((contract) => contract.id)).size).toBe(contracts.length);
    expect(new Set(transactions.map((transaction) => transaction.id)).size).toBe(transactions.length);
    contracts.forEach((contract) => expect(contract.address).toMatch(addressPattern));
    transactions.forEach((transaction) => expect(transaction.hash).toMatch(transactionPattern));
  });

  it("preserves the milestone's provenance-aware totals", () => {
    expect(contracts.filter((contract) => contract.provenance === "stonkhedge")).toHaveLength(16);
    expect(contracts.filter((contract) => contract.provenance === "market")).toHaveLength(3);
    expect(transactions.filter((transaction) => transaction.signedByProject)).toHaveLength(29);
    expect(transactions.filter((transaction) => !transaction.signedByProject)).toHaveLength(2);
  });

  it("links editorial entries only to files that exist in the repository", () => {
    progress.entries.flatMap((entry) => entry.docs).forEach((document) => {
      expect(existsSync(resolve(process.cwd(), document.path)), document.path).toBe(true);
    });
  });
});
