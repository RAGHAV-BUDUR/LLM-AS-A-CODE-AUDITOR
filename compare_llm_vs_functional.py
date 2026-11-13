
import pandas as pd

# Input files
LLM_FILE = "data/evaluation_results.csv"
FUNCTIONAL_FILE = "data/correctness_results.csv"

# Output file
OUTPUT_FILE = "data/llm_functional_comparison.csv"


# Load both datasets
llm_df = pd.read_csv(LLM_FILE)
functional_df = pd.read_csv(FUNCTIONAL_FILE)


# Select required columns from LLM evaluation
llm_selected = llm_df[
    [
        "submission_id",
        "problem_id",
        "correctness",
        "security",
        "readability",
        "efficiency",
        "overall_score"
    ]
].copy()


# Select required columns from functional testing
functional_selected = functional_df[
    [
        "submission_id",
        "passed",
        "failed",
        "total",
        "accuracy_percent",
        "status"
    ]
].copy()


# Rename status columns to avoid confusion
functional_selected = functional_selected.rename(
    columns={
        "status": "functional_status"
    }
)


# Merge using submission_id
comparison = pd.merge(
    llm_selected,
    functional_selected,
    on="submission_id",
    how="inner",
    validate="one_to_one"
)


# Convert score columns to numeric
score_columns = [
    "correctness",
    "security",
    "readability",
    "efficiency",
    "overall_score",
    "accuracy_percent"
]

for column in score_columns:
    comparison[column] = pd.to_numeric(
        comparison[column],
        errors="coerce"
    )


# Convert LLM correctness score from 1-10 to percentage scale
comparison["llm_correctness_percent"] = (
    comparison["correctness"] * 10
)


# Calculate difference between LLM and functional accuracy
comparison["score_difference"] = (
    comparison["llm_correctness_percent"]
    - comparison["accuracy_percent"]
)


# Identify large disagreements (at least 30 percentage points)
comparison["disagreement"] = (
    comparison["score_difference"].abs() >= 30
)


# Save detailed comparison
comparison.to_csv(
    OUTPUT_FILE,
    index=False
)


# Display summary
print("\n========== LLM VS FUNCTIONAL COMPARISON ==========\n")

print("Matched submissions:", len(comparison))

print(
    "LLM average correctness score:",
    round(comparison["correctness"].mean(), 2)
)

print(
    "Functional average accuracy:",
    round(comparison["accuracy_percent"].mean(), 2),
    "%"
)

print(
    "Average absolute score difference:",
    round(comparison["score_difference"].abs().mean(), 2),
    "percentage points"
)

print(
    "Submissions with large disagreement:",
    comparison["disagreement"].sum()
)


# Calculate correlation
print("\n========== CORRELATION ANALYSIS ==========\n")

pearson = comparison[
    ["correctness", "accuracy_percent"]
].corr(method="pearson").iloc[0, 1]

spearman = comparison[
    ["correctness", "accuracy_percent"]
].corr(method="spearman").iloc[0, 1]

print("Pearson correlation:", round(pearson, 4))
print("Spearman correlation:", round(spearman, 4))


# Display submissions with largest disagreement
print("\n========== LARGEST DISAGREEMENTS ==========\n")

print(
    comparison[
        [
            "submission_id",
            "correctness",
            "accuracy_percent",
            "score_difference",
            "functional_status"
        ]
    ]
    .assign(
        absolute_difference=lambda x:
        x["score_difference"].abs()
    )
    .sort_values(
        "absolute_difference",
        ascending=False
    )
    .head(10)
    .to_string(index=False)
)


print("\nComparison saved to:", OUTPUT_FILE)
