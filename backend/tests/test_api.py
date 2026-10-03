from fastapi.testclient import TestClient

import app.main as main
from app.services import candidate_service, question_service

client = TestClient(main.app)


def test_health(monkeypatch):
    monkeypatch.setattr(main, "verify_neo4j_connection", lambda: True)
    monkeypatch.setattr(main, "verify_mongodb_connection", lambda: False)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "neo4j": True, "mongodb": False}


def test_candidate_endpoint(monkeypatch):
    fake = {"items": [{"candidate_id": "C1", "name": "Candidate C1"}], "total": 1, "facets": {}}
    monkeypatch.setattr(candidate_service, "list_candidates", lambda **kw: fake)
    r = client.get("/api/candidates?q=c1")
    assert r.status_code == 200 and r.json()["total"] == 1


def test_candidate_not_found(monkeypatch):
    from app.utils.errors import NotFoundError

    def boom(cid):
        raise NotFoundError("missing")
    monkeypatch.setattr(candidate_service, "get_candidate", boom)
    assert client.get("/api/candidates/NOPE").status_code == 404


def test_question_endpoint(monkeypatch):
    monkeypatch.setattr(question_service, "list_questions", lambda *a, **k: {"items": [], "total": 0, "page": 1, "page_size": 20, "facets": {}})
    r = client.get("/api/questions?page=1&page_size=20")
    assert r.status_code == 200 and r.json()["total"] == 0