
import pandas as pd
import ast

df = pd.read_csv(
    "data/submissions.csv",
    encoding="utf-8-sig"
)

for _, row in df.iterrows():

    print("\n" + "=" * 55)
    print("SUBMISSION:", row["submission_id"])
    print("PROBLEM:", row["problem_id"])

    try:
        tree = ast.parse(str(row["code"]))

        functions = [
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        if not functions:
            print("No function definition found")
            continue

        for function in functions:
            parameters = [
                arg.arg for arg in function.args.args
            ]

            print("Function:", function.name)
            print("Parameters:", parameters)

    except SyntaxError as error:
        print("Syntax Error:", error)

print("\nINTERFACE INSPECTION COMPLETED")
