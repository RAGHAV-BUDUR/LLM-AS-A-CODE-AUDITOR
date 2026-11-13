
import pandas as pd
import subprocess
import tempfile
import os
import sys

INPUT_FILE = "data/submissions.csv"
OUTPUT_FILE = "data/correctness_results.csv"

df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

# Initial test cases for prime number programs
TEST_CASES = {
    "P01": [
        ("print(is_prime(2))", "True"),
        ("print(is_prime(3))", "True"),
        ("print(is_prime(4))", "False"),
        ("print(is_prime(1))", "False"),
        ("print(is_prime(0))", "False"),
        ("print(is_prime(17))", "True"),
        ("print(is_prime(25))", "False"),
        ("print(is_prime(-7))", "False"),
    ]
}

results = []

for index, row in df.iterrows():

    problem_id = row["problem_id"]

    # Only P01 is tested in this first version
    if problem_id not in TEST_CASES:
        continue

    code = str(row["code"])
    passed = 0
    failed = 0
    errors = []

    for test_input, expected in TEST_CASES[problem_id]:

        # Combine generated function with the test call
        complete_code = code + "\n\n" + test_input

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                encoding="utf-8",
                delete=False
            ) as temp_file:

                temp_file.write(complete_code)
                temp_path = temp_file.name

            process = subprocess.run(
                [sys.executable, "-I", temp_path],
                capture_output=True,
                text=True,
                timeout=3
            )

            actual = process.stdout.strip()

            if process.returncode == 0 and actual == expected:
                passed += 1
            else:
                failed += 1
                errors.append(
                    f"Expected {expected}, got {actual or process.stderr.strip()}"
                )

        except subprocess.TimeoutExpired:
            failed += 1
            errors.append("Execution timeout")

        except Exception as error:
            failed += 1
            errors.append(str(error))

        finally:
            if "temp_path" in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
                del temp_path

    results.append({
        "submission_id": row["submission_id"],
        "problem_id": problem_id,
        "total_tests": len(TEST_CASES[problem_id]),
        "passed_tests": passed,
        "failed_tests": failed,
        "correctness_percentage": round(
            (passed / len(TEST_CASES[problem_id])) * 100, 2
        ),
        "errors": " | ".join(errors)
    })

    print(
        f"{row['submission_id']}: "
        f"Passed {passed}, Failed {failed}"
    )

results_df = pd.DataFrame(results)
results_df.to_csv(OUTPUT_FILE, index=False)

print("\nCORRECTNESS TESTING COMPLETED")
print("Submissions tested:", len(results_df))
print("Results saved to:", OUTPUT_FILE)
