import { Pencil, Trash2 } from 'lucide-react';
import { Badge, EmptyState, ScoreBar } from './ui';

export default function CandidateTable({ items, onOpen, onEdit, onDelete }) {
  if (!items.length) return <EmptyState text="No candidates match the filters" />;
  return (
    <div className="card overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>{['ID', 'Name', 'Domain', 'Education', 'Exp (yrs)', 'Job type', 'Avg score', 'Skill coverage', 'Role compatibility', ''].map((h) => <th key={h} className="th">{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((c) => (
            <tr key={c.candidate_id} className="cursor-pointer hover:bg-indigo-50/40" onClick={() => onOpen(c)}>
              <td className="td font-mono text-xs">{c.candidate_id}</td>
              <td className="td font-medium text-slate-900">{c.name}</td>
              <td className="td">{c.domain || '—'}</td>
              <td className="td max-w-[200px] truncate">{c.education || '—'}</td>
              <td className="td">{c.experience_years ?? '—'}</td>
              <td className="td">{c.job_type ? <Badge>{c.job_type}</Badge> : '—'}</td>
              <td className="td">{c.avg_score ?? '—'}</td>
              <td className="td w-36"><div className="mb-1 text-xs">{c.skill_coverage}%</div><ScoreBar value={c.skill_coverage} tone="emerald" /></td>
              <td className="td text-xs">{c.best_role ? <>{c.best_role} <Badge tone="indigo">{c.best_role_compat}%</Badge></> : '—'}</td>
              <td className="td whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                <button className="mr-2 text-slate-400 hover:text-indigo-600" onClick={() => onEdit(c)}><Pencil size={15} /></button>
                <button className="text-slate-400 hover:text-rose-600" onClick={() => onDelete(c)}><Trash2 size={15} /></button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}