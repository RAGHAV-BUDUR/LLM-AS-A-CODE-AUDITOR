
import pandas as pd
from scipy.stats import pearsonr, spearmanr

EVALUATION_FILE = "data/evaluation_results.csv"
FUNCTIONAL_FILE = "data/correctness_results.csv"

OUTPUT_FILE = "data/qwen_reliability_analysis.csv"

# Load datasets
evaluation = pd.read_csv(EVALUATION_FILE)
functional = pd.read_csv(FUNCTIONAL_FILE)

# Merge AI scores with functional test results
merged = pd.merge(
    evaluation,
    functional,
    on=["submission_id", "problem_id"],
    how="inner",
    suffixes=("_judge", "_test")
)

print("\nMATCHED SUBMISSIONS:", len(merged))

if len(merged) == 0:
    raise ValueError("No matching submissions found. Check submission IDs.")

# Convert score and accuracy columns to numeric
for column in ["correctness", "security", "readability", "efficiency"]:
    merged[column] = pd.to_numeric(merged[column], errors="coerce")

merged["accuracy_percent"] = pd.to_numeric(
    merged["accuracy_percent"], errors="coerce"
)

# Save merged dataset
merged.to_csv(OUTPUT_FILE, index=False)

# Summary
print("\nAVERAGE SCORES")

for column in [
    "correctness",
    "security",
    "readability",
    "efficiency"
]:
    print(f"{column}: {merged[column].mean():.3f}")

print(
    "Average overall judge score:",
    merged[["correctness", "security", "readability", "efficiency"]]
    .mean(axis=1).mean().round(3)
)

print(
    "Average functional accuracy:",
    round(merged["accuracy_percent"].mean(), 3)
)

print(
    "Pooled functional pass rate:",
    round(
        merged["passed"].sum() / merged["total"].sum() * 100,
        2
    )
)

# Correlation analysis
print("\nCORRELATION: JUDGE SCORES VS FUNCTIONAL ACCURACY")

for dimension in [
    "correctness",
    "security",
    "readability",
    "efficiency"
]:
    valid = merged[[dimension, "accuracy_percent"]].dropna()

    if valid[dimension].nunique() < 2 or valid["accuracy_percent"].nunique() < 2:
        print(dimension, ": Not enough score variation")
        continue

    pearson = pearsonr(
        valid[dimension],
        valid["accuracy_percent"]
    )

    spearman = spearmanr(
        valid[dimension],
        valid["accuracy_percent"]
    )

    print(
        f"{dimension}: "
        f"Pearson={pearson.statistic:.4f} "
        f"(p={pearson.pvalue:.4f}), "
        f"Spearman={spearman.statistic:.4f} "
        f"(p={spearman.pvalue:.4f})"
    )

# Correctness score distribution
print("\nCORRECTNESS SCORE DISTRIBUTION")
print(merged["correctness"].value_counts().sort_index())

# High AI scores despite functional failures
print("\nHIGH AI SCORES WITH FAILED TESTS")

failures = merged[
    (merged["accuracy_percent"] < 100) &
    (merged["correctness"] >= 8)
]

print(
    failures[
        [
            "submission_id",
            "correctness",
            "passed",
            "total",
            "accuracy_percent"
        ]
    ].to_string(index=False)
)

print("\nSaved results:", OUTPUT_FILE)
