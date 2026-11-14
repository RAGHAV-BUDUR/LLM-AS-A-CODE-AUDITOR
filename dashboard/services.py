"""Data and integration helpers for the research demonstration dashboard."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DIMENSIONS = ("correctness", "security", "readability", "efficiency")


def read_csv(name: str) -> pd.DataFrame:
    """Read a project CSV without failing when a result is not present yet."""
    path = DATA / name
    if not path.is_file():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except (OSError, pd.errors.ParserError, UnicodeError):
        return pd.DataFrame()


def available_models() -> list[str]:
    """Return local Ollama model names, or an empty list if Ollama is down."""
    import ollama

    response = ollama.list()
    model_items = response.get("models", []) if isinstance(response, dict) else getattr(response, "models", [])
    names = []
    for item in model_items:
        if isinstance(item, dict):
            name = item.get("model") or item.get("name")
        else:
            name = getattr(item, "model", None) or getattr(item, "name", None)
        if name:
            names.append(name)
    return sorted(set(names))


def evaluate_live(problem: str, code: str, model: str) -> dict:
    """Reuse the established evaluator and retain its verified result separately."""
    if not problem.strip() or not code.strip():
        raise ValueError("Enter both a task description and Python code.")
    sys.path.insert(0, str(ROOT))
    from evaluator import evaluate_submission, validate_python_code

    is_valid, validation_msg = validate_python_code(code)
    result, scores, overall = evaluate_submission(problem.strip(), code, model)
    record = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "judge_model": model,
        "problem": problem.strip(),
        "code": code,
        "is_valid_python": is_valid,
        "validation_message": validation_msg,
        **{key: {"score": scores[key], "explanation": result[key]["explanation"]}
           for key in DIMENSIONS},
        "overall_score": overall,
    }
    path = DATA / "live_evaluations" / "evaluations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def matching_tasks() -> pd.DataFrame:
    questions = read_csv("questions.csv")
    return questions if {"problem_id", "problem_description"}.issubset(questions.columns) else pd.DataFrame()


def _extract_function(code: str, allowed_names: list[str]) -> tuple[str, str]:
    tree = ast.parse(code)
    funcs = {
        node.name: node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    name = next((candidate for candidate in allowed_names if candidate in funcs), None)
    if not name:
        raise ValueError("No expected function was found for this task.")

    required = set()
    pending = [name]
    while pending:
        current = pending.pop()
        if current in required or current not in funcs:
            continue
        required.add(current)
        for node in ast.walk(funcs[current]):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in funcs:
                pending.append(node.id)

    nodes = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    nodes.extend(funcs[n] for n in funcs if n in required)
    return ast.unparse(ast.Module(body=nodes, type_ignores=[])), name


def _run_case(clean_code: str, function_name: str, args: tuple, timeout: int = 3):
    """Run one testcase in a temporary, restricted-environment subprocess.

    This limits accidental damage but is not a hardened security sandbox.
    """
    worker = (
        "import json\n" + clean_code + "\n"
        + f"_result = {function_name}(*{args!r})\n"
        + "print('__DASHBOARD_RESULT__' + json.dumps(_result))\n"
    )
    environment = {
        key: os.environ[key]
        for key in ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP")
        if key in os.environ
    }
    with tempfile.TemporaryDirectory(prefix="code-audit-") as cwd:
        process = subprocess.run(
            [sys.executable, "-I", "-S", "-c", worker],
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    if process.returncode:
        raise RuntimeError((process.stderr or "Process exited with an error")[-2000:])
    lines = [line for line in process.stdout.splitlines() if line.startswith("__DASHBOARD_RESULT__")]
    if not lines:
        raise ValueError("Function did not return a JSON-serializable result.")
    return json.loads(lines[-1].removeprefix("__DASHBOARD_RESULT__"))


def run_functional(problem_id: str, code: str) -> list[dict]:
    """Run configured tests for a known task; return one transparent row per test."""
    if not code.strip():
        raise ValueError("Paste Python code before running tests.")
    sys.path.insert(0, str(ROOT))
    from benchmark_config import FUNCTION_MAP
    from test_cases import TEST_CASES

    if problem_id not in TEST_CASES or problem_id not in FUNCTION_MAP:
        return []
    clean_code, function_name = _extract_function(code, FUNCTION_MAP[problem_id])
    outcomes = []
    for index, case in enumerate(TEST_CASES[problem_id], start=1):
        args, expected = case[:-1], case[-1]
        try:
            actual = _run_case(clean_code, function_name, args)
            # Follow existing benchmark conventions for order-insensitive duplicates.
            if problem_id == "P07" and isinstance(actual, list):
                actual = sorted(actual)
            if problem_id == "P20" and isinstance(actual, str):
                if actual == "Password is strong.":
                    actual = True
                elif actual.startswith("Password "):
                    actual = False
                else:
                    raise ValueError("Unsupported P20 return format")
            passed = actual == expected
            outcomes.append({"test": index, "inputs": repr(args), "expected": repr(expected),
                             "actual": repr(actual), "outcome": "PASSED" if passed else "INCORRECT_OUTPUT",
                             "detail": "" if passed else "Returned value differs from expected output."})
        except subprocess.TimeoutExpired:
            outcomes.append({"test": index, "inputs": repr(args), "expected": repr(expected),
                             "actual": "", "outcome": "TIMEOUT", "detail": "Exceeded 3-second limit."})
        except Exception as exc:
            outcomes.append({"test": index, "inputs": repr(args), "expected": repr(expected),
                             "actual": "", "outcome": "ERROR", "detail": str(exc)[:1000]})
    return outcomes

