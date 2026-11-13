
import csv
import ollama
import re
import os

MODEL = "qwen2.5-coder:3b"

INPUT_FILE = "data/questions.csv"
OUTPUT_FILE = "data/submissions.csv"

# Start with 2 questions for testing.
# Change to None when ready to generate all 20.
LIMIT = None

VARIATIONS = [
    "Write a simple and correct Python solution. Use clear variable names.",
    "Write an efficient Python solution with appropriate edge-case handling.",
    "Write an alternative Python solution using a different approach where possible."
]


def extract_code(response):

    match = re.search(
        r"```(?:python)?\s*(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return response.strip()


def generate_submission(problem, instruction):

    prompt = f"""
You are an expert Python programmer.

Programming problem:
{problem}

Instructions:
{instruction}

Requirements:
- Return executable Python code.
- Include necessary functions.
- Handle important edge cases.
- Do not include unnecessary explanations.
- Put the code inside a Python code block.
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        keep_alive=0
    )

    return extract_code(response["message"]["content"])


def main():

    os.makedirs("data", exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as file:
        questions = list(csv.DictReader(file))

    if LIMIT is not None:
        questions = questions[:LIMIT]

    total = len(questions) * len(VARIATIONS)
    count = 0

    file_exists = os.path.exists(OUTPUT_FILE)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "submission_id",
                "problem_id",
                "problem_description",
                "model",
                "variation",
                "code"
            ]
        )

        writer.writeheader()

        for question in questions:

            problem_id = question["problem_id"]
            problem = question["problem_description"]

            print(f"\nGenerating submissions for {problem_id}: {problem}")

            for index, instruction in enumerate(VARIATIONS, start=1):

                count += 1

                print(f"\n[{count}/{total}] Generating submission...")

                try:

                    code = generate_submission(problem, instruction)

                    writer.writerow({
                        "submission_id": f"{problem_id}_S{index}",
                        "problem_id": problem_id,
                        "problem_description": problem,
                        "model": MODEL,
                        "variation": index,
                        "code": code
                    })

                    file.flush()

                    print("Submission saved successfully!")

                except Exception as error:

                    print(f"Error generating submission: {error}")

    print("\n===================================")
    print("DATASET GENERATION COMPLETED")
    print(f"Total generated: {count}")
    print(f"Saved in: {OUTPUT_FILE}")
    print("===================================")


if __name__ == "__main__":
    main()
