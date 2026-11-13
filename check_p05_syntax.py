
import pandas as pd
import ast

df = pd.read_csv("data/submissions.csv", encoding="utf-8-sig")

p05 = df[df["problem_id"] == "P05"]

print("\nP05 SYNTAX CHECK\n")

for _, row in p05.iterrows():
    submission_id = row["submission_id"]
    code = row["code"]

    try:
        ast.parse(code)
        print(f"{submission_id}: SYNTAX VALID")

    except SyntaxError as error:
        print(f"{submission_id}: SYNTAX ERROR")
        print(f"  Line: {error.lineno}")
        print(f"  Message: {error.msg}")
