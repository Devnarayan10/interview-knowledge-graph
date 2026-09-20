import pandas as pd
import re
import os
import hashlib


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/raw/synthetic_interview_dataset.csv"
OUTPUT_FILE = "data/processed/interview_performance_dataset.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("GENERATING SYNTHETIC INTERVIEW PERFORMANCE DATA")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)


# ============================================================
# CLEAN ANSWER TEXT
# ============================================================

def clean_answer(answer, question):

    if pd.isna(answer):
        return ""

    answer = str(answer).strip()

    if pd.isna(question):
        return answer

    question = str(question).strip()

    # Remove exact question if appended to answer
    if answer.endswith(question):
        answer = answer[:-len(question)].strip()

    # Sometimes punctuation/spacing differs slightly
    escaped_question = re.escape(question)

    answer = re.sub(
        r"\s*" + escaped_question + r"\s*$",
        "",
        answer,
        flags=re.IGNORECASE
    ).strip()

    return answer


df["clean_answer"] = df.apply(
    lambda row: clean_answer(
        row["answer"],
        row["question"]
    ),
    axis=1
)


# ============================================================
# DIFFICULTY NORMALIZATION
# ============================================================

def difficulty_score(value):

    value = str(value).lower()

    if "easy" in value:
        return 1

    if "medium" in value:
        return 2

    if "hard" in value or "difficult" in value:
        return 3

    return 2


# ============================================================
# SYNTHETIC SCORE GENERATION
# ============================================================

def generate_score(row):

    answer = row["clean_answer"]

    if not answer:
        return 30

    words = answer.split()
    word_count = len(words)

    score = 50

    # --------------------------------------------------------
    # Answer length
    # --------------------------------------------------------

    if word_count >= 80:
        score += 12

    elif word_count >= 50:
        score += 8

    elif word_count >= 30:
        score += 5

    elif word_count < 15:
        score -= 10


    # --------------------------------------------------------
    # Structured response indicators
    # --------------------------------------------------------

    answer_lower = answer.lower()

    strong_indicators = [
        "for example",
        "because",
        "therefore",
        "result",
        "achieved",
        "improved",
        "increased",
        "reduced",
        "solved",
        "implemented",
        "developed",
        "designed",
        "analyzed",
        "learned"
    ]

    indicator_count = sum(
        1
        for word in strong_indicators
        if word in answer_lower
    )

    score += min(
        indicator_count * 3,
        15
    )


    # --------------------------------------------------------
    # Specificity
    # --------------------------------------------------------

    specificity_terms = [
        "project",
        "team",
        "system",
        "application",
        "model",
        "database",
        "python",
        "machine learning",
        "data",
        "api",
        "cloud",
        "aws",
        "sql",
        "algorithm"
    ]

    specificity_count = sum(
        1
        for term in specificity_terms
        if term in answer_lower
    )

    score += min(
        specificity_count * 2,
        10
    )


    # --------------------------------------------------------
    # Vague response penalty
    # --------------------------------------------------------

    vague_terms = [
        "i don't know",
        "not sure",
        "maybe",
        "i guess",
        "probably"
    ]

    vague_count = sum(
        1
        for term in vague_terms
        if term in answer_lower
    )

    score -= vague_count * 5


    # --------------------------------------------------------
    # Difficulty adjustment
    # --------------------------------------------------------

    difficulty = difficulty_score(
        row["difficulty"]
    )

    if difficulty == 3:
        score -= 2

    elif difficulty == 1:
        score += 2


    # --------------------------------------------------------
    # Deterministic variation
    #
    # Prevents every similar answer from receiving
    # exactly the same score.
    # --------------------------------------------------------

    answer_id = str(
        row["answer_id"]
    )

    hash_value = int(
        hashlib.md5(
            answer_id.encode()
        ).hexdigest()[:8],
        16
    )

    variation = (
        hash_value % 7
    ) - 3

    score += variation


    # Keep score between 35 and 95

    score = max(
        35,
        min(
            95,
            score
        )
    )

    return int(score)


df["score"] = df.apply(
    generate_score,
    axis=1
)


# ============================================================
# SYNTHETIC EMOTION
# ============================================================

def generate_emotion(score):

    if score >= 85:
        return "Confident"

    if score >= 70:
        return "Positive"

    if score >= 55:
        return "Neutral"

    if score >= 45:
        return "Uncertain"

    return "Nervous"


df["emotion"] = df["score"].apply(
    generate_emotion
)


# ============================================================
# SYNTHETIC RECRUITER FEEDBACK
# ============================================================

def generate_feedback(row):

    score = row["score"]

    answer = row["clean_answer"]

    word_count = len(
        answer.split()
    )

    answer_lower = answer.lower()

    has_example = (
        "for example" in answer_lower
        or "one time" in answer_lower
        or "when i" in answer_lower
    )

    has_result = any(
        term in answer_lower
        for term in [
            "result",
            "achieved",
            "improved",
            "increased",
            "reduced"
        ]
    )

    feedback_parts = []


    if score >= 80:

        feedback_parts.append(
            "Strong response with good relevance and clarity."
        )

    elif score >= 65:

        feedback_parts.append(
            "Reasonable response that addresses the question."
        )

    else:

        feedback_parts.append(
            "Response needs more detail and stronger evidence."
        )


    if word_count < 30:

        feedback_parts.append(
            "The answer could provide more specific details."
        )

    elif word_count >= 70:

        feedback_parts.append(
            "The response provides useful supporting detail."
        )


    if has_example:

        feedback_parts.append(
            "Provides an example or practical context."
        )

    else:

        feedback_parts.append(
            "Adding a concrete example would improve the response."
        )


    if has_result:

        feedback_parts.append(
            "Mentions an outcome or result."
        )

    else:

        feedback_parts.append(
            "A clearer outcome or measurable result would strengthen it."
        )


    return " ".join(
        feedback_parts
    )


df["feedback"] = df.apply(
    generate_feedback,
    axis=1
)


# ============================================================
# SAVE PROCESSED DATASET
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)


output_columns = [
    "candidate_id",
    "candidate_source_id",
    "round_id",
    "question_id",
    "question",
    "question_category",
    "target_role",
    "source_role",
    "difficulty",
    "question_experience",
    "answer_id",
    "answer",
    "clean_answer",
    "answer_source",
    "score",
    "emotion",
    "feedback",
    "keywords",
    "synthetic_record"
]


df[
    output_columns
].to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print(
    f"\nInput records: {len(df)}"
)

print(
    f"Output records: {len(df)}"
)

print(
    f"\nAverage score: {df['score'].mean():.2f}"
)

print(
    "\nScore distribution:"
)

print(
    df["score"]
    .describe()
    .to_string()
)

print(
    "\nEmotion distribution:"
)

print(
    df["emotion"]
    .value_counts()
    .to_string()
)

print(
    f"\nSaved to:\n{OUTPUT_FILE}"
)

print("\n" + "=" * 70)
print("PERFORMANCE DATA GENERATION COMPLETE")
print("=" * 70)