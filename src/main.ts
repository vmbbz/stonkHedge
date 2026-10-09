import "./styles.css";
import type { ArchitectureScene } from "./architecture";
import {
  assessGuardianAsset,
  issuerGapBps,
  normalizedPerSharePrice,
  parseGuardianResponse,
  type GuardianAsset,
  type GuardianComparison,
} from "./bnb/gapGuardian";
import {
  assessReadOnlyQuote,
  formatRawTokenAmount,
  parseReadOnlyQuoteResponse,
  type ReadOnlyQuote,
} from "./bnb/readOnlyQuote";
import {
  parseSimulationProofResponse,
  type PublicSimulationProof,
} from "./bnb/simulationProof";
import {
  architectureNodes,
  contracts,
  explorerBase,
  lifecycleFacts,
  metrics,
  progress,
  repositoryBase,
  terminalFacts,
  transactions,
} from "./data/protocol";
import type { ArchitectureNode, ContractRecord, ProgressEntry, TransactionRecord } from "./data/model";

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) throw new Error("Missing #app root");

const assetUrl = (path: string) => `${import.meta.env.BASE_URL}${path.replace(/^\//, "")}`;
const shorten = (value: string, left = 6, right = 4) => `${value.slice(0, left)}…${right ? value.slice(-right) : ""}`;
const repoUrl = (path: string) => `${repositoryBase}/${path}`;
const txUrl = (hash: string) => `${explorerBase}/tx/${hash}`;
const addressUrl = (address: string) => `${explorerBase}/address/${address}`;
const bscTokenUrl = (address: string) => `https://bscscan.com/token/${address}`;
const escapeHtml = (value: string) => value
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");
const formatUsd = (value: number) => new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: value < 1 ? 6 : 2,
}).format(value);
const formatAge = (milliseconds: number) => {
  const seconds = Math.max(0, Math.floor(milliseconds / 1_000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.floor(minutes / 60)}h ago`;
};
const formatClock = (timestamp: number | null) => timestamp === null
  ? "Not reported"
  : new Intl.DateTimeFormat("en-ZA", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Africa/Johannesburg",
    }).format(timestamp);
const canRenderWebGL = () => {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
};

const icon = (name: "arrow" | "check" | "copy" | "external" | "target") => {
  const paths = {
    arrow: '<path d="m5 12 14 0m-6-6 6 6-6 6"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    external: '<path d="M15 3h6v6m0-6L10 14"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/>',
  };
  return `<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${paths[name]}</svg>`;
};

const milestoneCard = (entry: ProgressEntry, index: number) => `
  <article class="milestone ${entry.status}" data-entry-id="${entry.id}">
    <div class="milestone-index" aria-hidden="true">${String(index + 1).padStart(2, "0")}</div>
    <div class="milestone-body">
      <div class="milestone-meta">
        <span>${entry.eyebrow}</span><time>${entry.date}</time>
        <span class="status-pill">${entry.status === "next" ? "Next gate" : entry.status === "in-progress" ? "In progress" : "Verified"}</span>
      </div>
      <h3>${entry.title}</h3>
      <p class="target"><span>${icon("target")}</span>${entry.target}</p>
      <p>${entry.summary}</p>
      <ul class="outcomes">${entry.outcomes.map((outcome) => `<li>${icon("check")}${outcome}</li>`).join("")}</ul>
      <div class="evidence-row">
        ${entry.evidence.map((item) => `<span>${item}</span>`).join("")}
        ${entry.commits.map((commit) => `<a href="https://github.com/vmbbz/stonkHedge/commit/${commit}" target="_blank" rel="noreferrer">commit ${shorten(commit, 7, 0)}</a>`).join("")}
      </div>
      <div class="milestone-links">
        ${entry.docs.map((doc) => `<a href="${repoUrl(doc.path)}" target="_blank" rel="noreferrer">${doc.label}${icon("external")}</a>`).join("")}
        <button class="plain-button inspect-entry" type="button" data-entry="${entry.id}">Inspect evidence ${icon("arrow")}</button>
      </div>
    </div>
    ${entry.media.length ? `<div class="milestone-media">${entry.media[0]?.endsWith(".mp4")
      ? `<video src="${assetUrl(entry.media[0])}" muted loop playsinline preload="metadata" aria-label="StonkHedge milestone animation"></video>`
      : `<img src="${assetUrl(entry.media[0] ?? "")}" alt="StonkHedge crystal character milestone artwork" loading="lazy" />`}</div>` : ""}
  </article>`;

const contractRow = (contract: ContractRecord) => `
  <article class="ledger-row" data-kind="${contract.provenance}" data-search="${contract.name.toLowerCase()} ${contract.address.toLowerCase()} ${contract.layer.toLowerCase()}">
    <div class="ledger-kind"><span class="contract-dot ${contract.provenance}"></span>${contract.layer}</div>
    <div><strong>${contract.name}</strong><span>${contract.role}</span></div>
    <div class="address-cell"><a href="${addressUrl(contract.address)}" target="_blank" rel="noreferrer"><code>${shorten(contract.address, 8, 6)}</code>${icon("external")}</a><button class="copy" type="button" data-copy="${contract.address}" aria-label="Copy ${contract.name} address">${icon("copy")}</button></div>
    <div>${contract.blockNumber ? `<span class="block">#${contract.blockNumber.toLocaleString()}</span>` : '<span class="muted">Reused / external</span>'}</div>
  </article>`;

const transactionRow = (transaction: TransactionRecord) => `
  <article class="tx-row" data-phase="${transaction.phase}" data-search="${transaction.label.toLowerCase()} ${transaction.hash.toLowerCase()}">
    <div class="tx-sequence"><span>${transaction.phase}</span><strong>${transaction.phase === "funding" ? "EXT" : String(transaction.index).padStart(2, "0")}</strong></div>
    <div class="tx-copy"><strong>${transaction.label}</strong><span>${transaction.reason}</span></div>
    <div class="tx-proof"><a href="${txUrl(transaction.hash)}" target="_blank" rel="noreferrer"><code>${shorten(transaction.hash, 9, 7)}</code>${icon("external")}</a><span>block ${transaction.blockNumber.toLocaleString()}</span></div>
  </article>`;

app.innerHTML = `
  <header class="site-header">
    <a class="wordmark" href="#top" aria-label="StonkHedge home"><span class="mark">S</span><span>StonkHedge</span></a>
    <nav aria-label="Primary">
      <a href="#gap-guardian">BNB Gap</a>
      <a href="#architecture">Architecture</a>
      <a href="#timeline">Timeline</a>
      <a href="#contracts">Contracts</a>
      <a href="#transactions">Transactions</a>
    </nav>
    <a class="network-chip" href="${explorerBase}" target="_blank" rel="noreferrer"><span></span>Testnet · 46630</a>
  </header>

  <main id="main">
    <section class="hero" id="top">
      <div class="hero-glow"></div>
      <div class="hero-copy">
        <div class="eyebrow"><span class="live-dot"></span>Building in public · updated ${progress.updatedAt}</div>
        <h1>Hedging gets<br/><em>a little weird.</em></h1>
        <p class="hero-lede">Follow a proof-backed trail from test assets and deployed contracts into a live, one-transaction-at-a-time Panoptic lifecycle.</p>
        <div class="hero-actions">
          <a class="primary-button" href="#timeline">Explore the build ${icon("arrow")}</a>
          <a class="secondary-button" href="${repoUrl("docs/progress/2026-09-19-lifecycle-receipt-bound-continuation.md")}" target="_blank" rel="noreferrer">Read the live checkpoint ${icon("external")}</a>
        </div>
        <p class="truth-note">Valueless mechanism test. Not a market quote, audit, endorsement, or mainnet release.</p>
      </div>
      <div class="hero-visual" aria-label="StonkHedge green crystal character">
        <div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>
        <img src="${assetUrl("/media/stonkhedge-crystal.png")}" alt="A cheerful translucent green crystal character wearing a red bow tie" />
        <div class="float-card card-one"><span>${transactions.filter((transaction) => transaction.signedByProject).length}</span>canonical txs</div>
        <div class="float-card card-two"><span>19</span>deployments</div>
        <div class="float-card card-three"><span>${lifecycleFacts.completedCalls}/${lifecycleFacts.totalCalls}</span>lifecycle</div>
      </div>
      <div class="scroll-cue">Scroll the ledger <span>↓</span></div>
    </section>

    <section class="metrics wrap" aria-label="Milestone totals">
      ${metrics.map((metric) => `<div class="metric"><strong>${metric.value}</strong><span>${metric.label}</span><small>${metric.note}</small></div>`).join("")}
    </section>

    <section class="section guardian-section" id="gap-guardian">
      <div class="guardian-orb guardian-orb-one"></div>
      <div class="guardian-orb guardian-orb-two"></div>
      <div class="wrap guardian-shell">
        <div class="guardian-heading">
          <div>
            <span class="kicker">BNB Hack · live simulation-only API</span>
            <h2>One stock.<br/><em>Two wrappers.</em></h2>
          </div>
          <div class="guardian-intro">
            <p>Gap Guardian resolves BSC tokenized-stock representations, normalizes each token by its token-to-share ratio, and surfaces issuer, freshness, and underlying-session differences before any wallet is involved.</p>
            <div class="guardian-boundary"><span class="live-dot"></span>BSC · chain 56 · no signing</div>
          </div>
        </div>
        <form class="guardian-search" id="guardian-search" role="search">
          <label for="guardian-query">Ticker, company, or BSC contract</label>
          <div>
            <input id="guardian-query" name="q" type="search" value="NVDA" maxlength="80" autocomplete="off" spellcheck="false" />
            <button type="submit">Compare live ${icon("arrow")}</button>
          </div>
          <small>First accepted candidate: NVDAon by Ondo and NVDAB by bStocks.</small>
        </form>
        <div class="guardian-results" id="guardian-results" aria-live="polite">
          <div class="guardian-loading"><span></span><p>Resolving issuer representations and market state…</p></div>
        </div>
        <form class="guardian-quote" id="guardian-quote-form">
          <div class="guardian-quote-heading">
            <div><span class="kicker">Bounded route lens</span><h3>Ask what exactly 5.10 USDT can buy.</h3></div>
            <p>The quote request sends only the selected public token address, exact amount, and a public receiver address. A separate button can compile and simulate fresh unsigned bytes on the server, but cannot sign or broadcast them.</p>
          </div>
          <div class="guardian-quote-fields">
            <label>Representation<select id="guardian-quote-asset" required disabled><option value="">Run the comparison first</option></select></label>
            <label>Exact USDT input<input id="guardian-quote-amount" type="text" inputmode="decimal" value="5.1" maxlength="20" autocomplete="off" readonly aria-readonly="true" /></label>
            <label>Public BSC receiver<input id="guardian-quote-receiver" type="text" placeholder="0x… (no key or connection)" maxlength="42" autocomplete="off" spellcheck="false" /></label>
            <button type="submit" disabled>Get read-only quote ${icon("arrow")}</button>
          </div>
          <small>Binance enforces a 5 USD notional floor; the 5.10 USDT buffer cleared that live gate. Route count is availability evidence, not a claim about reserve depth. Quotes expire quickly.</small>
        </form>
        <div class="guardian-quote-result" id="guardian-quote-result" aria-live="polite">
          <p>Select a representation and enter a public receiver to inspect a bounded route.</p>
        </div>
        <div class="guardian-simulation-result" id="guardian-simulation-result" aria-live="polite">
          <p>Unsigned simulation becomes available after a fresh bounded quote.</p>
        </div>
        <p class="guardian-disclosure">Binance documents its “reference price” as a per-share conversion derived from on-chain token price—not an official traditional-market quote. This monitor is informational; its transaction lane ends at unsigned simulation and cannot sign or broadcast.</p>
      </div>
    </section>

    <section class="section architecture-section" id="architecture">
      <div class="wrap section-heading split-heading">
        <div><span class="kicker">Protocol constellation</span><h2>See how the pieces connect.</h2></div>
        <p>Blue is infrastructure we qualified and reused. Acid green is the shared Panoptic layer StonkHedge deployed. Coral is the first per-market graph. Violet is what comes next.</p>
      </div>
      <div class="architecture-shell wrap">
        <div class="architecture-canvas" id="architecture-canvas">
          <div class="webgl-fallback">Interactive WebGL unavailable. Use the component buttons to explore the same architecture.</div>
          <div class="architecture-labels" aria-hidden="true"></div>
        </div>
        <div class="architecture-panel" id="architecture-panel" aria-live="polite">
          <span class="panel-kicker">Selected node</span>
          <h3>Public lifecycle ${lifecycleFacts.completedCalls} / ${lifecycleFacts.totalCalls}</h3>
          <p>${lifecycleFacts.checkpointSummary} Next: ${lifecycleFacts.nextLabel}.</p>
          <a href="#timeline">Open lifecycle evidence ${icon("arrow")}</a>
        </div>
        <div class="architecture-controls" role="group" aria-label="Architecture components">
          ${architectureNodes.map((node) => `<button type="button" data-node="${node.id}" class="${node.id === "lifecycle" ? "active" : ""}"><span class="node-dot ${node.layer}"></span>${node.label.replace("\n", " ")}</button>`).join("")}
        </div>
      </div>
    </section>

    <section class="park-section" id="park">
      <div class="park-intro wrap">
        <span class="kicker">Protocol Park</span>
        <h2>Infrastructure should feel alive.</h2>
        <p>Walk the route from shared foundations to the first market—and watch the two-actor lifecycle advance one verified public receipt at a time.</p>
      </div>
      <div class="park-scene" id="protocol-park" aria-label="A playful layered park showing StonkHedge's completed and upcoming milestones">
        <div class="park-sky-fill"></div>
        <img class="park-layer park-sky" data-depth="0.08" src="${assetUrl("/media/park/sky.png")}" alt="" />
        <img class="park-layer cloud cloud-left" data-depth="0.22" src="${assetUrl("/media/park/cloud-left.png")}" alt="" />
        <img class="park-layer cloud cloud-right" data-depth="0.18" src="${assetUrl("/media/park/cloud-right.png")}" alt="" />
        <img class="park-layer park-skyline" data-depth="0.12" src="${assetUrl("/media/park/skyline.png")}" alt="" />
        <img class="park-layer tree tree-left" data-depth="0.34" src="${assetUrl("/media/park/tree-left.png")}" alt="" />
        <img class="park-layer tree tree-center" data-depth="0.26" src="${assetUrl("/media/park/tree-center.png")}" alt="" />
        <img class="park-layer tree tree-canopy" data-depth="0.3" src="${assetUrl("/media/park/tree-canopy.png")}" alt="" />
        <img class="park-layer tree tree-small" data-depth="0.2" src="${assetUrl("/media/park/tree-small.png")}" alt="" />
        <div class="park-ground"></div>
        <img class="park-layer park-walkway" data-depth="0.18" src="${assetUrl("/media/park/walkway.png")}" alt="" />
        <img class="park-layer park-grass" data-depth="0.28" src="${assetUrl("/media/park/grass.png")}" alt="" />
        <img class="park-layer platform" data-depth="0.2" src="${assetUrl("/media/park/platform.png")}" alt="" />
        <img class="park-layer bench bench-left" data-depth="0.38" src="${assetUrl("/media/park/bench-left.png")}" alt="" />
        <img class="park-layer bench bench-right" data-depth="0.31" src="${assetUrl("/media/park/bench-right.png")}" alt="" />
        <img class="park-layer lamp" data-depth="0.42" src="${assetUrl("/media/park/lamp.png")}" alt="" />
        <img class="park-layer flowers flowers-left" data-depth="0.48" src="${assetUrl("/media/park/flowers-left.png")}" alt="" />
        <img class="park-layer flowers flowers-right" data-depth="0.43" src="${assetUrl("/media/park/flowers-right.png")}" alt="" />
        <img class="park-layer park-character" data-depth="0.32" src="${assetUrl("/media/stonkhedge-crystal.png")}" alt="The StonkHedge crystal character standing at the public-genesis milestone" />
        <a class="park-marker marker-stack" href="#timeline" aria-label="Shared stack milestone complete">
          <span>01</span><strong>Shared stack</strong><small>16 deployments · complete</small>
        </a>
        <a class="park-marker marker-genesis" href="#timeline" aria-label="Market genesis milestone complete">
          <span>02</span><strong>Market genesis</strong><small>PLTR/WETH · complete</small>
        </a>
        <a class="park-marker marker-next" href="#timeline" aria-label="Two-actor public lifecycle is in progress">
          <span>03</span><strong>Two-actor lifecycle</strong><small>${lifecycleFacts.completedCalls} / ${lifecycleFacts.totalCalls} public · verified</small>
        </a>
        <div class="park-caption"><span class="live-dot"></span>Move your pointer to explore the layers</div>
      </div>
    </section>

    <section class="section timeline-section" id="timeline">
      <div class="wrap section-heading split-heading">
        <div><span class="kicker">Build log</span><h2>Every leap leaves a receipt.</h2></div>
        <p>Targets, decisions, commits, evidence, and boundaries travel together. The final card stays open until the two-actor lifecycle is genuinely proven.</p>
      </div>
      <div class="timeline wrap">${progress.entries.map(milestoneCard).join("")}</div>
    </section>

    <section class="section ledger-section" id="contracts">
      <div class="wrap section-heading split-heading">
        <div><span class="kicker">Contract atlas</span><h2>Deployed by us—or clearly not.</h2></div>
        <p>Search all 19 StonkHedge deployments alongside the qualified Robinhood and candidate V4 dependencies they connect to.</p>
      </div>
      <div class="wrap toolbar">
        <div class="filter-group" role="group" aria-label="Filter contracts">
          <button class="filter active" type="button" data-contract-filter="all">All</button>
          <button class="filter" type="button" data-contract-filter="stonkhedge">Shared</button>
          <button class="filter" type="button" data-contract-filter="market">Market</button>
          <button class="filter" type="button" data-contract-filter="external">External</button>
        </div>
        <label class="search"><span class="sr-only">Search contracts</span><input id="contract-search" type="search" placeholder="Search name or 0x address" /></label>
      </div>
      <div class="ledger wrap" id="contract-ledger">${contracts.map(contractRow).join("")}</div>
    </section>

    <section class="section transaction-section" id="transactions">
      <div class="wrap section-heading split-heading">
        <div><span class="kicker">Transaction trail</span><h2>Why this transaction, right now?</h2></div>
        <p>The answer sits next to every receipt. Faucet events remain visibly separate from the project-signed deployment, genesis, and lifecycle totals.</p>
      </div>
      <div class="wrap toolbar">
        <div class="filter-group" role="group" aria-label="Filter transactions">
          <button class="filter active" type="button" data-tx-filter="all">All ${transactions.length} events</button>
          <button class="filter" type="button" data-tx-filter="shared">${transactions.filter((transaction) => transaction.phase === "shared").length} shared</button>
          <button class="filter" type="button" data-tx-filter="genesis">${transactions.filter((transaction) => transaction.phase === "genesis").length} genesis</button>
          <button class="filter" type="button" data-tx-filter="lifecycle">${lifecycleFacts.completedCalls} lifecycle</button>
          <button class="filter" type="button" data-tx-filter="funding">${transactions.filter((transaction) => transaction.phase === "funding").length} external funding</button>
        </div>
        <label class="search"><span class="sr-only">Search transactions</span><input id="tx-search" type="search" placeholder="Search action or tx hash" /></label>
      </div>
      <div class="transaction-list wrap" id="transaction-list">${transactions.map(transactionRow).join("")}</div>
    </section>

    <section class="section proof-section">
      <div class="wrap proof-grid">
        <div class="proof-video">
          <video src="${assetUrl("/media/stonkhedge-progress.mp4")}" muted loop autoplay playsinline preload="metadata" poster="${assetUrl("/media/stonkhedge-testnet-hero.jpg")}" aria-label="Animated StonkHedge brand scene"></video>
        </div>
        <div class="proof-copy">
          <span class="kicker">Current checkpoint</span>
          <h2>${lifecycleFacts.headline.replace(". ", ".<br/>")}</h2>
          <p>The public sequence is verified through index ${lifecycleFacts.completedThrough}. ${lifecycleFacts.checkpointSummary} The next plan-bound action is “${lifecycleFacts.nextLabel}.”</p>
          <dl>
            <div><dt>Latest verified block</dt><dd>${terminalFacts.referenceBlock.toLocaleString()}</dd></div>
            <div><dt>Lifecycle</dt><dd>${lifecycleFacts.completedCalls} / ${lifecycleFacts.totalCalls} calls</dd></div>
            <div><dt>Writer collateral</dt><dd>PLTR + WETH</dd></div>
            <div><dt>Next gate</dt><dd>Index ${lifecycleFacts.nextAuthorizedIndex} · ${lifecycleFacts.nextLabel}</dd></div>
          </dl>
          <a class="primary-button" href="${repoUrl("docs/progress/2026-09-19-lifecycle-receipt-bound-continuation.md")}" target="_blank" rel="noreferrer">Inspect the receipt ledger ${icon("external")}</a>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="wrap footer-grid">
      <div><a class="wordmark" href="#top"><span class="mark">S</span><span>StonkHedge</span></a><p>Mechanism testing in public, with receipts.</p></div>
      <div><span>Source of truth</span><a href="${repoUrl("docs/architecture/robinhood-testnet-system.md")}" target="_blank" rel="noreferrer">Architecture</a><a href="${repoUrl("manifests/markets/robinhood-testnet-pltr-weth-lifecycle-continuation-public-progress-2026-09-19.json")}" target="_blank" rel="noreferrer">Lifecycle manifest</a></div>
      <div><span>Boundaries</span><p>Robinhood Chain Testnet only. No real value, withdrawal, liquidation, or mainnet activity.</p></div>
    </div>
  </footer>

  <dialog id="evidence-dialog">
    <button class="dialog-close" type="button" aria-label="Close evidence panel">×</button>
    <div id="dialog-content"></div>
  </dialog>
  <div class="toast" role="status" aria-live="polite"></div>
`;

const renderGuardianAsset = (
  asset: GuardianAsset,
  gapBps: number | null,
  now: number,
) => {
  const assessment = assessGuardianAsset(asset, now, gapBps);
  const perShare = normalizedPerSharePrice(asset);
  const supportedProtections = Object.entries(asset.profile.protections)
    .filter(([, protection]) => protection.supported)
    .map(([name]) => name.replace(/([a-z])([A-Z])/gu, "$1 $2").toLowerCase());
  const session = asset.market.statusInfo.marketStatus
    ?? (asset.market.statusInfo.openState ? "open · unlabeled" : "unreported");
  const sessionDetail = asset.market.statusInfo.reasonMsg
    ?? (asset.market.statusInfo.openState ? "Underlying marked open" : "No reason reported");
  return `
    <article class="guardian-card ${assessment.level}">
      <div class="guardian-card-top">
        <div class="issuer-mark ${escapeHtml(asset.asset.platformId)}">${escapeHtml(asset.asset.platformId.slice(0, 1).toUpperCase())}</div>
        <div><span>${escapeHtml(asset.asset.platformId)}</span><h3>${escapeHtml(asset.asset.tokenSymbol)}</h3></div>
        <span class="guardian-risk ${assessment.level}">${escapeHtml(assessment.label)}</span>
      </div>
      <div class="guardian-price">
        <span>Normalized per share</span>
        <strong>${formatUsd(perShare)}</strong>
        <small>Raw token ${formatUsd(Number(asset.price.tokenPrice))} · ratio ${escapeHtml(asset.profile.tokenToShareRatio)}</small>
      </div>
      <dl class="guardian-facts">
        <div><dt>Reported reference</dt><dd>${formatUsd(Number(asset.price.referencePrice))}</dd></div>
        <div><dt>Price freshness</dt><dd>${formatAge(assessment.priceAgeMs)}</dd></div>
        <div><dt>Underlying session</dt><dd>${escapeHtml(session)}</dd></div>
        <div><dt>Session detail</dt><dd>${escapeHtml(sessionDetail)}</dd></div>
        <div><dt>Next open</dt><dd>${escapeHtml(formatClock(asset.market.statusInfo.nextOpenTime))}</dd></div>
        <div><dt>Protection evidence</dt><dd>${supportedProtections.length ? escapeHtml(supportedProtections.join(", ")) : "None reported"}</dd></div>
      </dl>
      <div class="guardian-reasons">
        ${assessment.reasons.map((reason) => `<span>${escapeHtml(reason)}</span>`).join("")}
      </div>
      <a class="guardian-address" href="${bscTokenUrl(asset.asset.tokenContractAddress)}" target="_blank" rel="noreferrer">
        <code>${escapeHtml(shorten(asset.asset.tokenContractAddress, 9, 7))}</code>${icon("external")}
      </a>
    </article>`;
};

const renderGuardianComparison = (comparison: GuardianComparison) => {
  const results = document.querySelector<HTMLElement>("#guardian-results");
  if (!results) return;
  const gapBps = issuerGapBps(comparison.assets);
  const now = Date.now();
  const observedAt = Math.max(
    comparison.timestamps.search,
    comparison.timestamps.price,
    ...comparison.timestamps.profiles,
    ...comparison.timestamps.markets,
  );
  results.innerHTML = `
    <div class="guardian-summary">
      <div><span>Resolved underlying</span><strong>${escapeHtml(comparison.ticker)}</strong><small>${escapeHtml(comparison.companyName)}</small></div>
      <div><span>Issuer-normalized gap</span><strong>${gapBps === null ? "—" : `${gapBps.toFixed(2)} bps`}</strong><small>${comparison.assets.length} BSC representation${comparison.assets.length === 1 ? "" : "s"}</small></div>
      <div><span>API observation</span><strong>${formatAge(Math.max(0, now - observedAt))}</strong><small>${escapeHtml(formatClock(observedAt))}</small></div>
    </div>
    <div class="guardian-grid">
      ${comparison.assets.map((asset) => renderGuardianAsset(asset, gapBps, now)).join("")}
    </div>`;
  const assetSelect = document.querySelector<HTMLSelectElement>("#guardian-quote-asset");
  const quoteButton = document.querySelector<HTMLButtonElement>("#guardian-quote-form button[type='submit']");
  if (assetSelect) {
    assetSelect.innerHTML = comparison.assets.map((asset) => `
      <option value="${escapeHtml(asset.asset.tokenContractAddress)}">${escapeHtml(asset.asset.tokenSymbol)} · ${escapeHtml(asset.asset.platformId)}</option>`).join("");
    assetSelect.disabled = false;
  }
  if (quoteButton) quoteButton.disabled = comparison.assets.length === 0;
  latestGuardianComparison = comparison;
};

const guardianForm = document.querySelector<HTMLFormElement>("#guardian-search");
const guardianInput = document.querySelector<HTMLInputElement>("#guardian-query");
const guardianResults = document.querySelector<HTMLElement>("#guardian-results");
let guardianRequest: AbortController | undefined;
let latestGuardianComparison: GuardianComparison | undefined;

const loadGuardianComparison = async (query: string) => {
  if (!guardianResults || !guardianForm) return;
  const normalized = query.trim();
  if (!normalized || normalized.length > 80 || /[\u0000-\u001f\u007f]/u.test(normalized)) {
    guardianResults.innerHTML = '<div class="guardian-error"><strong>Check the search</strong><p>Use 1–80 visible characters.</p></div>';
    return;
  }
  guardianRequest?.abort();
  const supersededQuoteRequest = quoteRequest;
  quoteRequest = undefined;
  supersededQuoteRequest?.abort();
  const supersededSimulationRequest = simulationRequest;
  simulationRequest = undefined;
  supersededSimulationRequest?.abort();
  if (quoteExpiryTimer !== undefined) {
    window.clearTimeout(quoteExpiryTimer);
    quoteExpiryTimer = undefined;
  }
  const controller = new AbortController();
  guardianRequest = controller;
  const button = guardianForm.querySelector<HTMLButtonElement>("button[type='submit']");
  if (button) button.disabled = true;
  latestGuardianComparison = undefined;
  const quoteSelect = document.querySelector<HTMLSelectElement>("#guardian-quote-asset");
  const quoteButton = document.querySelector<HTMLButtonElement>("#guardian-quote-form button[type='submit']");
  if (quoteSelect) {
    quoteSelect.disabled = true;
    quoteSelect.innerHTML = '<option value="">Waiting for comparison</option>';
  }
  if (quoteButton) quoteButton.disabled = true;
  const currentQuote = document.querySelector<HTMLElement>("#guardian-quote-result");
  if (currentQuote) currentQuote.innerHTML = "<p>Refresh a comparison before requesting a route.</p>";
  const currentSimulation = document.querySelector<HTMLElement>("#guardian-simulation-result");
  if (currentSimulation) currentSimulation.innerHTML = "<p>Refresh a comparison and quote before running an unsigned simulation.</p>";
  guardianResults.setAttribute("aria-busy", "true");
  guardianResults.innerHTML = '<div class="guardian-loading"><span></span><p>Resolving issuer representations and market state…</p></div>';
  const timeout = window.setTimeout(() => controller.abort(), 15_000);
  try {
    const response = await fetch(`/api/bnb/rwa?operation=compare&q=${encodeURIComponent(normalized)}`, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    const body: unknown = await response.json();
    if (!response.ok) {
      const error = typeof body === "object" && body !== null && "message" in body
        && typeof body.message === "string"
        ? body.message
        : `The comparison service returned HTTP ${response.status}`;
      throw new Error(error);
    }
    renderGuardianComparison(parseGuardianResponse(body));
  } catch (error) {
    if (controller.signal.aborted && guardianRequest !== controller) return;
    const message = controller.signal.aborted
      ? "The live comparison timed out. Try again."
      : error instanceof Error ? error.message : "The live comparison could not be loaded.";
    guardianResults.innerHTML = `<div class="guardian-error"><strong>Live data unavailable</strong><p>${escapeHtml(message)}</p><small>No cached or invented price was substituted.</small></div>`;
  } finally {
    window.clearTimeout(timeout);
    if (guardianRequest === controller) {
      guardianResults.removeAttribute("aria-busy");
      if (button) button.disabled = false;
    }
  }
};

guardianForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  void loadGuardianComparison(guardianInput?.value ?? "");
});

const quoteForm = document.querySelector<HTMLFormElement>("#guardian-quote-form");
const quoteAsset = document.querySelector<HTMLSelectElement>("#guardian-quote-asset");
const quoteAmount = document.querySelector<HTMLInputElement>("#guardian-quote-amount");
const quoteReceiver = document.querySelector<HTMLInputElement>("#guardian-quote-receiver");
const quoteResult = document.querySelector<HTMLElement>("#guardian-quote-result");
const simulationResult = document.querySelector<HTMLElement>("#guardian-simulation-result");
let quoteRequest: AbortController | undefined;
let quoteExpiryTimer: number | undefined;
let simulationRequest: AbortController | undefined;

void loadGuardianComparison(guardianInput?.value ?? "NVDA");

const renderReadOnlyQuote = (quote: ReadOnlyQuote) => {
  if (!quoteResult) return;
  const assessment = assessReadOnlyQuote(quote);
  const best = quote.routes.find((route) => route.isBest) ?? quote.routes[0];
  if (!best) return;
  const output = formatRawTokenAmount(best.toTokenAmount, best.toToken.decimal);
  const routeNames = [...new Set(best.dexRouterList.map((segment) => segment.dexProtocol.dexName))];
  const impact = best.priceImpactPercent === null ? "Not reported" : `${Math.abs(Number(best.priceImpactPercent)).toFixed(2)}%`;
  const usableSeconds = Math.floor(assessment.usableForMs / 1_000);
  quoteResult.innerHTML = `
    <article class="quote-card ${assessment.level}">
      <div class="quote-card-top"><div><span>Best bounded route</span><h3>${escapeHtml(quote.input.displayAmount)} USDT → ${escapeHtml(best.toToken.tokenSymbol)}</h3></div><span class="guardian-risk ${assessment.level}">${escapeHtml(assessment.label)}</span></div>
      <div class="quote-output"><span>Estimated output</span><strong>${escapeHtml(output)} ${escapeHtml(best.toToken.tokenSymbol)}</strong><small>${escapeHtml(best.vendorName)} · ${escapeHtml(best.executionMode)} · no transaction built</small></div>
      <dl class="quote-facts">
        <div><dt>Price impact</dt><dd>${escapeHtml(impact)}</dd></div>
        <div><dt>Freshness window</dt><dd>${usableSeconds}s remaining</dd></div>
        <div><dt>Liquidity evidence</dt><dd>${assessment.routeCount} vendor route${assessment.routeCount === 1 ? "" : "s"}</dd></div>
        <div><dt>Reported path</dt><dd>${routeNames.length ? escapeHtml(routeNames.join(" + ")) : "No segments reported"}</dd></div>
        <div><dt>Receiver binding</dt><dd><code>${escapeHtml(shorten(quote.userWalletAddress, 8, 6))}</code></dd></div>
        <div><dt>Approval target</dt><dd>${best.approveTarget ? `<code>${escapeHtml(shorten(best.approveTarget, 8, 6))}</code>` : "Not reported"}</dd></div>
      </dl>
      <div class="guardian-reasons">${assessment.reasons.map((reason) => `<span>${escapeHtml(reason)}</span>`).join("")}</div>
      <p class="quote-depth-note">Route availability and reported impact are quote-level evidence; they do not prove pool reserves, fill certainty, or future execution.</p>
      <button class="simulation-button" type="button" ${assessment.level === "blocked" ? "disabled" : ""}>Compile & simulate a fresh route ${icon("arrow")}</button>
      <p class="simulation-boundary">Build and simulation stay server-side. No calldata is returned, no wallet is connected, and nothing can be signed or broadcast.</p>
    </article>`;
  if (simulationResult) {
    simulationResult.innerHTML = "<p>Ready to compile a fresh route and test it without a wallet.</p>";
  }
  if (quoteExpiryTimer !== undefined) window.clearTimeout(quoteExpiryTimer);
  quoteExpiryTimer = window.setTimeout(() => {
    if (!quoteResult) return;
    const expired = assessReadOnlyQuote(quote, quote.expiresAt);
    const risk = quoteResult.querySelector<HTMLElement>(".guardian-risk");
    const card = quoteResult.querySelector<HTMLElement>(".quote-card");
    if (risk) risk.textContent = expired.label;
    if (card) card.className = "quote-card blocked";
    const freshness = quoteResult.querySelectorAll<HTMLElement>(".quote-facts dd")[1];
    if (freshness) freshness.textContent = "Expired · refresh required";
  }, Math.max(0, quote.expiresAt - Date.now()));
};

quoteForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!quoteResult || !quoteAsset || !quoteAmount || !quoteReceiver || !latestGuardianComparison) return;
  const receiver = quoteReceiver.value.trim();
  const amount = quoteAmount.value.trim();
  if (!/^0x[a-fA-F0-9]{40}$/u.test(receiver)) {
    quoteResult.innerHTML = '<div class="guardian-error compact"><strong>Check the receiver</strong><p>Enter a public 0x BSC address. Never enter a private key.</p></div>';
    return;
  }
  if (!/^(0|[1-9]\d*)(?:\.\d{1,18})?$/u.test(amount) || Number(amount) !== 5.1) {
    quoteResult.innerHTML = '<div class="guardian-error compact"><strong>Check the amount</strong><p>This live quote currently requires exactly 5.10 USDT.</p></div>';
    return;
  }
  quoteRequest?.abort();
  if (quoteExpiryTimer !== undefined) {
    window.clearTimeout(quoteExpiryTimer);
    quoteExpiryTimer = undefined;
  }
  const controller = new AbortController();
  quoteRequest = controller;
  const button = quoteForm.querySelector<HTMLButtonElement>("button[type='submit']");
  if (button) button.disabled = true;
  quoteResult.setAttribute("aria-busy", "true");
  quoteResult.innerHTML = '<div class="guardian-loading compact"><span></span><p>Requesting bounded routes…</p></div>';
  const timeout = window.setTimeout(() => controller.abort(), 20_000);
  try {
    const parameters = new URLSearchParams({
      operation: "quote",
      q: latestGuardianComparison.ticker,
      token: quoteAsset.value,
      receiver,
      amount,
    });
    const response = await fetch(`/api/bnb/rwa?${parameters.toString()}`, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    const body: unknown = await response.json();
    if (!response.ok) {
      const message = typeof body === "object" && body !== null && "message" in body
        && typeof body.message === "string"
        ? body.message
        : `The quote service returned HTTP ${response.status}`;
      throw new Error(message);
    }
    renderReadOnlyQuote(parseReadOnlyQuoteResponse(body));
  } catch (error) {
    if (controller.signal.aborted && quoteRequest !== controller) return;
    const message = controller.signal.aborted
      ? "The quote request timed out. Try again."
      : error instanceof Error ? error.message : "The quote request could not be loaded.";
    quoteResult.innerHTML = `<div class="guardian-error compact"><strong>Quote unavailable</strong><p>${escapeHtml(message)}</p><small>No cached route was substituted.</small></div>`;
  } finally {
    window.clearTimeout(timeout);
    if (quoteRequest === controller) {
      quoteResult.removeAttribute("aria-busy");
      if (button) button.disabled = false;
    }
  }
});

const renderSimulationProof = (proof: PublicSimulationProof) => {
  if (!simulationResult) return;
  const blocked = proof.verdict === "BLOCKED";
  simulationResult.innerHTML = `
    <article class="simulation-card ${blocked ? "blocked" : "clear"}">
      <div class="simulation-card-top">
        <div><span>Unsigned transaction rehearsal</span><h3>${escapeHtml(proof.input.displayAmount)} USDT → ${escapeHtml(proof.asset.tokenSymbol)}</h3></div>
        <span class="guardian-risk ${blocked ? "blocked" : "clear"}">${blocked ? "Blocked as expected" : "Simulation clear"}</span>
      </div>
      <div class="simulation-verdict">
        <strong>${blocked ? "No signing gate opened" : "Both unsigned calls simulated successfully"}</strong>
        <p>${blocked ? "The exact route remains non-executable and requires remediation plus a fresh simulation." : "This is still only a prediction. It grants no authority to sign or spend."}</p>
      </div>
      <dl class="quote-facts simulation-facts">
        <div><dt>Approval</dt><dd>${escapeHtml(proof.approval.simulation.status)}</dd></div>
        <div><dt>Swap</dt><dd>${escapeHtml(proof.swap.simulation.status)}</dd></div>
        <div><dt>Exact approval</dt><dd>${escapeHtml(proof.input.displayAmount)} USDT</dd></div>
        <div><dt>Slippage cap</dt><dd>${escapeHtml(proof.route.slippagePercent)}%</dd></div>
        <div><dt>Approval selector</dt><dd><code>${escapeHtml(proof.approval.transaction.selector)}</code></dd></div>
        <div><dt>Swap selector</dt><dd><code>${escapeHtml(proof.swap.transaction.selector)}</code></dd></div>
        <div><dt>Minimum output</dt><dd><code>${escapeHtml(proof.swap.minimumOutputRaw)}</code> raw</dd></div>
        <div><dt>Vendor</dt><dd>${escapeHtml(proof.route.vendorName)}</dd></div>
      </dl>
      <div class="guardian-reasons">${(proof.reasons.length ? proof.reasons : ["Exact approval and swap simulations returned SUCCESS"]).map((reason) => `<span>${escapeHtml(reason)}</span>`).join("")}</div>
      <details class="simulation-hashes"><summary>Inspect non-executable byte fingerprints</summary><dl>
        <div><dt>Quote ID SHA-256</dt><dd><code>${escapeHtml(proof.route.quoteIdHash)}</code></dd></div>
        <div><dt>Approval SHA-256</dt><dd><code>${escapeHtml(proof.approval.transaction.calldataHash)}</code></dd></div>
        <div><dt>Swap SHA-256</dt><dd><code>${escapeHtml(proof.swap.transaction.calldataHash)}</code></dd></div>
      </dl></details>
      <p class="simulation-boundary">Simulation only · no raw calldata · no wallet · no private key · no signing · no broadcast</p>
    </article>`;
};

quoteResult?.addEventListener("click", async (event) => {
  const target = event.target;
  const button = target instanceof Element ? target.closest<HTMLButtonElement>(".simulation-button") : null;
  if (!button || !simulationResult || !quoteAsset || !quoteAmount || !quoteReceiver || !latestGuardianComparison) return;
  simulationRequest?.abort();
  const controller = new AbortController();
  simulationRequest = controller;
  button.disabled = true;
  simulationResult.setAttribute("aria-busy", "true");
  simulationResult.innerHTML = '<div class="guardian-loading compact"><span></span><p>Compiling fresh exact bytes and running two unsigned simulations…</p></div>';
  const timeout = window.setTimeout(() => controller.abort(), 30_000);
  try {
    const parameters = new URLSearchParams({
      operation: "simulate",
      q: latestGuardianComparison.ticker,
      token: quoteAsset.value,
      receiver: quoteReceiver.value.trim(),
      amount: quoteAmount.value.trim(),
    });
    const response = await fetch(`/api/bnb/rwa?${parameters.toString()}`, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    const body: unknown = await response.json();
    if (!response.ok) {
      const message = typeof body === "object" && body !== null && "message" in body
        && typeof body.message === "string"
        ? body.message
        : `The simulation service returned HTTP ${response.status}`;
      throw new Error(message);
    }
    renderSimulationProof(parseSimulationProofResponse(body));
  } catch (error) {
    if (controller.signal.aborted && simulationRequest !== controller) return;
    const message = controller.signal.aborted
      ? "The unsigned simulation timed out. Refresh the quote and try again."
      : error instanceof Error ? error.message : "The unsigned simulation could not be completed.";
    simulationResult.innerHTML = `<div class="guardian-error compact"><strong>Simulation unavailable</strong><p>${escapeHtml(message)}</p><small>No wallet or transaction fallback was attempted.</small></div>`;
  } finally {
    window.clearTimeout(timeout);
    if (simulationRequest === controller) {
      simulationResult.removeAttribute("aria-busy");
      button.disabled = false;
    }
  }
});

const nodeDescription = (node: ArchitectureNode) => {
  const contract = node.contractId ? contracts.find((candidate) => candidate.id === node.contractId) : undefined;
  const descriptions: Record<string, string> = {
    assets: "Five faucet Stock Tokens plus WETH are external test assets. PLTR is the first market's base asset.",
    liquidity: "Position NFT 3903 supplies bounded two-sided liquidity to the exact PLTR/WETH PoolKey.",
    lifecycle: `The hash-bound two-actor lifecycle is public through index ${lifecycleFacts.completedThrough}. ${lifecycleFacts.checkpointSummary} Every call still stops for receipt and state verification.`,
    next: `The next exact plan-bound action is “${lifecycleFacts.nextLabel}.”`,
  };
  return {
    title: node.label.replace("\n", " "),
    body: contract?.role ?? descriptions[node.id] ?? "A verified component in the current testnet architecture.",
    contract,
  };
};

const architecturePanel = document.querySelector<HTMLElement>("#architecture-panel");
const selectNode = (node: ArchitectureNode) => {
  if (!architecturePanel) return;
  const info = nodeDescription(node);
  architecturePanel.innerHTML = `
    <span class="panel-kicker">${node.layer} layer</span>
    <h3>${info.title}</h3><p>${info.body}</p>
    ${info.contract ? `<a href="${addressUrl(info.contract.address)}" target="_blank" rel="noreferrer"><code>${shorten(info.contract.address, 9, 7)}</code> ${icon("external")}</a>` : `<a href="#timeline">Follow the evidence ${icon("arrow")}</a>`}`;
  document.querySelectorAll<HTMLButtonElement>("[data-node]").forEach((button) => button.classList.toggle("active", button.dataset.node === node.id));
};

const architectureContainer = document.querySelector<HTMLElement>("#architecture-canvas");
let architectureScene: ArchitectureScene | undefined;
if (architectureContainer && canRenderWebGL()) {
  architectureContainer.classList.add("has-webgl");
  void import("./architecture").then(({ ArchitectureScene }) => {
    architectureScene = new ArchitectureScene(architectureContainer, architectureNodes, selectNode);
  });
}

document.querySelectorAll<HTMLButtonElement>("[data-node]").forEach((button) => {
  button.addEventListener("click", () => {
    const node = architectureNodes.find((candidate) => candidate.id === button.dataset.node);
    if (node) {
      selectNode(node);
      architectureScene?.select(node.id);
    }
  });
});

const wireFilter = (buttonSelector: string, rowSelector: string, kindKey: "kind" | "phase", searchSelector: string) => {
  const buttons = Array.from(document.querySelectorAll<HTMLButtonElement>(buttonSelector));
  const rows = Array.from(document.querySelectorAll<HTMLElement>(rowSelector));
  const search = document.querySelector<HTMLInputElement>(searchSelector);
  let active = "all";
  const apply = () => {
    const query = search?.value.trim().toLowerCase() ?? "";
    rows.forEach((row) => {
      const kind = row.dataset[kindKey];
      const matchesKind = active === "all" || kind === active;
      const matchesSearch = !query || row.dataset.search?.includes(query);
      row.hidden = !(matchesKind && matchesSearch);
    });
  };
  buttons.forEach((button) => button.addEventListener("click", () => {
    active = button.dataset.contractFilter ?? button.dataset.txFilter ?? "all";
    buttons.forEach((candidate) => candidate.classList.toggle("active", candidate === button));
    apply();
  }));
  search?.addEventListener("input", apply);
};

wireFilter("[data-contract-filter]", ".ledger-row", "kind", "#contract-search");
wireFilter("[data-tx-filter]", ".tx-row", "phase", "#tx-search");

const toast = document.querySelector<HTMLElement>(".toast");
document.querySelectorAll<HTMLButtonElement>("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const value = button.dataset.copy;
    if (!value) return;
    await navigator.clipboard.writeText(value);
    if (toast) {
      toast.textContent = "Address copied";
      toast.classList.add("show");
      window.setTimeout(() => toast.classList.remove("show"), 1600);
    }
  });
});

const dialog = document.querySelector<HTMLDialogElement>("#evidence-dialog");
const dialogContent = document.querySelector<HTMLElement>("#dialog-content");
document.querySelectorAll<HTMLButtonElement>(".inspect-entry").forEach((button) => {
  button.addEventListener("click", () => {
    const entry = progress.entries.find((candidate) => candidate.id === button.dataset.entry);
    if (!entry || !dialog || !dialogContent) return;
    const entryContracts = entry.contractRefs.map((id) => contracts.find((candidate) => candidate.id === id)).filter(Boolean) as ContractRecord[];
    const entryTransactions = entry.transactionRefs.map((id) => transactions.find((candidate) => candidate.id === id)).filter(Boolean) as TransactionRecord[];
    dialogContent.innerHTML = `
      <span class="kicker">${entry.eyebrow} · ${entry.date}</span><h2>${entry.title}</h2><p>${entry.summary}</p>
      ${entryContracts.length ? `<h3>Connected contracts</h3><ul class="dialog-list">${entryContracts.map((contract) => `<li><span>${contract.name}</span><a href="${addressUrl(contract.address)}" target="_blank" rel="noreferrer"><code>${shorten(contract.address, 8, 6)}</code></a></li>`).join("")}</ul>` : ""}
      ${entryTransactions.length ? `<h3>Selected receipts</h3><ul class="dialog-list">${entryTransactions.map((transaction) => `<li><span>${transaction.label}</span><a href="${txUrl(transaction.hash)}" target="_blank" rel="noreferrer"><code>${shorten(transaction.hash, 8, 6)}</code></a></li>`).join("")}</ul>` : ""}
      <h3>Related records</h3><ul class="dialog-list">${entry.docs.map((doc) => `<li><span>${doc.label}</span><a href="${repoUrl(doc.path)}" target="_blank" rel="noreferrer">Open ${icon("external")}</a></li>`).join("")}</ul>`;
    dialog.showModal();
  });
});

document.querySelector<HTMLButtonElement>(".dialog-close")?.addEventListener("click", () => dialog?.close());
dialog?.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});

const autoVideos = document.querySelectorAll<HTMLVideoElement>("video[autoplay]");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (reduceMotion) {
  autoVideos.forEach((video) => video.pause());
} else {
  const mediaObserver = new IntersectionObserver((entries) => entries.forEach((entry) => {
    const video = entry.target as HTMLVideoElement;
    if (entry.isIntersecting) void video.play().catch(() => undefined);
    else video.pause();
  }));
  autoVideos.forEach((video) => mediaObserver.observe(video));
}

const park = document.querySelector<HTMLElement>("#protocol-park");
if (park && !reduceMotion) {
  const layers = Array.from(park.querySelectorAll<HTMLElement>("[data-depth]"));
  park.addEventListener("pointermove", (event) => {
    const bounds = park.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width - 0.5;
    const y = (event.clientY - bounds.top) / bounds.height - 0.5;
    layers.forEach((layer) => {
      const depth = Number(layer.dataset.depth ?? 0);
      layer.style.setProperty("--parallax-x", `${x * depth * 42}px`);
      layer.style.setProperty("--parallax-y", `${y * depth * 24}px`);
    });
  });
  park.addEventListener("pointerleave", () => {
    layers.forEach((layer) => {
      layer.style.setProperty("--parallax-x", "0px");
      layer.style.setProperty("--parallax-y", "0px");
    });
  });
}
