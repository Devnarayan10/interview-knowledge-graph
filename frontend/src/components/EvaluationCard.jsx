import { Badge, ScoreBar } from './ui';

const Metric = ({ label, value, max = 10, suffix = '/10', tone }) => (
  <div className="card p-4">
    <div className="text-xs font-medium uppercase text-slate-500">{label}</div>
    <div className="my-1 text-2xl font-bold text-slate-900">{value}<span className="text-sm font-normal text-slate-400">{suffix}</span></div>
    <ScoreBar value={value} max={max} tone={tone} />
  </div>
);

export default function EvaluationCard({ ev }) {
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800">{ev.label}</div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Overall" value={ev.overall_score} />
        <Metric label="Technical" value={ev.technical_score} tone="emerald" />
        <Metric label="Communication" value={ev.communication_score} tone="amber" />
        <Metric label="Skill coverage" value={ev.skill_coverage} max={100} suffix="%" tone="emerald" />
      </div>
      <p className="text-sm text-slate-700">{ev.summary} {ev.role && <Badge tone="indigo">{ev.role}</Badge>}</p>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="card p-4">
          <h4 className="mb-2 font-semibold text-emerald-700">Strengths</h4>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">{ev.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </div>
        <div className="card p-4">
          <h4 className="mb-2 font-semibold text-rose-700">Weaknesses</h4>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">{ev.weaknesses.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </div>
      </div>
      <div className="card p-4">
        <h4 className="mb-2 font-semibold text-slate-800">How this was calculated</h4>
        <ul className="list-decimal space-y-1 pl-5 text-xs text-slate-600">{ev.explanation.map((s, i) => <li key={i}>{s}</li>)}</ul>
      </div>
    </div>
  );
}