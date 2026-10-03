import { useState } from 'react';
import { Briefcase, Brain, Database, HelpCircle, MessageSquare, Share2, Smile, Users, Video } from 'lucide-react';
import { api, errMsg } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Async, ChartCard, PageHeader, SimpleBar, SimplePie, StatCard } from '../components/ui';

export default function Dashboard() {
  const state = useApi(api.dashboard, []);
  const [seeding, setSeeding] = useState(false);
  const [msg, setMsg] = useState('');

  const seed = async () => {
    setSeeding(true);
    setMsg('');
    try {
      await api.seed();
      state.reload();
    } catch (e) {
      setMsg(errMsg(e));
    } finally {
      setSeeding(false);
    }
  };

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Live counts from Neo4j and MongoDB. Data is synthetic (CareerCorpus profiles matched to Ankshi questions)."
        actions={<button className="btn-primary" disabled={seeding} onClick={seed}><Database size={16} />{seeding ? 'Seeding…' : 'Seed / re-seed database'}</button>} />
      {msg && <div className="mb-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{msg}</div>}
      <Async state={state}>
        {(d) => (
          <div className="space-y-6">
            {!d.mongodb_available && <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">MongoDB is unavailable: interview and emotion statistics are hidden.</div>}
            {d.counts.candidates === 0 && <div className="rounded-lg bg-indigo-50 p-3 text-sm text-indigo-800">The graph is empty. Click “Seed / re-seed database”.</div>}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Candidates" value={d.counts.candidates} icon={Users} />
              <StatCard label="Questions" value={d.counts.questions} icon={HelpCircle} tone="amber" />
              <StatCard label="Answers" value={d.counts.answers} icon={MessageSquare} tone="emerald" />
              <StatCard label="Skills" value={d.counts.skills} icon={Brain} tone="cyan" />
              <StatCard label="Roles" value={d.counts.roles} icon={Briefcase} tone="rose" />
              <StatCard label="Relationships" value={d.counts.relationships} icon={Share2} />
              <StatCard label="Interviews (MongoDB)" value={d.counts.interviews} icon={Video} tone="emerald" />
              <StatCard label="Emotion logs (MongoDB)" value={d.counts.emotion_logs} icon={Smile} tone="amber" />
            </div>
            <div className="card p-4 text-sm text-slate-600">Average answer score (system-derived): <b className="text-slate-900">{d.avg_score ?? '—'} / 10</b></div>
            <div className="grid gap-6 lg:grid-cols-2">
              <ChartCard title="Candidates by domain"><SimpleBar data={d.charts.candidates_by_domain} /></ChartCard>
              <ChartCard title="Questions by difficulty"><SimplePie data={d.charts.questions_by_difficulty} /></ChartCard>
              <ChartCard title="Role distribution" subtitle="Candidates interviewed per role"><SimpleBar data={d.charts.role_distribution} vertical color="#ef4444" /></ChartCard>
              <ChartCard title="Skill distribution" subtitle="Candidates holding each skill"><SimpleBar data={d.charts.skill_distribution} vertical color="#10b981" height={320} /></ChartCard>
              <ChartCard title="Average answer score by role"><SimpleBar data={d.charts.score_by_role} color="#f59e0b" /></ChartCard>
              <ChartCard title="Emotion distribution" subtitle="MongoDB emotion_logs"><SimplePie data={d.charts.emotion_distribution} /></ChartCard>
              <ChartCard title="Interview statistics" subtitle="Rounds per candidate"><SimpleBar data={d.charts.rounds_per_candidate} color="#8b5cf6" /></ChartCard>
            </div>
          </div>
        )}
      </Async>
    </>
  );
}