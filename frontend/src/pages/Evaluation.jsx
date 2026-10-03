import { useState } from 'react';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import EvaluationCard from '../components/EvaluationCard';
import { Async, EmptyState, PageHeader } from '../components/ui';

export default function Evaluation() {
  const list = useApi(() => api.candidates(), []);
  const [id, setId] = useState('');
  const ev = useApi(() => (id ? api.evaluation(id) : Promise.resolve(null)), [id]);
  return (
    <>
      <PageHeader title="Candidate evaluation" subtitle="Deterministic, explainable scoring computed from answer scores, difficulty, skill coverage and keyword evidence. No LLM is involved." />
      <Async state={list}>
        {(d) => (
          <select className="input mb-6 max-w-md" value={id} onChange={(e) => setId(e.target.value)}>
            <option value="">Select candidate…</option>
            {d.items.map((c) => <option key={c.candidate_id} value={c.candidate_id}>{c.candidate_id} · {c.name}</option>)}
          </select>
        )}
      </Async>
      {!id ? <EmptyState text="Choose a candidate to evaluate" /> : <Async state={ev}>{(e) => <EvaluationCard ev={e} />}</Async>}
    </>
  );
}