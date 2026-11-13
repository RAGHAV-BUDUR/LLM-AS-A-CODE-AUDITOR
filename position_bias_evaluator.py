
import gzip
import json
import csv
import os
import requests

INPUT_FILE = "data/external_human_dataset/human-preference-alignment.jsonl.gz"
BASELINE_FILE = "data/external_human_dataset/llm_pairwise_results.csv"
OUTPUT_FILE = "data/external_human_dataset/position_bias_results.csv"

MODEL = "llama3.2:3b"

FIELDNAMES = [
    "task_id",
    "original_choice",
    "reversed_raw_choice",
    "reversed_normalized_choice",
    "preference_changed",
    "status"
]


def judge_reversed_pair(record):

    prompt = f"""
You are an independent code evaluation judge.

Compare two Python code solutions for the programming task.

Evaluate:
1. Correctness
2. Efficiency
3. Readability
4. Security

Task:
{record['instruction']}

CODE A:
{record['choices'][1]}

CODE B:
{record['choices'][0]}

Choose the better solution.
Do not prefer longer code or more comments.
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

    return choice


def main():

    # Load original LLM decisions
    original_results = {}

    with open(BASELINE_FILE, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["status"] == "SUCCESS":
                original_results[row["task_id"]] = row["llm_choice"]

    # Load original dataset
    with gzip.open(INPUT_FILE, "rt", encoding="utf-8") as file:
        records = [json.loads(line) for line in file]

    # Create output file if it does not exist
    if not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()

    # Read already completed comparisons
    completed = set()

    with open(OUTPUT_FILE, "r", newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            if row["status"] == "SUCCESS":
                completed.add(row["task_id"])

    print(f"Original decisions loaded: {len(original_results)}")
    print(f"Already reversed: {len(completed)}")
    print(f"Remaining: {len(records) - len(completed)}")

    for index, record in enumerate(records, start=1):

        task_id = record["task_id"]

        if task_id not in original_results:
            continue

        if task_id in completed:
            print(f"Skipping {task_id} - already completed")
            continue

        print(f"\n[{index}/{len(records)}] Reversing {task_id}")

        original_choice = original_results[task_id]

        try:
            reversed_raw = judge_reversed_pair(record)

            # Convert reversed decision back to original A/B orientation
            if reversed_raw == "A":
                normalized = "B"
            elif reversed_raw == "B":
                normalized = "A"
            else:
                normalized = "Tie"

            changed = normalized != original_choice
            status = "SUCCESS"

            print(f"Original choice: {original_choice}")
            print(f"Reversed raw choice: {reversed_raw}")
            print(f"Normalized choice: {normalized}")
            print(f"Preference changed: {changed}")

        except Exception as error:
            reversed_raw = ""
            normalized = ""
            changed = ""
            status = "ERROR"

            print(f"Error: {error}")

        row = {
            "task_id": task_id,
            "original_choice": original_choice,
            "reversed_raw_choice": reversed_raw,
            "reversed_normalized_choice": normalized,
            "preference_changed": changed,
            "status": status
        }

        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writerow(row)
            file.flush()

        if status == "SUCCESS":
            completed.add(task_id)

        print(f"Saved: {task_id} ({status})")

    print("\nPOSITION BIAS EXPERIMENT FINISHED")
    print(f"Successful comparisons: {len(completed)}")
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
