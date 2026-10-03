import { Link } from 'react-router-dom';
import { Badge, SkillBadge } from './ui';

export default function CandidateCard({ item }) {
  return (
    <Link to={`/candidates/${encodeURIComponent(item.candidate_id)}`} className="card block p-4 transition hover:border-indigo-300">
      <div className="flex items-center justify-between">
        <div className="font-semibold text-slate-900">{item.name}</div>
        <Badge tone="indigo">{item.similarity}% similar</Badge>
      </div>
      <div className="mb-2 text-xs text-slate-500">{item.candidate_id} · {item.domain || 'No domain'}</div>
      <div className="flex flex-wrap gap-1">{item.shared_skills.map((s) => <SkillBadge key={s} name={s} tone="emerald" />)}</div>
    </Link>
  );
}