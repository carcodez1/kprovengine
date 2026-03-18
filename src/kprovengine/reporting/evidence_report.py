from __future__ import annotations

import json
import mimetypes
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from kprovengine.manifest.hashing import sha256_file
from kprovengine.version import __version__

TEXT_EXTENSIONS = {
    ".json",
    ".md",
    ".txt",
    ".py",
    ".toml",
    ".yaml",
    ".yml",
    ".csv",
    ".log",
    ".eml",
    ".html",
    ".css",
    ".js",
}

TEXT_SIZE_LIMIT_BYTES = 2_000_000


@dataclass(frozen=True)
class GitMetadata:
    repo_root: str
    relative_path: str
    tracked: bool
    status: str
    last_commit: str | None
    last_author: str | None
    last_author_email: str | None
    last_committed_at: str | None
    commit_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "relative_path": self.relative_path,
            "tracked": self.tracked,
            "status": self.status,
            "last_commit": self.last_commit,
            "last_author": self.last_author,
            "last_author_email": self.last_author_email,
            "last_committed_at": self.last_committed_at,
            "commit_count": self.commit_count,
        }


def build_report_archive(manifest_path: str | Path) -> dict[str, Any]:
    manifest_file = Path(manifest_path).expanduser().resolve()
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    artifacts = [_enrich_artifact(a) for a in manifest.get("artifacts", [])]
    claims = [_normalize_claim(c) for c in manifest.get("claims", [])]
    cost_models = [_normalize_cost_model(c) for c in manifest.get("cost_models", [])]
    edges = [_normalize_edge(e) for e in manifest.get("edges", [])]

    archive = {
        "generated_at": _iso_utc(datetime.now(UTC)),
        "generator": {"name": "kprovengine", "version": __version__},
        "manifest_path": str(manifest_file),
        "report": manifest.get("report", {}),
        "subject": manifest.get("subject", {}),
        "summary_notes": manifest.get("summary_notes", []),
        "artifacts": artifacts,
        "claims": claims,
        "cost_models": cost_models,
        "edges": edges,
        "stats": _build_stats(artifacts, cost_models),
    }
    return archive


def render_report_html(archive: dict[str, Any]) -> str:
    payload = json.dumps(archive, indent=2, sort_keys=True)
    title = archive.get("report", {}).get("title") or "Evidence Report"
    subtitle = archive.get("report", {}).get("subtitle") or ""
    subject = archive.get("subject", {})
    subject_line = " | ".join(
        part
        for part in (
            subject.get("consultant"),
            subject.get("client"),
            subject.get("matter"),
        )
        if part
    )
    template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE__</title>
  <style>
    :root {{
      --bg: #07111f;
      --panel: rgba(9, 18, 33, 0.86);
      --panel-2: rgba(16, 27, 47, 0.92);
      --line: rgba(145, 181, 255, 0.22);
      --line-strong: rgba(120, 171, 255, 0.6);
      --text: #eaf1ff;
      --muted: #a9bbda;
      --accent: #7dd3fc;
      --accent-2: #38bdf8;
      --good: #86efac;
      --warn: #fcd34d;
      --bad: #fda4af;
      --shadow: 0 24px 80px rgba(0, 0, 0, 0.36);
      --radius: 18px;
      --font: "SF Pro Display", "Segoe UI", Inter, Helvetica, Arial, sans-serif;
      --mono: "SFMono-Regular", "Cascadia Code", Menlo, Consolas, monospace;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--font);
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(56, 189, 248, 0.22), transparent 28%),
        radial-gradient(circle at top right, rgba(59, 130, 246, 0.18), transparent 24%),
        linear-gradient(180deg, #040913 0%, #07111f 100%);
      min-height: 100vh;
    }}
    a {{
      color: var(--accent);
      text-decoration: none;
    }}
    a:hover {{ text-decoration: underline; }}
    .shell {{
      max-width: 1600px;
      margin: 0 auto;
      padding: 28px;
      display: grid;
      gap: 18px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.6fr 1fr;
      gap: 18px;
    }}
    .card {{
      background: var(--panel);
      backdrop-filter: blur(18px);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }}
    .hero-main {{
      padding: 28px;
    }}
    .hero-main h1 {{
      margin: 0;
      font-size: 36px;
      letter-spacing: -0.04em;
    }}
    .hero-main p {{
      margin: 12px 0 0;
      color: var(--muted);
      line-height: 1.5;
      max-width: 70ch;
    }}
    .hero-meta {{
      margin-top: 20px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .pill {{
      border: 1px solid var(--line);
      background: rgba(56, 189, 248, 0.08);
      color: var(--text);
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 13px;
    }}
    .stats {{
      padding: 22px;
      display: grid;
      gap: 12px;
    }}
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}
    .stat {{
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
    }}
    .stat-label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .stat-value {{
      margin-top: 8px;
      font-size: 28px;
      font-weight: 700;
    }}
    .notes {{
      padding: 18px 22px;
      display: grid;
      gap: 10px;
    }}
    .note {{
      padding: 12px 14px;
      border-left: 3px solid var(--accent-2);
      background: rgba(56, 189, 248, 0.08);
      border-radius: 12px;
      color: var(--muted);
    }}
    .workspace {{
      display: grid;
      grid-template-columns: 1.3fr 0.95fr;
      gap: 18px;
      min-height: 700px;
    }}
    .graph-panel {{
      padding: 20px;
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 14px;
    }}
    .panel-head {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
    }}
    .panel-head h2 {{
      margin: 0;
      font-size: 22px;
      letter-spacing: -0.02em;
    }}
    .panel-head p {{
      margin: 8px 0 0;
      color: var(--muted);
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .toolbar input, .toolbar select {{
      min-width: 180px;
      background: var(--panel-2);
      color: var(--text);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 11px 12px;
      font: inherit;
    }}
    #graph {{
      width: 100%;
      height: 100%;
      min-height: 520px;
      border-radius: 18px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0)),
        rgba(3, 8, 18, 0.65);
      border: 1px solid var(--line);
    }}
    .details {{
      padding: 18px;
      display: grid;
      gap: 12px;
      grid-template-rows: auto auto 1fr;
    }}
    .details h2 {{
      margin: 0;
      font-size: 22px;
    }}
    .detail-card {{
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      display: grid;
      gap: 10px;
    }}
    .detail-card h3 {{
      margin: 0;
      font-size: 18px;
    }}
    .detail-card p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.45;
    }}
    .detail-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px 10px;
      font-size: 14px;
    }}
    .detail-grid dt {{
      color: var(--muted);
    }}
    .detail-grid dd {{
      margin: 0;
      font-family: var(--mono);
      word-break: break-word;
    }}
    .linked-list {{
      display: grid;
      gap: 8px;
      max-height: 280px;
      overflow: auto;
    }}
    .linked-item {{
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.02);
      border-radius: 12px;
      padding: 10px 12px;
      font-size: 14px;
    }}
    .tables {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
    }}
    .table-panel {{
      padding: 18px;
      display: grid;
      gap: 12px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    thead th {{
      text-align: left;
      color: var(--muted);
      font-weight: 600;
      padding: 0 0 10px;
      border-bottom: 1px solid var(--line);
    }}
    tbody td {{
      padding: 12px 0;
      border-bottom: 1px solid rgba(145, 181, 255, 0.12);
      vertical-align: top;
    }}
    .mono {{
      font-family: var(--mono);
      font-size: 13px;
      word-break: break-word;
    }}
    .tag-list {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .tag {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      padding: 5px 8px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--muted);
      background: rgba(255,255,255,0.02);
    }}
    .confidence-high {{ color: var(--good); }}
    .confidence-medium {{ color: var(--warn); }}
    .confidence-low {{ color: var(--bad); }}
    .footer {{
      color: var(--muted);
      text-align: right;
      font-size: 13px;
      padding-bottom: 8px;
    }}
    @media (max-width: 1180px) {{
      .hero,
      .workspace,
      .tables {{
        grid-template-columns: 1fr;
      }}
      .stats-grid {{
        grid-template-columns: repeat(4, 1fr);
      }}
    }}
    @media (max-width: 880px) {{
      .shell {{
        padding: 16px;
      }}
      .stats-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .detail-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <article class="card hero-main">
        <h1>__TITLE__</h1>
        <p>__SUBTITLE__</p>
        <div class="hero-meta">
          <span class="pill">__SUBJECT_LINE__</span>
          <span class="pill">Generated by kprovengine __VERSION__</span>
          <span class="pill">__GENERATED_AT__</span>
        </div>
      </article>
      <aside class="card stats">
        <div class="stats-grid" id="stats-grid"></div>
      </aside>
    </section>

    <section class="card notes" id="notes"></section>

    <section class="workspace">
      <article class="card graph-panel">
        <div class="panel-head">
          <div>
            <h2>Interactive Evidence Map</h2>
            <p>Artifacts, claims, and cost models are linked explicitly. Click a node to inspect the source, file stats, and relationship chain.</p>
          </div>
        </div>
        <div class="toolbar">
          <input id="search" type="search" placeholder="Filter by file, tag, claim, or summary">
          <select id="kind-filter">
            <option value="all">All node types</option>
            <option value="artifact">Artifacts only</option>
            <option value="claim">Claims only</option>
            <option value="cost_model">Cost models only</option>
          </select>
        </div>
        <svg id="graph" viewBox="0 0 1100 620" preserveAspectRatio="xMidYMid meet"></svg>
      </article>

      <aside class="card details">
        <h2>Selected Node</h2>
        <div class="detail-card" id="selected-node"></div>
        <div class="detail-card">
          <h3>Linked Evidence</h3>
          <div class="linked-list" id="linked-evidence"></div>
        </div>
      </aside>
    </section>

    <section class="tables">
      <article class="card table-panel">
        <div class="panel-head">
          <div>
            <h2>Artifact Archive</h2>
            <p>Every file or source used in this report, enriched with hashes, timestamps, and Git metadata where available.</p>
          </div>
        </div>
        <div id="artifact-table"></div>
      </article>

      <article class="card table-panel">
        <div class="panel-head">
          <div>
            <h2>Cost Models</h2>
            <p>Defensible floor, likely professional value, and replacement-cost framing live side by side.</p>
          </div>
        </div>
        <div id="cost-table"></div>
      </article>
    </section>

    <div class="footer">Manifest: <span class="mono">__MANIFEST_PATH__</span></div>
  </div>

  <script>
    const REPORT_DATA = __PAYLOAD__;

    const state = {{
      query: "",
      kind: "all",
      selectedId: null,
    }};

    const statsGrid = document.getElementById("stats-grid");
    const notesEl = document.getElementById("notes");
    const graphEl = document.getElementById("graph");
    const selectedNodeEl = document.getElementById("selected-node");
    const linkedEvidenceEl = document.getElementById("linked-evidence");
    const artifactTableEl = document.getElementById("artifact-table");
    const costTableEl = document.getElementById("cost-table");
    const searchEl = document.getElementById("search");
    const kindFilterEl = document.getElementById("kind-filter");

    const allNodes = [
      ...REPORT_DATA.artifacts.map((item) => ({{ ...item, node_type: "artifact" }})),
      ...REPORT_DATA.claims.map((item) => ({{ ...item, node_type: "claim" }})),
      ...REPORT_DATA.cost_models.map((item) => ({{ ...item, node_type: "cost_model" }})),
    ];

    const edges = REPORT_DATA.edges;
    const nodeIndex = Object.fromEntries(allNodes.map((node) => [node.id, node]));

    function confidenceClass(confidence) {{
      if (!confidence) return "";
      const normalized = confidence.toLowerCase();
      if (normalized.startsWith("high")) return "confidence-high";
      if (normalized.startsWith("low")) return "confidence-low";
      return "confidence-medium";
    }}

    function bytesLabel(value) {{
      if (!value && value !== 0) return "n/a";
      const units = ["B", "KB", "MB", "GB"];
      let size = value;
      let unit = units[0];
      for (const candidate of units) {{
        unit = candidate;
        if (size < 1024 || candidate === units[units.length - 1]) break;
        size /= 1024;
      }}
      return `${{size.toFixed(size >= 10 || unit === "B" ? 0 : 1)}} ${{unit}}`;
    }}

    function statCard(label, value) {{
      return `<div class="stat"><div class="stat-label">${{label}}</div><div class="stat-value">${{value}}</div></div>`;
    }}

    function renderStats() {{
      const stats = REPORT_DATA.stats;
      statsGrid.innerHTML = [
        statCard("Artifacts", stats.artifact_count),
        statCard("Local files", stats.local_artifact_count),
        statCard("Git enriched", stats.git_enriched_count),
        statCard("Total bytes", bytesLabel(stats.total_bytes)),
      ].join("");
    }}

    function renderNotes() {{
      const notes = REPORT_DATA.summary_notes || [];
      notesEl.innerHTML = notes.length
        ? notes.map((note) => `<div class="note">${{note}}</div>`).join("")
        : `<div class="note">No summary notes were provided in the manifest.</div>`;
    }}

    function nodeMatches(node) {{
      const kindMatches = state.kind === "all" || node.node_type === state.kind;
      const haystack = [
        node.label,
        node.summary,
        ...(node.tags || []),
        node.kind,
        node.path,
        node.url,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return kindMatches && haystack.includes(state.query);
    }}

    function filteredNodes() {{
      return allNodes.filter(nodeMatches);
    }}

    function filteredEdges(visibleIds) {{
      return edges.filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target));
    }}

    function nodeColor(nodeType) {{
      if (nodeType === "claim") return "#7dd3fc";
      if (nodeType === "cost_model") return "#c084fc";
      return "#38bdf8";
    }}

    function buildLayout(nodes) {{
      const columns = {{
        artifact: 170,
        claim: 560,
        cost_model: 930,
      }};
      const groups = {{
        artifact: nodes.filter((node) => node.node_type === "artifact"),
        claim: nodes.filter((node) => node.node_type === "claim"),
        cost_model: nodes.filter((node) => node.node_type === "cost_model"),
      }};
      const positions = {{}};
      for (const [kind, items] of Object.entries(groups)) {{
        const gap = Math.max(88, 520 / Math.max(items.length, 1));
        items.forEach((item, index) => {{
          positions[item.id] = {{
            x: columns[kind],
            y: 80 + (index * gap),
          }};
        }});
      }}
      return positions;
    }}

    function renderGraph() {{
      const nodes = filteredNodes();
      const visibleIds = new Set(nodes.map((node) => node.id));
      const visibleEdges = filteredEdges(visibleIds);
      const positions = buildLayout(nodes);

      const labels = {{
        artifact: "Artifacts",
        claim: "Claims",
        cost_model: "Cost models",
      }};
      const headings = Object.entries(labels)
        .map(([kind, label]) => {{
          const x = kind === "artifact" ? 80 : kind === "claim" ? 470 : 830;
          return `<text x="${{x}}" y="32" fill="rgba(234,241,255,0.72)" font-size="16" font-weight="600">${{label}}</text>`;
        }})
        .join("");

      const edgeSvg = visibleEdges
        .map((edge) => {{
          const source = positions[edge.source];
          const target = positions[edge.target];
          const active = state.selectedId && (edge.source === state.selectedId || edge.target === state.selectedId);
          const stroke = active ? "var(--line-strong)" : "rgba(125, 211, 252, 0.15)";
          const width = active ? 2.4 : 1.3;
          const path = `M ${{source.x + 50}} ${{source.y}} C ${{source.x + 140}} ${{source.y}}, ${{target.x - 140}} ${{target.y}}, ${{target.x - 50}} ${{target.y}}`;
          return `<path d="${{path}}" fill="none" stroke="${{stroke}}" stroke-width="${{width}}" />`;
        }})
        .join("");

      const nodeSvg = nodes
        .map((node) => {{
          const pos = positions[node.id];
          const selected = node.id === state.selectedId;
          const width = node.node_type === "artifact" ? 250 : 230;
          const height = 56;
          const x = pos.x - width / 2;
          const y = pos.y - height / 2;
          const tags = (node.tags || []).slice(0, 2).join(" · ");
          const meta = node.node_type === "cost_model"
            ? (node.amount !== null && node.amount !== undefined ? `$${{Number(node.amount).toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }})}}` : "Cost model")
            : node.kind || node.node_type;
          return `
            <g class="graph-node" data-node-id="${{node.id}}" transform="translate(${{x}}, ${{y}})" style="cursor:pointer">
              <rect width="${{width}}" height="${{height}}" rx="14"
                fill="${{selected ? "rgba(56, 189, 248, 0.20)" : "rgba(13, 25, 47, 0.96)"}}"
                stroke="${{selected ? "rgba(125, 211, 252, 0.95)" : "rgba(145, 181, 255, 0.24)"}}"
                stroke-width="${{selected ? 2 : 1.1}}" />
              <circle cx="18" cy="28" r="6" fill="${{nodeColor(node.node_type)}}" />
              <text x="34" y="24" fill="#eaf1ff" font-size="14" font-weight="600">${{escapeXml(node.label)}}</text>
              <text x="34" y="42" fill="rgba(234,241,255,0.58)" font-size="11">${{escapeXml(meta)}}${{tags ? " · " + escapeXml(tags) : ""}}</text>
            </g>`;
        }})
        .join("");

      graphEl.innerHTML = headings + edgeSvg + nodeSvg;
      graphEl.querySelectorAll(".graph-node").forEach((element) => {{
        element.addEventListener("click", () => {{
          state.selectedId = element.getAttribute("data-node-id");
          renderGraph();
          renderSelection();
        }});
      }});

      if (!state.selectedId && nodes.length) {{
        state.selectedId = nodes[0].id;
        renderGraph();
        renderSelection();
      }}
    }}

    function escapeXml(value) {{
      return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    function renderSelection() {{
      const node = nodeIndex[state.selectedId];
      if (!node) {{
        selectedNodeEl.innerHTML = "<p>Select a node from the graph.</p>";
        linkedEvidenceEl.innerHTML = "";
        return;
      }}

      const links = [];
      if (node.path) {{
        links.push(`<a href="${{pathToFileUri(node.path)}}" target="_blank">Open local file</a>`);
      }}
      if (node.url) {{
        links.push(`<a href="${{node.url}}" target="_blank">Open source URL</a>`);
      }}

      const metadata = [
        ["Type", node.node_type],
        ["Kind", node.kind || "n/a"],
        ["Confidence", node.confidence || "n/a"],
      ];
      if (node.path) metadata.push(["Path", node.path]);
      if (node.url) metadata.push(["URL", node.url]);
      if (node.sha256) metadata.push(["SHA-256", node.sha256]);
      if (node.size_bytes !== null && node.size_bytes !== undefined) metadata.push(["Size", bytesLabel(node.size_bytes)]);
      if (node.modified_at) metadata.push(["Modified", node.modified_at]);
      if (node.git && node.git.repo_root) {{
        metadata.push(["Git repo", node.git.repo_root]);
        metadata.push(["Git tracked", String(node.git.tracked)]);
        metadata.push(["Git status", node.git.status || "clean"]);
        metadata.push(["Last commit", node.git.last_commit || "n/a"]);
      }}
      if (node.amount !== null && node.amount !== undefined) metadata.push(["Amount", `$${{Number(node.amount).toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }})}}`]);
      if (node.hours !== null && node.hours !== undefined) metadata.push(["Hours", String(node.hours)]);
      if (node.rate !== null && node.rate !== undefined) metadata.push(["Rate", `$${{Number(node.rate).toFixed(2)}}`]);

      selectedNodeEl.innerHTML = `
        <h3>${{node.label}}</h3>
        <p>${{node.summary || "No summary provided."}}</p>
        <div class="tag-list">${{(node.tags || []).map((tag) => `<span class="tag">${{tag}}</span>`).join("")}}</div>
        <div>${{links.join(" · ")}}</div>
        <dl class="detail-grid">
          ${{metadata.map(([label, value]) => `<dt>${{label}}</dt><dd class="${{label === "Confidence" ? confidenceClass(String(value)) : ""}}">${{escapeHtml(value)}}</dd>`).join("")}}
        </dl>`;

      const related = edges
        .filter((edge) => edge.source === node.id || edge.target === node.id)
        .map((edge) => {{
          const otherId = edge.source === node.id ? edge.target : edge.source;
          const other = nodeIndex[otherId];
          return {{ edge, other }};
        }})
        .sort((a, b) => a.other.label.localeCompare(b.other.label));

      linkedEvidenceEl.innerHTML = related.length
        ? related.map(({ edge, other }) => `
            <div class="linked-item">
              <strong>${{other.label}}</strong><br>
              <span class="mono">${{edge.kind}}</span><br>
              <span style="color:var(--muted)">${{other.summary || "No summary provided."}}</span>
            </div>`).join("")
        : `<div class="linked-item">No linked nodes for this selection.</div>`;
    }}

    function escapeHtml(value) {{
      return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }}

    function pathToFileUri(path) {{
      return "file://" + encodeURI(path);
    }}

    function renderArtifactTable() {{
      const artifacts = REPORT_DATA.artifacts.filter(nodeMatches);
      artifactTableEl.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Artifact</th>
              <th>Stats / linkage</th>
            </tr>
          </thead>
          <tbody>
            ${artifacts.map((item) => `
              <tr>
                <td>
                  <strong>${{item.label}}</strong><br>
                  <span class="tag">${{item.kind || "artifact"}}</span>
                  <span class="tag ${confidenceClass(item.confidence)}">${{item.confidence || "n/a"}}</span>
                  <p style="margin-top:8px">${{item.summary || ""}}</p>
                </td>
                <td>
                  <div class="mono">${{item.path || item.url || "n/a"}}</div>
                  <div>Size: ${{bytesLabel(item.size_bytes)}}</div>
                  <div>SHA-256: <span class="mono">${{item.sha256 || "n/a"}}</span></div>
                  <div>Git: ${{item.git && item.git.repo_root ? item.git.repo_root : "not available"}}</div>
                </td>
              </tr>`).join("")}
          </tbody>
        </table>`;
    }}

    function renderCostTable() {{
      const costs = REPORT_DATA.cost_models.filter(nodeMatches);
      costTableEl.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Hours / amount</th>
            </tr>
          </thead>
          <tbody>
            ${costs.map((item) => `
              <tr>
                <td>
                  <strong>${{item.label}}</strong><br>
                  <span class="tag ${confidenceClass(item.confidence)}">${{item.confidence || "n/a"}}</span>
                  <p style="margin-top:8px">${{item.summary || ""}}</p>
                </td>
                <td>
                  <div>Hours: <span class="mono">${{item.hours ?? "n/a"}}</span></div>
                  <div>Rate: <span class="mono">${{item.rate !== null && item.rate !== undefined ? "$" + Number(item.rate).toFixed(2) : "n/a"}}</span></div>
                  <div>Amount: <span class="mono">${{item.amount !== null && item.amount !== undefined ? "$" + Number(item.amount).toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }}) : "n/a"}}</span></div>
                </td>
              </tr>`).join("")}
          </tbody>
        </table>`;
    }}

    function sync() {{
      renderStats();
      renderNotes();
      renderGraph();
      renderArtifactTable();
      renderCostTable();
      renderSelection();
    }}

    searchEl.addEventListener("input", (event) => {{
      state.query = event.target.value.trim().toLowerCase();
      state.selectedId = null;
      sync();
    }});

    kindFilterEl.addEventListener("change", (event) => {{
      state.kind = event.target.value;
      state.selectedId = null;
      sync();
    }});

    sync();
  </script>
</body>
</html>
"""
    template = template.replace("{{", "{").replace("}}", "}")

    return (
        template.replace("__TITLE__", escape(title))
        .replace("__SUBTITLE__", escape(subtitle))
        .replace("__SUBJECT_LINE__", escape(subject_line or "Evidence-focused consulting dossier"))
        .replace("__VERSION__", escape(archive["generator"]["version"]))
        .replace("__GENERATED_AT__", escape(archive["generated_at"]))
        .replace("__MANIFEST_PATH__", escape(archive["manifest_path"]))
        .replace("__PAYLOAD__", payload)
    )


def write_report(manifest_path: str | Path, html_output: str | Path, archive_output: str | Path | None = None) -> dict[str, Any]:
    archive = build_report_archive(manifest_path)
    html = render_report_html(archive)

    html_path = Path(html_output).expanduser()
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")

    if archive_output is not None:
        archive_path = Path(archive_output).expanduser()
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path.write_text(json.dumps(archive, indent=2, sort_keys=True), encoding="utf-8")

    return archive


def _normalize_claim(claim: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(claim)
    normalized.setdefault("kind", "claim")
    normalized.setdefault("tags", [])
    return normalized


def _normalize_cost_model(cost_model: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(cost_model)
    normalized.setdefault("kind", "cost_model")
    normalized.setdefault("tags", [])
    return normalized


def _normalize_edge(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": edge["source"],
        "target": edge["target"],
        "kind": edge.get("kind", "supports"),
    }


def _enrich_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(artifact)
    enriched.setdefault("tags", [])
    enriched.setdefault("kind", "artifact")
    enriched["size_bytes"] = None
    enriched["sha256"] = None
    enriched["modified_at"] = None
    enriched["created_at"] = None
    enriched["mime_type"] = None
    enriched["line_count"] = None
    enriched["git"] = None

    raw_path = artifact.get("path")
    if raw_path:
        path = Path(raw_path).expanduser().resolve()
        enriched["path"] = str(path)
        if path.exists():
            stat = path.stat()
            enriched["size_bytes"] = stat.st_size
            enriched["modified_at"] = _iso_utc(datetime.fromtimestamp(stat.st_mtime, tz=UTC))
            enriched["created_at"] = _iso_utc(datetime.fromtimestamp(stat.st_ctime, tz=UTC))
            enriched["mime_type"] = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            if path.is_file():
                enriched["sha256"] = sha256_file(path)
                enriched["line_count"] = _line_count(path)
            git = _git_metadata(path)
            enriched["git"] = git.to_dict() if git is not None else None
        else:
            enriched["missing"] = True

    return enriched


def _line_count(path: Path) -> int | None:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return None
    if path.stat().st_size > TEXT_SIZE_LIMIT_BYTES:
        return None
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return None


def _git_metadata(path: Path) -> GitMetadata | None:
    if not path.exists():
        return None
    directory = path if path.is_dir() else path.parent
    repo_root = _git_command(["git", "-C", str(directory), "rev-parse", "--show-toplevel"])
    if repo_root is None:
        return None

    repo_path = Path(repo_root)
    relative_path = str(path.relative_to(repo_path))
    tracked = _git_command(["git", "-C", repo_root, "ls-files", "--error-unmatch", relative_path]) is not None
    status = _git_command(["git", "-C", repo_root, "status", "--short", "--", relative_path]) or ""

    last_commit = None
    last_author = None
    last_author_email = None
    last_committed_at = None
    commit_count = 0

    if tracked:
        log_line = _git_command(
            [
                "git",
                "-C",
                repo_root,
                "log",
                "-1",
                "--format=%H%x1f%an%x1f%ae%x1f%aI",
                "--",
                relative_path,
            ]
        )
        if log_line:
            parts = log_line.split("\x1f")
            if len(parts) == 4:
                last_commit, last_author, last_author_email, last_committed_at = parts

        commit_history = _git_command(
            ["git", "-C", repo_root, "log", "--format=%H", "--", relative_path]
        )
        if commit_history:
            commit_count = len([line for line in commit_history.splitlines() if line.strip()])

    return GitMetadata(
        repo_root=repo_root,
        relative_path=relative_path,
        tracked=tracked,
        status=status.strip(),
        last_commit=last_commit,
        last_author=last_author,
        last_author_email=last_author_email,
        last_committed_at=last_committed_at,
        commit_count=commit_count,
    )


def _git_command(args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _build_stats(artifacts: list[dict[str, Any]], cost_models: list[dict[str, Any]]) -> dict[str, Any]:
    local_artifacts = [artifact for artifact in artifacts if artifact.get("path")]
    git_enriched = [artifact for artifact in artifacts if artifact.get("git")]
    total_bytes = sum(int(artifact["size_bytes"]) for artifact in local_artifacts if artifact.get("size_bytes"))
    return {
        "artifact_count": len(artifacts),
        "local_artifact_count": len(local_artifacts),
        "external_artifact_count": len([artifact for artifact in artifacts if artifact.get("url")]),
        "git_enriched_count": len(git_enriched),
        "missing_artifact_count": len([artifact for artifact in artifacts if artifact.get("missing")]),
        "total_bytes": total_bytes,
        "cost_model_count": len(cost_models),
    }


def _iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
