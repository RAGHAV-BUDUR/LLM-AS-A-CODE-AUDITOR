
import pandas as pd
import ast
import subprocess
import sys
import json

from test_cases import TEST_CASES
from benchmark_config import FUNCTION_MAP

df = pd.read_csv("data/submissions.csv", encoding="utf-8-sig")

results = []

for _, row in df[df["problem_id"] == "P20"].iterrows():

    submission_id = row["submission_id"]
    code = str(row["code"])

    try:
        tree = ast.parse(code)

        # Find the expected function
        function_names = FUNCTION_MAP["P20"]

        selected_function = next(
            (
                node.name for node in tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name in function_names
            ),
            None
        )

        if not selected_function:
            raise ValueError("Expected function not found")

        # Keep imports and the selected function only.
        required_nodes = [
            node for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
            or (
                isinstance(node, ast.FunctionDef)
                and node.name == selected_function
            )
        ]

        clean_tree = ast.Module(
            body=required_nodes,
            type_ignores=[]
        )

        clean_code = ast.unparse(clean_tree)

        passed = 0
        failed = 0

        for password, expected in TEST_CASES["P20"]:

            test_script = "import json\n" + clean_code + f"""

result = {selected_function}({json.dumps(password)})

if isinstance(result, bool):
    actual = result
elif result == "Password is strong.":
    actual = True
elif isinstance(result, str) and result.startswith("Password "):
    actual = False
else:
    raise ValueError("Unsupported return format")

print(json.dumps(actual))
"""

            process = subprocess.run(
                [sys.executable, "-c", test_script],
                capture_output=True,
                text=True,
                timeout=5
            )

            if process.returncode != 0:
                failed += 1
                print(f"\nERROR in {submission_id}")
                print("STDERR:", process.stderr)
                print("STDOUT:", process.stdout)
                continue

            try:
                actual = json.loads(process.stdout.strip().splitlines()[-1])
            except Exception:
                failed += 1
                print(f"\nOUTPUT ERROR in {submission_id}: {error}")
                ("STDOUT:", process.stdout)
                continue

            if actual == expected:
                passed += 1
            else:
                failed += 1

        results.append({
            "submission_id": submission_id,
            "passed": passed,
            "failed": failed,
            "total": passed + failed
        })

    except Exception as error:
        results.append({
            "submission_id": submission_id,
            "passed": 0,
            "failed": len(TEST_CASES["P20"]),
            "total": len(TEST_CASES["P20"]),
            "error": str(error)
        })

results_df = pd.DataFrame(results)

print("\nP20 PASSWORD TEST RESULTS")
print(results_df.to_string(index=False))

results_df.to_csv(
    "data/password_test_results.csv",
    index=False
)

print("\nResults saved to data/password_test_results.csv")
