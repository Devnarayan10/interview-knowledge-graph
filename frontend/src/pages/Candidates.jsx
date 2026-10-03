import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search } from 'lucide-react';
import { api, errMsg } from '../services/api';
import { useApi } from '../hooks/useApi';
import CandidateTable from '../components/CandidateTable';
import { Async, Field, Modal, PageHeader } from '../components/ui';

const EMPTY = { name: '', education: '', domain: '', job_type: '', experience_years: '', skills: '' };

function CandidateForm({ initial, onSaved, onClose }) {
  const editing = !!initial?.candidate_id;
  const [form, setForm] = useState(editing ? { ...initial, skills: (initial.skills || []).join(', '), experience_years: initial.experience_years ?? '' } : EMPTY);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setErr('');
    const body = {
      name: form.name, education: form.education || null, domain: form.domain || null, job_type: form.job_type || null,
      experience_years: form.experience_years === '' ? null : Number(form.experience_years),
      skills: form.skills.split(',').map((s) => s.trim()).filter(Boolean),
    };
    try {
      if (editing) await api.updateCandidate(initial.candidate_id, body);
      else await api.createCandidate(body);
      onSaved();
    } catch (ex) {
      setErr(errMsg(ex));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit}>
      <Field label="Name"><input required className="input" value={form.name} onChange={set('name')} /></Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Domain"><input className="input" value={form.domain || ''} onChange={set('domain')} /></Field>
        <Field label="Job type"><input className="input" value={form.job_type || ''} onChange={set('job_type')} /></Field>
        <Field label="Education"><input className="input" value={form.education || ''} onChange={set('education')} /></Field>
        <Field label="Experience (years)"><input type="number" min="0" step="0.5" className="input" value={form.experience_years} onChange={set('experience_years')} /></Field>
      </div>
      <Field label="Skills (comma separated)"><input className="input" value={form.skills} onChange={set('skills')} placeholder="Python, SQL, Docker" /></Field>
      {err && <div className="mb-3 rounded bg-rose-50 p-2 text-sm text-rose-700">{err}</div>}
      <div className="flex justify-end gap-2">
        <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn-primary" disabled={busy}>{busy ? 'Saving…' : editing ? 'Update' : 'Create'}</button>
      </div>
    </form>
  );
}

export default function Candidates() {
  const nav = useNavigate();
  const [q, setQ] = useState('');
  const [domain, setDomain] = useState('');
  const [jobType, setJobType] = useState('');
  const [modal, setModal] = useState(null); // {mode:'create'|'edit', item}
  const [error, setError] = useState('');
  const state = useApi(() => api.candidates({ q, domain, job_type: jobType }), [q, domain, jobType]);

  const remove = async (c) => {
    if (!window.confirm(`Delete ${c.name} (${c.candidate_id}) and all their answers, rounds and interview documents?`)) return;
    try {
      await api.deleteCandidate(c.candidate_id);
      state.reload();
    } catch (e) {
      setError(errMsg(e));
    }
  };

  return (
    <>
      <PageHeader title="Candidates" subtitle="Searchable candidate table backed by Neo4j. Click a row to open the profile."
        actions={<button className="btn-primary" onClick={() => setModal({ mode: 'create' })}><Plus size={16} /> New candidate</button>} />
      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative min-w-[240px] flex-1">
          <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
          <input className="input pl-9" placeholder="Search by name, id, education or skill…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <select className="input w-48" value={domain} onChange={(e) => setDomain(e.target.value)}>
          <option value="">All domains</option>
          {(state.data?.facets.domains || []).map((d) => <option key={d}>{d}</option>)}
        </select>
        <select className="input w-44" value={jobType} onChange={(e) => setJobType(e.target.value)}>
          <option value="">All job types</option>
          {(state.data?.facets.job_types || []).map((d) => <option key={d}>{d}</option>)}
        </select>
      </div>
      {error && <div className="mb-3 rounded bg-rose-50 p-2 text-sm text-rose-700">{error}</div>}
      <Async state={state}>
        {(d) => (
          <>
            <div className="mb-2 text-xs text-slate-500">{d.total} candidate(s)</div>
            <CandidateTable items={d.items} onOpen={(c) => nav(`/candidates/${encodeURIComponent(c.candidate_id)}`)}
              onEdit={(c) => setModal({ mode: 'edit', item: c })} onDelete={remove} />
          </>
        )}
      </Async>
      {modal && (
        <Modal title={modal.mode === 'edit' ? 'Edit candidate' : 'New candidate'} onClose={() => setModal(null)}>
          <CandidateForm initial={modal.item} onClose={() => setModal(null)} onSaved={() => { setModal(null); state.reload(); }} />
        </Modal>
      )}
    </>
  );
}