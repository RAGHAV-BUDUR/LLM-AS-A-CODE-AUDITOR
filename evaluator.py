"""Automated Python Code Evaluation using LLM-as-a-Judge.

Exclusively audits Python code across four core dimensions:
Correctness, Security, Readability, and Efficiency.
"""

from __future__ import annotations

import ast
import csv
import json
import os
import re

INPUT_FILE = "data/submissions.csv"
OUTPUT_FILE = "data/evaluation_results.csv"

DEFAULT_JUDGE_MODEL = "llama3.2:3b"

DIMENSIONS = [
    "correctness",
    "security",
    "readability",
    "efficiency",
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
    "error",
]


def extract_python_code(text: str) -> str:
    """Extract code from markdown code fences if present; otherwise return stripped text."""
    if not text:
        return ""
    clean = text.strip()
    match = re.search(r"```(?:python)?\s*\n?(.*?)\n?```", clean, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return clean


def validate_python_code(code: str) -> tuple[bool, str]:
    """Validate that the submitted snippet is strictly valid, non-trivial Python code.

    Rejects C/C++, other non-Python languages, syntax errors, and empty/meaningless inputs.
    Extracts code from markdown blocks if conversational markdown wrapper text is provided.
    Returns:
        (is_valid, error_message)
    """
    if not code or not code.strip():
        return False, "Code snippet is empty. Please submit a valid Python implementation."

    clean = extract_python_code(code)

    # 1. Explicit C / C++ pattern detection
    c_patterns = [
        (r'#\s*include\s*[<\"].*?[>\"]', "C/C++ preprocessor directive (#include)"),
        (r'#\s*define\s+\w+', "C/C++ macro definition (#define)"),
        (r'\b(int|void|char|double|float|long|unsigned)\s+main\s*\(', "C/C++ main() function"),
        (r'\b(int|void|char|double|float|long|unsigned)\s+\*+\w+', "C/C++ pointer declaration"),
        (r'\bprintf\s*\(', "C standard library printf()"),
        (r'\bscanf\s*\(', "C standard library scanf()"),
        (r'\bstd::(cout|cin|endl|string|vector)\b', "C++ standard library namespace (std::)"),
        (r'\bcout\s*<<', "C++ stream output (cout <<)"),
        (r'\bcin\s*>>', "C++ stream input (cin >>)"),
        (r'\b(malloc|calloc|free)\s*\(', "C dynamic memory allocation (malloc/free)"),
        (r'\b(struct|union|typedef)\s+\w+\s*\{', "C struct/typedef definition"),
        (r'(\bint|\bfloat|\bdouble|\bchar)\s+\w+\s*(=|;|,)', "C/C++ static type variable declaration"),
        (r'\bfor\s*\(\s*(int\s+)?\w+\s*=\s*\d+;', "C-style for loop"),
    ]
    for pattern, desc in c_patterns:
        if re.search(pattern, clean, re.IGNORECASE):
            return False, f"Non-Python code detected ({desc}). This auditor strictly evaluates Python programs only."

    # 2. Syntax validation via Python's AST parser
    try:
        tree = ast.parse(clean)
    except SyntaxError as exc:
        line_info = f" at line {exc.lineno}" if exc.lineno else ""
        return False, f"Syntax error in Python code{line_info}: {exc.msg}. Please provide syntactically valid Python."

    # 3. Check for meaningful Python executable structures
    # Disallow bare identifiers (e.g. 'abcd') or isolated literals ('123')
    meaningful_nodes = (
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
        ast.Assign,
        ast.AnnAssign,
        ast.AugAssign,
        ast.For,
        ast.While,
        ast.If,
        ast.With,
        ast.Try,
        ast.Import,
        ast.ImportFrom,
        ast.Return,
        ast.Call,
        ast.Yield,
        ast.YieldFrom,
        ast.Assert,
    )
    has_meaningful = any(isinstance(node, meaningful_nodes) for node in ast.walk(tree))

    if not has_meaningful:
        if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
            val = tree.body[0].value
            if isinstance(val, (ast.Name, ast.Constant)):
                return (
                    False,
                    f"Non-functional input: '{clean}' is only a bare identifier or literal with no executable logic.",
                )
        return False, "Submitted snippet does not contain functional Python definitions or statements."

    return True, ""


def evaluate_submission(
    problem: str,
    code: str,
    judge_model: str | None = None,
    strict_raise: bool = False,
) -> tuple[dict, dict[str, int | float], float]:
    """Evaluate submitted code against the problem requirements.

    First verifies code is genuine Python. If invalid (e.g. C code or gibberish),
    deterministically assigns a rejection score of 1/10 across all dimensions to prevent
    hallucination and model complacency bias.
    """
    model = judge_model or DEFAULT_JUDGE_MODEL

    # Extract clean python code if wrapped in markdown explanations
    clean_code = extract_python_code(code)

    # Pre-validation for Python-only constraint
    is_valid, validation_error = validate_python_code(clean_code)
    if not is_valid:
        if strict_raise:
            raise ValueError(validation_error)

        rejection_result = {
            "correctness": {
                "score": 1,
                "explanation": f"REJECTED: {validation_error}",
            },
            "security": {
                "score": 1,
                "explanation": "Security cannot be audited on invalid, non-executable, or non-Python code.",
            },
            "readability": {
                "score": 1,
                "explanation": "Code lacks valid Python syntax or recognizable structure.",
            },
            "efficiency": {
                "score": 1,
                "explanation": "Algorithmic efficiency cannot be assessed on non-Python or non-functional input.",
            },
        }
        rejection_scores = {dim: 1 for dim in DIMENSIONS}
        return rejection_result, rejection_scores, 1.0

    prompt = f"""You are an expert, objective Python code auditor.

Evaluate the submitted Python code across four core dimensions:

1. Correctness (1 to 10):
- Does the code strictly solve the problem requirements?
- Score 1-3 if the solution fails requirements, has fatal logic/runtime errors, or is incomplete.
- Score 4-7 if it works partially or misses critical edge cases.
- Score 8-10 only if it completely and correctly satisfies the requirements.

2. Security (1 to 10):
- Does the code avoid security vulnerabilities, injection risks, and unhandled exceptions on invalid input?
- Do not invent non-existent vulnerabilities. Score 8-10 for standard, clean Python logic.

3. Readability (1 to 10):
- Is the code readable, idiomatic Python (PEP 8), with clear naming and structure?

4. Efficiency (1 to 10):
- Is the time and space complexity optimal for the problem?

RULES:
- Evaluate strictly against the given problem requirements.
- The submitted code must be valid Python. Do NOT award high scores (8-10) to placeholder, incomplete, or non-functional code.
- Be rigorous and objective. Avoid complacency bias or leniency bias.
- Provide a clear, honest explanation for every score.
- Scores must be integers between 1 and 10.
- Return valid JSON only.

PROBLEM:
{problem}

SUBMITTED PYTHON CODE:
{clean_code}

Return this JSON structure:
{{
  "correctness": {{
    "score": 1,
    "explanation": "Detailed explanation of correctness"
  }},
  "security": {{
    "score": 1,
    "explanation": "Detailed explanation of security"
  }},
  "readability": {{
    "score": 1,
    "explanation": "Detailed explanation of readability"
  }},
  "efficiency": {{
    "score": 1,
    "explanation": "Detailed explanation of efficiency"
  }}
}}
"""

    try:
        import ollama
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            keep_alive=0,
        )
        content = response["message"]["content"]
        result = json.loads(content)
    except Exception as exc:
        raise RuntimeError(f"Ollama inference error with model '{model}': {exc}") from exc

    scores: dict[str, int | float] = {}
    for dimension in DIMENSIONS:
        if dimension not in result or "score" not in result[dimension]:
            raise ValueError(f"Judge output missing dimension or score: '{dimension}'")

        score = result[dimension]["score"]
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError(f"Invalid non-numeric score for {dimension}: {score}")

        score_val = int(round(score))
        if not 1 <= score_val <= 10:
            raise ValueError(f"Score out of range [1-10] for {dimension}: {score_val}")

        scores[dimension] = score_val

    overall = round(sum(scores.values()) / len(DIMENSIONS), 2)
    return result, scores, overall


def main():
    if not os.path.exists(INPUT_FILE):
        print("Submission dataset not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as file:
        submissions = list(csv.DictReader(file))

    if not submissions:
        print("No submissions found!")
        return

    completed_ids = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                if row.get("status") == "success":
                    completed_ids.add(row["submission_id"])

    new_file = not os.path.exists(OUTPUT_FILE)
    completed_count = len(completed_ids)

    print("=" * 55)
    print("       AUTOMATED CODE EVALUATION SYSTEM")
    print(f"       Judge Model: {DEFAULT_JUDGE_MODEL}")
    print("=" * 55)

    with open(OUTPUT_FILE, "a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()

        for index, submission in enumerate(submissions, start=1):
            submission_id = submission["submission_id"]
            if submission_id in completed_ids:
                print(f"\nSkipping {submission_id} - already evaluated")
                continue

            print(f"\n[{index}/{len(submissions)}] Evaluating {submission_id}...")

            row = {
                "submission_id": submission_id,
                "problem_id": submission["problem_id"],
                "problem_description": submission["problem_description"],
                "generator_model": submission.get("model", ""),
                "judge_model": DEFAULT_JUDGE_MODEL,
                "status": "error",
                "error": "",
            }

            try:
                result, scores, overall = evaluate_submission(
                    submission["problem_description"],
                    submission["code"],
                    judge_model=DEFAULT_JUDGE_MODEL,
                )

                for dimension in DIMENSIONS:
                    row[dimension] = scores[dimension]
                    row[f"{dimension}_explanation"] = result[dimension]["explanation"]

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
