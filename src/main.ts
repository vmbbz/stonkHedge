import "./styles.css";
import type { ArchitectureScene } from "./architecture";
import {
  architectureNodes,
  contracts,
  explorerBase,
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
        <span class="status-pill">${entry.status === "next" ? "Next gate" : "Verified"}</span>
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
        <p class="hero-lede">Follow a proof-backed trail from test assets to a registered Panoptic market—every contract, transaction, decision, and honest boundary included.</p>
        <div class="hero-actions">
          <a class="primary-button" href="#timeline">Explore the build ${icon("arrow")}</a>
          <a class="secondary-button" href="${repoUrl("docs/progress/2026-09-11-public-genesis-milestone.md")}" target="_blank" rel="noreferrer">Read the milestone ${icon("external")}</a>
        </div>
        <p class="truth-note">Valueless mechanism test. Not a market quote, audit, endorsement, or mainnet release.</p>
      </div>
      <div class="hero-visual" aria-label="StonkHedge green crystal character">
        <div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>
        <img src="${assetUrl("/media/stonkhedge-crystal.png")}" alt="A cheerful translucent green crystal character wearing a red bow tie" />
        <div class="float-card card-one"><span>29</span>canonical txs</div>
        <div class="float-card card-two"><span>19</span>deployments</div>
        <div class="float-card card-three"><span>0</span>allowances left</div>
      </div>
      <div class="scroll-cue">Scroll the ledger <span>↓</span></div>
    </section>

    <section class="metrics wrap" aria-label="Milestone totals">
      ${metrics.map((metric) => `<div class="metric"><strong>${metric.value}</strong><span>${metric.label}</span><small>${metric.note}</small></div>`).join("")}
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
          <h3>PanopticPool + 2 Trackers</h3>
          <p>The first deployed per-market options graph, connected to the exact PLTR/WETH PoolKey.</p>
          <a href="#contracts">Open contract ledger ${icon("arrow")}</a>
        </div>
        <div class="architecture-controls" role="group" aria-label="Architecture components">
          ${architectureNodes.map((node) => `<button type="button" data-node="${node.id}" class="${node.id === "market" ? "active" : ""}"><span class="node-dot ${node.layer}"></span>${node.label.replace("\n", " ")}</button>`).join("")}
        </div>
      </div>
    </section>

    <section class="park-section" id="park">
      <div class="park-intro wrap">
        <span class="kicker">Protocol Park</span>
        <h2>Infrastructure should feel alive.</h2>
        <p>Walk the route from shared foundations to the first market—and see the two-actor lifecycle advancing under an explicit no-broadcast boundary.</p>
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
        <a class="park-marker marker-next" href="#timeline" aria-label="Two-actor lifecycle planning is in progress">
          <span>03</span><strong>Two-actor lifecycle</strong><small>fork pass · no authorization</small>
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
        <p>The answer sits next to every receipt. Faucet events are intentionally outside the 29 project-signed total.</p>
      </div>
      <div class="wrap toolbar">
        <div class="filter-group" role="group" aria-label="Filter transactions">
          <button class="filter active" type="button" data-tx-filter="all">All 31 events</button>
          <button class="filter" type="button" data-tx-filter="shared">16 shared</button>
          <button class="filter" type="button" data-tx-filter="genesis">13 genesis</button>
          <button class="filter" type="button" data-tx-filter="funding">2 external funding</button>
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
          <h2>Genesis complete.<br/>Lifecycle next.</h2>
          <p>The graph exists. Now the harder proof begins: two actors, bounded collateral, one option position, premium and solvency observations, a clean close, and explicit cleanup.</p>
          <dl>
            <div><dt>Reconciled block</dt><dd>${terminalFacts.referenceBlock.toLocaleString()}</dd></div>
            <div><dt>LP NFT</dt><dd>#${terminalFacts.lpNft}</dd></div>
            <div><dt>SFPM pool ID</dt><dd>${terminalFacts.sfpmPoolId}</dd></div>
            <div><dt>Authorization</dt><dd>Closed · 0 actions remain</dd></div>
          </dl>
          <a class="primary-button" href="${repoUrl("docs/roadmap/2026-09-09-market-genesis.md")}" target="_blank" rel="noreferrer">Inspect the next gate ${icon("external")}</a>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="wrap footer-grid">
      <div><a class="wordmark" href="#top"><span class="mark">S</span><span>StonkHedge</span></a><p>Mechanism testing in public, with receipts.</p></div>
      <div><span>Source of truth</span><a href="${repoUrl("docs/architecture/robinhood-testnet-system.md")}" target="_blank" rel="noreferrer">Architecture</a><a href="${repoUrl("manifests/markets/robinhood-testnet-pltr-weth-public-genesis-2026-09-11.json")}" target="_blank" rel="noreferrer">Genesis manifest</a></div>
      <div><span>Boundaries</span><p>Robinhood Chain Testnet only. No real value. No public trading lifecycle yet.</p></div>
    </div>
  </footer>

  <dialog id="evidence-dialog">
    <button class="dialog-close" type="button" aria-label="Close evidence panel">×</button>
    <div id="dialog-content"></div>
  </dialog>
  <div class="toast" role="status" aria-live="polite"></div>
`;

const nodeDescription = (node: ArchitectureNode) => {
  const contract = node.contractId ? contracts.find((candidate) => candidate.id === node.contractId) : undefined;
  const descriptions: Record<string, string> = {
    assets: "Five faucet Stock Tokens plus WETH are external test assets. PLTR is the first market's base asset.",
    liquidity: "Position NFT 3903 supplies bounded two-sided liquidity to the exact PLTR/WETH PoolKey.",
    next: "A separately planned two-actor lifecycle will test collateral, options, premium, solvency, close, and cleanup.",
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
