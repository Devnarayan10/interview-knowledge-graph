import pandas as pd
import os


INPUT_FILE = "data/raw/synthetic_interview_dataset.csv"
OUTPUT_DIR = "data/processed/applications"


os.makedirs(OUTPUT_DIR, exist_ok=True)


print("=" * 70)
print("GENERATING RECRUITER APPLICATION DATA")
print("=" * 70)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "candidate_id",
    "target_role",
    "round_id"
]

for column in required_columns:

    if column not in df.columns:

        raise ValueError(
            f"Required column missing: {column}"
        )


# ============================================================
# ROLE CATALOGUE
# ============================================================

roles = [

    ("R001", "Accountant"),

    ("R002", "Banking / Financial Analyst"),

    ("R003", "Data Scientist"),

    ("R004", "DevOps Engineer"),

    ("R005", "Fashion / Apparel Professional"),

    ("R006", "Financial Analyst"),

    ("R007", "HR Specialist"),

    ("R008", "Marketing Associate"),

    ("R009", "QA Analyst"),

    ("R010", "Research Assistant"),

    ("R011", "Software Engineer"),

    ("R012", "Teacher / Trainer")

]


roles_df = pd.DataFrame(
    roles,
    columns=[
        "role_id",
        "title"
    ]
)


roles_df.to_csv(
    f"{OUTPUT_DIR}/roles.csv",
    index=False
)


# ============================================================
# ROLE NAME → ROLE ID
# ============================================================

role_mapping = dict(
    zip(
        roles_df["title"],
        roles_df["role_id"]
    )
)


# ============================================================
# CHECK TARGET ROLES
# ============================================================

target_roles = sorted(
    df["target_role"]
    .dropna()
    .astype(str)
    .unique()
)


print("\nTarget roles found in dataset:")

for role in target_roles:
    print(f"  {role}")


# Check for unknown roles

unknown_roles = [
    role
    for role in target_roles
    if role not in role_mapping
]


if unknown_roles:

    raise ValueError(
        "These target roles are not in the role catalogue:\n"
        + "\n".join(unknown_roles)
    )


# ============================================================
# CANDIDATE → TARGET ROLE
# ============================================================

candidate_roles = (

    df[
        [
            "candidate_id",
            "target_role"
        ]
    ]

    .dropna()

    .drop_duplicates()
)


# ============================================================
# VERIFY EACH CANDIDATE HAS ONE TARGET ROLE
# ============================================================

role_counts = (

    candidate_roles

    .groupby("candidate_id")["target_role"]

    .nunique()
)


multiple_roles = role_counts[
    role_counts > 1
]


if not multiple_roles.empty:

    print(
        "\nWARNING:"
        "\nSome candidates have multiple target roles:"
    )

    print(
        multiple_roles
    )

    raise ValueError(
        "Candidate-to-role mapping is ambiguous."
    )


# ============================================================
# APPLICATIONS
# ============================================================

applications = []


for index, row in candidate_roles.iterrows():

    candidate_id = str(
        row["candidate_id"]
    )

    target_role = str(
        row["target_role"]
    )

    role_id = role_mapping[
        target_role
    ]

    applications.append({

        "application_id":
            f"APP{len(applications) + 1:04d}",

        "candidate_id":
            candidate_id,

        "role_id":
            role_id,

        "role_title":
            target_role,

        "status":
            "Interview",

        "source":
            "Synthetic Interview Dataset"

    })


applications_df = pd.DataFrame(
    applications
)


applications_df.to_csv(
    f"{OUTPUT_DIR}/applications.csv",
    index=False
)


# ============================================================
# APPLICATION → INTERVIEW ROUND
# ============================================================

round_data = (

    df[
        [
            "candidate_id",
            "round_id"
        ]
    ]

    .dropna()

    .drop_duplicates()
)


application_lookup = dict(
    zip(
        applications_df["candidate_id"],
        applications_df["application_id"]
    )
)


application_rounds = []


for _, row in round_data.iterrows():

    candidate_id = str(
        row["candidate_id"]
    )

    round_id = str(
        row["round_id"]
    )

    application_id = application_lookup.get(
        candidate_id
    )


    if application_id is None:

        continue


    application_rounds.append({

        "application_id":
            application_id,

        "round_id":
            round_id

    })


application_rounds_df = pd.DataFrame(
    application_rounds
)


application_rounds_df.to_csv(
    f"{OUTPUT_DIR}/application_rounds.csv",
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)

print("GENERATED FILES")

print("=" * 70)

print(
    f"Roles: {len(roles_df)}"
)

print(
    f"Applications: {len(applications_df)}"
)

print(
    f"Application-Round relationships: "
    f"{len(application_rounds_df)}"
)


print("\nApplications by role:")

print(
    applications_df[
        "role_title"
    ]
    .value_counts()
    .to_string()
)


print("\n" + "=" * 70)

print(
    "APPLICATION DATA GENERATION COMPLETE"
)

print("=" * 70)