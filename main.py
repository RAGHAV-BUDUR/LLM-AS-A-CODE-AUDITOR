
import ollama

GENERATOR_MODEL = "qwen2.5-coder:3b"
JUDGE_MODEL = "llama3.2:3b"


def generate_code(problem):

    print("\n[1] Generating code using Qwen...\n")

    response = ollama.chat(
        model=GENERATOR_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a Python programming assistant. Generate correct, simple Python code. Return the code and a short explanation."
            },
            {
                "role": "user",
                "content": problem
            }
        ],
        keep_alive=0
    )

    return response["message"]["content"]


import json
import ollama


def evaluate_code(problem, code):

    print("\n[2] Evaluating code using Llama...\n")

    prompt = f"""
You are an expert Python code auditor.

Evaluate the submitted code using these dimensions:

1. Correctness: 1 to 10
2. Security: 1 to 10
3. Readability: 1 to 10
4. Efficiency: 1 to 10

Rules:
- Evaluate only against the given problem requirements.
- Do not penalize features that were not requested.
- Explain every score.
- Do not invent security vulnerabilities.
- Return valid JSON only.
- Scores must be integers between 1 and 10.

PROBLEM:
{problem}

CODE:
{code}

Return this exact JSON structure:

{{
    "correctness": {{
        "score": 0,
        "explanation": ""
    }},
    "security": {{
        "score": 0,
        "explanation": ""
    }},
    "readability": {{
        "score": 0,
        "explanation": ""
    }},
    "efficiency": {{
        "score": 0,
        "explanation": ""
    }}
}}
"""

    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        format="json",
        keep_alive=0
    )

    result = json.loads(response["message"]["content"])

    dimensions = [
        "correctness",
        "security",
        "readability",
        "efficiency"
    ]

    scores = []

    for dimension in dimensions:

        score = result[dimension]["score"]

        if not isinstance(score, int) or not 1 <= score <= 10:
            raise ValueError(f"Invalid score for {dimension}")

        scores.append(score)

    overall = sum(scores) / len(scores)

    result["overall_score"] = round(overall, 2)

    return json.dumps(result, indent=4)



def main():

    print("=" * 55)
    print("       LLM-BASED AUTOMATED CODE AUDITOR")
    print("=" * 55)

    problem = input("\nEnter your programming problem: ")

    if not problem.strip():
        print("Please enter a valid programming problem.")
        return

    # Generate code
    generated_code = generate_code(problem)

    print("\n========== GENERATED CODE ==========\n")
    print(generated_code)

    # Evaluate code
    evaluation = evaluate_code(problem, generated_code)

    print("\n========== AI JUDGE EVALUATION ==========\n")
    print(evaluation)

    print("\n========== AUDIT COMPLETED ==========")


if __name__ == "__main__":
    main()
