# LLM-as-a-Code-Auditor: In-Depth Technical & Syllabus-Aligned Architectural Report

## Executive Summary & System Overview

**LLM-as-a-Code-Auditor** is an end-to-end applied Generative AI system that implements and evaluates **LLM-as-a-Judge** architectures for automated Python software auditing. 

In automated code generation, traditional compiler passes and linters verify syntactic validity but fail to evaluate semantic design intent, algorithmic complexity, maintainability, and subtle security risks. Conversely, human peer review is slow and cost-prohibitive. This project builds a dual-model pipeline using locally hosted open-weights Large Language Models via Ollama to automate multidimensional code evaluation across:
1. **Correctness** (1–10)
2. **Security** (1–10)
3. **Readability** (1–10)
4. **Efficiency** (1–10)

Crucially, the project does not blindly trust the LLM judge. It treats the judge itself as an experimental subject, benchmarking its scores against:
- **Deterministic ground-truth unit test suites** executed inside isolated subprocess environments.
- **Empirical bias detection frameworks** measuring position bias, verbosity bias, and self-enhancement bias.
- **Syntactic AST validation guards** that prevent LLM hallucination on non-Python or malformed code.

---

## 1. Syllabus Mapping: Concepts Applied in This Project

| Syllabus Unit | Core Theoretical Concepts | Concrete Implementation in This Project |
| :--- | :--- | :--- |
| **Unit 1: Foundations of GenAI & Prompting** | • Decoder-only LLMs<br>• Contextual Embeddings & BPE<br>• Landscape: Llama 3.2 & Qwen 2.5 Coder<br>• Prompt Anatomy (Instructions, Context, Input, Indicators)<br>• Prompting Techniques: Role Prompting, Zero-Shot, Chain-of-Thought (CoT) | • **Dual-LLM deployment** via Ollama: `qwen2.5-coder:3b` (generation specialist) and `llama3.2:3b` (evaluator judge).<br>• **Role Prompting**: System roles defining "Python programming assistant" vs. "independent Python code auditor".<br>• **Prompt Anatomy**: Carefully delimited Problem, Instructions, Target Code, and Output format specifications in `main.py` and `evaluator.py`. |
| **Unit 2: Practical Prompting & Structured Generation** | • Structured Output (JSON, Lists, CSV)<br>• Output parsers & JSON Schema enforcement<br>• Prompt Chaining & Pipeline workflows<br>• Prompting tactics & Classification / Scoring | • **Constrained JSON Generation**: Using Ollama's `format="json"` API enforce strict key-value JSON schema.<br>• **Defensive Schema Parsing**: In-code numeric type guards, range validation `[1, 10]`, and fallback parsers.<br>• **Prompt Chaining**: `Problem -> Generator LLM -> Code Extractor -> Pre-Validation -> Judge LLM -> Aggregator -> Telemetry/JSONL`.<br>• **CSV Data Pipelines**: Ingestion of `questions.csv`, generation of `submissions.csv`, and logging to `evaluation_results.csv`. |
| **Unit 3: Autonomous Agents, Frameworks & Prompt Optimization** | • Agents with tools and execution environments<br>• Programmatic prompt optimization<br>• Iterative refinement & feedback loops<br>• Guardrails and evaluation frameworks | • **Tool & Environment Execution**: `universal_test_runner.py` and `dashboard/services.py` act as sandboxed execution tools executing generated code against test cases.<br>• **Iterative Prompt Refinement**: Removal of positive anchoring bias (`"score": 8` template bug) through empirical error analysis.<br>• **Evaluation Benchmark**: Systematic framework comparing LLM scores with ground truth unit tests. |
| **Unit 4: Building AI-Powered Applications** | • Building full-stack AI-powered applications<br>• Interactive web interfaces<br>• Defensive engineering against jailbreaks / invalid inputs<br>• Subprocess execution and local model orchestration | • **Full-Stack Streamlit Dashboard** (`dashboard/app.py` & `services.py`) with reactive components, real-time Ollama health checks, and visual metric cards.<br>• **AST-level Pre-validation Guards**: Multi-stage regex and Abstract Syntax Tree filtering against foreign languages (C/C++) and gibberish. |

---

## 2. End-to-End System Architecture & Data Flow

The system operates across three tiers: User Interfaces, Orchestration / Evaluation Core, and Local Inference Engine.

```mermaid
flowchart TD
    User([User / Developer]) -->|Interactive Query| CLI[main.py CLI Interface]
    User -->|Web Interaction| Streamlit[Streamlit UI - dashboard/app.py]
    
    subgraph Core_Pipeline [Orchestration & Validation Engine]
        CLI --> GenDispatch[generator.py / generate_code]
        Streamlit --> LiveEval[dashboard/services.py: evaluate_live]
        
        GenDispatch -->|Prompt with Role & Problem| GenModel[Qwen 2.5 Coder 3B]
        GenModel -->|Raw Markdown Output| Extractor[extract_python_code]
        
        Extractor --> ASTVal[validate_python_code AST Guard]
        LiveEval --> ASTVal
        
        ASTVal -->|Invalid: C/C++ or Gibberish| DeterministicReject[Deterministic Rejection: 1/10 across all metrics]
        ASTVal -->|Valid Python Code| JudgeDispatch[evaluator.py: evaluate_submission]
        
        JudgeDispatch -->|Hardened Prompt + Structured JSON| JudgeModel[Llama 3.2 3B Judge]
        JudgeModel -->|Structured JSON Output| JSONParser[Type & Range Validator]
    end

    subgraph Ground_Truth [Deterministic Verification]
        Streamlit -->|Run Tests| TestRunner[services.py: run_functional]
        TestRunner --> SubprocessEnv[Isolated Python Subprocess -I -S]
        SubprocessEnv --> TestCases[(test_cases.py: Test Suites)]
    end

    subgraph Storage [Persistent Storage & Datasets]
        JSONParser --> LiveLogs[(data/live_evaluations/evaluations.jsonl)]
        JSONParser --> BenchCSV[(data/evaluation_results.csv)]
        DeterministicReject --> LiveLogs
    end

    JSONParser --> Streamlit
    DeterministicReject --> Streamlit
    JSONParser --> CLI
    DeterministicReject --> CLI
```

---

## 3. Detailed Component Deep-Dive & Code Snippets

### 3.1 Unit 1 & 2 Application: Role Prompting, Anatomy, and Structured JSON Output

In `evaluator.py`, the evaluation prompt implements **Role Prompting**, explicit **Rules**, and strict **Output Indicators**. 

#### Code Implementation (`evaluator.py`):
```python
def evaluate_submission(
    problem: str,
    code: str,
    judge_model: str | None = None,
    strict_raise: bool = False,
) -> tuple[dict, dict[str, int | float], float]:
    model = judge_model or DEFAULT_JUDGE_MODEL

    # Extract clean python code if wrapped in markdown explanations
    clean_code = extract_python_code(code)

    # Pre-validation for Python-only constraint
    is_valid, validation_error = validate_python_code(clean_code)
    if not is_valid:
        # Deterministic scoring prevents model hallucination on invalid code
        rejection_result = {
            "correctness": {"score": 1, "explanation": f"REJECTED: {validation_error}"},
            "security": {"score": 1, "explanation": "Security cannot be audited on invalid, non-executable, or non-Python code."},
            "readability": {"score": 1, "explanation": "Code lacks valid Python syntax or recognizable structure."},
            "efficiency": {"score": 1, "explanation": "Algorithmic efficiency cannot be assessed on non-Python or non-functional input."},
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
```

#### Why Structured JSON Parsing is Critical:
The LLM response is returned as JSON via Ollama's constrained grammar engine (`format="json"`). To guarantee defensive runtime execution, programmatic post-validation parses and asserts numerical boundaries:

```python
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
```

---

### 3.2 Unit 3 Application: Guardrails, Defense Against Leniency Bias, and Python Language Policy

A major challenge uncovered during benchmarking was **Model Hallucination and Leniency Bias**.

#### The Problem Discovered:
When tested with invalid inputs like:
- **Bare tokens:** `"abcd"`
- **C/C++ code:** `#include <stdio.h>\nint main() { printf("Hello"); return 0; }`

The unconstrained `llama3.2:3b` model previously gave `"abcd"` a **Correctness score of 8/10, Security 10/10, and Efficiency 8/10!**

#### Root Cause Analysis:
1. **Positive Numerical Anchoring:** The initial JSON example in the prompt template contained `"score": 8`. Small language models strongly anchor to template constants when inputs are ambiguous or senseless.
2. **Missing Language Boundaries:** The LLM received C code or random strings and attempted to hallucinate Python equivalents or assume functionality.

#### The Architectural Solution:
We designed an AST and Regex-based multi-tier pre-validation guardrail:

```python
def validate_python_code(code: str) -> tuple[bool, str]:
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
    meaningful_nodes = (
        ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign,
        ast.AnnAssign, ast.AugAssign, ast.For, ast.While, ast.If,
        ast.With, ast.Try, ast.Import, ast.ImportFrom, ast.Return,
        ast.Call, ast.Yield, ast.YieldFrom, ast.Assert,
    )
    has_meaningful = any(isinstance(node, meaningful_nodes) for node in ast.walk(tree))

    if not has_meaningful:
        if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
            val = tree.body[0].value
            if isinstance(val, (ast.Name, ast.Constant)):
                return False, f"Non-functional input: '{clean}' is only a bare identifier or literal with no executable logic."
        return False, "Submitted snippet does not contain functional Python definitions or statements."

    return True, ""
```

---

### 3.3 Prompt Refinement & Markdown Boundary Normalization

When using conversational code models like `qwen2.5-coder:3b`, responses contain natural language conversational wrappers:
```markdown
Certainly! Below is a simple Python code block that adds two numbers:
```python
def add_numbers(a, b):
    return a + b
```
Hope this helps!
```

If passed directly into `ast.parse()`, line 1 (`"Certainly!..."`) raises `SyntaxError: invalid syntax`, triggering a false-positive rejection.

To resolve this, we introduced regex markdown block extraction:

```python
def extract_python_code(text: str) -> str:
    """Extract code from markdown code fences if present; otherwise return stripped text."""
    if not text:
        return ""
    clean = text.strip()
    match = re.search(r"```(?:python)?\s*\n?(.*?)\n?```", clean, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return clean
```

---

### 3.4 Unit 4 Application: Sandboxed Subprocess Functional Testing

The system provides an empirical ground truth by testing candidate code against predetermined test fixtures (`test_cases.py`) inside an isolated Python subprocess without third-party network access.

```python
def _run_case(clean_code: str, function_name: str, args: tuple, timeout: int = 3):
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
```

The flags `-I` (isolated mode) and `-S` (don't import `site` packages) prevent the untrusted code from modifying user libraries or accessing ambient state.

---

## 4. Key Improvements and Iterations Log

| Stage | Observation / Vulnerability | Root Cause | Implemented Solution |
| :--- | :--- | :--- | :--- |
| **Initial Prototype** | `main.py` had hardcoded models and crashed if models weren't accessible via CLI. | Rigid programmatic constants; no CLI arguments. | Implemented `argparse` in `main.py` supporting `--problem`, `--code`, `--code-file`, `--judge-model`, and `--generator-model`. |
| **Leniency Vulnerability** | Inputting `"abcd"` yielded an **8/10 score** from Llama 3.2 3B. | Prompt template schema had `"score": 8` in the example; model anchored to default value. | Stripped numerical anchor to neutral `"score": 1`, added strict tier descriptions and AST pre-validation. |
| **Language Boundary Issue** | C code with `#include` and `int main()` was evaluated without error. | The evaluator assumed all incoming text was Python code. | Implemented `validate_python_code()` regex + AST filter to reject foreign languages. |
| **Over-strict Parsing Bug** | Model-generated valid Python code was given a **1/10 score** for `SyntaxError at line 1`. | Conversational introduction text (`"Certainly! Here is your code..."`) was parsed directly as code. | Added `extract_python_code()` regex to isolate the code payload inside fenced blocks. |
| **Testing Coverage** | No automated tests existed to verify validation boundaries. | Reliance on manual UI testing. | Added `tests/test_validation.py` running 7 test suites via `unittest`. |

---

## 5. How to Run and Verify the System

### 5.1 CLI Execution
```powershell
# Interactive mode:
python main.py

# Audit specific problem and code snippet:
python main.py --problem "Add two numbers" --code "def add_numbers(a, b): return a + b"

# Test rejection on C code:
python main.py --problem "Add two numbers" --code "#include <stdio.h>`nint main() { return 0; }"
```

### 5.2 Automated Unit Testing
```powershell
python -m unittest discover -s tests -v
```

### 5.3 Web Dashboard Launch
```powershell
python -m streamlit run dashboard/app.py
```

---

## 6. Conclusion

By combining **Foundational GenAI concepts** (Tokenization, Local Model Orchestration, Role Prompting), **Structured Output Engineering** (JSON schema validation, defensiveness), and **Application-level Guardrails** (AST checking, Subprocess sandboxing, and Bias testing), this project proves that automated LLM evaluation can be made reliable, secure, and resilient against hallucination.
