
import csv
import json
import os
import requests

INPUT_FILE = "data/submissions.csv"
OUTPUT_FILE = "data/controlled_verbosity_scoring_results.csv"

MODEL = "llama3.2:3b"

FIELDNAMES = [
    "submission_id",
    "original_score",
    "original_reason",
    "verbose_score",
    "verbose_reason",
    "score_difference",
    "status"
]

VERBOSE_HEADER = """# DETAILED IMPLEMENTATION OVERVIEW
# This solution is designed to address the programming task.
# The implementation below contains the complete logic
# required to solve the problem.
# Each statement contributes to the overall solution.
# The code is presented with additional explanatory
# context to make its structure easier to understand.
#
"""


def evaluate_code(problem, code):

    prompt = f"""
You are an independent code quality evaluator.

Evaluate the following Python solution for the programming task.

Assess these four dimensions:
1. Correctness
2. Security
3. Readability
4. Efficiency

Give an overall quality score from 1 to 10.

IMPORTANT:
- Focus on the actual implementation and its quality.
- Do not reward code merely for being longer.
- Do not give extra credit just because comments or
  explanatory text make the solution look detailed.
- Comments should only affect readability if they
  genuinely improve understanding.
- Judge the code using the same standards for every submission.

Programming task:
{problem}

Python solution:
{code}

Return only valid JSON in this format:
{{"score": 8, "reason": "Brief explanation"}}

The score must be an integer between 1 and 10.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
                "seed": 42
            },
            "keep_alive": "5m"
        },
        timeout=300
    )

    response.raise_for_status()

    result = json.loads(response.json()["response"])

    score = int(result["score"])

    if score < 1 or score > 10:
        raise ValueError(f"Invalid score: {score}")

    return score, result.get("reason", "")


def main():

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(INPUT_FILE, "r", newline="", encoding="utf-8-sig") as file:
        submissions = list(csv.DictReader(file))

    selected = [
        row for row in submissions
        if row["variation"] == "1"
    ]

    print("Selected submissions:", len(selected))

    if not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()

    completed = set()

    with open(OUTPUT_FILE, "r", newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            if row["status"] == "SUCCESS":
                completed.add(row["submission_id"])

    print("Already completed:", len(completed))
    print("Remaining:", len(selected) - len(completed))

    for index, row in enumerate(selected, start=1):

        submission_id = row["submission_id"]

        if submission_id in completed:
            print(f"Skipping {submission_id}")
            continue

        print(f"\n[{index}/{len(selected)}] Evaluating {submission_id}")

        original_code = row["code"]
        verbose_code = VERBOSE_HEADER + original_code

        try:

            original_score, original_reason = evaluate_code(
                row["problem_description"],
                original_code
            )

            print("Original score:", original_score)

            verbose_score, verbose_reason = evaluate_code(
                row["problem_description"],
                verbose_code
            )

            print("Verbose score:", verbose_score)

            difference = verbose_score - original_score

            print("Score difference:", difference)

            status = "SUCCESS"

        except Exception as error:

            print("Error:", error)

            original_score = ""
            original_reason = ""
            verbose_score = ""
            verbose_reason = ""
            difference = ""
            status = "ERROR"

        result_row = {
            "submission_id": submission_id,
            "original_score": original_score,
            "original_reason": original_reason,
            "verbose_score": verbose_score,
            "verbose_reason": verbose_reason,
            "score_difference": difference,
            "status": status
        }

        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writerow(result_row)
            file.flush()
            os.fsync(file.fileno())

        print("Saved:", submission_id, status)

    print("\nCONTROLLED VERBOSITY SCORING FINISHED")
    print("Results saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
