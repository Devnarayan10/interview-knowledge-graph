import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

INPUT_FILE = "data/processed/interview_performance_dataset.csv"

URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
DATABASE = "interviewkg"

PASSWORD = os.getenv("NEO4J_PASSWORD")


if not PASSWORD:
    raise ValueError(
        "NEO4J_PASSWORD was not found in the .env file."
    )


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("POPULATING ANSWER LAYER")
print("=" * 70)

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Dataset not found:\n{INPUT_FILE}"
    )


df = pd.read_csv(INPUT_FILE)

print(
    f"\nRecords loaded from CSV: {len(df)}"
)


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "answer_id",
    "answer",
    "clean_answer",
    "score",
    "emotion",
    "feedback",
    "candidate_id",
    "question_id",
    "round_id"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        "Missing required columns: "
        + ", ".join(missing_columns)
    )


# ============================================================
# NEO4J CONNECTION
# ============================================================

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

try:

    driver.verify_connectivity()

    print(
        f"Neo4j connection successful."
    )

    print(
        f"Using database: {DATABASE}"
    )


    # ========================================================
    # CYPHER QUERY
    # ========================================================

    QUERY = """
    MATCH (a:Answer)
    WHERE trim(toString(a.answer_id)) = trim(toString($answer_id))

    SET
        a.answer = $answer,
        a.clean_answer = $clean_answer,
        a.score = $score,
        a.feedback = $feedback,
        a.emotion = $emotion,
        a.candidate_id = $candidate_id,
        a.question_id = $question_id,
        a.round_id = $round_id

    WITH a

    OPTIONAL MATCH (c:Candidate {
        candidate_id: $candidate_id
    })

    OPTIONAL MATCH (q:Question {
        question_id: $question_id
    })

    OPTIONAL MATCH (r:InterviewRound {
        round_id: $round_id
    })

    FOREACH (_ IN CASE
        WHEN c IS NOT NULL THEN [1]
        ELSE []
    END |
        MERGE (c)-[:GAVE_ANSWER]->(a)
    )

    FOREACH (_ IN CASE
        WHEN q IS NOT NULL THEN [1]
        ELSE []
    END |
        MERGE (q)-[:HAS_ANSWER]->(a)
    )

    FOREACH (_ IN CASE
        WHEN r IS NOT NULL THEN [1]
        ELSE []
    END |
        MERGE (r)-[:HAS_ANSWER]->(a)
    )

    RETURN a.answer_id AS answer_id
    """


    # ========================================================
    # IMPORT
    # ========================================================

    updated = 0
    missing = []


    with driver.session(
        database=DATABASE
    ) as session:

        for _, row in df.iterrows():

            # ------------------------------------------------
            # Convert CSV values safely
            # ------------------------------------------------

            params = {

                "answer_id": str(
                    row["answer_id"]
                ).strip(),

                "answer": (
                    None
                    if pd.isna(row["answer"])
                    else str(row["answer"]).strip()
                ),

                "clean_answer": (
                    None
                    if pd.isna(row["clean_answer"])
                    else str(
                        row["clean_answer"]
                    ).strip()
                ),

                "score": (
                    None
                    if pd.isna(row["score"])
                    else float(row["score"])
                ),

                "emotion": (
                    None
                    if pd.isna(row["emotion"])
                    else str(
                        row["emotion"]
                    ).strip()
                ),

                "feedback": (
                    None
                    if pd.isna(row["feedback"])
                    else str(
                        row["feedback"]
                    ).strip()
                ),

                "candidate_id": (
                    None
                    if pd.isna(row["candidate_id"])
                    else str(
                        row["candidate_id"]
                    ).strip()
                ),

                "question_id": (
                    None
                    if pd.isna(row["question_id"])
                    else str(
                        row["question_id"]
                    ).strip()
                ),

                "round_id": (
                    None
                    if pd.isna(row["round_id"])
                    else str(
                        row["round_id"]
                    ).strip()
                )
            }


            # ------------------------------------------------
            # Execute Cypher
            # ------------------------------------------------

            result = session.run(
                QUERY,
                params
            ).single()


            # ------------------------------------------------
            # Track result
            # ------------------------------------------------

            if result is None:

                missing.append(
                    params["answer_id"]
                )

            else:

                updated += 1


    # ========================================================
    # FINAL REPORT
    # ========================================================

    print("\n" + "=" * 70)
    print("ANSWER IMPORT COMPLETE")
    print("=" * 70)

    print(
        f"Records processed : {len(df)}"
    )

    print(
        f"Answers updated   : {updated}"
    )

    print(
        f"Answers missing   : {len(missing)}"
    )


    if missing:

        print(
            "\nMissing Answer IDs:"
        )

        print(
            ", ".join(missing)
        )

    else:

        print(
            "\nAll 120 Answer nodes were successfully updated."
        )

    print("=" * 70)


finally:

    driver.close()