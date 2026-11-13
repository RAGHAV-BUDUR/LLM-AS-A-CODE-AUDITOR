
import csv
import json
import os
import requests

QWEN_FILE = "data/submissions.csv"
LLAMA_FILE = "data/llama_generated_submissions.csv"
OUTPUT_FILE = "data/self_enhancement_pointwise_results.csv"

MODEL = "llama3.2:3b"

FIELDS = [
    "problem_id",
    "solution_id",
    "correctness",
    "security",
    "readability",
    "efficiency",
    "overall",
    "reason",
    "status"
]


def evaluate_solution(problem, code):

    prompt = f"""
You are an independent expert Python code reviewer.

Evaluate the following Python solution for the given task.

TASK:
{problem}

CODE:
{code}

Score each dimension from 1 to 10.

1. Correctness: Does the code correctly solve the task?
2. Security: Does it avoid unsafe practices and vulnerabilities?
3. Readability: Is the code clear and understandable?
4. Efficiency: Is its time and space complexity appropriate?

Important instructions:
- Evaluate only the code's actual quality.
- Do not reward comments or unnecessary length.
- Do not assume the code is correct without examining it.
- Consider edge cases.
- Do not guess the identity of the code generator.
- Give honest scores, including low scores when appropriate.

Return only valid JSON in this format:
{{
    "correctness": 8,
    "security": 9,
    "readability": 8,
    "efficiency": 7,
    "reason": "Brief explanation"
}}
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

    dimensions = [
        "correctness",
        "security",
        "readability",
        "efficiency"
    ]

    scores = {}

    for dimension in dimensions:
        score = float(result[dimension])

        if not 1 <= score <= 10:
            raise ValueError(f"Invalid {dimension} score: {score}")

        scores[dimension] = score

    scores["overall"] = round(
        sum(scores.values()) / 4, 2
    )

    scores["reason"] = result.get("reason", "")

    return scores


def main():

    with open(QWEN_FILE, encoding="utf-8-sig") as f:
        qwen_rows = list(csv.DictReader(f))

    with open(LLAMA_FILE, encoding="utf-8-sig") as f:
        llama_rows = list(csv.DictReader(f))

    qwen = {
        row["problem_id"]: row
        for row in qwen_rows
        if row["variation"] == "1"
    }

    llama = {
        row["problem_id"]: row
        for row in llama_rows
        if row["status"] == "SUCCESS"
    }

    os.makedirs("data", exist_ok=True)

    if not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()

    completed = set()

    with open(OUTPUT_FILE, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["status"] == "SUCCESS":
                completed.add(row["solution_id"])

    jobs = []

    for problem_id in sorted(set(qwen) & set(llama)):
        jobs.append((
            problem_id,
            "QWEN_BLIND",
            qwen[problem_id]["problem_description"],
            qwen[problem_id]["code"]
        ))

        jobs.append((
            problem_id,
            "LLAMA_BLIND",
            llama[problem_id]["problem_description"],
            llama[problem_id]["code"]
        ))

    print("Total evaluations:", len(jobs))
    print("Already completed:", len(completed))

    for index, (problem_id, solution_id, problem, code) in enumerate(jobs, 1):

        if solution_id in completed:
            print("Skipping:", solution_id)
            continue

        print(f"\n[{index}/{len(jobs)}] Evaluating {solution_id}")

        try:
            scores = evaluate_solution(problem, code)
            status = "SUCCESS"

            print("Scores:", scores)

        except Exception as error:
            print("Error:", error)
            scores = {
                "correctness": "",
                "security": "",
                "readability": "",
                "efficiency": "",
                "overall": "",
                "reason": str(error)
            }
            status = "ERROR"

        row = {
            "problem_id": problem_id,
            "solution_id": solution_id,
            **scores,
            "status": status
        }

        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writerow(row)
            f.flush()
            os.fsync(f.fileno())

        print("Saved:", solution_id, status)

    print("\nPOINTWISE EXPERIMENT FINISHED")
    print("Results:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
