import { useEffect, useMemo, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

export const NODE_COLORS = {
  Candidate: '#6366f1', Question: '#f59e0b', Skill: '#10b981', Role: '#ef4444', Company: '#8b5cf6',
  Answer: '#94a3b8', Technology: '#06b6d4', InterviewRound: '#ec4899',
};
const RADIUS = { Candidate: 7, Role: 7, Company: 7, Skill: 5.5, Technology: 5, InterviewRound: 5, Question: 4, Answer: 3 };

export default function GraphViewer({ data, visibleTypes, search, selectedId, onSelect, height = 620 }) {
  const wrap = useRef(null);
  const fg = useRef(null);
  const fitted = useRef(false);
  const [width, setWidth] = useState(800);

  useEffect(() => {
    const el = wrap.current;
    if (!el) return undefined;
    const ro = new ResizeObserver(() => setWidth(el.clientWidth));
    ro.observe(el);
    setWidth(el.clientWidth);
    return () => ro.disconnect();
  }, []);

  const graph = useMemo(() => {
    const nodes = data.nodes.filter((n) => visibleTypes.has(n.type)).map((n) => ({ ...n }));
    const ids = new Set(nodes.map((n) => n.id));
    const links = data.links.filter((l) => ids.has(l.source) && ids.has(l.target)).map((l) => ({ ...l }));
    fitted.current = false;
    return { nodes, links };
  }, [data, visibleTypes]);

  const q = search.trim().toLowerCase();
  const matches = (n) => q && n.name.toLowerCase().includes(q);

  return (
    <div ref={wrap} className="card overflow-hidden bg-white">
      <ForceGraph2D
        ref={fg}
        width={width}
        height={height}
        graphData={graph}
        nodeLabel={(n) => `${n.type}: ${n.name}`}
        linkLabel={(l) => l.type}
        linkColor={() => 'rgba(100,116,139,0.35)'}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        cooldownTicks={120}
        onEngineStop={() => {
          if (!fitted.current && fg.current) {
            fg.current.zoomToFit(400, 40);
            fitted.current = true;
          }
        }}
        onNodeClick={(n) => onSelect(n)}
        onBackgroundClick={() => onSelect(null)}
        nodeCanvasObject={(node, ctx, scale) => {
          const r = RADIUS[node.type] || 4;
          const dim = q && !matches(node);
          ctx.globalAlpha = dim ? 0.12 : 1;
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
          ctx.fillStyle = NODE_COLORS[node.type] || '#64748b';
          ctx.fill();
          if (node.id === selectedId || matches(node)) {
            ctx.lineWidth = 2 / scale;
            ctx.strokeStyle = '#0f172a';
            ctx.stroke();
          }
          const showLabel = !dim && (scale > 2.2 || ['Candidate', 'Role', 'Company'].includes(node.type) || matches(node) || node.id === selectedId);
          if (showLabel) {
            const label = node.name.length > 28 ? `${node.name.slice(0, 27)}…` : node.name;
            ctx.font = `${11 / scale}px Sans-Serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillStyle = '#1e293b';
            ctx.fillText(label, node.x, node.y + r + 1);
          }
          ctx.globalAlpha = 1;
        }}
        nodePointerAreaPaint={(node, color, ctx) => {
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, (RADIUS[node.type] || 4) + 2, 0, 2 * Math.PI);
          ctx.fill();
        }}
      />
    </div>
  );
}