#!/usr/bin/env python3
"""End-to-end validation against a running backend. Usage: python validate_system.py [base_url]"""

import json
import sys
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")


def get(path: str):
    with urllib.request.urlopen(BASE + path, timeout=60) as r:
        return json.loads(r.read())


def main() -> int:
    failures = 0

    def check(name, fn):
        nonlocal failures
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, str(exc)[:150]
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")

    check("health", lambda: ((h := get("/health"))["neo4j"] and h["mongodb"], str(get("/health"))))
    summary = get("/api/dashboard/summary")
    c = summary["counts"]
    check("dashboard counts > 0", lambda: (all(c[k] > 0 for k in ("candidates", "questions", "answers", "skills", "roles", "interviews", "emotion_logs")), str(c)))
    cands = get("/api/candidates")["items"]
    cid = cands[0]["candidate_id"]
    qs = get("/api/questions?page_size=5")
    for name, path in [
        ("candidate profile", f"/api/candidates/{cid}"), ("evaluation", f"/api/evaluation/{cid}"),
        ("recommendations", f"/api/recommendations/candidate/{cid}"), ("similar", f"/api/recommendations/similar/{cid}"),
        ("question detail", f"/api/questions/{qs['items'][0]['question_id']}"),
        ("interviews", "/api/interviews"), ("graph", "/api/graph"), ("graph candidate", f"/api/graph/candidate/{cid}"),
        ("analytics overview", "/api/analytics/overview"), ("analytics skills", "/api/analytics/skills"),
        ("analytics roles", "/api/analytics/roles"), ("analytics difficulties", "/api/analytics/difficulties"),
        ("analytics gds", "/api/analytics/gds"), ("analytics mongo", "/api/analytics/mongo"),
        ("db neo4j", "/api/database/neo4j"), ("db mongodb", "/api/database/mongodb"),
        ("db indexes", "/api/database/indexes"), ("skills", "/api/skills"), ("roles", "/api/roles"),
    ]:
        check(name, lambda p=path: (bool(get(p)), ""))
    g = get("/api/graph")
    check("graph has nodes and links", lambda: (g["stats"]["nodes"] > 0 and g["stats"]["links"] > 0, str(g["stats"])))
    print(f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())