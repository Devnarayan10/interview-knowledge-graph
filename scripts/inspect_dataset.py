import pandas as pd
import os


FILE = "data/raw/synthetic_interview_dataset.csv"


if not os.path.exists(FILE):
    raise FileNotFoundError(
        f"Dataset not found:\n{FILE}"
    )


df = pd.read_csv(FILE)


print("\n" + "=" * 70)
print("DATASET INSPECTION")
print("=" * 70)


print("\nNumber of rows:")
print(len(df))


print("\nNumber of columns:")
print(len(df.columns))


print("\nColumn names:")
for i, column in enumerate(df.columns, start=1):
    print(f"{i}. {column}")


print("\n" + "=" * 70)
print("DATA TYPES")
print("=" * 70)

print(df.dtypes)


print("\n" + "=" * 70)
print("MISSING VALUES")
print("=" * 70)

missing = df.isnull().sum()

print(
    missing[missing > 0]
    .sort_values(ascending=False)
)


print("\n" + "=" * 70)
print("FIRST 5 ROWS")
print("=" * 70)

print(
    df.head().to_string()
)


print("\n" + "=" * 70)
print("UNIQUE VALUES")
print("=" * 70)


for column in df.columns:

    unique_count = df[column].nunique()

    print(
        f"{column}: {unique_count} unique values"
    )


print("\n" + "=" * 70)
print("DATASET INSPECTION COMPLETE")
print("=" * 70)