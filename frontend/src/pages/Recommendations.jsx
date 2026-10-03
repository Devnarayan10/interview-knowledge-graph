import { useState } from 'react';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import CandidateCard from '../components/CandidateCard';
import { Async, Badge, EmptyState, PageHeader, ScoreBar, SkillBadge } from '../components/ui';

export default function Recommendations() {
  const list = useApi(() => api.candidates(), []);
  const [id, setId] = useState('');
  const [role, setRole] = useState('');
  const recs = useApi(() => (id ? api.roleRecs(id) : Promise.resolve(null)), [id]);
  const sim = useApi(() => (id ? api.similar(id) : Promise.resolve(null)), [id]);
  const gap = useApi(() => (id && role ? api.skillGap(id, role) : Promise.resolve(null)), [id, role]);

  return (
    <>
      <PageHeader title="Recommendations" subtitle="System-generated role compatibility based on skill overlap. This is not a hiring decision." />
      <Async state={list}>
        {(d) => (
          <select className="input mb-6 max-w-md" value={id} onChange={(e) => { setId(e.target.value); setRole(''); }}>
            <option value="">Select candidate…</option>
            {d.items.map((c) => <option key={c.candidate_id} value={c.candidate_id}>{c.candidate_id} · {c.name}</option>)}
          </select>
        )}
      </Async>
      {!id ? <EmptyState text="Choose a candidate" /> : (
        <div className="space-y-8">
          <Async state={recs}>
            {(r) => r && (
              <div>
                <h2 className="mb-1 text-lg font-bold">Role compatibility</h2>
                <p className="mb-3 text-xs text-slate-500">{r.label}. Click a role for the skill-gap analysis.</p>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {r.roles.map((x) => (
                    <button key={x.role_id} onClick={() => setRole(x.role_id)}
                      className={`card p-4 text-left transition hover:border-indigo-300 ${role === x.role_id ? 'border-indigo-500 ring-2 ring-indigo-200' : ''}`}>
                      <div className="flex justify-between"><b>{x.title}</b><Badge tone="indigo">{x.coverage}%</Badge></div>
                      <div className="my-2"><ScoreBar value={x.coverage} tone="emerald" /></div>
                      <div className="text-xs text-slate-500">{x.matched.length} of {x.required.length} required skills matched</div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </Async>
          {role && (
            <Async state={gap}>
              {(g) => g && (
                <div className="card p-5">
                  <h2 className="mb-1 text-lg font-bold">Skill gap — {g.role.title}</h2>
                  <p className="mb-3 text-sm text-slate-600">Coverage: <b>{g.coverage}%</b> ({g.matched.length}/{g.required.length})</p>
                  <ScoreBar value={g.coverage} tone="emerald" />
                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    <div><h4 className="mb-1 text-sm font-semibold text-emerald-700">Matched skills</h4><div className="flex flex-wrap gap-1">{g.matched.length ? g.matched.map((s) => <SkillBadge key={s} name={s} tone="emerald" />) : <span className="text-sm text-slate-400">None</span>}</div></div>
                    <div><h4 className="mb-1 text-sm font-semibold text-rose-700">Missing skills</h4><div className="flex flex-wrap gap-1">{g.missing.length ? g.missing.map((s) => <SkillBadge key={s} name={s} tone="rose" />) : <span className="text-sm text-slate-400">None</span>}</div></div>
                  </div>
                </div>
              )}
            </Async>
          )}
          <Async state={sim}>
            {(s) => s && (
              <div>
                <h2 className="mb-1 text-lg font-bold">Similar candidates</h2>
                <p className="mb-3 text-xs text-slate-500">{s.method}</p>
                {s.items.length ? <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">{s.items.map((i) => <CandidateCard key={i.candidate_id} item={i} />)}</div> : <EmptyState text="No candidates share skills" />}
              </div>
            )}
          </Async>
        </div>
      )}
    </>
  );
}