#!/usr/bin/env python3
"""Seed Neo4j + MongoDB from data/synthetic_interview_dataset.csv (idempotent).

Usage (inside the backend container):  python seed_database.py [path/to/csv]
"""

import json
import logging
import sys

logging.basicConfig(level=logging.INFO)


def main() -> int:
    from app.services import seed_service
    path = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        result = seed_service.seed_all(path)
    except Exception as exc:
        print(f"SEED FAILED: {exc}")
        return 1
    print(json.dumps(result, indent=2, default=str))
    if result["report"]["missing_columns"]:
        print("\nWARNING: dataset is missing expected columns:", result["report"]["missing_columns"])
    return 0


if __name__ == "__main__":
    sys.exit(main())