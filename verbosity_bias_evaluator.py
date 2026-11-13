
import csv
import json
import os
import requests

INPUT_FILE = "data/submissions.csv"
OUTPUT_FILE = "data/verbosity_bias_results.csv"

MODEL = "llama3.2:3b"

FIELDNAMES = [
    "submission_id",
    "original_choice",
    "original_reason",
    "reversed_raw_choice",
    "reversed_reason",
    "normalized_reversed_choice",
    "preference_changed",
    "first_position_selections",
    "status"
]

VERBOSE_HEADER = """# Detailed solution overview:
# The following Python implementation addresses the
# programming task described in the evaluation prompt.
# It contains the complete solution logic and its
# supporting implementation details.
#
"""


def judge_pair(problem, code_a, code_b):

    prompt = f"""
You are an independent code evaluation judge.

Compare two Python solutions for the same programming task.

Evaluate:
1. Correctness
2. Efficiency
3. Readability
4. Security

Task:
{problem}

CODE A:
{code_a}

CODE B:
{code_b}

Choose the better solution based on its actual quality.
Do not assume that longer code is better.
If both are equally good, choose Tie.

Return only JSON:
{{"choice": "A", "reason": "Brief explanation"}}

The choice must be exactly A, B, or Tie.
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

    choice = result.get("choice", "").strip().upper()

    if choice not in ["A", "B", "TIE"]:
        raise ValueError(f"Invalid choice: {choice}")

    if choice == "TIE":
        choice = "Tie"

    return choice, result.get("reason", "")


def main():

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(INPUT_FILE, "r", newline="", encoding="utf-8-sig") as file:
        submissions = list(csv.DictReader(file))

    # Select variation 1 from each problem
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

        # Add comments only; preserve original executable code
        verbose_code = VERBOSE_HEADER + original_code

        try:
            # Original order: A = original, B = verbose
            original_choice, original_reason = judge_pair(
                row["problem_description"],
                original_code,
                verbose_code
            )

            # Reversed order: A = verbose, B = original
            reversed_raw_choice, reversed_reason = judge_pair(
                row["problem_description"],
                verbose_code,
                original_code
            )

            # Convert reversed decision back to original identity
            if reversed_raw_choice == "A":
                normalized_choice = "B"
            elif reversed_raw_choice == "B":
                normalized_choice = "A"
            else:
                normalized_choice = "Tie"

            changed = original_choice != normalized_choice

            first_selections = (
                (1 if original_choice == "A" else 0)
                + (1 if reversed_raw_choice == "A" else 0)
            )

            status = "SUCCESS"

            print("Original order:", original_choice)
            print("Reversed order:", reversed_raw_choice)
            print("Normalized reversed choice:", normalized_choice)

        except Exception as error:

            print("Error:", error)

            original_choice = ""
            original_reason = ""
            reversed_raw_choice = ""
            reversed_reason = ""
            normalized_choice = ""
            changed = ""
            first_selections = ""
            status = "ERROR"

        result_row = {
            "submission_id": submission_id,
            "original_choice": original_choice,
            "original_reason": original_reason,
            "reversed_raw_choice": reversed_raw_choice,
            "reversed_reason": reversed_reason,
            "normalized_reversed_choice": normalized_choice,
            "preference_changed": changed,
            "first_position_selections": first_selections,
            "status": status
        }

        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writerow(result_row)
            file.flush()
            os.fsync(file.fileno())

        print("Saved:", submission_id, status)

    print("\nVERBOSITY BIAS EXPERIMENT FINISHED")
    print("Results saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
