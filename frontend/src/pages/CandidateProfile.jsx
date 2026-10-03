import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import CandidateCard from '../components/CandidateCard';
import { Async, Badge, ChartCard, EmptyState, PageHeader, ScoreBar, SimpleBar, SimplePie, SkillBadge, StatCard, diffTone } from '../components/ui';

export default function CandidateProfile() {
  const { id } = useParams();
  const prof = useApi(() => api.candidate(id), [id]);
  const ev = useApi(() => api.evaluation(id), [id]);
  const recs = useApi(() => api.roleRecs(id), [id]);
  const sim = useApi(() => api.similar(id), [id]);

  return (
    <>
      <Link to="/candidates" className="mb-3 inline-flex items-center gap-1 text-sm text-indigo-600"><ArrowLeft size={14} /> Candidates</Link>
      <Async state={prof}>
        {(p) => {
          const c = p.candidate;
          return (
            <div className="space-y-6">
              <PageHeader title={c.name} subtitle={`${c.candidate_id} · ${c.education || 'Education n/a'} · ${c.domain || 'Domain n/a'} · ${c.job_type || 'Job type n/a'}`}
                actions={<Link to="/graph" state={{ candidateId: c.candidate_id }} className="btn-ghost">View in graph</Link>} />
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard label="Experience (yrs)" value={c.experience_years} />
                <StatCard label="Interview rounds" value={p.stats.rounds} tone="amber" />
                <StatCard label="Questions answered" value={p.stats.answers} tone="emerald" />
                <StatCard label="Average score" value={p.stats.avg_score} tone="rose" />
              </div>
              <div className="card p-4">
                <h3 className="mb-2 font-semibold">Skills</h3>
                <div className="flex flex-wrap gap-1.5">{p.skills.length ? p.skills.map((s) => <SkillBadge key={s} name={s} />) : <span className="text-sm text-slate-400">No skills</span>}</div>
              </div>
              <div className="grid gap-6 lg:grid-cols-2">
                <ChartCard title="Answer scores" subtitle="Per question (0–10)">
                  <SimpleBar data={p.answers.map((a) => ({ name: a.question_id, value: a.score }))} color="#6366f1" />
                </ChartCard>
                <ChartCard title="Emotion summary" subtitle="MongoDB emotion_logs">
                  {p.emotions.length ? <SimplePie data={p.emotions.map((e) => ({ name: e.label, value: e.count }))} /> : <EmptyState text="No emotion logs" />}
                </ChartCard>
              </div>
              <div className="grid gap-6 lg:grid-cols-2">
                <Async state={ev}>
                  {(e) => (
                    <div className="card p-4">
                      <h3 className="mb-2 font-semibold">Evaluation <Badge tone="indigo">{e.overall_score}/10</Badge></h3>
                      <p className="mb-2 text-xs text-slate-500">{e.label}</p>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div><h4 className="text-sm font-medium text-emerald-700">Strengths</h4><ul className="list-disc pl-4 text-xs text-slate-600">{e.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
                        <div><h4 className="text-sm font-medium text-rose-700">Weaknesses</h4><ul className="list-disc pl-4 text-xs text-slate-600">{e.weaknesses.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
                      </div>
                    </div>
                  )}
                </Async>
                <Async state={recs}>
                  {(r) => (
                    <div className="card p-4">
                      <h3 className="mb-1 font-semibold">Recommended roles &amp; skill gaps</h3>
                      <p className="mb-3 text-xs text-slate-500">{r.label}</p>
                      <div className="space-y-3">
                        {r.roles.slice(0, 3).map((x) => (
                          <div key={x.role_id}>
                            <div className="flex justify-between text-sm"><b>{x.title}</b><span>{x.coverage}%</span></div>
                            <ScoreBar value={x.coverage} tone="emerald" />
                            {x.missing.length > 0 && <div className="mt-1 flex flex-wrap gap-1">{x.missing.map((m) => <SkillBadge key={m} name={m} tone="rose" />)}</div>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </Async>
              </div>
              <div className="card overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50"><tr>{['Round', 'Question', 'Difficulty', 'Score', 'Skills demonstrated'].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
                  <tbody className="divide-y divide-slate-100">
                    {p.answers.map((a) => (
                      <tr key={a.answer_id}>
                        <td className="td font-mono text-xs">{a.round_id.split('__').pop()}</td>
                        <td className="td max-w-md">{a.question}</td>
                        <td className="td"><Badge tone={diffTone(a.difficulty)}>{a.difficulty || '—'}</Badge></td>
                        <td className="td font-semibold">{a.score}</td>
                        <td className="td"><div className="flex flex-wrap gap-1">{a.skills.map((s) => <SkillBadge key={s} name={s} tone="emerald" />)}</div></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <h3 className="mb-3 font-semibold">Similar candidates</h3>
                <Async state={sim}>
                  {(s) => (s.items.length ? <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">{s.items.map((i) => <CandidateCard key={i.candidate_id} item={i} />)}</div> : <EmptyState text="No candidates share skills" />)}
                </Async>
              </div>
            </div>
          );
        }}
      </Async>
    </>
  );
}