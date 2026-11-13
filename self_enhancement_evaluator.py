
import csv
import json
import os
import requests

QWEN_FILE = "data/submissions.csv"
LLAMA_FILE = "data/llama_generated_submissions.csv"

OUTPUT_FILE = "data/self_enhancement_results.csv"

MODEL = "llama3.2:3b"

FIELDNAMES = [
    "problem_id",
    "original_choice",
    "original_reason",
    "reversed_raw_choice",
    "reversed_reason",
    "normalized_reversed_choice",
    "llama_preference_count",
    "qwen_preference_count",
    "tie_count",
    "status"
]


def judge_pair(problem, code_a, code_b):

    prompt = f"""
You are an independent code evaluation judge.

Compare two Python solutions for the same programming task.

Evaluate:
1. Functional correctness
2. Efficiency
3. Readability
4. Security
5. Edge-case handling

Task:
{problem}

SOLUTION A:
{code_a}

SOLUTION B:
{code_b}

Choose the better solution based on its actual quality.

Do not assume either solution is better because of its
style, length, comments, or presentation.

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

    with open(QWEN_FILE, "r", newline="", encoding="utf-8-sig") as file:
        qwen_rows = list(csv.DictReader(file))

    with open(LLAMA_FILE, "r", newline="", encoding="utf-8-sig") as file:
        llama_rows = list(csv.DictReader(file))

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

    problem_ids = sorted(set(qwen) & set(llama))

    print("Matched problems:", len(problem_ids))

    os.makedirs("data", exist_ok=True)

    if not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()

    completed = set()

    with open(OUTPUT_FILE, "r", newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            if row["status"] == "SUCCESS":
                completed.add(row["problem_id"])

    print("Already completed:", len(completed))
    print("Remaining:", len(problem_ids) - len(completed))

    for index, problem_id in enumerate(problem_ids, start=1):

        if problem_id in completed:
            print("Skipping:", problem_id)
            continue

        print(f"\n[{index}/{len(problem_ids)}] Comparing {problem_id}")

        qwen_code = qwen[problem_id]["code"]
        llama_code = llama[problem_id]["code"]

        problem = qwen[problem_id]["problem_description"]

        try:

            # Original order: A = Qwen, B = Llama
            original_choice, original_reason = judge_pair(
                problem, qwen_code, llama_code
            )

            # Reversed order: A = Llama, B = Qwen
            reversed_raw_choice, reversed_reason = judge_pair(
                problem, llama_code, qwen_code
            )

            # Normalize reversed choice to original identities
            if reversed_raw_choice == "A":
                normalized = "B"
            elif reversed_raw_choice == "B":
                normalized = "A"
            else:
                normalized = "Tie"

            # Count preferences for Llama and Qwen
            llama_count = (
                (1 if original_choice == "B" else 0)
                + (1 if reversed_raw_choice == "A" else 0)
            )

            qwen_count = (
                (1 if original_choice == "A" else 0)
                + (1 if reversed_raw_choice == "B" else 0)
            )

            tie_count = (
                (1 if original_choice == "Tie" else 0)
                + (1 if reversed_raw_choice == "Tie" else 0)
            )

            status = "SUCCESS"

            print("Original choice:", original_choice)
            print("Reversed choice:", reversed_raw_choice)
            print("Llama preferences:", llama_count)
            print("Qwen preferences:", qwen_count)

        except Exception as error:

            print("Error:", error)

            original_choice = ""
            original_reason = ""
            reversed_raw_choice = ""
            reversed_reason = ""
            normalized = ""
            llama_count = ""
            qwen_count = ""
            tie_count = ""
            status = "ERROR"

        result = {
            "problem_id": problem_id,
            "original_choice": original_choice,
            "original_reason": original_reason,
            "reversed_raw_choice": reversed_raw_choice,
            "reversed_reason": reversed_reason,
            "normalized_reversed_choice": normalized,
            "llama_preference_count": llama_count,
            "qwen_preference_count": qwen_count,
            "tie_count": tie_count,
            "status": status
        }

        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writerow(result)
            file.flush()
            os.fsync(file.fileno())

        print("Saved:", problem_id, status)

    print("\nSELF-ENHANCEMENT EXPERIMENT FINISHED")
    print("Results saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
