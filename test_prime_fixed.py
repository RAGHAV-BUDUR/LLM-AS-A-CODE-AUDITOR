
import pandas as pd
import subprocess
import tempfile
import os
import sys
import ast

INPUT_FILE = "data/submissions.csv"
OUTPUT_FILE = "data/correctness_results.csv"

df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

TEST_CASES = [
    (2, True),
    (3, True),
    (4, False),
    (1, False),
    (0, False),
    (17, True),
    (25, False),
    (-7, False)
]

results = []

for _, row in df[df["problem_id"] == "P01"].iterrows():

    submission_id = row["submission_id"]
    code = str(row["code"])

    passed = 0
    failed = 0
    errors = []

    try:
        # Parse generated code
        tree = ast.parse(code)

        # Extract only the is_prime function
        functions = [
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "is_prime"
        ]

        if not functions:
            raise ValueError("is_prime function not found")

        function_code = ast.unparse(functions[0])

        for number, expected in TEST_CASES:

            test_code = (
                function_code
                + "\n"
                + f"print(is_prime({number}))"
            )

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                encoding="utf-8",
                delete=False
            ) as temp:

                temp.write(test_code)
                temp_path = temp.name

            try:
                process = subprocess.run(
                    [sys.executable, "-I", temp_path],
                    capture_output=True,
                    text=True,
                    timeout=3
                )

                actual = process.stdout.strip()

                if process.returncode == 0 and actual == str(expected):
                    passed += 1
                else:
                    failed += 1
                    errors.append(
                        f"Input {number}: Expected {expected}, "
                        f"got {actual or process.stderr.strip()}"
                    )

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    except Exception as error:
        failed = len(TEST_CASES)
        errors.append(str(error))

    results.append({
        "submission_id": submission_id,
        "problem_id": "P01",
        "total_tests": len(TEST_CASES),
        "passed_tests": passed,
        "failed_tests": failed,
        "correctness_percentage": round(
            passed / len(TEST_CASES) * 100, 2
        ),
        "errors": " | ".join(errors)
    })

    print(f"{submission_id}: Passed {passed}, Failed {failed}")

pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)

print("\nFIXED CORRECTNESS TESTING COMPLETED")
print("Results saved to:", OUTPUT_FILE)
