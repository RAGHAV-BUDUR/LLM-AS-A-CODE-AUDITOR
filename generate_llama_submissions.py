
import csv
import os
import requests

INPUT_FILE = "data/questions.csv"
OUTPUT_FILE = "data/llama_generated_submissions.csv"

MODEL = "llama3.2:3b"

FIELDNAMES = [
    "submission_id",
    "problem_id",
    "category",
    "problem_description",
    "model",
    "code",
    "status"
]


def generate_code(problem):

    prompt = f"""
You are an expert Python programmer.

Write a complete Python solution for the following task.

Task:
{problem}

Requirements:
1. Write correct and efficient Python code.
2. Include a suitable function.
3. Handle important edge cases.
4. Use clear variable names.
5. Do not include explanations outside the code.
6. Return only executable Python code.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "seed": 42
            },
            "keep_alive": "5m"
        },
        timeout=300
    )

    response.raise_for_status()

    code = response.json()["response"].strip()

    # Remove Markdown code fences if generated
    if code.startswith("```"):
        lines = code.splitlines()

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        code = "\n".join(lines).strip()

    if not code:
        raise ValueError("Model returned empty code")

    return code


def main():

    os.makedirs("data", exist_ok=True)

    with open(INPUT_FILE, "r", newline="", encoding="utf-8-sig") as file:
        questions = list(csv.DictReader(file))

    print("Total questions:", len(questions))

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
    print("Remaining:", len(questions) - len(completed))

    for index, question in enumerate(questions, start=1):

        problem_id = question["problem_id"]

        if problem_id in completed:
            print("Skipping:", problem_id)
            continue

        print(f"\n[{index}/{len(questions)}] Generating {problem_id}")

        try:

            code = generate_code(question["problem_description"])
            status = "SUCCESS"

            print("Generated successfully")

        except Exception as error:

            print("Error:", error)
            code = ""
            status = "ERROR"

        result = {
            "submission_id": problem_id + "_LLAMA",
            "problem_id": problem_id,
            "category": question["category"],
            "problem_description": question["problem_description"],
            "model": MODEL,
            "code": code,
            "status": status
        }

        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writerow(result)
            file.flush()
            os.fsync(file.fileno())

        print("Saved:", problem_id, status)

        if status == "SUCCESS":
            completed.add(problem_id)

    print("\nLLAMA CODE GENERATION FINISHED")
    print("Successful generations:", len(completed), "/", len(questions))
    print("Saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
