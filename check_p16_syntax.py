
import pandas as pd
import ast

df = pd.read_csv(
    "data/submissions.csv",
    encoding="utf-8-sig"
)

p16 = df[df["problem_id"] == "P16"]

print("\nP16 SYNTAX CHECK\n")

for _, row in p16.iterrows():

    submission_id = row["submission_id"]
    code = row["code"]

    try:
        ast.parse(code)
        print(f"{submission_id}: SYNTAX VALID")

    except SyntaxError as error:
        print(f"{submission_id}: SYNTAX ERROR")
        print("Line:", error.lineno)
        print("Message:", error.msg)
