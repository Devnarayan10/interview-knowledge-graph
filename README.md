# Interview Knowledge Graph for AI-Powered Candidate Evaluation

An AI-powered interview analysis system that represents interview information as a **Knowledge Graph** (Neo4j) with raw/semi-structured interview data stored in **MongoDB**.

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Folder structure & configuration | ✅ Complete |
| 2 | Neo4j implementation | Pending |
| 3 | MongoDB implementation | Pending |
| 4 | Seed data | Pending |
| 5 | FastAPI endpoints | Pending |
| 6 | Analytics & GDS | Pending |
| 7 | AI/NLP pipeline | Pending |
| 8 | React frontend | Pending |
| 9 | Frontend-backend integration | Pending |
| 10 | Dockerization | Pending |
| 11 | API testing | Pending |
| 12 | End-to-end testing | Pending |

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI   │────▶│    Neo4j    │
│  Dashboard  │     │   Backend   │     │ Graph + GDS │
│  (Port 5173)│     │  (Port 8000)│     │ (7474/7687) │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   MongoDB   │
                    │  (Port      │
                    │   27017)    │
                    └─────────────┘
```

---

## Technologies

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI, Uvicorn |
| Graph DB | Neo4j, Cypher, Neo4j GDS |
| Document DB | MongoDB |
| AI/NLP | Whisper, spaCy, Hugging Face, Sentence Transformers |
| Frontend | React, Tailwind CSS, Vite |
| Deployment | Docker, Docker Compose |

---

## Why Neo4j?

Neo4j is ideal for this project because interview evaluation involves **highly connected data**:

- Candidates answer questions that test skills required for roles at companies
- Feedback, emotions, and technologies form multi-hop relationships
- Graph traversal queries (e.g., "weakest skills for ML Engineer candidates") are natural in Cypher
- **GDS algorithms** (PageRank, Louvain, Node Similarity) reveal patterns impossible in relational DBs

## Why MongoDB?

MongoDB stores **flexible, semi-structured** interview artifacts:

- Full transcripts with embedded `emotion_timeline` arrays
- Audio/video references and timestamps
- Raw NLP output before graph normalization

This separation follows the **polyglot persistence** pattern: structured relationships in Neo4j, unstructured blobs in MongoDB.

---

## Project Structure

```
interview-knowledge-graph/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment configuration
│   │   ├── database/
│   │   │   ├── neo4j.py         # Neo4j driver & sessions
│   │   │   └── mongodb.py       # MongoDB client & collections
│   │   ├── models/              # Domain models (Phase 5)
│   │   ├── schemas/             # Pydantic schemas (Phase 5)
│   │   ├── routes/              # API routes (Phase 5)
│   │   ├── services/            # Business logic (Phase 5-6)
│   │   ├── ai/                  # AI/NLP pipeline (Phase 7)
│   │   ├── utils/
│   │   └── seed/                # Seeding utilities (Phase 4)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── seed_database.py
├── frontend/
│   ├── src/
│   │   ├── components/          # React components (Phase 8)
│   │   ├── pages/               # Dashboard pages (Phase 8)
│   │   ├── services/api.js      # API client
│   │   ├── hooks/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── Dockerfile
├── database/
│   ├── neo4j/
│   │   ├── constraints.cypher   # Unique constraints & indexes
│   │   ├── seed.cypher          # Seed reference patterns
│   │   └── gds.cypher           # GDS projection reference
│   └── mongodb/
│       └── seed.js              # Collection initialization
├── sample_data/
│   ├── candidates.json
│   ├── questions.json
│   └── interviews.json
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Database Schema

### Neo4j Nodes

| Label | Key Properties |
|-------|----------------|
| `Candidate` | candidate_id, name, email, experience_years |
| `Question` | question_id, text, difficulty, category |
| `Skill` | skill_id, name, category |
| `Role` | role_id, title, department |
| `Company` | company_id, name, industry |
| `Answer` | answer_id, transcript_text, score, timestamp |
| `Emotion` | emotion_id, label, confidence |
| `Feedback` | feedback_id, strengths, weaknesses, summary |
| `Technology` | tech_id, name |
| `InterviewRound` | round_id, round_number, date |

### Neo4j Relationships

```
(Candidate)-[:PARTICIPATES_IN]->(InterviewRound)
(InterviewRound)-[:INCLUDES]->(Question)
(Candidate)-[:ANSWERED]->(Answer)
(Answer)-[:IN_RESPONSE_TO]->(Question)
(Question)-[:TESTS_SKILL]->(Skill)
(Answer)-[:DEMONSTRATES]->(Skill)
(Candidate)-[:EXPRESSED]->(Emotion)
(Answer)-[:RECEIVED]->(Feedback)
(Skill)-[:REQUIRED_FOR]->(Role)
(Skill)-[:RELATED_TO]->(Technology)
(Role)-[:OFFERED_BY]->(Company)
(Candidate)-[:APPLIED_TO]->(Company)
```

### MongoDB Collections

**raw_interviews** — embedded emotion timelines, transcripts, audio refs

**emotion_logs** — referenced emotion segments with timestamps

---

## Installation

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended)
- OR: Python 3.11+, Node.js 20+, Neo4j 5.15+, MongoDB 7.0+

### Quick Start (Docker)

```bash
# 1. Clone or navigate to project
cd interview-knowledge-graph

# 2. Copy environment file
cp .env.example .env

# 3. Build and start all services
docker compose up --build

# 4. Open in browser
# Frontend:  http://localhost:5173
# API Docs:  http://localhost:8000/docs
# Neo4j:     http://localhost:7474  (neo4j / interview_graph_password)
# Health:    http://localhost:8000/health
```

### Local Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Environment Variables

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://neo4j:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `interview_graph_password` | Neo4j password |
| `MONGODB_URI` | `mongodb://mongodb:27017` | MongoDB connection URI |
| `MONGODB_DATABASE` | `interview_db` | MongoDB database name |
| `LLM_PROVIDER` | `mock` | LLM provider (mock/openai/gemini/llama) |
| `AUTO_SEED` | `true` | Auto-seed on startup |
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | Frontend API base URL |

---

## API Endpoints (Planned — Phase 5)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/candidates` | List all candidates |
| GET | `/api/candidates/{id}` | Get candidate details |
| GET | `/api/candidates/{id}/profile` | Full evaluation profile |
| GET | `/api/skills` | List skills |
| GET | `/api/questions` | List questions |
| GET | `/api/graph` | Graph data for visualization |
| GET | `/api/analytics/strongest-candidates/{skill}` | Top candidates by skill |
| GET | `/api/analytics/difficult-questions` | Lowest-scoring questions |
| GET | `/api/analytics/skill-cooccurrence` | Skills tested together |
| GET | `/api/analytics/candidate-communities` | Louvain communities |
| POST | `/api/interviews/process` | Process interview transcript |

Full Swagger docs: `http://localhost:8000/docs`

---

## GDS Algorithms (Planned — Phase 6)

| Algorithm | Projection | Purpose |
|-----------|------------|---------|
| PageRank | `roleSkillGraph` | Important skills for roles |
| Louvain | `candidateSkillGraph` | Candidate skill communities |
| Node Similarity | `companyQuestionGraph` | Similar companies by questions |

---

## Seeding

```bash
# Via Docker (automatic when AUTO_SEED=true)
docker compose up --build

# Manual seed script (Phase 4)
cd backend && python seed_database.py

# API endpoint (Phase 5)
curl -X POST http://localhost:8000/api/seed
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Neo4j won't start | Wait 60s for GDS plugin load; check `docker logs ikg-neo4j` |
| Backend can't connect | Ensure Neo4j/MongoDB healthchecks pass before backend starts |
| CORS errors | Verify `CORS_ORIGINS` in `.env` includes frontend URL |
| GDS not available | Confirm enterprise image with `NEO4J_PLUGINS=["graph-data-science"]` |
| Port conflicts | Change ports in `docker-compose.yml` |

---

## License

Academic project — Neo4j Enterprise evaluation license used for GDS features.
