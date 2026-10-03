"""Deterministic, explainable candidate evaluation (no LLM, no paid API)."""

from app.services.shared import best_role, candidate_skill_map, interviewed_roles, role_requirements, run
from app.utils.errors import NotFoundError

LABEL = "System-generated evaluation based on synthetic interview data."
DIFF_WEIGHT = {"easy": 1.0, "medium": 1.5, "hard": 2.0}
BEHAVIORAL_HINTS = ("behav", "hr", "situation", "soft", "culture", "leadership", "communication")


def _is_behavioral(category: str | None) -> bool:
    c = (category or "").lower()
    return any(h in c for h in BEHAVIORAL_HINTS)


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def compute_evaluation(answers: list[dict], coverage_pct: float, matched: list[str], missing: list[str],
                       role: str | None = None) -> dict:
    """Pure function (unit-testable). Scores are on a 0-10 scale; coverage is a percentage."""
    scored = [a for a in answers if a.get("score") is not None]
    tech_pool = [a for a in scored if not _is_behavioral(a.get("category"))] or scored
    beh_pool = [a for a in scored if _is_behavioral(a.get("category"))]

    wsum = sum(DIFF_WEIGHT.get((a.get("difficulty") or "").lower(), 1.0) for a in tech_pool)
    technical = sum(a["score"] * DIFF_WEIGHT.get((a.get("difficulty") or "").lower(), 1.0) for a in tech_pool) / wsum if wsum else 0.0
    length_score = _avg([min((a.get("word_count") or 0) / 80, 1.0) * 10 for a in scored])
    beh_score = _avg([a["score"] for a in beh_pool]) if beh_pool else _avg([a["score"] for a in scored])
    communication = 0.5 * length_score + 0.5 * beh_score
    overall = 0.5 * technical + 0.2 * communication + 0.3 * (coverage_pct / 10)

    by_cat: dict[str, list[float]] = {}
    by_skill: dict[str, list[float]] = {}
    for a in scored:
        by_cat.setdefault(a.get("category") or "General", []).append(a["score"])
        for s in a.get("skills") or []:
            by_skill.setdefault(s, []).append(a["score"])

    strengths = [f"Strong performance in {c} questions (average {_avg(v):.1f}/10)" for c, v in by_cat.items() if _avg(v) >= 7]
    strengths += [f"Skill evidence: {s} (average {_avg(v):.1f}/10)" for s, v in
                  sorted(by_skill.items(), key=lambda kv: -_avg(kv[1])) if _avg(v) >= 7][:3]
    if matched:
        strengths.append("Holds role skills: " + ", ".join(matched[:5]))
    weaknesses = [f"Below-average performance in {c} questions (average {_avg(v):.1f}/10)" for c, v in by_cat.items() if _avg(v) < 5]
    weaknesses += [f"Missing role skill: {m}" for m in missing[:5]]
    hard_low = [a for a in scored if (a.get("difficulty") or "").lower() == "hard" and a["score"] < 5]
    if hard_low:
        weaknesses.append(f"{len(hard_low)} hard question(s) scored below 5/10")

    summary = (f"Overall {overall:.1f}/10 (technical {technical:.1f}, communication {communication:.1f}); "
               f"skill coverage {coverage_pct:.0f}%" + (f" for {role}." if role else "."))
    explanation = [
        f"Technical = difficulty-weighted mean of answer scores (Easy 1.0, Medium 1.5, Hard 2.0) over {len(tech_pool)} answers = {technical:.2f}.",
        f"Communication = 0.5 * answer-length score ({length_score:.2f}) + 0.5 * behavioural/overall score ({beh_score:.2f}) = {communication:.2f}.",
        f"Skill coverage = matched required skills / required skills for the role = {coverage_pct:.1f}%.",
        f"Overall = 0.5*technical + 0.2*communication + 0.3*(coverage/10) = {overall:.2f}.",
        "Answer score = 10 * (0.55*keyword coverage + 0.25*length factor + 0.20*skill evidence), computed at seed time.",
    ]
    return {
        "overall_score": round(overall, 1), "technical_score": round(technical, 1),
        "communication_score": round(communication, 1), "skill_coverage": round(coverage_pct, 1),
        "strengths": strengths or ["No standout strengths detected from the available data"],
        "weaknesses": weaknesses or ["No significant weaknesses detected from the available data"],
        "summary": summary, "explanation": explanation,
        "breakdown": {"answers": len(scored), "by_category": {c: round(_avg(v), 2) for c, v in by_cat.items()},
                      "matched_skills": matched, "missing_skills": missing},
    }


def evaluate_candidate(cid: str) -> dict:
    cand = candidate_skill_map().get(cid)
    if not cand:
        raise NotFoundError(f"Candidate {cid} not found")
    answers = run("""
        MATCH (:Candidate {candidate_id:$id})-[:ANSWERED]->(a:Answer)-[:IN_RESPONSE_TO]->(q:Question)
        OPTIONAL MATCH (a)-[:DEMONSTRATES]->(s:Skill)
        RETURN a.answer_id AS answer_id, a.score AS score, a.word_count AS word_count,
               q.difficulty AS difficulty, q.category AS category, collect(DISTINCT s.name) AS skills
    """, id=cid)
    role = best_role(cand["skills"], role_requirements(), interviewed_roles().get(cid))
    result = compute_evaluation(answers, role["coverage"] if role else 0.0,
                                role["matched"] if role else [], role["missing"] if role else [],
                                role["title"] if role else None)
    return {"candidate_id": cid, "name": cand["name"], "role": role["title"] if role else None,
            "label": LABEL, **result}