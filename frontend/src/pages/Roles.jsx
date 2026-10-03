import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Async, Badge, ChartCard, PageHeader, SimpleBar, SkillBadge } from '../components/ui';

export default function Roles() {
  const state = useApi(api.roles, []);
  return (
    <>
      <PageHeader title="Roles" subtitle="Required skills per role are derived from the questions asked for the role and the skills of candidates interviewed for it (REQUIRED_FOR weight)." />
      <Async state={state}>
        {(d) => (
          <div className="space-y-6">
            <ChartCard title="Average answer score by role">
              <SimpleBar data={d.items.map((r) => ({ name: r.title, value: r.avg_score || 0 }))} color="#ef4444" />
            </ChartCard>
            <div className="grid gap-4 md:grid-cols-2">
              {d.items.map((r) => (
                <div key={r.role_id} className="card p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-slate-900">{r.title}</h3>
                    <Badge tone="indigo">{r.department || 'n/a'}</Badge>
                  </div>
                  <div className="my-2 flex gap-4 text-xs text-slate-500">
                    <span>{r.questions} questions</span><span>{r.candidates} candidates</span><span>avg score {r.avg_score ?? '—'}</span>
                  </div>
                  <div className="mb-1 text-xs font-semibold uppercase text-slate-500">Required skills</div>
                  <div className="flex flex-wrap gap-1">
                    {r.required_skills.map((s) => <SkillBadge key={s.name} name={`${s.name} · ${s.weight}`} tone="emerald" />)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Async>
    </>
  );
}