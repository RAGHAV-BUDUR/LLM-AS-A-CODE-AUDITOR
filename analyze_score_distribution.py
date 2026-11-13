
import pandas as pd

df = pd.read_csv("data/llm_functional_comparison.csv")

print("\n========== LLM CORRECTNESS SCORE DISTRIBUTION ==========")
print(df["correctness"].value_counts().sort_index())

print("\n========== FUNCTIONAL ACCURACY DISTRIBUTION ==========")
print(df["accuracy_percent"].value_counts().sort_index())

print("\n========== SCORE VARIATION ==========")

print("\nLLM correctness:")
print(df["correctness"].describe())

print("\nFunctional accuracy:")
print(df["accuracy_percent"].describe())

print("\n========== UNIQUE VALUES ==========")
print("Unique LLM correctness scores:",
      df["correctness"].nunique())

print("Unique functional accuracy values:",
      df["accuracy_percent"].nunique())

print("\n========== FUNCTIONAL STATUS ==========")
print(df["functional_status"].value_counts())

print("\n========== CROSS-TABULATION ==========")
print(pd.crosstab(
    df["correctness"],
    df["functional_status"]
))
