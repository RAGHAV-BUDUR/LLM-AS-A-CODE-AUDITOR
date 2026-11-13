
import pandas as pd
import ast
import subprocess
import sys
import json

from test_cases import TEST_CASES

# Main function for each submission
FUNCTION_MAP = {
    "P05_S1": "sort_list_of_integers",
    "P05_S2": "sort_list",
    "P05_S3": "sort_list_of_integers"
}

df = pd.read_csv(
    "data/submissions.csv",
    encoding="utf-8-sig"
)

results = []

for _, row in df[df["problem_id"] == "P05"].iterrows():

    submission_id = row["submission_id"]
    code = str(row["code"])

    print(f"\nTesting {submission_id}...")

    try:
        # Parse original submission
        tree = ast.parse(code)

        function_name = FUNCTION_MAP[submission_id]

        # Extract required functions
        if submission_id == "P05_S2":

            # sort_list depends on bubble_sort
            required_names = {
                "bubble_sort",
                "sort_list"
            }

        else:
            required_names = {function_name}

        required_nodes = [
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name in required_names
        ]

        # Verify all required functions were found
        found_names = {
            node.name for node in required_nodes
        }

        if found_names != required_names:
            raise ValueError(
                f"Missing functions: {required_names - found_names}"
            )

        # Convert extracted functions back to Python code
        clean_code = ast.unparse(
            ast.Module(
                body=required_nodes,
                type_ignores=[]
            )
        )

        passed = 0
        failed = 0

        # Execute each test case separately
        for input_list, expected in TEST_CASES["P05"]:

            test_script = "import json\n" + clean_code + f"""

result = {function_name}({json.dumps(input_list)})

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
                print("Input:", input_list)
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
            "failed": len(TEST_CASES["P05"]),
            "total": len(TEST_CASES["P05"])
        })

    except Exception as error:

        print("Testing error:", error)

        results.append({
            "submission_id": submission_id,
            "passed": 0,
            "failed": len(TEST_CASES["P05"]),
            "total": len(TEST_CASES["P05"])
        })


# Display results
results_df = pd.DataFrame(results)

print("\n========== P05 SORTING TEST RESULTS ==========")

print(results_df.to_string(index=False))

# Save results
results_df.to_csv(
    "data/sorting_test_results.csv",
    index=False
)

print("\nResults saved to data/sorting_test_results.csv")
