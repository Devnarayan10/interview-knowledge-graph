import os
import pandas as pd

from neo4j import GraphDatabase
from dotenv import load_dotenv


load_dotenv()


URI = os.getenv(
    "NEO4J_URI",
    "bolt://localhost:7687"
)

USERNAME = os.getenv(
    "NEO4J_USERNAME",
    "neo4j"
)

PASSWORD = os.getenv(
    "NEO4J_PASSWORD"
)

DATABASE = os.getenv(
    "NEO4J_DATABASE",
    "neo4j"
)

DATA_DIR = "data/processed/applications"


driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

driver.verify_connectivity()


def load_csv(filename):

    path = os.path.join(
        DATA_DIR,
        filename
    )

    return (
        pd.read_csv(path)
        .fillna("")
        .to_dict("records")
    )


def run_query(query, rows):

    with driver.session(
        database=DATABASE
    ) as session:

        session.run(
            query,
            rows=rows
        )


# ============================================================
# ROLE
# ============================================================

rows = load_csv("roles.csv")

run_query(
    """
    UNWIND $rows AS row

    MERGE (r:Role {
        role_id: row.role_id
    })

    SET
        r.title = row.title
    """,
    rows
)


# ============================================================
# APPLICATION
# ============================================================

rows = load_csv("applications.csv")

run_query(
    """
    UNWIND $rows AS row

    MATCH (c:Candidate {
        candidate_id: row.candidate_id
    })

    MATCH (r:Role {
        role_id: row.role_id
    })

    MERGE (a:Application {
        application_id:
            row.application_id
    })

    SET
        a.status = row.status,
        a.source = row.source

    MERGE
        (c)-[:HAS_APPLICATION]->(a)

    MERGE
        (a)-[:APPLIED_FOR]->(r)
    """,
    rows
)


# ============================================================
# APPLICATION → INTERVIEW ROUND
# ============================================================

rows = load_csv(
    "application_rounds.csv"
)

run_query(
    """
    UNWIND $rows AS row

    MATCH (a:Application {
        application_id:
            row.application_id
    })

    MATCH (r:InterviewRound {
        round_id:
            row.round_id
    })

    MERGE
        (a)-[:HAS_ROUND]->(r)
    """,
    rows
)


print("=" * 70)
print("APPLICATION LAYER LOADED")
print("=" * 70)

driver.close()