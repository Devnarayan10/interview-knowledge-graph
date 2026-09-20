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
    "interviewkg"
)
DATA_DIR = "data/processed"
if not PASSWORD:
    raise ValueError(
        "NEO4J_PASSWORD is not set."
    )

print("=" * 70)
print("CONNECTING TO NEO4J")
print("=" * 70)

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

driver.verify_connectivity()

print("Neo4j connection successful.")

def run_query(query, parameters=None):

    with driver.session(
        database=DATABASE
    ) as session:

        result = session.run(
            query,
            parameters or {}
        )

        return result.consume()

def load_csv(filename):

    path = os.path.join(
        DATA_DIR,
        filename
    )

    print(
        f"Loading {filename}..."
    )

    return pd.read_csv(
        path
    )

candidates = load_csv(
    "candidates.csv"
)

query = """
UNWIND $rows AS row

MERGE (c:Candidate {
    candidate_id: row.candidate_id
})

SET
    c.source_id = row.candidate_source_id,
    c.domain = row.domain,
    c.education = row.education,
    c.skills_text = row.skills,
    c.skills_and_achievements =
        row.skills_and_achievements,
    c.experience = row.experience,
    c.job_type = row.job_type
"""

run_query(
    query,
    {
        "rows":
            candidates.fillna("")
            .to_dict("records")
    }
)

print(
    f"Created/updated {len(candidates)} candidates."
)


questions = load_csv(
    "questions.csv"
)

query = """
UNWIND $rows AS row

MERGE (q:Question {
    question_id: row.question_id
})

SET
    q.text = row.question,
    q.category = row.category,
    q.difficulty = row.difficulty,
    q.experience = row.experience,
    q.source_type = row.source_type,
    q.keywords = row.keywords
"""

run_query(
    query,
    {
        "rows":
            questions.fillna("")
            .to_dict("records")
    }
)

print(
    f"Created/updated {len(questions)} questions."
)

answers = load_csv(
    "answers.csv"
)

query = """
UNWIND $rows AS row

MERGE (a:Answer {
    answer_id: row.answer_id
})

SET
    a.transcript_text = row.transcript_text,
    a.source = row.source
"""

run_query(
    query,
    {
        "rows":
            answers.fillna("")
            .to_dict("records")
    }
)

print(
    f"Created/updated {len(answers)} answers."
)

roles = load_csv(
    "roles.csv"
)

query = """
UNWIND $rows AS row

MERGE (r:Role {
    role_id: row.role_id
})

SET
    r.title = row.title
"""

run_query(
    query,
    {
        "rows":
            roles.fillna("")
            .to_dict("records")
    }
)

print(
    f"Created/updated {len(roles)} roles."
)

skills = load_csv(
    "skills.csv"
)

query = """
UNWIND $rows AS row

MERGE (s:Skill {
    skill_id: row.skill_id
})

SET
    s.name = row.name,
    s.category = row.category
"""

run_query(
    query,
    {
        "rows":
            skills.fillna("")
            .to_dict("records")
    }
)

print(
    f"Created/updated {len(skills)} skills."
)

rounds = load_csv(
    "interview_rounds.csv"
)

query = """
UNWIND $rows AS row

MERGE (r:InterviewRound {
    round_id: row.round_id
})

SET
    r.round_number =
        toInteger(row.round_number),
    r.date = row.date
"""

run_query(
    query,
    {
        "rows":
            rounds.fillna("")
            .to_dict("records")
    }
)

print(
    f"Created/updated {len(rounds)} interview rounds."
)

candidate_skill = load_csv(
    "candidate_skill.csv"
)

query = """
UNWIND $rows AS row

MATCH (c:Candidate {
    candidate_id: row.candidate_id
})

MATCH (s:Skill {
    skill_id: row.skill_id
})

MERGE (c)-[:HAS_SKILL]->(s)
"""

run_query(
    query,
    {
        "rows":
            candidate_skill
            .fillna("")
            .to_dict("records")
    }
)

print(
    f"Created {len(candidate_skill)} candidate-skill relationships."
)

candidate_round = load_csv(
    "candidate_round.csv"
)

query = """
UNWIND $rows AS row

MATCH (c:Candidate {
    candidate_id: row.candidate_id
})

MATCH (r:InterviewRound {
    round_id: row.round_id
})

MERGE (c)-[:PARTICIPATES_IN]->(r)
"""

run_query(
    query,
    {
        "rows":
            candidate_round
            .fillna("")
            .to_dict("records")
    }
)

print(
    f"Created {len(candidate_round)} candidate-round relationships."
)

round_question = load_csv(
    "round_question.csv"
)

query = """
UNWIND $rows AS row

MATCH (r:InterviewRound {
    round_id: row.round_id
})

MATCH (q:Question {
    question_id: row.question_id
})

MERGE (r)-[:INCLUDES]->(q)
"""

run_query(
    query,
    {
        "rows":
            round_question
            .fillna("")
            .to_dict("records")
    }
)

print(
    f"Created {len(round_question)} round-question relationships."
)

answer_question = load_csv(
    "answer_question.csv"
)

query = """
UNWIND $rows AS row

MATCH (a:Answer {
    answer_id: row.answer_id
})

MATCH (q:Question {
    question_id: row.question_id
})

MERGE (a)-[:ANSWERS]->(q)
"""

run_query(
    query,
    {
        "rows":
            answer_question
            .fillna("")
            .to_dict("records")
    }
)

print(
    f"Created {len(answer_question)} answer-question relationships."
)

question_role = load_csv(
    "question_role.csv"
)

query = """
UNWIND $rows AS row

MATCH (q:Question {
    question_id: row.question_id
})

MATCH (r:Role {
    role_id: row.role_id
})

MERGE (q)-[:RELEVANT_TO]->(r)
"""

run_query(
    query,
    {
        "rows":
            question_role
            .fillna("")
            .to_dict("records")
    }
)

print(
    f"Created {len(question_role)} question-role relationships."
)

question_skill = load_csv(
    "question_skill.csv"
)

query = """
UNWIND $rows AS row

MATCH (q:Question {
    question_id: row.question_id
})

MATCH (s:Skill {
    skill_id: row.skill_id
})

MERGE (q)-[:TESTS_SKILL]->(s)
"""

run_query(
    query,
    {
        "rows":
            question_skill
            .fillna("")
            .to_dict("records")
    }
)

print(
    f"Created {len(question_skill)} question-skill relationships."
)

print("\n" + "=" * 70)
print("NEO4J IMPORT COMPLETE")
print("=" * 70)

driver.close()