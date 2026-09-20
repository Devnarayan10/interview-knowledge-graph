import pandas as pd
import os
import ast
import re

INPUT_FILE = "data/raw/synthetic_interview_dataset.csv"
OUTPUT_DIR = "data/processed"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def normalize_text(value):
    value = clean_text(value)

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value
    )

    return value.strip("_")


def parse_skills(value):

    value = clean_text(value)

    if not value:
        return []

    try:

        parsed = ast.literal_eval(value)

        if isinstance(parsed, list):

            return [
                clean_text(x)
                for x in parsed
                if clean_text(x)
            ]

    except (ValueError, SyntaxError):
        pass

    if "," in value:

        return [
            x.strip()
            for x in value.split(",")
            if x.strip()
        ]

    if ";" in value:

        return [
            x.strip()
            for x in value.split(";")
            if x.strip()
        ]

    return [value]


def parse_keywords(value):

    value = clean_text(value)

    if not value:
        return []

    value = value.replace("[", "")
    value = value.replace("]", "")

    value = value.replace("'", "")
    value = value.replace('"', "")

    return [
        x.strip()
        for x in value.split()
        if x.strip()
    ]

print("=" * 70)
print("LOADING DATASET")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

for column in df.columns:

    if df[column].dtype == "object":

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

print("\nCreating candidates.csv...")

candidate_columns = [
    "candidate_id",
    "candidate_source_id",
    "candidate_domain",
    "education",
    "skills",
    "skills_and_achievements",
    "candidate_experience",
    "job_type"
]

candidates = (
    df[candidate_columns]
    .drop_duplicates(
        subset=["candidate_id"]
    )
    .copy()
)

candidates.rename(
    columns={
        "candidate_domain": "domain",
        "candidate_experience": "experience"
    },
    inplace=True
)

candidates.to_csv(
    f"{OUTPUT_DIR}/candidates.csv",
    index=False
)

print(
    f"Candidates: {len(candidates)}"
)

print("\nCreating questions.csv...")

question_columns = [
    "question_id",
    "question",
    "question_category",
    "target_role",
    "source_role",
    "difficulty",
    "question_experience",
    "source_type",
    "keywords"
]

questions = (
    df[question_columns]
    .drop_duplicates(
        subset=["question_id"]
    )
    .copy()
)

questions.rename(
    columns={
        "question_category": "category",
        "question_experience": "experience"
    },
    inplace=True
)

questions.to_csv(
    f"{OUTPUT_DIR}/questions.csv",
    index=False
)

print(
    f"Questions: {len(questions)}"
)

print("\nCreating answers.csv...")

answer_columns = [
    "answer_id",
    "answer",
    "answer_source",
    "question_id",
    "candidate_id"
]

answers = (
    df[answer_columns]
    .drop_duplicates(
        subset=["answer_id"]
    )
    .copy()
)

answers.rename(
    columns={
        "answer": "transcript_text",
        "answer_source": "source"
    },
    inplace=True
)

answers.to_csv(
    f"{OUTPUT_DIR}/answers.csv",
    index=False
)

print(
    f"Answers: {len(answers)}"
)

print("\nCreating roles.csv...")

role_values = set()

for column in [
    "target_role",
    "source_role"
]:

    for value in df[column]:

        value = clean_text(value)

        if value:

            role_values.add(value)


roles = []

for index, role in enumerate(
    sorted(role_values),
    start=1
):

    roles.append({

        "role_id": f"R{index:03d}",

        "title": role

    })


roles = pd.DataFrame(roles)

roles.to_csv(
    f"{OUTPUT_DIR}/roles.csv",
    index=False
)

print(
    f"Roles: {len(roles)}"
)

print("\nCreating skills.csv...")

skill_dictionary = {}

for value in df["skills"]:

    for skill in parse_skills(value):

        normalized = normalize_text(skill)

        if normalized:

            if normalized not in skill_dictionary:

                skill_dictionary[
                    normalized
                ] = skill

for category in df["question_category"]:

    category = clean_text(category)

    if category:

        normalized = normalize_text(category)

        if normalized not in skill_dictionary:

            skill_dictionary[
                normalized
            ] = category


skills = []

for index, skill in enumerate(
    sorted(skill_dictionary.values()),
    start=1
):

    skills.append({

        "skill_id": f"S{index:03d}",

        "name": skill,

        "category": "General"

    })


skills = pd.DataFrame(skills)

skills.to_csv(
    f"{OUTPUT_DIR}/skills.csv",
    index=False
)

print(
    f"Skills: {len(skills)}"
)

print("\nCreating interview_rounds.csv...")

round_columns = [
    "round_id",
    "candidate_id"
]

rounds = (
    df[round_columns]
    .drop_duplicates(
        subset=["round_id"]
    )
    .copy()
)

rounds["round_number"] = (
    rounds
    .groupby("candidate_id")
    .cumcount()
    + 1
)

rounds["date"] = ""

rounds.to_csv(
    f"{OUTPUT_DIR}/interview_rounds.csv",
    index=False
)

print(
    f"Interview rounds: {len(rounds)}"
)

print("\nCreating candidate_skill.csv...")

candidate_skill_rows = []

for _, row in (
    df[
        ["candidate_id", "skills"]
    ]
    .drop_duplicates()
    .iterrows()
):

    candidate_id = row["candidate_id"]

    candidate_skills = parse_skills(
        row["skills"]
    )

    for skill in candidate_skills:

        normalized = normalize_text(skill)

        matching = skills[
            skills["name"]
            .apply(normalize_text)
            == normalized
        ]

        if not matching.empty:

            candidate_skill_rows.append({

                "candidate_id":
                    candidate_id,

                "skill_id":
                    matching.iloc[0]["skill_id"]

            })


candidate_skill = (
    pd.DataFrame(
        candidate_skill_rows
    )
    .drop_duplicates()
)

candidate_skill.to_csv(
    f"{OUTPUT_DIR}/candidate_skill.csv",
    index=False
)

print(
    f"Candidate-Skill relationships: "
    f"{len(candidate_skill)}"
)

print("\nCreating candidate_round.csv...")

candidate_round = (
    df[
        ["candidate_id", "round_id"]
    ]
    .drop_duplicates()
)

candidate_round.to_csv(
    f"{OUTPUT_DIR}/candidate_round.csv",
    index=False
)

print("\nCreating round_question.csv...")

round_question = (
    df[
        ["round_id", "question_id"]
    ]
    .drop_duplicates()
)

round_question.to_csv(
    f"{OUTPUT_DIR}/round_question.csv",
    index=False
)

print("\nCreating answer_question.csv...")

answer_question = (
    df[
        ["answer_id", "question_id"]
    ]
    .drop_duplicates()
)

answer_question.to_csv(
    f"{OUTPUT_DIR}/answer_question.csv",
    index=False
)

print("\nCreating question_role.csv...")

question_role = (
    df[
        ["question_id", "target_role"]
    ]
    .drop_duplicates()
)

question_role = question_role[
    question_role["target_role"] != ""
]

question_role = question_role.merge(
    roles,
    left_on="target_role",
    right_on="title",
    how="left"
)

question_role = question_role[
    ["question_id", "role_id"]
]

question_role.to_csv(
    f"{OUTPUT_DIR}/question_role.csv",
    index=False
)

print("\nCreating question_skill.csv...")

question_skill_rows = []

for _, row in (
    df[
        ["question_id", "question_category"]
    ]
    .drop_duplicates()
    .iterrows()
):

    question_id = row["question_id"]

    category = clean_text(
        row["question_category"]
    )

    normalized = normalize_text(
        category
    )

    matching = skills[
        skills["name"]
        .apply(normalize_text)
        == normalized
    ]

    if not matching.empty:

        question_skill_rows.append({

            "question_id":
                question_id,

            "skill_id":
                matching.iloc[0]["skill_id"]

        })


question_skill = (
    pd.DataFrame(
        question_skill_rows
    )
    .drop_duplicates()
)

question_skill.to_csv(
    f"{OUTPUT_DIR}/question_skill.csv",
    index=False
)

print(
    f"Question-Skill relationships: "
    f"{len(question_skill)}"
)

print("\n" + "=" * 70)
print("PREPROCESSING COMPLETE")
print("=" * 70)

print(
    f"Candidates       : {len(candidates)}"
)

print(
    f"Questions        : {len(questions)}"
)

print(
    f"Answers          : {len(answers)}"
)

print(
    f"Roles            : {len(roles)}"
)

print(
    f"Skills           : {len(skills)}"
)

print(
    f"Interview Rounds : {len(rounds)}"
)

print(
    f"Candidate-Skill  : {len(candidate_skill)}"
)

print(
    f"Question-Skill   : {len(question_skill)}"
)

print("\nOutput directory:")
print(OUTPUT_DIR)