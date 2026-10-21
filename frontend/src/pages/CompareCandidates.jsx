import { useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Async, ChartCard, EmptyState, Loading, PageHeader, SkillBadge } from '../components/ui';

const load = (id) => (id ? Promise.all([api.candidate(id), api.evaluation(id), api.roleRecs(id)]) : Promise.resolve(null));

export default function CompareCandidates() {
  const list = useApi(() => api.candidates(), []);
  const [a, setA] = useState('');
  const [b, setB] = useState('');
  const A = useApi(() => load(a), [a]);
  const B = useApi(() => load(b), [b]);

  const select = (value, set, other) => (
    <select className="input" value={value} onChange={(e) => set(e.target.value)}>
      <option value="">Select candidate…</option>
      {(list.data?.items || []).filter((c) => c.candidate_id !== other).map((c) => <option key={c.candidate_id} value={c.candidate_id}>{c.candidate_id} · {c.name}</option>)}
    </select>
  );

  const ready = Array.isArray(A.data) && Array.isArray(B.data);
  let body = <EmptyState text="Select two candidates to compare" />;
  if ((a && A.loading) || (b && B.loading)) body = <Loading />;
  else if ((a && A.error) || (b && B.error)) body = <div role="alert" className="card p-4 text-rose-700">Comparison could not be loaded: {String(A.error?.message || B.error?.message || 'Unknown error')}</div>;
  else if (ready) {
    const [pa, ea, ra] = A.data;
    const [pb, eb, rb] = B.data;
    const sa = new Set((pa.skills || []).map((s) => s.toLowerCase()));
    const sb = new Set((pb.skills || []).map((s) => s.toLowerCase()));
    const shared = (pa.skills || []).filter((s) => sb.has(s.toLowerCase()));
    const chart = [
      { name: 'Overall', A: ea.overall_score, B: eb.overall_score },
      { name: 'Technical', A: ea.technical_score, B: eb.technical_score },
      { name: 'Communication', A: ea.communication_score, B: eb.communication_score },
      { name: 'Coverage (÷10)', A: ea.skill_coverage / 10, B: eb.skill_coverage / 10 },
      { name: 'Avg answer', A: pa.stats.avg_score || 0, B: pb.stats.avg_score || 0 },
    ];
    const rows = [
      ['Education', pa.candidate.education, pb.candidate.education],
      ['Domain', pa.candidate.domain, pb.candidate.domain],
      ['Experience (yrs)', pa.candidate.experience_years, pb.candidate.experience_years],
      ['Questions answered', pa.stats.answers, pb.stats.answers],
      ['Best-fit role', `${(ra.roles || [])[0]?.title} (${(ra.roles || [])[0]?.coverage}%)`, `${(rb.roles || [])[0]?.title} (${(rb.roles || [])[0]?.coverage}%)`],
    ];
    body = (
      <div className="space-y-6">
        <ChartCard title="Score comparison" subtitle={ea.label}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chart}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis domain={[0, 10]} /><Tooltip /><Legend />
              <Bar dataKey="A" name={pa.candidate.name} fill="#6366f1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="B" name={pb.candidate.name} fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50"><tr><th className="th">Attribute</th><th className="th">{pa.candidate.name}</th><th className="th">{pb.candidate.name}</th></tr></thead>
            <tbody className="divide-y divide-slate-100">{rows.map(([l, x, y]) => <tr key={l}><td className="td font-medium">{l}</td><td className="td">{x ?? '—'}</td><td className="td">{y ?? '—'}</td></tr>)}</tbody>
          </table>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="card p-4"><h4 className="mb-2 text-sm font-semibold">Only {pa.candidate.name}</h4><div className="flex flex-wrap gap-1">{(pa.skills || []).filter((s) => !sb.has(s.toLowerCase())).map((s) => <SkillBadge key={s} name={s} />)}</div></div>
          <div className="card p-4"><h4 className="mb-2 text-sm font-semibold">Shared skills</h4><div className="flex flex-wrap gap-1">{shared.map((s) => <SkillBadge key={s} name={s} tone="emerald" />)}</div></div>
          <div className="card p-4"><h4 className="mb-2 text-sm font-semibold">Only {pb.candidate.name}</h4><div className="flex flex-wrap gap-1">{(pb.skills || []).filter((s) => !sa.has(s.toLowerCase())).map((s) => <SkillBadge key={s} name={s} tone="cyan" />)}</div></div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {[[pa, ea, ra], [pb, eb, rb]].map(([p, e, r]) => (
            <div key={p.candidate.candidate_id} className="card p-4">
              <h4 className="mb-2 font-semibold">{p.candidate.name}</h4>
              <h5 className="text-sm font-medium text-emerald-700">Strengths</h5><ul className="mb-2 list-disc pl-5 text-xs text-slate-600">{e.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
              <h5 className="text-sm font-medium text-rose-700">Weaknesses</h5><ul className="mb-2 list-disc pl-5 text-xs text-slate-600">{e.weaknesses.map((s, i) => <li key={i}>{s}</li>)}</ul>
              <h5 className="text-sm font-medium">Role compatibility</h5><ul className="text-xs text-slate-600">{(r.roles || []).slice(0, 3).map((x) => <li key={x.role_id}>{x.title}: {x.coverage}%</li>)}</ul>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <>
      <PageHeader title="Compare candidates" subtitle="Side-by-side comparison of skills, scores, role compatibility and evaluation." />
      <Async state={list}>
        {() => <div className="mb-6 grid gap-3 md:grid-cols-2">{select(a, setA, b)}{select(b, setB, a)}</div>}
      </Async>
      {body}
    </>
  );
}