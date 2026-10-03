import { useState } from 'react';
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react';
import { api, errMsg } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Async, Badge, EmptyState, Field, Loading, Modal, PageHeader, SkillBadge, diffTone } from '../components/ui';

function InterviewDetail({ id }) {
  const s = useApi(() => api.interview(id), [id]);
  return (
    <Async state={s}>
      {(d) => (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2 text-sm">
            <Badge tone="indigo">{d.candidate_id}</Badge><Badge>{d.round_label}</Badge><Badge tone="amber">{d.target_role}</Badge><Badge tone="emerald">{d.status}</Badge>
            <span className="text-slate-500">{d.started_at && new Date(d.started_at).toLocaleString()}</span>
          </div>
          {d.qa.map((x, i) => (
            <div key={x.answer_id} className="rounded-lg border border-slate-200 p-3">
              <div className="mb-1 flex flex-wrap items-center gap-2 text-xs">
                <b>Q{i + 1}</b> <Badge tone={diffTone(x.difficulty)}>{x.difficulty}</Badge><Badge>{x.category}</Badge>
                <span className="ml-auto font-semibold">Score {x.score}/10</span>
              </div>
              <p className="text-sm font-medium text-slate-800">{x.question}</p>
              <p className="mt-1 text-sm text-slate-600">{x.answer}</p>
              <div className="mt-2 flex flex-wrap items-center gap-1">
                {(x.skills_tested || []).map((s) => <SkillBadge key={s} name={s} tone="amber" />)}
                {(x.skills_demonstrated || []).map((s) => <SkillBadge key={`d${s}`} name={s} tone="emerald" />)}
                {x.emotion && <Badge tone="cyan">{x.emotion.label} · {x.emotion.confidence}</Badge>}
              </div>
              {x.feedback && <p className="mt-2 text-xs text-slate-500">{x.feedback.summary} Strengths: {x.feedback.strengths}. Gaps: {x.feedback.weaknesses}.</p>}
            </div>
          ))}
          {d.emotion_timeline?.length > 0 && <p className="text-xs text-slate-500">{d.emotion_timeline.length} embedded emotion samples (MongoDB array).</p>}
          <details className="text-xs text-slate-500"><summary className="cursor-pointer">Metadata (flexible schema)</summary><pre className="mt-2 overflow-x-auto rounded bg-slate-50 p-2">{JSON.stringify(d.metadata, null, 2)}</pre></details>
        </div>
      )}
    </Async>
  );
}

function InterviewForm({ initial, onSaved, onClose }) {
  const editing = !!initial;
  const cands = useApi(() => api.candidates(), []);
  const qs = useApi(() => api.questions({ page_size: 200 }), []);
  const [form, setForm] = useState({ candidate_id: '', round_label: '', target_role: initial?.target_role || '', notes: '' });
  const [qa, setQa] = useState([{ question_id: '', answer_text: '', score: '' }]);
  const [status, setStatus] = useState(initial?.status || 'completed');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setErr('');
    try {
      if (editing) await api.updateInterview(initial.interview_id, { target_role: form.target_role || null, notes: form.notes || null, status });
      else {
        await api.createInterview({
          candidate_id: form.candidate_id, round_label: form.round_label || null, target_role: form.target_role || null, notes: form.notes || null,
          qa: qa.filter((x) => x.question_id && x.answer_text).map((x) => ({ question_id: x.question_id, answer_text: x.answer_text, score: x.score === '' ? null : Number(x.score) })),
        });
      }
      onSaved();
    } catch (ex) {
      setErr(errMsg(ex));
    } finally {
      setBusy(false);
    }
  };

  if (!editing && (cands.loading || qs.loading)) return <Loading />;
  return (
    <form onSubmit={submit}>
      {!editing && (
        <div className="grid grid-cols-2 gap-3">
          <Field label="Candidate">
            <select required className="input" value={form.candidate_id} onChange={(e) => setForm({ ...form, candidate_id: e.target.value })}>
              <option value="">Select…</option>{(cands.data?.items || []).map((c) => <option key={c.candidate_id} value={c.candidate_id}>{c.candidate_id} · {c.name}</option>)}
            </select>
          </Field>
          <Field label="Round label (optional)"><input className="input" value={form.round_label} onChange={(e) => setForm({ ...form, round_label: e.target.value })} placeholder="R3" /></Field>
        </div>
      )}
      <div className="grid grid-cols-2 gap-3">
        <Field label="Target role"><input className="input" value={form.target_role} onChange={(e) => setForm({ ...form, target_role: e.target.value })} /></Field>
        {editing ? (
          <Field label="Status"><select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>{['completed', 'in_review', 'cancelled'].map((s) => <option key={s}>{s}</option>)}</select></Field>
        ) : <Field label="Notes"><input className="input" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></Field>}
      </div>
      {editing && <Field label="Notes"><input className="input" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></Field>}
      {!editing && (
        <div className="mb-3 space-y-3">
          {qa.map((x, i) => (
            <div key={i} className="rounded-lg border border-slate-200 p-3">
              <select className="input mb-2" value={x.question_id} onChange={(e) => setQa(qa.map((y, j) => (j === i ? { ...y, question_id: e.target.value } : y)))}>
                <option value="">Select question…</option>{(qs.data?.items || []).map((q) => <option key={q.question_id} value={q.question_id}>{q.question_id} · {q.text.slice(0, 70)}</option>)}
              </select>
              <textarea className="input mb-2" rows={2} placeholder="Answer" value={x.answer_text} onChange={(e) => setQa(qa.map((y, j) => (j === i ? { ...y, answer_text: e.target.value } : y)))} />
              <div className="flex items-center gap-2">
                <input type="number" min="0" max="10" step="0.1" className="input w-40" placeholder="Score (optional)" value={x.score} onChange={(e) => setQa(qa.map((y, j) => (j === i ? { ...y, score: e.target.value } : y)))} />
                {qa.length > 1 && <button type="button" className="text-xs text-rose-600" onClick={() => setQa(qa.filter((_, j) => j !== i))}>Remove</button>}
              </div>
            </div>
          ))}
          <button type="button" className="btn-ghost" onClick={() => setQa([...qa, { question_id: '', answer_text: '', score: '' }])}><Plus size={14} /> Add question</button>
        </div>
      )}
      {err && <div className="mb-3 rounded bg-rose-50 p-2 text-sm text-rose-700">{err}</div>}
      <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={onClose}>Cancel</button><button className="btn-primary" disabled={busy}>{busy ? 'Saving…' : editing ? 'Update' : 'Create'}</button></div>
    </form>
  );
}

export default function Interviews() {
  const [candidate, setCandidate] = useState('');
  const [role, setRole] = useState('');
  const [page, setPage] = useState(1);
  const [modal, setModal] = useState(null);
  const [error, setError] = useState('');
  const cands = useApi(() => api.candidates(), []);
  const roles = useApi(() => api.roles(), []);
  const state = useApi(() => api.interviews({ candidate_id: candidate, target_role: role, page, page_size: 15 }), [candidate, role, page]);

  const remove = async (i) => {
    if (!window.confirm(`Delete interview ${i.interview_id}? This removes the MongoDB document, its emotion logs and the graph answers.`)) return;
    try { await api.deleteInterview(i.interview_id); state.reload(); } catch (e) { setError(errMsg(e)); }
  };

  return (
    <>
      <PageHeader title="Interview explorer" subtitle="Flexible interview documents come from MongoDB; feedback and skills are joined from Neo4j."
        actions={<button className="btn-primary" onClick={() => setModal({ mode: 'create' })}><Plus size={16} /> New interview</button>} />
      <div className="mb-4 flex flex-wrap gap-3">
        <select className="input w-60" value={candidate} onChange={(e) => { setCandidate(e.target.value); setPage(1); }}>
          <option value="">All candidates</option>{(cands.data?.items || []).map((c) => <option key={c.candidate_id} value={c.candidate_id}>{c.candidate_id} · {c.name}</option>)}
        </select>
        <select className="input w-60" value={role} onChange={(e) => { setRole(e.target.value); setPage(1); }}>
          <option value="">All roles</option>{(roles.data?.items || []).map((r) => <option key={r.role_id}>{r.title}</option>)}
        </select>
      </div>
      {error && <div className="mb-3 rounded bg-rose-50 p-2 text-sm text-rose-700">{error}</div>}
      <Async state={state}>
        {(d) => (d.items.length ? (
          <>
            <div className="card overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50"><tr>{['Interview', 'Candidate', 'Round', 'Role', 'Date', 'Questions', 'Avg score', ''].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {d.items.map((i) => (
                    <tr key={i.interview_id}>
                      <td className="td font-mono text-xs">{i.interview_id}</td><td className="td">{i.candidate_id}</td><td className="td">{i.round_label}</td>
                      <td className="td">{i.target_role}</td><td className="td">{i.started_at && new Date(i.started_at).toLocaleDateString()}</td>
                      <td className="td">{i.questions}</td><td className="td font-semibold">{i.avg_score ?? '—'}</td>
                      <td className="td whitespace-nowrap">
                        <button className="mr-2 text-slate-400 hover:text-indigo-600" onClick={() => setModal({ mode: 'view', item: i })}><Eye size={15} /></button>
                        <button className="mr-2 text-slate-400 hover:text-indigo-600" onClick={() => setModal({ mode: 'edit', item: i })}><Pencil size={15} /></button>
                        <button className="text-slate-400 hover:text-rose-600" onClick={() => remove(i)}><Trash2 size={15} /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-3 flex items-center justify-between text-sm text-slate-500">
              <span>{d.total} interview(s)</span>
              <div className="flex gap-2"><button className="btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button><button className="btn-ghost" disabled={page * d.page_size >= d.total} onClick={() => setPage(page + 1)}>Next</button></div>
            </div>
          </>
        ) : <EmptyState text="No interviews found" />)}
      </Async>
      {modal?.mode === 'view' && <Modal wide title={`Interview ${modal.item.interview_id}`} onClose={() => setModal(null)}><InterviewDetail id={modal.item.interview_id} /></Modal>}
      {(modal?.mode === 'create' || modal?.mode === 'edit') && (
        <Modal wide={modal.mode === 'create'} title={modal.mode === 'edit' ? 'Edit interview' : 'New interview'} onClose={() => setModal(null)}>
          <InterviewForm initial={modal.mode === 'edit' ? modal.item : null} onClose={() => setModal(null)} onSaved={() => { setModal(null); state.reload(); }} />
        </Modal>
      )}
    </>
  );
}