
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --------------------------------------------------
# 1. SETUP
# --------------------------------------------------

OUTPUT_DIR = "data/final_graphs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid")

def save_plot(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


# --------------------------------------------------
# 2. QWEN JUDGE RELIABILITY
# --------------------------------------------------

file = "data/qwen_reliability_analysis.csv"

if os.path.exists(file):
    df = pd.read_csv(file)

    # Correctness score distribution
    if "correctness" in df.columns:
        plt.figure(figsize=(8, 5))
        sns.countplot(data=df, x="correctness")
        plt.title("Distribution of LLM Correctness Scores")
        plt.xlabel("LLM Correctness Score")
        plt.ylabel("Number of Submissions")
        save_plot("01_correctness_score_distribution.png")

    # LLM correctness score vs functional accuracy
   
    # LLM correctness score vs functional accuracy
    if {"correctness", "accuracy_percent"}.issubset(df.columns):
        plt.figure(figsize=(9, 6))

        sns.stripplot(
            data=df,
            x="correctness",
            y="accuracy_percent",
            jitter=0.18,
            alpha=0.7,
            size=7
        )

        plt.title(
            "LLM Correctness Score vs Functional Accuracy",
            fontsize=13
        )
        plt.xlabel("LLM Correctness Score")
        plt.ylabel("Functional Accuracy (%)")
        plt.ylim(-5, 105)
        plt.grid(axis="y", alpha=0.3)

        save_plot("02_llm_vs_functional_accuracy.png")


# --------------------------------------------------
# 3. HUMAN PREFERENCE ALIGNMENT
# --------------------------------------------------

alignment = pd.DataFrame({
    "Reference": ["Human Majority Annotations", "Dataset GT Choice"],
    "Agreement (%)": [44.14, 55.17]
})

plt.figure(figsize=(8, 5))
sns.barplot(data=alignment, x="Reference", y="Agreement (%)")
plt.title("LLM Judge Agreement with Human Preferences")
plt.ylabel("Agreement (%)")
plt.ylim(0, 100)
save_plot("03_human_preference_alignment.png")


# --------------------------------------------------
# 4. CONTROLLED POSITION BIAS
# --------------------------------------------------

position = pd.DataFrame({
    "Metric": ["Preference Changes", "Stable Preferences"],
    "Count": [127, 18]
})

plt.figure(figsize=(8, 5))
sns.barplot(data=position, x="Metric", y="Count")
plt.title("Controlled Position Sensitivity")
plt.ylabel("Number of Pairs (out of 145)")
save_plot("04_position_sensitivity.png")

plt.figure(figsize=(7, 5))
plt.pie(
    [93.10, 6.90],
    labels=["First-position selections", "Other selections"],
    autopct="%1.1f%%",
    startangle=90
)
plt.title("First-Position Selection Rate")
save_plot("05_first_position_selection.png")


# --------------------------------------------------
# 5. VERBOSITY EXPERIMENT
# --------------------------------------------------

verbosity = pd.DataFrame({
    "Code Version": ["Original Code", "Code with Extra Comments"],
    "Average Score": [8.30, 8.00]
})

plt.figure(figsize=(8, 5))
sns.barplot(data=verbosity, x="Code Version", y="Average Score")
plt.title("Effect of Added Comments on LLM Scores")
plt.ylabel("Average LLM Score (out of 10)")
plt.ylim(0, 10)
save_plot("06_verbosity_score_comparison.png")

verbosity_changes = pd.DataFrame({
    "Score Outcome": ["Decreased", "Unchanged", "Increased"],
    "Submissions": [6, 14, 0]
})

plt.figure(figsize=(8, 5))
sns.barplot(
    data=verbosity_changes,
    x="Score Outcome",
    y="Submissions"
)
plt.title("Score Changes After Adding Comments")
plt.ylabel("Number of Submissions (out of 20)")
save_plot("07_verbosity_score_changes.png")


# --------------------------------------------------
# 6. SELF-ENHANCEMENT EXPERIMENT
# --------------------------------------------------

self_enhancement = pd.DataFrame({
    "Generator Model": ["Qwen 2.5 Coder", "Llama 3.2"],
    "Average Overall Score": [8.05, 8.088]
})

plt.figure(figsize=(8, 5))
sns.barplot(
    data=self_enhancement,
    x="Generator Model",
    y="Average Overall Score"
)
plt.title("Pointwise Scores: Qwen vs Llama Generated Code")
plt.ylabel("Average Overall Score (out of 10)")
plt.ylim(0, 10)
save_plot("08_self_enhancement_scores.png")


# --------------------------------------------------
# 7. FUNCTIONAL TEST PERFORMANCE
# --------------------------------------------------

functional = pd.DataFrame({
    "Model": ["Qwen 2.5 Coder", "Llama 3.2"],
    "Passed Tests": [245, 86],
    "Total Tests": [261, 87],
    "Pass Rate (%)": [93.87, 98.85]
})

plt.figure(figsize=(8, 5))
sns.barplot(
    data=functional,
    x="Model",
    y="Pass Rate (%)"
)
plt.title("Functional Test Pass Rates")
plt.ylabel("Pass Rate (%)")
plt.ylim(0, 100)
save_plot("09_functional_test_pass_rates.png")


# --------------------------------------------------
# 8. RESEARCH SUMMARY
# --------------------------------------------------

summary = pd.DataFrame({
    "Experiment": [
        "Human Preference Alignment",
        "Controlled Position Sensitivity",
        "Verbosity Score Difference",
        "Self-Enhancement Score Difference",
        "Qwen Functional Test Pass Rate",
        "Llama Functional Test Pass Rate"
    ],
    "Result": [
        "44.14% (human majority)",
        "87.59% preference changes",
        "-0.30 points",
        "+0.038 points for Llama",
        "93.87%",
        "98.85%"
    ]
})

summary.to_csv(
    os.path.join(OUTPUT_DIR, "research_summary.csv"),
    index=False
)

print("\n----------------------------------")
print("FINAL RESEARCH VISUALIZATIONS DONE")
print("----------------------------------")
print(f"All graphs and summary saved in: {OUTPUT_DIR}")
