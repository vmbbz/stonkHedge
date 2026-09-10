export type EntryStatus = "complete" | "in-progress" | "next";
export type Provenance = "stonkhedge" | "external" | "market";

export interface DocLink {
  label: string;
  path: string;
}

export interface ProgressEntry {
  id: string;
  date: string;
  eyebrow: string;
  title: string;
  target: string;
  status: EntryStatus;
  summary: string;
  outcomes: string[];
  commits: string[];
  contractRefs: string[];
  transactionRefs: string[];
  evidence: string[];
  media: string[];
  docs: DocLink[];
}

export interface ProgressContent {
  schemaVersion: number;
  project: string;
  network: string;
  chainId: number;
  updatedAt: string;
  entries: ProgressEntry[];
}

export interface ContractRecord {
  id: string;
  name: string;
  address: string;
  role: string;
  provenance: Provenance;
  layer: string;
  transactionId?: string;
  blockNumber?: number;
  detail?: string;
}

export interface TransactionRecord {
  id: string;
  phase: "funding" | "shared" | "genesis";
  index: number;
  nonce?: number;
  label: string;
  hash: string;
  blockNumber: number;
  toOrCreated: string;
  reason: string;
  signedByProject: boolean;
}

export interface ArchitectureNode {
  id: string;
  contractId?: string;
  label: string;
  layer: "external" | "shared" | "market" | "next";
  position: [number, number, number];
  connections: string[];
}

export interface Metric {
  value: string;
  label: string;
  note: string;
}
