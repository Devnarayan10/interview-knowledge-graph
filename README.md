\# Interview Knowledge Graph for AI-Powered Candidate Evaluation



BCSE406L NoSQL Database project. A polyglot-persistence system: \*\*Neo4j\*\* stores the interview knowledge graph, \*\*MongoDB\*\* stores flexible interview/session documents and emotion logs, \*\*FastAPI\*\* exposes them, and a \*\*React\*\* dashboard visualises everything.



> \*\*Data note.\*\* `data/synthetic\_interview\_dataset.csv` is \*synthetic\*: CareerCorpus candidate profiles are associated with semantically compatible Ankshi interview questions. The original candidates never answered these questions. Names, answer scores, emotions, feedback and dates are derived deterministically (see "Derived fields").



\## Problem statement

Interview data is highly connected (candidates → rounds → questions → skills → roles) and partly unstructured (transcripts, emotion timelines). Relational schemas model this awkwardly. We use a graph database for relationships and a document database for semi-structured sessions.



\## Objectives

Model the interview domain as a graph; store flexible interview documents; demonstrate CRUD, indexing, aggregation and graph analytics; provide explainable (non-LLM) evaluation, skill-gap analysis and role compatibility; provide an application UI and DA2 evidence.



\## Architecture

```

CSV → loader.transform() → seed\_service ─┬─► Neo4j  (MERGE, constraints)

&#x20;                                         └─► MongoDB (upsert, indexes)

FastAPI (routes → services) ──► React (Vite, Tailwind, Recharts, react-force-graph-2d)

```



\## Technology stack

Neo4j 5 Enterprise (evaluation licence) + GDS plugin · MongoDB 7 · Python 3.11, FastAPI, Pydantic v2 · React 18, Vite, Tailwind, React Router, Recharts, Lucide, react-force-graph-2d · Docker Compose.



\## Neo4j model

Nodes: Candidate, Question, Skill, Role, Company, Answer, Emotion, Feedback, Technology, InterviewRound.

Relationships: `PARTICIPATES\_IN`, `INCLUDES`, `ANSWERED`, `IN\_RESPONSE\_TO`, `TESTS\_SKILL`, `DEMONSTRATES`, `EXPRESSED`, `RECEIVED`, `REQUIRED\_FOR`, `RELATED\_TO`, plus `OFFERED\_BY`/`APPLIED\_TO` (only if the dataset has a `company` column).

Added (justified) relationships: `HAS\_SKILL` (Candidate→Skill, needed for skill gaps and similarity), `INTERVIEWED\_FOR` (Candidate→Role), `FOR\_ROLE` (Question→Role).

Constraints: uniqueness on all ten id properties. Indexes: Candidate.name, Skill.name, Question.category, Role.title, Company.name, Answer.candidate\_id, Answer.round\_id. All are applied automatically at startup and by every seed run.



\## MongoDB model (`interview\_db`)

\* `raw\_interviews` — one document per interview round: embedded `qa\[]`, `transcript\[]`, `emotion\_timeline\[]`, variable `metadata{}`.

\* `emotion\_logs` — one document per emotion sample (3 per answer), referencing `interview\_id`, `candidate\_id`, `answer\_id`.

Indexes: candidate\_id, round\_id, target\_role, started\_at (interviews); candidate\_id, interview\_id, label, timestamp, confidence (emotions).

Design: embedding for data always read with the interview; referencing (ids) between MongoDB and Neo4j and for high-volume emotion logs.



\## Dataset

Place the CSV at `data/synthetic\_interview\_dataset.csv`. All counts shown in the UI are computed from the databases; nothing is hard-coded.



\### Derived fields (the CSV has no such columns)

| Field | Derivation |

|---|---|

| Candidate.name | `Candidate <candidate\_id>` |

| experience\_years | number before "year(s)" in `candidate\_experience`, else null |

| Skill nodes | union of candidate `skills` |

| TESTS\_SKILL | skill names found in question text + keywords |

| DEMONSTRATES | skill names found in answer text + keywords |

| Role.department | most common candidate\_domain among that role's rows |

| REQUIRED\_FOR.weight | 2 × questions of the role testing the skill + candidates interviewed for the role holding it (top 10) |

| Answer.score | 10 × (0.55·keyword coverage + 0.25·min(words/80,1) + 0.20·min(skills/2,1)) |

| Emotion / Feedback / dates | deterministic pseudo-random values seeded by ids; marked `synthetic` |

| Company | only created if a `company` column exists |



\## Seeding

`POST /api/seed`, `python seed\_database.py`, or automatically on first start when the graph is empty (`AUTO\_SEED=true`). Idempotent: Neo4j uses `MERGE` on unique ids; MongoDB uses `ReplaceOne(upsert=True)` on deterministic `\_id`s.



\## Docker

`docker compose up -d --build` starts neo4j (7474/7687), mongodb (27017), backend (8000), frontend (5173) with named volumes. The backend waits for both databases; the frontend waits for a healthy backend.



\## API (all under `/api`, plus `/health`)

Dashboard `GET /dashboard/summary` · Candidates / Questions / Interviews CRUD (`GET`, `GET /{id}`, `POST`, `PUT /{id}`, `DELETE /{id}`) · `GET /evaluation/{id}` · `GET /graph`, `GET /graph/candidate/{id}` · `GET /analytics/{overview|skills|roles|difficulties|gds|mongo}` · `GET /recommendations/{candidate|similar|skill-gap}/{id}` · `GET /skills`, `/roles` · `GET /database/{neo4j|mongodb|indexes}` · `POST /seed`. Interactive docs at `/docs`.



\## Frontend

Dashboard, Candidates (+profile), Compare, Interviews, Questions, Skills, Roles, Knowledge Graph, Evaluation, Recommendations, Database \& NoSQL, About. Every call hits a real endpoint; loading, error and empty states are handled.



\## CRUD

Candidates, Questions (Neo4j) and Interviews (MongoDB, synced to Neo4j) support create/read/update/delete from both the API and the UI. Deletes require confirmation and cascade to dependent answers/rounds/emotions.



\## Queries, indexes, aggregation

`database/neo4j/queries.cypher` (20 queries incl. 3 GDS) and `database/mongodb/queries.js` (11 queries). MongoDB aggregations are exposed at `/api/analytics/mongo` and on the Database page.



\## Graph analytics

PageRank, Louvain and Node Similarity run through GDS using explicit native projections that are dropped afterwards. If GDS is unavailable the API returns a labelled fallback (degree centrality, skill category groups, Jaccard) and never crashes.



\## Evaluation, skill gaps, recommendations

Evaluation: technical = difficulty-weighted mean score (Easy 1, Medium 1.5, Hard 2); communication = ½ length score + ½ behavioural score; overall = 0.5·technical + 0.2·communication + 0.3·coverage/10. Skill gap: matched/missing required skills for a role. Role compatibility: coverage % per role. Similar candidates: Jaccard over skills. All outputs are labelled system-generated.



\## NoSQL concepts

Flexible schema, embedding vs referencing, indexing, aggregation, scalability/distribution (replica sets, sharding, causal clusters — described, not deployed), polyglot persistence. See the Database \& NoSQL page and `docs/viva\_questions.md`.



\## Testing

```

docker compose exec backend python -m pytest -q

docker compose exec backend python validate\_system.py

```



\## DA2 screenshots

See `docs/da2\_evidence\_checklist.md`.



\## Team contribution

Fill in per member (design, graph model, MongoDB model, backend, frontend, testing).



\## Limitations

Synthetic data; scores/emotions are derived, not measured; no Company nodes without a company column; single-node databases; no authentication; no real speech/NLP/LLM models.



\## Future enhancements

Real transcripts with Whisper/spaCy/Sentence-Transformers behind optional interfaces, authentication, Neo4j clustering, MongoDB sharding, pagination for very large graphs.

