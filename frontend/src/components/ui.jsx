import { AlertTriangle, Inbox, Loader2, X } from 'lucide-react';
import {
  Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend,
} from 'recharts';

export const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#8b5cf6', '#ec4899', '#84cc16', '#14b8a6', '#f97316'];

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 max-w-3xl text-sm text-slate-500">{subtitle}</p>}
      </div>
      <div className="flex flex-wrap gap-2">{actions}</div>
    </div>
  );
}

export function StatCard({ label, value, icon: Icon, tone = 'indigo' }) {
  const tones = { indigo: 'bg-indigo-50 text-indigo-600', emerald: 'bg-emerald-50 text-emerald-600', amber: 'bg-amber-50 text-amber-600', rose: 'bg-rose-50 text-rose-600', cyan: 'bg-cyan-50 text-cyan-600' };
  return (
    <div className="card flex items-center gap-4 p-4">
      {Icon && <div className={`rounded-lg p-3 ${tones[tone] || tones.indigo}`}><Icon size={20} /></div>}
      <div>
        <div className="text-2xl font-bold text-slate-900">{value ?? '—'}</div>
        <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      </div>
    </div>
  );
}

export function Loading({ text = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-slate-500">
      <Loader2 className="animate-spin" size={18} /> {text}
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="card flex flex-col items-center gap-3 border-rose-200 bg-rose-50 p-8 text-center">
      <AlertTriangle className="text-rose-500" />
      <p className="text-sm text-rose-700">{message}</p>
      {onRetry && <button className="btn-ghost" onClick={onRetry}>Retry</button>}
    </div>
  );
}

export function EmptyState({ text = 'No data available' }) {
  return (
    <div className="flex flex-col items-center gap-2 py-10 text-slate-400">
      <Inbox /> <span className="text-sm">{text}</span>
    </div>
  );
}

export function Async({ state, children }) {
  if (state.loading && !state.data) return <Loading />;
  if (state.error) return <ErrorState message={state.error} onRetry={state.reload} />;
  if (!state.data) return <EmptyState />;
  return children(state.data);
}

export function Badge({ children, tone = 'slate' }) {
  const tones = {
    slate: 'bg-slate-100 text-slate-700', indigo: 'bg-indigo-100 text-indigo-700', emerald: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-700', rose: 'bg-rose-100 text-rose-700', cyan: 'bg-cyan-100 text-cyan-700',
  };
  return <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone] || tones.slate}`}>{children}</span>;
}

export const SkillBadge = ({ name, tone = 'indigo' }) => <Badge tone={tone}>{name}</Badge>;

export const diffTone = (d) => ({ easy: 'emerald', medium: 'amber', hard: 'rose' }[(d || '').toLowerCase()] || 'slate');

export function ChartCard({ title, subtitle, children }) {
  return (
    <div className="card p-4">
      <div className="mb-3">
        <h3 className="font-semibold text-slate-800">{title}</h3>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

export function ScoreBar({ value, max = 100, tone = 'indigo' }) {
  const pct = Math.max(0, Math.min(100, ((value ?? 0) / max) * 100));
  const colors = { indigo: 'bg-indigo-500', emerald: 'bg-emerald-500', amber: 'bg-amber-500' };
  return (
    <div className="h-2 w-full rounded-full bg-slate-100">
      <div className={`h-2 rounded-full ${colors[tone] || colors.indigo}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

export function Modal({ title, onClose, children, wide }) {
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/50 p-4" onClick={onClose}>
      <div className={`card my-8 w-full ${wide ? 'max-w-4xl' : 'max-w-xl'}`} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
          <h3 className="font-semibold text-slate-900">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700"><X size={18} /></button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

export const Field = ({ label, children }) => (
  <label className="mb-3 block text-sm">
    <span className="mb-1 block font-medium text-slate-600">{label}</span>
    {children}
  </label>
);

export function SimpleBar({ data, color = '#6366f1', height = 260, vertical = false, dataKey = 'value' }) {
  if (!data?.length) return <EmptyState />;
  return (
    <ResponsiveContainer width="100%" height={height}>
      {vertical ? (
        <BarChart data={data} layout="vertical" margin={{ left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey={dataKey} fill={color} radius={[0, 4, 4, 0]} />
        </BarChart>
      ) : (
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={55} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey={dataKey} fill={color} radius={[4, 4, 0, 0]} />
        </BarChart>
      )}
    </ResponsiveContainer>
  );
}

export function SimplePie({ data, height = 260 }) {
  if (!data?.length) return <EmptyState />;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90} paddingAngle={2}>
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}