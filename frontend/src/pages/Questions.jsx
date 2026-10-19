import { useState } from 'react';
import { Pencil, Plus, Search, Trash2 } from 'lucide-react';
import { api, errMsg } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Async, Badge, EmptyState, Field, Modal, PageHeader, SkillBadge, diffTone } from '../components/ui';

function QuestionForm({ initial, onSaved, onClose }) {
  const editing = !!initial?.question_id;
  const [f, setF] = useState(editing
    ? { ...initial, skills: (initial.skills || []).join(', ') }
    : { text: '', category: '', difficulty: '', target_role: '', experience: '', skills: '' });
  const [err, setErr] = useState('');
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    const body = {
      text: f.text, category: f.category || null, difficulty: f.difficulty || null,
      target_role: f.target_role || null, experience: f.experience || null,
      skills: f.skills.split(',').map((s) => s.trim()).filter(Boolean),
    };
    try {
      if (editing) await api.updateQuestion(initial.question_id, body);
      else await api.createQuestion(body);
      onSaved();
    } catch (ex) {
      setErr(errMsg(ex));
    }
  };

  return (
    <form onSubmit={submit}>
      <Field label="Question text"><textarea required rows={3} className="input" value={f.text} onChange={set('text')} /></Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Category"><input className="input" value={f.category || ''} onChange={set('category')} /></Field>
        <Field label="Difficulty">
          <select className="input" value={f.difficulty || ''} onChange={set('difficulty')}>
            <option value="">—</option>{['Easy', 'Medium', 'Hard'].map((d) => <option key={d}>{d}</option>)}
          </select>
        </Field>
        <Field label="Target role"><input className="input" value={f.target_role || ''} onChange={set('target_role')} /></Field>
        <Field label="Experience level"><input className="input" value={f.experience || ''} onChange={set('experience')} /></Field>
      </div>
      <Field label="Skills tested (comma separated)"><input className="input" value={f.skills} onChange={set('skills')} /></Field>
      {err && <div className="mb-3 rounded bg-rose-50 p-2 text-sm text-rose-700">{err}</div>}
      <div className="flex justify-end gap-2">
        <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn-primary">{editing ? 'Update' : 'Create'}</button>
      </div>
    </form>
  );
}

function QuestionDetail({ id }) {
  const s = useApi(() => api.question(id), [id]);
  return (
    <Async state={s}>
      {(q) => (
        <div className="space-y-3 text-sm">
          <p className="font-medium text-slate-900">{q.text}</p>
          <div className="flex flex-wrap gap-2">
            <Badge tone={diffTone(q.difficulty)}>{q.difficulty}</Badge><Badge>{q.category}</Badge>
            <Badge tone="amber">{q.target_role}</Badge><Badge tone="indigo">{q.experience}</Badge>
          </div>
          <div>
            <div className="mb-1 text-xs font-semibold uppercase text-slate-500">Related skills (TESTS_SKILL)</div>
            <div className="flex flex-wrap gap-1">
              {(q.skills || []).length ? (q.skills || []).map((x) => <SkillBadge key={x} name={x} tone="emerald" />) : <span className="text-slate-400">None derived</span>}
            </div>
          </div>
          <div className="text-slate-600">Answers recorded: <b>{q.answers}</b> · Average score: <b>{q.avg_score ?? '—'}</b></div>
          {q.keywords?.length > 0 && <div className="text-xs text-slate-500">Keywords: {q.keywords.join(', ')}</div>}
        </div>
      )}
    </Async>
  );
}

export default function Questions() {
  const [f, setF] = useState({ q: '', category: '', difficulty: '', role: '', experience: '' });
  const [page, setPage] = useState(1);
  const [modal, setModal] = useState(null);
  const [error, setError] = useState('');
  const state = useApi(() => api.questions({ ...f, page, page_size: 15 }), [f, page]);

  const setFilter = (k) => (e) => {
    setF({ ...f, [k]: e.target.value });
    setPage(1);
  };
  const facets = state.data?.facets || { categories: [], difficulties: [], roles: [], experiences: [] };

  const remove = async (q) => {
    if (!window.confirm(`Delete question ${q.question_id} and every answer given to it?`)) return;
    try {
      await api.deleteQuestion(q.question_id);
      state.reload();
    } catch (e) {
      setError(errMsg(e));
    }
  };

  const select = (key, label, options) => (
    <select className="input w-44" value={f[key]} onChange={setFilter(key)}>
      <option value="">{label}</option>
      {options.map((o) => <option key={o}>{o}</option>)}
    </select>
  );

  return (
    <>
      <PageHeader title="Question bank" subtitle="Search, filter and manage interview questions stored as Question nodes in Neo4j."
        actions={<button className="btn-primary" onClick={() => setModal({ mode: 'create' })}><Plus size={16} /> New question</button>} />
      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative min-w-[240px] flex-1">
          <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
          <input className="input pl-9" placeholder="Search question text…" value={f.q} onChange={setFilter('q')} />
        </div>
        {select('category', 'All categories', facets.categories)}
        {select('difficulty', 'All difficulties', facets.difficulties)}
        {select('role', 'All roles', facets.roles)}
        {select('experience', 'All experience', facets.experiences)}
      </div>
      {error && <div className="mb-3 rounded bg-rose-50 p-2 text-sm text-rose-700">{error}</div>}
      <Async state={state}>
        {(d) => (d.items.length ? (
          <>
            <div className="card overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50"><tr>{['ID', 'Question', 'Category', 'Difficulty', 'Role', 'Skills', ''].map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {d.items.map((q) => (
                    <tr key={q.question_id} className="cursor-pointer hover:bg-indigo-50/40" onClick={() => setModal({ mode: 'view', item: q })}>
                      <td className="td font-mono text-xs">{q.question_id}</td>
                      <td className="td max-w-md">{q.text}</td>
                      <td className="td">{q.category || '—'}</td>
                      <td className="td"><Badge tone={diffTone(q.difficulty)}>{q.difficulty || '—'}</Badge></td>
                      <td className="td text-xs">{q.target_role || '—'}</td>
                      <td className="td"><div className="flex flex-wrap gap-1">{(q.skills || []).slice(0, 3).map((s) => <SkillBadge key={s} name={s} tone="emerald" />)}</div></td>
                      <td className="td whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                        <button className="mr-2 text-slate-400 hover:text-indigo-600" onClick={() => setModal({ mode: 'edit', item: q })}><Pencil size={15} /></button>
                        <button className="text-slate-400 hover:text-rose-600" onClick={() => remove(q)}><Trash2 size={15} /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-3 flex items-center justify-between text-sm text-slate-500">
              <span>{d.total} question(s) · page {d.page} of {Math.max(1, Math.ceil(d.total / d.page_size))}</span>
              <div className="flex gap-2">
                <button className="btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
                <button className="btn-ghost" disabled={page * d.page_size >= d.total} onClick={() => setPage(page + 1)}>Next</button>
              </div>
            </div>
          </>
        ) : <EmptyState text="No questions match the filters" />)}
      </Async>
      {modal?.mode === 'view' && <Modal title={`Question ${modal.item.question_id}`} onClose={() => setModal(null)}><QuestionDetail id={modal.item.question_id} /></Modal>}
      {(modal?.mode === 'create' || modal?.mode === 'edit') && (
        <Modal title={modal.mode === 'edit' ? 'Edit question' : 'New question'} onClose={() => setModal(null)}>
          <QuestionForm initial={modal.item} onClose={() => setModal(null)} onSaved={() => { setModal(null); state.reload(); }} />
        </Modal>
      )}
    </>
  );
}