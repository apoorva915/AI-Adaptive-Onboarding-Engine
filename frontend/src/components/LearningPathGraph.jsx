import React, { useMemo } from "react";

export default function LearningPathGraph({ graph }) {
  const { nodes, edges } = graph || {};

  const layout = useMemo(() => {
    const safeNodes = Array.isArray(nodes) ? nodes : [];
    const safeEdges = Array.isArray(edges) ? edges : [];

    const byId = new Map();
    for (const n of safeNodes) {
      if (n?.id) byId.set(n.id, n);
    }

    // Build predecessor map for layering.
    const preds = new Map();
    const succs = new Map();
    const indeg = new Map();

    for (const n of safeNodes) {
      preds.set(n.id, new Set());
      succs.set(n.id, new Set());
      indeg.set(n.id, 0);
    }

    for (const e of safeEdges) {
      if (!byId.has(e.source) || !byId.has(e.target)) continue;
      preds.get(e.target).add(e.source);
      succs.get(e.source).add(e.target);
      indeg.set(e.target, (indeg.get(e.target) || 0) + 1);
    }

    // Topological order (Kahn) to compute depths (left-to-right DAG layout).
    const q = [];
    for (const [id, d] of indeg.entries()) {
      if (d === 0) q.push(id);
    }

    const topo = [];
    while (q.length) {
      const id = q.shift();
      topo.push(id);
      for (const nxt of succs.get(id) || []) {
        indeg.set(nxt, (indeg.get(nxt) || 0) - 1);
        if (indeg.get(nxt) === 0) q.push(nxt);
      }
    }

    // Depth = longest path from any source (based on prerequisites).
    const depth = new Map();
    for (const id of topo) {
      const p = preds.get(id) || new Set();
      let best = 0;
      for (const pre of p) {
        best = Math.max(best, (depth.get(pre) || 0) + 1);
      }
      depth.set(id, best);
    }

    // Group nodes by depth (columns).
    const layers = new Map();
    let maxDepth = 0;
    for (const id of byId.keys()) {
      const d = depth.get(id) || 0;
      maxDepth = Math.max(maxDepth, d);
      if (!layers.has(d)) layers.set(d, []);
      layers.get(d).push(id);
    }

    // Sort nodes in each layer by their step (stable, looks nicer).
    for (const [d, ids] of layers.entries()) {
      ids.sort((a, b) => (byId.get(a)?.step ?? 0) - (byId.get(b)?.step ?? 0));
    }

    // Layout constants
    const nodeW = 300;
    const nodeH = 72;
    const gapX = 130;
    const gapY = 36;
    const padX = 28;
    const padY = 24;

    const maxRows = Math.max(...Array.from(layers.values()).map((v) => v.length), 1);
    const width = padX * 2 + (maxDepth + 1) * nodeW + maxDepth * gapX;
    const height = padY * 2 + maxRows * nodeH + Math.max(0, maxRows - 1) * gapY;

    // Assign positions within each layer, centered vertically.
    const positions = new Map();
    for (let d = 0; d <= maxDepth; d++) {
      const ids = layers.get(d) || [];
      const colX = padX + d * (nodeW + gapX);
      const colHeight = ids.length * nodeH + Math.max(0, ids.length - 1) * gapY;
      const startY = padY + (height - padY * 2 - colHeight) / 2;
      ids.forEach((id, i) => {
        positions.set(id, { x: colX, y: startY + i * (nodeH + gapY) });
      });
    }

    // Draw edges as clean beziers (left-to-right).
    const drawnEdges = safeEdges
      .map((e) => {
        const s = positions.get(e.source);
        const t = positions.get(e.target);
        if (!s || !t) return null;

        const x1 = s.x + nodeW;
        const y1 = s.y + nodeH / 2;
        const x2 = t.x;
        const y2 = t.y + nodeH / 2;

        const dx = Math.max(60, (x2 - x1) * 0.55);
        const c1x = x1 + dx;
        const c2x = x2 - dx;

        return { ...e, x1, y1, x2, y2, c1x, c2x };
      })
      .filter(Boolean);

    // Node draw order: left to right, top to bottom.
    const sorted = [];
    for (let d = 0; d <= maxDepth; d++) {
      for (const id of layers.get(d) || []) sorted.push(byId.get(id));
    }

    return { sorted, drawnEdges, positions, width, height, nodeW, nodeH, depth };
  }, [nodes, edges]);

  const safeNodes = Array.isArray(nodes) ? nodes : [];
  const safeEdges = Array.isArray(edges) ? edges : [];

  if (safeNodes.length === 0) {
    return <div className="empty">No learning graph data.</div>;
  }

  return (
    <div className="lp-graph">
      <svg
        className="lp-graph-svg"
        viewBox={`0 0 ${layout.width} ${layout.height}`}
        role="img"
        aria-label="Adaptive learning path graph"
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(47,128,237,0.85)" />
          </marker>
        </defs>

        {layout.drawnEdges.map((e, idx) => (
          <path
            key={`${e.source}-${e.target}-${idx}`}
            d={`M ${e.x1} ${e.y1} C ${e.c1x} ${e.y1}, ${e.c2x} ${e.y2}, ${e.x2} ${e.y2}`}
            fill="none"
            stroke="rgba(14,165,233,0.62)"
            strokeWidth="2.2"
            markerEnd="url(#arrow)"
          />
        ))}

        {layout.sorted.map((n) => {
          const p = layout.positions.get(n.id);
          if (!p) return null;

          const label = n.label ?? n.id;
          const level = (layout.depth.get(n.id) || 0) + 1;
          const stepText = `Level ${level}`;

          return (
            <g key={n.id} transform={`translate(${p.x}, ${p.y})`}>
              <rect
                x="0"
                y="0"
                rx="10"
                ry="10"
                width={layout.nodeW}
                height={layout.nodeH}
                fill="#ffffff"
                stroke="#d8e2f0"
                style={{ filter: "drop-shadow(0 6px 16px rgba(31,42,68,0.10))" }}
              />
              {n.link ? (
                <a href={n.link} target="_blank" rel="noreferrer">
                  <g transform={`translate(${layout.nodeW - 102},-18)`}>
                    <path
                      d="M10 0 H78 A10 10 0 0 1 88 10 V12 A10 10 0 0 1 78 22 H46 L40 28 L38 22 H10 A10 10 0 0 1 0 12 V10 A10 10 0 0 1 10 0 Z"
                      fill="#0ea5e9"
                      stroke="rgba(255,255,255,0.2)"
                    />
                    <text
                      x="44"
                      y="14.5"
                      textAnchor="middle"
                      fill="#ffffff"
                      fontSize="10"
                      fontWeight="600"
                      fontFamily="system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif"
                    >
                      Open Module
                    </text>
                  </g>
                </a>
              ) : (
                <g transform={`translate(${layout.nodeW - 150},-18)`}>
                  <path
                    d="M10 0 H126 A10 10 0 0 1 136 10 V12 A10 10 0 0 1 126 22 H72 L64 28 L62 22 H10 A10 10 0 0 1 0 12 V10 A10 10 0 0 1 10 0 Z"
                    fill="#eaf2ff"
                    stroke="#cedcf0"
                  />
                  <text
                    x="68"
                    y="14.5"
                    textAnchor="middle"
                    fill="#42567b"
                    fontSize="9.5"
                    fontWeight="600"
                    fontFamily="system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif"
                  >
                    No course module
                  </text>
                </g>
              )}
              <text
                x="14"
                y="28"
                fill="#6f7f9f"
                fontSize="12"
                fontFamily="system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif"
              >
                {stepText}
              </text>
              <text
                x="14"
                y="54"
                fill="#1f2a44"
                fontSize="13"
                fontWeight="500"
                fontFamily="system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif"
              >
                {label}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="skill-meta">
        Nodes: {safeNodes.length} • Edges: {safeEdges.length}
      </div>
    </div>
  );
}

