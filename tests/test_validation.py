"""Unit tests for Python code validation and C-language rejection."""

import unittest
from evaluator import validate_python_code, evaluate_submission


class TestPythonCodeValidation(unittest.TestCase):
    """Test suite ensuring that only valid Python code is audited."""

    def test_rejects_empty_and_whitespace(self):
        valid, msg = validate_python_code("")
        self.assertFalse(valid)
        self.assertIn("empty", msg.lower())

        valid, msg = validate_python_code("   \n\t  ")
        self.assertFalse(valid)
        self.assertIn("empty", msg.lower())

    def test_rejects_bare_identifier_and_literals(self):
        """Ensure gibberish like 'abcd' or isolated numbers are rejected."""
        valid, msg = validate_python_code("abcd")
        self.assertFalse(valid)
        self.assertIn("bare identifier", msg.lower())

        valid, msg = validate_python_code("12345")
        self.assertFalse(valid)
        self.assertIn("bare identifier or literal", msg.lower())

    def test_rejects_c_and_cpp_code(self):
        """Ensure C and C++ snippets are strictly rejected."""
        c_samples = [
            "#include <stdio.h>\nint main() { printf(\"Hello\"); return 0; }",
            "#include <iostream>\nusing namespace std;\nint main() { cout << \"hi\"; return 0; }",
            "int main() {\n    int x = 10;\n    return 0;\n}",
            "void solve() {\n    printf(\"%d\", 42);\n}",
            "int a = 5;\nfloat b = 3.14;",
            "for(int i = 0; i < 10; i++) { printf(\"%d\", i); }",
            "#define MAX_LEN 100",
            "char *str = malloc(50);",
        ]
        for sample in c_samples:
            valid, msg = validate_python_code(sample)
            self.assertFalse(valid, f"Should have rejected C code: {sample[:30]}")
            self.assertTrue(
                "non-python" in msg.lower() or "syntax error" in msg.lower(),
                f"Expected rejection reason but got: {msg}",
            )

    def test_rejects_syntax_errors(self):
        """Ensure broken Python syntax is flagged."""
        broken_python = [
            "def broken_fn(:",
            "if x == 5",
            "for i in [1, 2, 3]\nprint(i)",
        ]
        for sample in broken_python:
            valid, msg = validate_python_code(sample)
            self.assertFalse(valid)
            self.assertIn("syntax error", msg.lower())

    def test_accepts_valid_python(self):
        """Ensure valid Python implementations are accepted."""
        valid_python = [
            "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True",
            "def calculate_grade(marks):\n    if marks >= 90: return 'A'\n    elif marks >= 80: return 'B'\n    return 'F'",
            "numbers = [1, 2, 3, 4, 5]\nsquares = [x**2 for x in numbers]\nprint(squares)",
            "class Student:\n    def __init__(self, name):\n        self.name = name",
            "Certainly! Here is the solution:\n```python\ndef add(a, b):\n    return a + b\n```\nHope that helps!",
        ]
        for sample in valid_python:
            valid, msg = validate_python_code(sample)
            self.assertTrue(valid, f"Failed on valid Python: {sample[:30]} with msg: {msg}")
            self.assertEqual(msg, "")


class TestEvaluatorRejection(unittest.TestCase):
    """Test deterministic rejection scoring without calling LLM."""

    def test_evaluate_submission_rejects_abcd(self):
        result, scores, overall = evaluate_submission("student grade calculator", "abcd")
        self.assertEqual(scores["correctness"], 1)
        self.assertEqual(scores["security"], 1)
        self.assertEqual(scores["readability"], 1)
        self.assertEqual(scores["efficiency"], 1)
        self.assertEqual(overall, 1.0)
        self.assertIn("REJECTED", result["correctness"]["explanation"])

    def test_evaluate_submission_rejects_c_code(self):
        c_code = '#include <stdio.h>\nint main() { printf("Hello"); return 0; }'
        result, scores, overall = evaluate_submission("print hello", c_code)
        self.assertEqual(scores["correctness"], 1)
        self.assertEqual(overall, 1.0)
        self.assertIn("REJECTED", result["correctness"]["explanation"])
        self.assertIn("Non-Python", result["correctness"]["explanation"])


if __name__ == "__main__":
    unittest.main()

