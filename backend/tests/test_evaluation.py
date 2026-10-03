from app.services.evaluation_service import compute_evaluation


def test_evaluation_is_deterministic_and_bounded():
    answers = [
        {"score": 8, "difficulty": "Hard", "category": "Technical", "word_count": 90, "skills": ["Python"]},
        {"score": 4, "difficulty": "Easy", "category": "Behavioral", "word_count": 30, "skills": []},
    ]
    a = compute_evaluation(answers, 60.0, ["Python"], ["Docker"], "Data Scientist")
    b = compute_evaluation(answers, 60.0, ["Python"], ["Docker"], "Data Scientist")
    assert a == b
    for key in ("overall_score", "technical_score", "communication_score"):
        assert 0 <= a[key] <= 10
    assert a["skill_coverage"] == 60.0
    assert any("Docker" in w for w in a["weaknesses"])
    assert len(a["explanation"]) >= 4


def test_empty_answers_do_not_crash():
    r = compute_evaluation([], 0.0, [], [])
    assert r["overall_score"] == 0.0