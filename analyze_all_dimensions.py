
import pandas as pd

df = pd.read_csv("data/evaluation_results.csv")

dimensions = [
    "correctness",
    "security",
    "readability",
    "efficiency"
]

print("\n========== ALL DIMENSION DISTRIBUTIONS ==========\n")

for dimension in dimensions:

    print(f"\n--- {dimension.upper()} ---")

    print("Score distribution:")
    print(df[dimension].value_counts().sort_index())

    print("\nStatistics:")
    print(df[dimension].describe())

    print("Unique scores:", df[dimension].nunique())


print("\n========== DIMENSION SUMMARY ==========\n")

summary = df[dimensions].agg(
    ["mean", "std", "min", "max", "nunique"]
).T

print(summary.to_string())
