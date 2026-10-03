import { PageHeader } from '../components/ui';

const Block = ({ title, children }) => <div className="card p-5"><h3 className="mb-2 font-semibold text-slate-900">{title}</h3><div className="space-y-2 text-sm text-slate-600">{children}</div></div>;

export default function About() {
  return (
    <>
      <PageHeader title="About" subtitle="Interview Knowledge Graph for AI-Powered Candidate Evaluation — BCSE406L NoSQL Database project." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Block title="Problem statement"><p>Interview data is highly connected (candidates, questions, skills, roles, answers) yet partly unstructured (transcripts, emotions). A single relational schema handles both poorly. This system models connections in Neo4j and flexible session data in MongoDB.</p></Block>
        <Block title="Architecture"><p>CSV dataset → seed engine → Neo4j (graph) + MongoDB (documents) → FastAPI → React dashboard.</p></Block>
        <Block title="About the data"><p>The dataset is synthetic: CareerCorpus candidate profiles are associated with semantically compatible Ankshi interview questions. The original candidates never answered these questions.</p><p>Names, answer scores, emotions, feedback and dates are generated deterministically from the data and are not real measurements.</p></Block>
        <Block title="About the evaluation"><p>Evaluation and role compatibility are transparent formulas over skill overlap and answer scores. No LLM, Whisper, spaCy or other model runs in this system, and the output is not a hiring decision.</p></Block>
      </div>
    </>
  );
}