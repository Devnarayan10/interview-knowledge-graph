from app.seed.loader import transform

ROWS = [
    {"candidate_id": "C1", "candidate_domain": "Data", "education": "B.Tech", "skills": "Python, SQL, Docker",
     "candidate_experience": "2 years", "job_type": "Full-time", "round_id": "R1", "question_id": "Q1",
     "question": "Explain Python decorators", "question_category": "Technical", "target_role": "Data Scientist",
     "difficulty": "Easy", "question_experience": "Fresher", "answer_id": "A1",
     "answer": "Python decorators wrap functions to add behaviour.", "keywords": "decorator, Python"},
    {"candidate_id": "C1", "candidate_domain": "Data", "education": "B.Tech", "skills": "Python, SQL, Docker",
     "candidate_experience": "2 years", "job_type": "Full-time", "round_id": "R1", "question_id": "Q2",
     "question": "What is a SQL join?", "question_category": "Technical", "target_role": "Data Scientist",
     "difficulty": "Medium", "question_experience": "Fresher", "answer_id": "A2",
     "answer": "A join combines rows from tables in SQL.", "keywords": "join, SQL"},
    {"candidate_id": "C2", "candidate_domain": "Web", "education": "B.E", "skills": "Python; React",
     "candidate_experience": "1 year", "job_type": "Intern", "round_id": "R1", "question_id": "Q3",
     "question": "Tell me about a conflict", "question_category": "Behavioral", "target_role": "Backend Developer",
     "difficulty": "Easy", "question_experience": "Fresher", "answer_id": "A3", "answer": "I resolved it calmly.",
     "keywords": ""},
]


def test_counts_are_derived_from_data():
    d = transform(ROWS)
    r = d["report"]
    assert (r["candidates"], r["questions"], r["answers"], r["roles"]) == (2, 3, 3, 2)
    assert r["emotion_logs"] == 9  # 3 samples per answer
    assert r["interviews"] == 2


def test_ids_are_stable_for_idempotent_merge():
    a, b = transform(ROWS), transform(ROWS)
    assert [x["answer_id"] for x in a["answers"]] == [x["answer_id"] for x in b["answers"]]
    assert [x["_id"] for x in a["emotion_logs"]] == [x["_id"] for x in b["emotion_logs"]]
    assert a["answers"] == b["answers"]


def test_relationships_are_derived_not_invented():
    d = transform(ROWS)
    assert {"candidate_id": "C1", "skill_id": "SK-python"} in d["candidate_skills"]
    assert {"question_id": "Q2", "skill_id": "SK-sql"} in d["question_skills"]
    assert d["companies"] == []  # no company column -> no company nodes
    assert all(0 < x["score"] <= 10 for x in d["answers"])