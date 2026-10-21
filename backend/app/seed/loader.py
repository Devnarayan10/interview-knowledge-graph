"""CSV -> graph/document transformation. Pure Python: no database access.

Derivations (documented because the CSV has no such columns):
  * Candidate.name        = "Candidate <candidate_id>"
  * experience_years      = number found in candidate_experience text ("3 years") else null
  * Skill                 = union of the candidate `skills` column
  * TESTS_SKILL           = skill names found in question text + keywords
  * DEMONSTRATES          = skill names found in answer text + keywords
  * Role                  = distinct target_role; department = most common candidate_domain
  * REQUIRED_FOR (weight) = 2 * (#questions of the role testing the skill) + (#candidates interviewed
                            for the role who hold the skill); top 10 per role
  * Answer.score          = 10 * (0.55*keyword_coverage + 0.25*min(words/80,1) + 0.20*min(skills/2,1))
  * Emotion / Feedback / dates = deterministic pseudo-random values seeded by ids (synthetic)
"""

import csv
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.utils.helpers import (
    TECH_VOCAB, categorize_skill, clean, parse_years, slugify, split_list, stable_hash,
)

DATASET_NAME = "synthetic_interview_dataset.csv"
EXPECTED_COLUMNS = [
    "candidate_id", "candidate_domain", "education", "skills", "candidate_experience", "job_type",
    "round_id", "question_id", "question", "question_category", "target_role", "difficulty",
    "question_experience", "answer_id", "answer", "keywords",
]
PHASES = [("start", 0), ("middle", 60), ("end", 150)]


def find_dataset() -> Path:
    here = Path(__file__).resolve()
    options = []
    if get_settings().dataset_path:
        options.append(Path(get_settings().dataset_path))
    options += [
        here.parents[2] / "data" / DATASET_NAME,
        here.parents[3] / "data" / DATASET_NAME,
        Path("/app/data") / DATASET_NAME,
    ]
    for p in options:
        if p.exists():
            return p
    raise FileNotFoundError(
        f"{DATASET_NAME} not found. Put it in <project>/data/ . Looked in: " + ", ".join(map(str, options))
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def _pattern(name: str):
    return re.compile(r"(?<![A-Za-z0-9+#])" + re.escape(name) + r"(?![A-Za-z0-9+#])", re.I)


def score_answer(answer: str, keywords: list[str], n_skills: int = 0):
    """Deterministic answer score. Returns (score, keyword_coverage, word_count, matched_keywords)."""
    text = (answer or "").lower()
    words = len(text.split())
    hits = [k for k in keywords if k.lower() in text]
    cov = len(hits) / len(keywords) if keywords else 0.5
    score = 10 * (0.55 * cov + 0.25 * min(words / 80, 1.0) + 0.20 * min(n_skills / 2, 1.0))
    return round(max(1.0, min(10.0, score)), 1), round(cov, 2), words, hits


def _emotion(rng: random.Random, score: float) -> tuple[str, float]:
    p = score / 10
    weights = {
        "confident": 0.5 * p + 0.05, "enthusiastic": 0.25 * p + 0.03, "neutral": 0.30,
        "hesitant": 0.35 * (1 - p) + 0.05, "nervous": 0.40 * (1 - p) + 0.05,
    }
    label = rng.choices(list(weights), weights=list(weights.values()))[0]
    return label, round(0.55 + 0.4 * rng.random(), 2)


def transform(rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("Dataset is empty")
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in rows[0]]

    vocab: dict[str, str] = {}
    for r in rows:
        for s in split_list(r.get("skills")):
            vocab.setdefault(s.lower(), s)
    skills = {k: {"skill_id": "SK-" + slugify(v), "name": v, "category": categorize_skill(v)} for k, v in vocab.items()}
    patterns = {k: _pattern(v) for k, v in vocab.items()}

    def find_skills(text: str) -> list[str]:
        return [k for k, p in patterns.items() if p.search(text)]

    candidates: dict[str, dict] = {}
    cand_skill_keys: dict[str, list[str]] = {}
    cand_rounds: dict[str, dict[str, int]] = defaultdict(dict)
    questions: dict[str, dict] = {}
    rounds: dict[str, dict] = {}
    interviews: dict[str, dict] = {}
    answers, emotion_logs = [], []
    q_skills, a_skills, c_skills = set(), set(), set()
    tested_by_role: dict[str, Counter] = defaultdict(Counter)
    role_domains: dict[str, Counter] = defaultdict(Counter)
    role_candidates: dict[str, set] = defaultdict(set)
    cand_roles: set[tuple[str, str]] = set()
    companies: dict[str, dict] = {}
    cand_company: set[tuple[str, str]] = set()

    for i, r in enumerate(rows):
        cid = r.get("candidate_id") or r.get("candidate_source_id") or f"C{i + 1:03d}"
        qid = r.get("question_id") or f"Q{i + 1:03d}"
        aid = r.get("answer_id") or f"A{i + 1:03d}"
        role = r.get("target_role") or r.get("source_role") or "General"
        rraw = r.get("round_id") or "R1"
        round_key = f"{cid}__{rraw}"
        qtext, atext = r.get("question", ""), r.get("answer", "")
        kws = split_list(r.get("keywords"))
        diff = r.get("difficulty") or "Medium"
        cat = r.get("question_category") or "General"

        if cid not in candidates:
            keys = [s.lower() for s in split_list(r.get("skills")) if s.lower() in skills]
            cand_skill_keys[cid] = keys
            candidates[cid] = {
                "candidate_id": cid, "name": f"Candidate {cid}", "email": None,
                "experience_years": parse_years(r.get("candidate_experience")),
                "education": r.get("education") or None, "domain": r.get("candidate_domain") or None,
                "job_type": r.get("job_type") or None, "skills": [skills[k]["name"] for k in keys],
                "source_id": r.get("candidate_source_id") or None,
                "experience_text": r.get("candidate_experience") or None,
            }
            for k in keys:
                c_skills.add((cid, skills[k]["skill_id"]))

        role_id = "R-" + slugify(role)
        role_domains[role][r.get("candidate_domain") or "General"] += 1
        role_candidates[role].add(cid)
        cand_roles.add((cid, role_id))

        # Documented, conservative category-to-skill mapping for behavioral questions.
        # These mappings describe skills a question is intended to test, not proof of ability.
        CATEGORY_SKILLS = {
            "leadership": ("Leadership", "Team Management"),
            "team collaboration": ("Communication", "Team Management"),
            "conflict resolution": ("Communication", "Negotiation"),
            "work style": ("Project Management", "Communication"),
            "culture fit": ("Communication",),
            "motivation": ("Communication",),
            "adaptability": ("Project Management",),
            "career goals": ("Communication",),
        }
        tested = find_skills(qtext + " " + " ".join(kws))
        tested = sorted(set(tested) | {name.lower() for name in CATEGORY_SKILLS.get(cat.lower(), ()) if name.lower() in skills})
        shown = find_skills(atext + " " + " ".join(kws))

        if qid not in questions:
            questions[qid] = {
                "question_id": qid, "text": qtext, "difficulty": diff, "category": cat,
                "target_role": role, "role_id": role_id, "experience": r.get("question_experience") or None,
                "keywords": kws,
            }
            for k in tested:
                q_skills.add((qid, skills[k]["skill_id"]))
                tested_by_role[role][k] += 1

        if rraw not in cand_rounds[cid]:
            cand_rounds[cid][rraw] = len(cand_rounds[cid]) + 1
        rnum = cand_rounds[cid][rraw]
        start = datetime(2025, 1, 6, 10, 0) + timedelta(days=stable_hash(round_key) % 180)

        if round_key not in rounds:
            rounds[round_key] = {
                "round_id": round_key, "round_label": rraw, "round_number": rnum, "candidate_id": cid,
                "date": start.date().isoformat(), "target_role": role,
            }
            interviews[round_key] = {
                "_id": round_key, "interview_id": round_key, "candidate_id": cid, "round_id": round_key,
                "round_label": rraw, "round_number": rnum, "target_role": role, "started_at": start,
                "status": "completed", "transcript": [], "qa": [], "emotion_timeline": [],
                "metadata": {k: v for k, v in {
                    "synthetic": True, "dataset": DATASET_NAME, "candidate_domain": r.get("candidate_domain"),
                    "job_type": r.get("job_type"), "source_role": r.get("source_role"),
                    "source_type": r.get("source_type"), "answer_source": r.get("answer_source"),
                    "merge_note": r.get("merge_note"),
                }.items() if v not in (None, "")},
            }

        iv = interviews[round_key]

        score, cov, words, hits = score_answer(atext, kws, len(shown))
        rng = random.Random(stable_hash(aid))
        t = 120 + len(iv["qa"]) * 240
        samples = []

        for phase, off in PHASES:
            label, conf = _emotion(rng, score)
            samples.append({
                "phase": phase,
                "timestamp_sec": t + off,
                "label": label,
                "confidence": conf
            })

        dom = samples[1]
        stamp = (start + timedelta(seconds=t)).isoformat()
        missed = [k for k in kws if k not in hits]

        answers.append({
            "answer_id": aid,
            "candidate_id": cid,
            "question_id": qid,
            "round_id": round_key,
            "transcript_text": atext,
            "score": score,
            "keyword_coverage": cov,
            "word_count": words,
            "timestamp": stamp,
            "emotion_id": "EMO-" + aid,
            "emotion_label": dom["label"],
            "emotion_confidence": dom["confidence"],
            "feedback_id": "FB-" + aid,
            "strengths": ", ".join(hits[:4]) or "Relevant answer",
            "weaknesses": ", ".join(missed[:4]) or "No major gaps detected",
            "summary": f"Scored {score}/10 on a {diff} {cat} question (keyword coverage {cov:.0%}).",
        })

        for k in shown:
            a_skills.add((aid, skills[k]["skill_id"]))

        iv["transcript"] += [
            {"speaker": "interviewer", "text": qtext, "t": t},
            {"speaker": "candidate", "text": atext, "t": t + 30},
        ]

        iv["qa"].append({
            "question_id": qid,
            "question": qtext,
            "category": cat,
            "difficulty": diff,
            "answer_id": aid,
            "answer": atext,
            "score": score,
            "skills_tested": [skills[k]["name"] for k in tested],
            "keywords": kws,
            "timestamp": stamp,
            "timestamp_sec": t,
            "emotion": {
                "label": dom["label"],
                "confidence": dom["confidence"]
            },
        })

        for idx, s in enumerate(samples):
            iv["emotion_timeline"].append({**s, "question_id": qid})

            emotion_logs.append({
                "_id": f"{aid}:{idx}",
                "interview_id": round_key,
                "candidate_id": cid,
                "question_id": qid,
                "answer_id": aid,
                "label": s["label"],
                "confidence": s["confidence"],
                "phase": s["phase"],
                "timestamp_sec": s["timestamp_sec"],
                "timestamp": start + timedelta(seconds=s["timestamp_sec"]),
                "target_role": role,
                "synthetic": True,
            })

        company = r.get("company")

        if company:
            companies["CO-" + slugify(company)] = {
                "company_id": "CO-" + slugify(company),
                "name": company,
                "industry": r.get("industry") or None,
            }
            cand_company.add((cid, "CO-" + slugify(company)))
    # Synthetic companies for DA2 demonstration.
    # These are fictional companies, not verified employers.
    DEMO_COMPANIES = {
        "Accountant": ("CO-demo-accounting", "Demo Accounting Services", "Accounting"),
        "Banking / Financial Analyst": ("CO-demo-banking", "Demo Banking Group", "Banking"),
        "Fashion / Apparel Professional": ("CO-demo-fashion", "Demo Fashion Studio", "Fashion"),
        "Financial Analyst": ("CO-demo-finance", "Demo Financial Consulting", "Finance"),
        "Research Assistant": ("CO-demo-research", "Demo Research Institute", "Research"),
        "Teacher / Trainer": ("CO-demo-education", "Demo Learning Academy", "Education"),
    }

    role_companies = []

    for role_name in role_domains:
        if role_name not in DEMO_COMPANIES:
            continue

        company_id, company_name, industry = DEMO_COMPANIES[role_name]

        companies[company_id] = {
            "company_id": company_id,
            "name": company_name,
            "industry": industry,
            "synthetic": True,
            "data_source": "DA2 demonstration",
        }

        role_companies.append({
            "role_id": "R-" + slugify(role_name),
            "company_id": company_id,
        })
    # Roles + REQUIRED_FOR
    roles, role_skills = {}, []

    for role, doms in role_domains.items():
        rid = "R-" + slugify(role)

        roles[rid] = {
            "role_id": rid,
            "title": role,
            "department": doms.most_common(1)[0][0]
        }

        holders = Counter(
            k
            for c in role_candidates[role]
            for k in cand_skill_keys[c]
        )

        weights = {
            k: tested_by_role[role][k] * 2 + holders[k]
            for k in set(tested_by_role[role]) | set(holders)
        }

        for k, w in sorted(
            weights.items(),
            key=lambda kv: (-kv[1], kv[0])
        )[:10]:
            if w > 0:
                role_skills.append({
                    "skill_id": skills[k]["skill_id"],
                    "role_id": rid,
                    "weight": w
                })

    techs = {
        k: {
            "tech_id": "T-" + slugify(v["name"]),
            "name": v["name"]
        }
        for k, v in skills.items()
        if k in TECH_VOCAB
    }

    skill_tech = [
        {
            "skill_id": skills[k]["skill_id"],
            "tech_id": t["tech_id"]
        }
        for k, t in techs.items()
    ]

    pair = lambda s, a, b: [
        {a: x, b: y}
        for x, y in sorted(s)
    ]

    data = {
        "candidates": list(candidates.values()),
        "questions": list(questions.values()),
        "skills": [{k: v for k, v in s.items()} for s in skills.values()],
        "roles": list(roles.values()),
        "technologies": list(techs.values()),
        "companies": list(companies.values()),
        "rounds": list(rounds.values()),
        "answers": answers,

        "candidate_roles": [
            {"candidate_id": c, "role_id": r}
            for c, r in sorted(cand_roles)
        ],

        "candidate_skills": pair(
            c_skills,
            "candidate_id",
            "skill_id"
        ),

        "question_skills": pair(
            q_skills,
            "question_id",
            "skill_id"
        ),

        "answer_skills": pair(
            a_skills,
            "answer_id",
            "skill_id"
        ),

        "candidate_companies": pair(
            cand_company,
            "candidate_id",
            "company_id"
        ),
        "role_companies": role_companies,
        "role_skills": role_skills,
        "skill_tech": skill_tech,
        "mongo_interviews": list(interviews.values()),
        "emotion_logs": emotion_logs,
    }

    data["report"] = {
        "rows": len(rows),
        "candidates": len(candidates),
        "questions": len(questions),
        "answers": len(answers),
        "skills": len(skills),
        "roles": len(roles),
        "companies": len(companies),
        "interviews": len(interviews),
        "emotion_logs": len(emotion_logs),
        "missing_columns": missing_cols,
        "columns_found": sorted(rows[0].keys()),
    }

    return data