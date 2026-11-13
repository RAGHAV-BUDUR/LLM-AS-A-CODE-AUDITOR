
import pandas as pd
from scipy.stats import pearsonr, spearmanr

POINTWISE_FILE = "data/self_enhancement_pointwise_results.csv"
QWEN_FILE = "data/correctness_results.csv"
LLAMA_FILE = "data/llama_correctness_results.csv"

OUTPUT_FILE = "data/self_enhancement_functional_comparison.csv"

# Load datasets
scores = pd.read_csv(POINTWISE_FILE)
qwen = pd.read_csv(QWEN_FILE)
llama = pd.read_csv(LLAMA_FILE)

# Keep only Qwen variation 1
qwen = qwen[qwen["submission_id"].str.endswith("_S1")].copy()

# Add generator identity
qwen["generator"] = "Qwen"
llama["generator"] = "Llama"

# Combine functional results
functional = pd.concat([qwen, llama], ignore_index=True)

# Map blind IDs to generator identities
scores["generator"] = scores["solution_id"].map({
    "QWEN_BLIND": "Qwen",
    "LLAMA_BLIND": "Llama"
})

# Merge using problem and generator
merged = pd.merge(
    scores,
    functional,
    on=["problem_id", "generator"],
    how="inner"
)

# Save detailed comparison
merged.to_csv(OUTPUT_FILE, index=False)

print("\nMATCHED RECORDS:", len(merged))

# Summary by generator
summary = merged.groupby("generator").agg(
    average_correctness_score=("correctness", "mean"),
    average_security_score=("security", "mean"),
    average_readability_score=("readability", "mean"),
    average_efficiency_score=("efficiency", "mean"),
    average_overall_score=("overall", "mean"),
    average_functional_accuracy=("accuracy_percent", "mean"),
    total_tests_passed=("passed", "sum"),
    total_tests=("total", "sum")
).round(3)

print("\nGENERATOR COMPARISON")
print(summary)

# Correlations between judge scores and functional accuracy
print("\nJUDGE SCORE VS FUNCTIONAL ACCURACY")

for dimension in [
    "correctness",
    "security",
    "readability",
    "efficiency",
    "overall"
]:
    pearson, _ = pearsonr(
        merged[dimension],
        merged["accuracy_percent"]
    )

    spearman, _ = spearmanr(
        merged[dimension],
        merged["accuracy_percent"]
    )

    print(
        f"{dimension}: "
        f"Pearson={pearson:.4f}, "
        f"Spearman={spearman:.4f}"
    )

print("\nDETAILED RESULTS")
print(
    merged[
        [
            "problem_id",
            "generator",
            "correctness",
            "overall",
            "passed",
            "total",
            "accuracy_percent"
        ]
    ].to_string(index=False)
)

print("\nSaved:", OUTPUT_FILE)
