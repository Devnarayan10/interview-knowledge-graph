#!/usr/bin/env python3
"""
Database seeding entry point.
Full implementation in Phase 4.

Usage:
    python seed_database.py
    POST /api/seed (Phase 5)
"""

import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("Seed script placeholder — full seeding implemented in Phase 4")
    logger.info("Run: docker compose up --build (with AUTO_SEED=true)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
