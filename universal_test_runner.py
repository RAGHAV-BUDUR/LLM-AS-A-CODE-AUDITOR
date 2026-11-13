
import ast
import json
import subprocess
import sys

import pandas as pd

from benchmark_config import FUNCTION_MAP
from test_cases import TEST_CASES


INPUT_FILE = "data/submissions.csv"
OUTPUT_FILE = "data/correctness_results.csv"
DETAIL_OUTPUT_FILE = "data/correctness_test_details.csv"


# Load original AI-generated submissions
df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

all_results = []
all_details = []


def extract_required_code(code, function_name):
    """
    Extract the selected function, its helper functions,
    and required imports. Ignore top-level example code.
    """

    tree = ast.parse(code)

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    if function_name not in functions:
        raise ValueError("Main function not found")

    required_names = set()
    pending = [function_name]

    # Discover helper-function dependencies
    while pending:

        current_name = pending.pop()

        if current_name in required_names:
            continue

        if current_name not in functions:
            continue

        required_names.add(current_name)

        function_node = functions[current_name]

        for node in ast.walk(function_node):

            if isinstance(node, ast.Name):
                if (
                    isinstance(node.ctx, ast.Load)
                    and node.id in functions
                    and node.id not in required_names
                ):
                    pending.append(node.id)

    # Preserve imports and required function definitions
    required_nodes = [
        node for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        or (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in required_names
        )
    ]

    clean_tree = ast.Module(
        body=required_nodes,
        type_ignores=[]
    )

    return ast.unparse(clean_tree)


def normalize_result(problem_id, actual):

    # P20 supports Boolean and descriptive text responses
    if problem_id == "P20":

        if isinstance(actual, bool):
            return actual

        if actual == "Password is strong.":
            return True

        if (
            isinstance(actual, str)
            and actual.startswith("Password ")
        ):
            return False

        raise ValueError("Unsupported P20 return format")

    # P07: duplicate order is not specified
    if problem_id == "P07" and isinstance(actual, list):
        return sorted(actual)

    return actual


def run_single_test(clean_code, function_name, args):

    arguments = repr(tuple(args))

    test_script = (
        "import json\n"
        + clean_code
        + "\n\n"
        + f"result = {function_name}(*{arguments})\n"
        + "print('__RESULT__' + json.dumps(result))\n"
    )

    process = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5
    )

    if process.returncode != 0:
        raise RuntimeError(process.stderr)

    # Find the result marker, ignoring other printed output
    result_lines = [
        line for line in process.stdout.splitlines()
        if line.startswith("__RESULT__")
    ]

    if not result_lines:
        raise ValueError("Function did not produce a readable result")

    return json.loads(
        result_lines[-1][len("__RESULT__"):]
    )


def add_detail(
    submission_id,
    problem_id,
    test_index,
    args,
    expected,
    actual,
    outcome,
    error_message=""
):
    """
    Save the result of one individual benchmark test.
    """

    all_details.append({
        "submission_id": submission_id,
        "problem_id": problem_id,
        "test_index": test_index,
        "input_args": json.dumps(args, ensure_ascii=False),
        "expected_output": json.dumps(expected, ensure_ascii=False),
        "actual_output": (
            json.dumps(actual, ensure_ascii=False)
            if actual is not None else ""
        ),
        "outcome": outcome,
        "error_message": error_message
    })


print("\n========== UNIVERSAL CORRECTNESS TESTING ==========\n")


for _, row in df.iterrows():

    submission_id = row["submission_id"]
    problem_id = row["problem_id"]
    code = str(row["code"])

    test_cases = TEST_CASES[problem_id]

    passed = 0
    failed = 0
    syntax_errors = 0
    runtime_errors = 0
    incorrect_outputs = 0
    other_errors = 0

    print(f"Testing {submission_id}...")

    try:

        # Parse code and identify its main function
        tree = ast.parse(code)

        available_functions = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        function_name = next(
            (
                name for name in FUNCTION_MAP[problem_id]
                if name in available_functions
            ),
            None
        )

        if function_name is None:
            raise ValueError("Expected function not found")

        # Extract function and helper dependencies
        clean_code = extract_required_code(
            code,
            function_name
        )

    except SyntaxError as error:

        print(f"  SYNTAX ERROR: {error.msg}")

        syntax_errors = 1
        failed = len(test_cases)

        # Record every test blocked by this syntax error
        for test_index, test_case in enumerate(test_cases, start=1):

            add_detail(
                submission_id,
                problem_id,
                test_index,
                test_case[:-1],
                test_case[-1],
                None,
                "SYNTAX_ERROR",
                str(error)
            )

        all_results.append({
            "submission_id": submission_id,
            "problem_id": problem_id,
            "function_name": None,
            "passed": passed,
            "failed": failed,
            "total": len(test_cases),
            "syntax_errors": syntax_errors,
            "runtime_errors": runtime_errors,
            "incorrect_outputs": incorrect_outputs,
            "other_errors": other_errors,
            "accuracy_percent": 0,
            "status": "SYNTAX_ERROR"
        })

        continue

    except Exception as error:

        print(f"  EXTRACTION ERROR: {error}")

        other_errors = 1
        failed = len(test_cases)

        for test_index, test_case in enumerate(test_cases, start=1):

            add_detail(
                submission_id,
                problem_id,
                test_index,
                test_case[:-1],
                test_case[-1],
                None,
                "EXTRACTION_ERROR",
                str(error)
            )

        all_results.append({
            "submission_id": submission_id,
            "problem_id": problem_id,
            "function_name": None,
            "passed": passed,
            "failed": failed,
            "total": len(test_cases),
            "syntax_errors": syntax_errors,
            "runtime_errors": runtime_errors,
            "incorrect_outputs": incorrect_outputs,
            "other_errors": other_errors,
            "accuracy_percent": 0,
            "status": "EXTRACTION_ERROR"
        })

        continue

    # Execute individual benchmark test cases
    for test_index, test_case in enumerate(test_cases, start=1):

        args = test_case[:-1]
        expected = test_case[-1]

        actual = None
        error_message = ""
        outcome = ""

        try:

            actual = run_single_test(
                clean_code,
                function_name,
                args
            )

            actual = normalize_result(
                problem_id,
                actual
            )

            if actual == expected:

                passed += 1
                outcome = "PASSED"

            else:

                failed += 1
                incorrect_outputs += 1
                outcome = "INCORRECT_OUTPUT"

        except subprocess.TimeoutExpired as error:

            failed += 1
            runtime_errors += 1
            outcome = "RUNTIME_ERROR"
            error_message = str(error)

        except RuntimeError as error:

            failed += 1
            runtime_errors += 1
            outcome = "RUNTIME_ERROR"
            error_message = str(error)

        except Exception as error:

            failed += 1
            other_errors += 1
            outcome = "OTHER_ERROR"
            error_message = str(error)

        # Record individual test result
        add_detail(
            submission_id,
            problem_id,
            test_index,
            args,
            expected,
            actual,
            outcome,
            error_message
        )

    total = len(test_cases)

    accuracy = (
        (passed / total) * 100
        if total else 0
    )

    if syntax_errors:
        status = "SYNTAX_ERROR"
    elif runtime_errors:
        status = "RUNTIME_ERROR"
    elif other_errors:
        status = "OTHER_ERROR"
    elif incorrect_outputs:
        status = "INCORRECT_OUTPUT"
    else:
        status = "ALL_TESTS_PASSED"

    print(
        f"  {passed}/{total} passed | "
        f"Accuracy: {accuracy:.2f}% | "
        f"{status}"
    )

    all_results.append({
        "submission_id": submission_id,
        "problem_id": problem_id,
        "function_name": function_name,
        "passed": passed,
        "failed": failed,
        "total": total,
        "syntax_errors": syntax_errors,
        "runtime_errors": runtime_errors,
        "incorrect_outputs": incorrect_outputs,
        "other_errors": other_errors,
        "accuracy_percent": round(accuracy, 2),
        "status": status
    })


# Save consolidated submission-level results
results_df = pd.DataFrame(all_results)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# Save individual test-level results
details_df = pd.DataFrame(all_details)

details_df.to_csv(
    DETAIL_OUTPUT_FILE,
    index=False
)


print("\n========== FINAL SUMMARY ==========\n")

print("Total submissions:", len(results_df))
print("Total test cases:", results_df["total"].sum())
print("Total passed:", results_df["passed"].sum())
print("Total failed:", results_df["failed"].sum())

print("\nStatus distribution:")
print(results_df["status"].value_counts().to_string())

print("\nResults by problem:")
print(
    results_df.groupby("problem_id")[
        ["passed", "failed", "total"]
    ].sum().to_string()
)

print("\nDetailed failure distribution:")
print(
    details_df["outcome"].value_counts().to_string()
)

print(f"\nSubmission summary saved to {OUTPUT_FILE}")
print(f"Detailed test results saved to {DETAIL_OUTPUT_FILE}")
