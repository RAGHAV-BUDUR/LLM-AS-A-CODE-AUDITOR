
import csv
import json
import os
import ollama

INPUT_FILE = "data/submissions.csv"
OUTPUT_FILE = "data/evaluation_results.csv"

JUDGE_MODEL = "llama3.2:3b"

DIMENSIONS = [
    "correctness",
    "security",
    "readability",
    "efficiency"
]

FIELDS = [
    "submission_id",
    "problem_id",
    "problem_description",
    "generator_model",
    "judge_model",
    "correctness",
    "correctness_explanation",
    "security",
    "security_explanation",
    "readability",
    "readability_explanation",
    "efficiency",
    "efficiency_explanation",
    "overall_score",
    "status",
    "error"
]


def evaluate_submission(problem, code, judge_model=None):

    prompt = f"""
You are an independent Python code auditor.

Evaluate the submitted code using four dimensions.

1. Correctness:
Does the code satisfy the actual problem requirements?

2. Security:
Does the code contain identifiable security vulnerabilities?

3. Readability:
Is the code understandable and maintainable?

4. Efficiency:
Is the algorithm computationally efficient?

Rules:
- Give integer scores from 1 to 10.
- Evaluate according to the given problem.
- Do not penalize missing features that were not requested.
- Do not invent security vulnerabilities.
- Explain every score.
- Return valid JSON only.

PROBLEM:
{problem}

SUBMITTED CODE:
{code}

Return this JSON structure:

{{
  "correctness": {{
    "score": 8,
    "explanation": "Reason for score"
  }},
  "security": {{
    "score": 8,
    "explanation": "Reason for score"
  }},
  "readability": {{
    "score": 8,
    "explanation": "Reason for score"
  }},
  "efficiency": {{
    "score": 8,
    "explanation": "Reason for score"
  }}
}}
"""

    response = ollama.chat(
        model=judge_model or JUDGE_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        format="json",
        keep_alive=0
    )

    result = json.loads(response["message"]["content"])

    scores = {}

    for dimension in DIMENSIONS:

        score = result[dimension]["score"]

        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError(f"Invalid score: {dimension}")

        if not 1 <= score <= 10:
            raise ValueError(f"Score out of range: {dimension}")

        scores[dimension] = score

    overall = sum(scores.values()) / len(DIMENSIONS)

    return result, scores, round(overall, 2)


def main():

    if not os.path.exists(INPUT_FILE):
        print("Submission dataset not found!")
        return

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        submissions = list(csv.DictReader(file))

    if not submissions:
        print("No submissions found!")
        return

    completed_ids = set()

    if os.path.exists(OUTPUT_FILE):

        with open(
            OUTPUT_FILE,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            for row in csv.DictReader(file):

                if row["status"] == "success":
                    completed_ids.add(row["submission_id"])

    new_file = not os.path.exists(OUTPUT_FILE)

    completed_count = len(completed_ids)

    print("=" * 55)
    print("       AUTOMATED CODE EVALUATION SYSTEM")
    print("=" * 55)

    with open(
        OUTPUT_FILE,
        "a",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(file, fieldnames=FIELDS)

        if new_file:
            writer.writeheader()

        for index, submission in enumerate(submissions, start=1):

            submission_id = submission["submission_id"]

            if submission_id in completed_ids:
                print(f"\nSkipping {submission_id} - already evaluated")
                continue

            print(
                f"\n[{index}/{len(submissions)}] "
                f"Evaluating {submission_id}..."
            )

            row = {
                "submission_id": submission_id,
                "problem_id": submission["problem_id"],
                "problem_description": submission["problem_description"],
                "generator_model": submission["model"],
                "judge_model": JUDGE_MODEL,
                "status": "error",
                "error": ""
            }

            try:

                result, scores, overall = evaluate_submission(
                    submission["problem_description"],
                    submission["code"]
                )

                for dimension in DIMENSIONS:

                    row[dimension] = scores[dimension]

                    row[f"{dimension}_explanation"] = (
                        result[dimension]["explanation"]
                    )

                row["overall_score"] = overall
                row["status"] = "success"

                completed_count += 1

                print("Evaluation successful!")
                print("Scores:", scores)
                print("Overall:", overall)

            except Exception as error:

                row["error"] = str(error)

                print("Evaluation failed:", error)

            writer.writerow(row)
            file.flush()

    print("\n" + "=" * 55)
    print("EVALUATION PROCESS FINISHED")
    print(f"Successfully evaluated: {completed_count}")
    print(f"Total submissions: {len(submissions)}")
    print(f"Results saved in: {OUTPUT_FILE}")
    print("=" * 55)


if __name__ == "__main__":
    main()
