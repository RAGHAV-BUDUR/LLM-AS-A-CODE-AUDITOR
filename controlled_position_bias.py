
import gzip
import json
import csv
import os
import requests

INPUT_FILE = "data/external_human_dataset/human-preference-alignment.jsonl.gz"
OUTPUT_FILE = "data/external_human_dataset/controlled_position_bias_results.csv"

MODEL = "llama3.2:3b"
LIMIT = 145
TEMPERATURE = 0
SEED = 42

FIELDNAMES = [
    "task_id",
    "original_choice",
    "reversed_raw_choice",
    "reversed_normalized_choice",
    "preference_changed",
    "first_position_selections",
    "status"
]


def judge_pair(instruction, code_a, code_b):

    prompt = f"""
You are an independent code evaluation judge.

Compare two Python code solutions for the same programming task.

Evaluate:
1. Correctness
2. Efficiency
3. Readability
4. Security

Task:
{instruction}

CODE A:
{code_a}

CODE B:
{code_b}

Choose the better solution based on code quality.
Do not prefer a solution merely because it appears first,
is longer, or contains more comments.

If both solutions are equally good, choose Tie.

Return only valid JSON:
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
            "keep_alive": "5m",
            "options": {
                "temperature": TEMPERATURE,
                "seed": SEED
            }
        },
        timeout=300
    )

    response.raise_for_status()

    result = json.loads(response.json()["response"])

    choice = result.get("choice", "").strip().upper()

    if choice not in ["A", "B", "TIE"]:
        raise ValueError(f"Invalid choice returned: {choice}")

    if choice == "TIE":
        choice = "Tie"

    return choice


def main():

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with gzip.open(INPUT_FILE, "rt", encoding="utf-8") as file:
        records = [json.loads(line) for line in file]

    records = records[:LIMIT]

    # Create CSV header if necessary
    if not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()

    # Resume completed pairs
    completed = set()

    with open(OUTPUT_FILE, "r", newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            if row["status"] == "SUCCESS":
                completed.add(row["task_id"])

    print(f"Dataset records: {len(records)}")
    print(f"Already completed: {len(completed)}")
    print(f"Remaining pairs: {len(records) - len(completed)}")
    print(f"Expected LLM calls remaining: {(len(records) - len(completed)) * 2}")
    print(f"Temperature: {TEMPERATURE}")
    print(f"Seed: {SEED}")

    for index, record in enumerate(records, start=1):

        task_id = record["task_id"]

        if task_id in completed:
            print(f"[{index}/{len(records)}] Skipping {task_id}")
            continue

        print(f"\n[{index}/{len(records)}] Evaluating {task_id}")

        try:
            original_choice = judge_pair(
                record["instruction"],
                record["choices"][0],
                record["choices"][1]
            )

            print(f"Original order choice: {original_choice}")

            reversed_raw_choice = judge_pair(
                record["instruction"],
                record["choices"][1],
                record["choices"][0]
            )

            print(f"Reversed order raw choice: {reversed_raw_choice}")

            # Convert reversed decision to original code identity
            if reversed_raw_choice == "A":
                reversed_normalized = "B"
            elif reversed_raw_choice == "B":
                reversed_normalized = "A"
            else:
                reversed_normalized = "Tie"

            changed = original_choice != reversed_normalized

            # Count first-position selections across both calls
            first_position_selections = (
                (1 if original_choice == "A" else 0) +
                (1 if reversed_raw_choice == "A" else 0)
            )

            status = "SUCCESS"

            print(f"Normalized reversed choice: {reversed_normalized}")
            print(f"Preference changed: {changed}")

        except Exception as error:

            original_choice = ""
            reversed_raw_choice = ""
            reversed_normalized = ""
            changed = ""
            first_position_selections = ""
            status = "ERROR"

            print(f"Error: {error}")

        row = {
            "task_id": task_id,
            "original_choice": original_choice,
            "reversed_raw_choice": reversed_raw_choice,
            "reversed_normalized_choice": reversed_normalized,
            "preference_changed": changed,
            "first_position_selections": first_position_selections,
            "status": status
        }

        # Save each completed pair immediately
        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writerow(row)
            file.flush()
            os.fsync(file.fileno())

        if status == "SUCCESS":
            completed.add(task_id)

        print(f"Saved: {task_id} ({status})")

    print("\nCONTROLLED POSITION EXPERIMENT FINISHED")
    print(f"Successful pairs: {len(completed)}/{len(records)}")
    print(f"Results: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
