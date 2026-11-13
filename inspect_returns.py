
import pandas as pd
import ast

df = pd.read_csv(
    "data/submissions.csv",
    encoding="utf-8-sig"
)

for _, row in df.iterrows():

    print("\n" + "=" * 55)
    print("SUBMISSION:", row["submission_id"])

    try:
        tree = ast.parse(str(row["code"]))

        for node in tree.body:

            if isinstance(node, ast.FunctionDef):

                print("\nFunction:", node.name)

                for child in ast.walk(node):

                    if isinstance(child, ast.Return):
                        print(
                            "Return:",
                            ast.unparse(child.value)
                            if child.value else "None"
                        )

    except SyntaxError as error:
        print("Syntax Error:", error)

print("\nRETURN INSPECTION COMPLETED")
