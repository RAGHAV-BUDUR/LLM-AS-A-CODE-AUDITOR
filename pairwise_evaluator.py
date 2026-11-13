
import gzip
import json
import csv
import os
import requests

INPUT_FILE = "data/external_human_dataset/human-preference-alignment.jsonl.gz"
OUTPUT_FILE = "data/external_human_dataset/llm_pairwise_results.csv"

MODEL = "llama3.2:3b"
LIMIT = 145

FIELDNAMES = [
    "task_id",
    "llm_choice",
    "llm_reason",
    "human_annotations",
    "human_gt_choice",
    "status"
]


def judge_pair(record):
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
{record['choices'][0]}

CODE B:
{record['choices'][1]}

Choose the better solution.
Do not prefer longer code or more comments.
If both are equally good, choose Tie.

Return only JSON in this format:
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
        raise ValueError(f"Invalid choice returned: {choice}")

    if choice == "TIE":
        choice = "Tie"

    return choice, result.get("reason", "")


def main():

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Load dataset
    with gzip.open(INPUT_FILE, "rt", encoding="utf-8") as file:
        records = [json.loads(line) for line in file]

    records = records[:LIMIT]

    # Create CSV header if file is missing or empty
    if not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as output:
            writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
            writer.writeheader()

    # Find already completed task IDs
    completed = set()

    with open(OUTPUT_FILE, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row.get("status") == "SUCCESS":
                completed.add(row["task_id"])

    print(f"Total dataset records: {len(records)}")
    print(f"Already completed: {len(completed)}")
    print(f"Remaining: {len(records) - len(completed)}")

    # Process and save each record immediately
    for index, record in enumerate(records, start=1):

        task_id = record["task_id"]

        if task_id in completed:
            print(f"[{index}/{len(records)}] Skipping {task_id} - already completed")
            continue

        print(f"\n[{index}/{len(records)}] Evaluating {task_id}")

        try:
            choice, reason = judge_pair(record)
            status = "SUCCESS"

            print(f"LLM choice: {choice}")

        except Exception as error:
            choice = ""
            reason = str(error)
            status = "ERROR"

            print(f"Error: {error}")

        row = {
            "task_id": task_id,
            "llm_choice": choice,
            "llm_reason": reason,
            "human_annotations": "|".join(record["annotations"]),
            "human_gt_choice": record["gt_choice"],
            "status": status
        }

        # Append instead of rewriting the entire CSV
        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
            writer.writerow(row)
            output.flush()

        if status == "SUCCESS":
            completed.add(task_id)

        print(f"Saved: {task_id} ({status})")

    print("\nPAIRWISE EVALUATION FINISHED")
    print(f"Successful comparisons: {len(completed)}/{len(records)}")
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
