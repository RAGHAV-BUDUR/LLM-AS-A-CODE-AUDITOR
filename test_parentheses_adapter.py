
import pandas as pd
import ast
import subprocess
import sys
import json

from test_cases import TEST_CASES

FUNCTION_NAME = "is_balanced_parentheses"

df = pd.read_csv(
    "data/submissions.csv",
    encoding="utf-8-sig"
)

results = []

for _, row in df[df["problem_id"] == "P16"].iterrows():

    submission_id = row["submission_id"]
    code = str(row["code"])

    print(f"\nTesting {submission_id}...")

    try:
        tree = ast.parse(code)

        function_node = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == FUNCTION_NAME
        )

        clean_code = ast.unparse(function_node)

        passed = 0
        failed = 0

        for input_string, expected in TEST_CASES["P16"]:

            test_script = "import json\n" + clean_code + f"""

result = {FUNCTION_NAME}({json.dumps(input_string)})

if not isinstance(result, bool):
    raise ValueError("Function must return a Boolean")

print(json.dumps(result))
"""

            process = subprocess.run(
                [sys.executable, "-c", test_script],
                capture_output=True,
                text=True,
                timeout=5
            )

            if process.returncode != 0:
                failed += 1
                print("Runtime error:")
                print(process.stderr)
                continue

            try:
                actual = json.loads(
                    process.stdout.strip().splitlines()[-1]
                )
            except Exception as error:
                failed += 1
                print("Output error:", error)
                continue

            if actual == expected:
                passed += 1
            else:
                failed += 1
                print("Incorrect result:")
                print("Input:", input_string)
                print("Expected:", expected)
                print("Actual:", actual)

        results.append({
            "submission_id": submission_id,
            "passed": passed,
            "failed": failed,
            "total": passed + failed
        })

    except SyntaxError as error:

        print("Syntax error:", error)

        results.append({
            "submission_id": submission_id,
            "passed": 0,
            "failed": len(TEST_CASES["P16"]),
            "total": len(TEST_CASES["P16"])
        })

    except Exception as error:

        print("Testing error:", error)

        results.append({
            "submission_id": submission_id,
            "passed": 0,
            "failed": len(TEST_CASES["P16"]),
            "total": len(TEST_CASES["P16"])
        })


results_df = pd.DataFrame(results)

print("\n========== P16 TEST RESULTS ==========")
print(results_df.to_string(index=False))

results_df.to_csv(
    "data/parentheses_test_results.csv",
    index=False
)

print("\nResults saved to data/parentheses_test_results.csv")
