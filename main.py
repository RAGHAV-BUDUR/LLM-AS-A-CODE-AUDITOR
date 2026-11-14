"""Main CLI interface for LLM-Based Automated Python Code Auditing.

Supports interactive prompts as well as CLI arguments to specify problem,
code file, generator model, and judge model.
Strictly audits Python code and rejects non-Python (e.g. C/C++) submissions.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from evaluator import evaluate_submission, extract_python_code, validate_python_code

DEFAULT_GENERATOR_MODEL = "qwen2.5-coder:3b"
DEFAULT_JUDGE_MODEL = "llama3.2:3b"


def generate_code(problem: str, model: str = DEFAULT_GENERATOR_MODEL) -> str:
    """Generate Python code using the specified generator model."""
    print(f"\n[1] Generating Python code using {model}...\n")
    try:
        import ollama
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Python programming assistant. Generate correct, simple, "
                        "and well-structured Python code. Return executable Python code inside a "
                        "```python code block."
                    ),
                },
                {"role": "user", "content": problem},
            ],
            keep_alive=0,
        )
        content = response["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"Ollama generation failed with model '{model}': {exc}") from exc

    return content


def evaluate_code(
    problem: str, code: str, judge_model: str = DEFAULT_JUDGE_MODEL
) -> tuple[dict, dict[str, int | float], float]:
    """Audit submitted Python code using the specified judge model."""
    print(f"\n[2] Evaluating code using {judge_model}...\n")
    return evaluate_submission(problem, code, judge_model=judge_model)


def main():
    parser = argparse.ArgumentParser(
        description="LLM-Based Automated Python Code Auditor",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--problem",
        "-p",
        type=str,
        help="Programming problem description to evaluate",
    )
    parser.add_argument(
        "--code",
        "-c",
        type=str,
        help="Python code string to audit directly (skips generation)",
    )
    parser.add_argument(
        "--code-file",
        "-f",
        type=Path,
        help="Path to file containing Python code to audit",
    )
    parser.add_argument(
        "--generator-model",
        type=str,
        default=DEFAULT_GENERATOR_MODEL,
        help="Model used for code generation",
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        default=DEFAULT_JUDGE_MODEL,
        help="Model used as LLM-as-a-Judge",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("       LLM-BASED AUTOMATED PYTHON CODE AUDITOR")
    print(f"       Generator: {args.generator_model} | Judge: {args.judge_model}")
    print("=" * 60)

    problem = args.problem
    if not problem:
        problem = input("\nEnter your programming problem: ").strip()

    if not problem:
        print("Error: Problem description cannot be empty.")
        sys.exit(1)

    code_to_audit = ""
    if args.code:
        code_to_audit = args.code
    elif args.code_file:
        if not args.code_file.is_file():
            print(f"Error: File '{args.code_file}' does not exist.")
            sys.exit(1)
        code_to_audit = args.code_file.read_text(encoding="utf-8")
    else:
        raw_generated = generate_code(problem, model=args.generator_model)
        print("\n========== GENERATED CODE ==========\n")
        print(raw_generated)
        code_to_audit = extract_python_code(raw_generated)

    # Validate Python code before auditing
    is_valid, validation_msg = validate_python_code(code_to_audit)
    if not is_valid:
        print("\n[!] Python Language Validation Notice:")
        print(f"    {validation_msg}")

    # Evaluate code
    result, scores, overall = evaluate_code(
        problem, code_to_audit, judge_model=args.judge_model
    )

    print("\n========== AI JUDGE EVALUATION ==========\n")
    print(json.dumps(result, indent=2))
    print(f"\nOverall Score: {overall}/10")
    print("\n========== AUDIT COMPLETED ==========")


if __name__ == "__main__":
    main()
