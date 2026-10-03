import { useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Async, Badge, ChartCard, PageHeader, StatCard } from '../components/ui';
import { Database as DbIcon, Share2 } from 'lucide-react';

const CONCEPTS = [
  ['Why Neo4j?', 'The domain is relationship-heavy: candidates answer questions that test skills required for roles. Neo4j stores these as first-class relationships, so multi-hop questions (skill gaps, similarity, co-occurrence) are short traversals instead of many joins.'],
  ['Why MongoDB?', 'Interview sessions are semi-structured: transcripts, timestamps, emotion timelines and metadata that varies per source. Documents hold all of this together, and new fields need no migration.'],
  ['Flexible schema', 'Documents in raw_interviews do not share an identical field set: only fields present in the source row are stored in metadata, and API-created interviews carry different metadata from seeded ones.'],
  ['Embedding', 'The qa array, transcript and emotion_timeline are embedded inside each interview document because they are always read together with the interview and never shared.'],
  ['Referencing', 'Documents reference graph entities by id (candidate_id, question_id, round_id), and emotion_logs reference interviews through interview_id. Neo4j holds the shared entities.'],
  ['Indexing', 'Neo4j: uniqueness constraints (which also create indexes) on every id plus indexes on name/title/category. MongoDB: single-field indexes on candidate_id, round_id, target_role, started_at, label and timestamp.'],
  ['Aggregation', 'MongoDB pipelines ($unwind, $group, $project, $sort) compute emotion distribution, interviews per role, average scores and phase trends. Cypher aggregations (count, avg, collect) cover the graph side.'],
  ['Scalability & distribution', 'MongoDB scales out with replica sets and sharding (for example by candidate_id). Neo4j scales reads with causal clusters and read replicas. This project runs single-node containers; distribution is described, not deployed.'],
  ['Polyglot persistence', 'Each store does what it is best at: Neo4j for connected data and algorithms, MongoDB for flexible documents and time-series-like logs. FastAPI joins them at the service layer.'],
];

function Section({ title, children }) {
  return <section className="mb-8"><h2 className="mb-3 text-lg font-bold text-slate-900">{title}</h2>{children}</section>;
}

export default function Database() {
  const neo = useApi(api.dbNeo4j, []);
  const mongo = useApi(api.dbMongo, []);
  const idx = useApi(api.dbIndexes, []);
  const agg = useApi(api.analyticsMongo, []);
  const [open, setOpen] = useState(null);

  return (
    <>
      <PageHeader title="Database & NoSQL" subtitle="Connection status, counts, indexes and the NoSQL design rationale. Useful for the viva." />

      <Section title="Neo4j (graph database)">
        <Async state={neo}>
          {(d) => (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm"><Badge tone={d.connected ? 'emerald' : 'rose'}>{d.connected ? 'Connected' : 'Unavailable'}</Badge><code className="text-xs text-slate-500">{d.uri}</code></div>
              {d.connected && (
                <>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{d.node_counts.map((n) => <StatCard key={n.label} label={`${n.label} nodes`} value={n.count} icon={Share2} />)}</div>
                  <div className="card p-4"><h3 className="mb-2 font-semibold">Relationship counts</h3><div className="flex flex-wrap gap-2">{d.relationship_counts.map((r) => <Badge key={r.type} tone="indigo">{r.type}: {r.count}</Badge>)}</div></div>
                </>
              )}
            </div>
          )}
        </Async>
      </Section>

      <Section title="MongoDB (document database)">
        <Async state={mongo}>
          {(d) => (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm"><Badge tone={d.connected ? 'emerald' : 'rose'}>{d.connected ? 'Connected' : 'Unavailable'}</Badge><code className="text-xs text-slate-500">database: {d.database}</code></div>
              {d.connected && (
                <div className="grid gap-4 lg:grid-cols-2">
                  {d.collections.map((c) => (
                    <div key={c.name} className="card p-4">
                      <div className="mb-2 flex items-center justify-between"><b className="flex items-center gap-2"><DbIcon size={16} />{c.name}</b><Badge tone="emerald">{c.documents} documents</Badge></div>
                      <pre className="max-h-64 overflow-auto rounded bg-slate-50 p-2 text-[11px]">{JSON.stringify(c.sample, null, 2)}</pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </Async>
      </Section>

      <Section title="Constraints and indexes">
        <Async state={idx}>
          {(d) => (
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="card overflow-x-auto p-4">
                <h3 className="mb-2 font-semibold">Neo4j constraints ({d.neo4j.constraints.length})</h3>
                <table className="min-w-full text-xs"><tbody>{d.neo4j.constraints.map((c) => <tr key={c.name} className="border-b border-slate-100"><td className="py-1 pr-3 font-mono">{c.name}</td><td className="pr-3">{(c.labelsOrTypes || []).join(',')}.{(c.properties || []).join(',')}</td><td>{c.type}</td></tr>)}</tbody></table>
                <h3 className="mb-2 mt-4 font-semibold">Neo4j indexes ({d.neo4j.indexes.length})</h3>
                <table className="min-w-full text-xs"><tbody>{d.neo4j.indexes.map((c) => <tr key={c.name} className="border-b border-slate-100"><td className="py-1 pr-3 font-mono">{c.name}</td><td className="pr-3">{(c.labelsOrTypes || []).join(',')}.{(c.properties || []).join(',')}</td><td>{c.type} · {c.state}</td></tr>)}</tbody></table>
              </div>
              <div className="card p-4">
                <h3 className="mb-2 font-semibold">MongoDB indexes</h3>
                {Object.entries(d.mongodb).map(([coll, list]) => Array.isArray(list) && (
                  <div key={coll} className="mb-3"><div className="text-sm font-medium">{coll}</div><ul className="text-xs text-slate-600">{list.map((i) => <li key={i.name} className="font-mono">{i.name} → {JSON.stringify(i.keys)}</li>)}</ul></div>
                ))}
              </div>
            </div>
          )}
        </Async>
      </Section>

      <Section title="Live MongoDB aggregations">
        <Async state={agg}>
          {(a) => {
            const phases = ['start', 'middle', 'end'];
            const labels = [...new Set(a.emotion_trends.map((t) => t.label))];
            const trend = phases.map((p) => ({ name: p, ...Object.fromEntries(labels.map((l) => [l, a.emotion_trends.find((t) => t.phase === p && t.label === l)?.count || 0])) }));
            return (
              <div className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-3">
                  <StatCard label="Avg emotion confidence" value={a.avg_emotion_confidence.avg} />
                  <StatCard label="Avg answer score" value={a.avg_answer_score.avg} tone="emerald" />
                  <StatCard label="Emotion samples" value={a.avg_emotion_confidence.samples} tone="amber" />
                </div>
                <div className="grid gap-4 lg:grid-cols-2">
                  <ChartCard title="Emotion trend across interview phases" subtitle="$group on phase + label">
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={trend}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" /><YAxis /><Tooltip /><Legend />
                        {labels.map((l, i) => <Bar key={l} dataKey={l} stackId="a" fill={['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'][i % 5]} />)}
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartCard>
                  <div className="card overflow-x-auto p-4">
                    <h3 className="mb-2 font-semibold">Interviews per role</h3>
                    <table className="min-w-full text-sm"><tbody>{a.interviews_per_role.map((r) => <tr key={r.role} className="border-b border-slate-100"><td className="py-1">{r.role}</td><td className="text-right font-semibold">{r.interviews}</td></tr>)}</tbody></table>
                    <h3 className="mb-2 mt-4 font-semibold">Candidate interview statistics (top 10)</h3>
                    <table className="min-w-full text-xs"><thead><tr><th className="text-left">Candidate</th><th>Interviews</th><th>Answers</th><th>Avg</th></tr></thead>
                      <tbody>{a.candidate_stats.map((c) => <tr key={c.candidate_id} className="border-b border-slate-100 text-center"><td className="py-1 text-left">{c.candidate_id}</td><td>{c.interviews}</td><td>{c.answers}</td><td>{c.avg_score}</td></tr>)}</tbody></table>
                  </div>
                </div>
              </div>
            );
          }}
        </Async>
      </Section>

      <Section title="NoSQL concepts used in this project">
        <div className="grid gap-3 md:grid-cols-2">
          {CONCEPTS.map(([t, body], i) => (
            <button key={t} onClick={() => setOpen(open === i ? null : i)} className="card p-4 text-left transition hover:border-indigo-300">
              <div className="font-semibold text-slate-900">{t}</div>
              {open === i && <p className="mt-2 text-sm text-slate-600">{body}</p>}
            </button>
          ))}
        </div>
      </Section>
    </>
  );
}