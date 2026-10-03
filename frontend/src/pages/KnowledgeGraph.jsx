import { useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Search } from 'lucide-react';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import GraphViewer, { NODE_COLORS } from '../components/GraphViewer';
import { Async, Badge, PageHeader } from '../components/ui';

const ALL_TYPES = Object.keys(NODE_COLORS);

function Details({ node, data, onFocus }) {
  const byId = useMemo(() => Object.fromEntries(data.nodes.map((n) => [n.id, n])), [data]);
  const edges = data.links.filter((l) => l.source === node.id || l.target === node.id);
  return (
    <div className="card space-y-3 p-4 text-sm">
      <div className="flex items-center gap-2">
        <span className="inline-block h-3 w-3 rounded-full" style={{ background: NODE_COLORS[node.type] }} />
        <b>{node.type}</b>
      </div>
      <div className="break-words font-medium text-slate-900">{node.name}</div>
      {node.type === 'Candidate' && (
        <div className="flex gap-2">
          <Link className="btn-primary" to={`/candidates/${encodeURIComponent(node.props.candidate_id)}`}>Open profile</Link>
          <button className="btn-ghost" onClick={() => onFocus(node.props.candidate_id)}>Focus subgraph</button>
        </div>
      )}
      <dl className="space-y-1 text-xs">
        {Object.entries(node.props).map(([k, v]) => (
          <div key={k}><dt className="inline font-semibold text-slate-500">{k}: </dt><dd className="inline break-words text-slate-700">{Array.isArray(v) ? v.join(', ') : String(v)}</dd></div>
        ))}
      </dl>
      <div>
        <div className="mb-1 text-xs font-semibold uppercase text-slate-500">Relationships ({edges.length})</div>
        <ul className="max-h-56 space-y-1 overflow-y-auto text-xs">
          {edges.slice(0, 60).map((e, i) => {
            const out = e.source === node.id;
            const other = byId[out ? e.target : e.source];
            return <li key={i}><Badge tone="indigo">{out ? '→' : '←'} {e.type}</Badge> {other?.name}</li>;
          })}
        </ul>
      </div>
    </div>
  );
}

export default function KnowledgeGraph() {
  const loc = useLocation();
  const [focus, setFocus] = useState(loc.state?.candidateId || '');
  const [visible, setVisible] = useState(new Set(ALL_TYPES));
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const state = useApi(() => (focus ? api.candidateGraph(focus) : api.graph()), [focus]);

  const toggle = (t) => {
    const next = new Set(visible);
    if (next.has(t)) next.delete(t); else next.add(t);
    setVisible(next);
  };

  return (
    <>
      <PageHeader title="Knowledge graph" subtitle="Live Neo4j data. Scroll to zoom, drag to pan, hover for labels, click a node for details."
        actions={focus && <button className="btn-ghost" onClick={() => { setFocus(''); setSelected(null); }}>Show full graph</button>} />
      <Async state={state}>
        {(d) => {
          const present = ALL_TYPES.filter((t) => d.stats.by_type[t]);
          return (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative min-w-[220px] flex-1">
                  <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
                  <input className="input pl-9" placeholder="Search nodes by name…" value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
                <Badge tone="indigo">{d.stats.nodes} nodes</Badge><Badge tone="indigo">{d.stats.links} relationships</Badge>
                {focus && <Badge tone="amber">Subgraph: {focus}</Badge>}
              </div>
              <div className="flex flex-wrap gap-2">
                {present.map((t) => (
                  <button key={t} onClick={() => toggle(t)}
                    className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs transition ${visible.has(t) ? 'border-slate-300 bg-white' : 'border-slate-200 bg-slate-100 text-slate-400'}`}>
                    <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: NODE_COLORS[t], opacity: visible.has(t) ? 1 : 0.3 }} />
                    {t} ({d.stats.by_type[t]})
                  </button>
                ))}
              </div>
              <div className="grid gap-4 xl:grid-cols-[1fr_340px]">
                <GraphViewer data={d} visibleTypes={visible} search={search} selectedId={selected?.id} onSelect={setSelected} />
                {selected ? <Details node={selected} data={d} onFocus={(id) => { setFocus(id); setSelected(null); }} />
                  : <div className="card p-4 text-sm text-slate-500">Select a node to see its properties and relationships.</div>}
              </div>
            </div>
          );
        }}
      </Async>
    </>
  );
}