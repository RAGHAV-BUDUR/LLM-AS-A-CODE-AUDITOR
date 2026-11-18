# LLM-as-a-Code-Auditor: Evaluative Benchmarking of LLM-as-a-Judge

A research project evaluating the use of Large Language Models (LLMs) as automated judges for Python code auditing.

Repository: [https://github.com/RAGHAV-BUDUR/LLM-AS-A-CODE-AUDITOR](https://github.com/RAGHAV-BUDUR/LLM-AS-A-CODE-AUDITOR)

## Project Overview

This project investigates how effectively an LLM can evaluate generated Python code across four core dimensions:

- **Correctness**
- **Security**
- **Readability**
- **Efficiency**

It compares pointwise and pairwise evaluation approaches and investigates critical evaluation biases, including position bias, verbosity bias, self-enhancement bias, and model leniency/anchoring bias.

The project also compares LLM evaluations with functional test outcomes and external human-preference annotations.

## Critical Improvements & Strict Language Enforcement

### 1. Strict Language Policy: Python Only
This tool is designed exclusively for **Python code auditing**.
- **C/C++ and Non-Python Rejection:** Submissions containing C/C++ code (e.g. `#include <stdio.h>`, `int main()`, `printf()`, `malloc()`, static type declarations, etc.) are strictly rejected.
- **AST-Based Syntax Validation:** Every submission undergoes AST parsing before reaching the model. Code containing syntax errors or non-functional gibberish (such as bare identifiers like `abcd` or lone literals) is intercepted.
- **Deterministic Rejection Scoring:** Non-Python or non-functional snippets are automatically scored **1/10** with explicit explanatory feedback, preventing LLM hallucination and wasted inference cycles.

### 2. Empirical Judge Bias Analysis: Llama vs. Qwen
During testing on edge cases (such as bare string `abcd` for a "student grade calculator" task):
- **Llama 3.2 3B Leniency & Anchoring Bias:** When unconstrained, Llama 3.2 3B exhibited severe leniency bias and anchored to few-shot prompt numbers, assigning an unjustifiable **8/10** across dimensions to non-code (`abcd`).
- **Qwen 2.5 Coder 3B Judge Performance:** When evaluated with Qwen 2.5 Coder 3B, the model correctly penalized the non-functional input, assigning **1/10**.
- **Hardened Anti-Bias Prompting:** The evaluation prompt was refactored to remove all positive numerical anchoring biases (such as default `"score": 8` in prompt schemas), enforce strict scoring tiers, and require evidence-based justification for scores above 1.

## Models Used

- **Qwen 2.5 Coder 3B:** Primary code-generation model and comparative judge.
- **Llama 3.2 3B:** Primary LLM-as-a-Judge model and secondary code generator.

Models are executed locally using Ollama.

## Dataset and Experiments

The project uses 20 Python programming tasks and generated code submissions.

Major experiments include:

1. Pointwise code evaluation across four dimensions.
2. Pairwise preference evaluation.
3. Functional correctness testing.
4. Position-bias analysis.
5. Verbosity-bias analysis.
6. Self-enhancement-bias analysis.
7. Human-preference alignment analysis.

## Research Results

Key observations from the experiments include:

- Qwen generated submissions passed 245 out of 261 functional test cases (93.87%).
- Llama generated submissions passed 86 out of 87 functional test cases (98.85%).
- In the controlled position-reversal experiment, 127 out of 145 pairs changed preference (87.59%).
- Pairwise judge agreement with human-majority labels was 64 out of 145 pairs (44.14%).

## Project Structure

```text
LLM-AS-A-CODE-AUDITOR/
|-- dashboard/             # Streamlit dashboard
|   |-- app.py             # Interactive research & evaluation UI
|   |-- services.py        # Dashboard backend, validation & test runners
|-- data/                  # Research datasets, test suites and outputs
|-- tests/                 # Automated unit tests for validation & evaluation
|   |-- test_validation.py # Tests for Python validation, C code rejection, abcd rejection
|-- main.py                # Flexible CLI for Python code generation and auditing
|-- generator.py           # Batch code generation
|-- evaluator.py           # Pointwise evaluation & Python validation logic
|-- pairwise_evaluator.py  # Pairwise evaluation
|-- benchmark_config.py    # Benchmark configuration
|-- test_cases.py          # Functional test cases
|-- requirements.txt       # Project dependencies
|-- README.md              # Project documentation
```

## Requirements

- Python 3.10 or newer
- Ollama installed and running locally
- `qwen2.5-coder:3b` model
- `llama3.2:3b` model

## Installation

Clone the repository:

```powershell
git clone https://github.com/RAGHAV-BUDUR/LLM-AS-A-CODE-AUDITOR.git
cd LLM-AS-A-CODE-AUDITOR
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Download the required Ollama models:

```powershell
ollama pull qwen2.5-coder:3b
ollama pull llama3.2:3b
```

Ensure Ollama is running (`ollama serve`) before executing model-based experiments.

## Running the Project

### 1. Interactive & CLI Code Auditing (`main.py`)

Run interactively:
```powershell
python main.py
```

Audit custom code directly via CLI:
```powershell
python main.py --problem "Check whether a number is prime" --code "def is_prime(n): return n > 1 and all(n % i != 0 for i in range(2, int(n**0.5) + 1))"
```

Audit code from a file:
```powershell
python main.py --problem "Calculate factorial" --code-file solution.py --judge-model qwen2.5-coder:3b
```

CLI options:
- `--problem`, `-p`: Programming problem description.
- `--code`, `-c`: Python code string to audit directly.
- `--code-file`, `-f`: Path to file containing Python code to audit.
- `--generator-model`: Model used for generation (default: `qwen2.5-coder:3b`).
- `--judge-model`: Model used for evaluation (default: `llama3.2:3b`).

### 2. Streamlit Dashboard

Launch the web dashboard:

```powershell
python -m streamlit run dashboard/app.py
```

The dashboard provides:
- **Project Overview:** Research context, models, and benchmark snapshot.
- **Code Evaluation:** Live code evaluation with language enforcement warnings, judge selection, and detailed dimension breakdowns.
- **Functional Testing:** Sandboxed execution of recognized tasks against benchmark test suites.
- **Research Results:** Visual charts for position sensitivity, verbosity bias, and accuracy.
- **About the Experiments:** Methodological details and findings.

### 3. Running Unit Tests

Run the automated test suite verifying Python validation, C-language rejection, and deterministic scoring:

```powershell
python -m unittest discover -s tests -v
```

## Execution Safety

The functional testing feature executes Python code in subprocesses with timeouts and isolated environments. These measures help limit accidental interference but do not provide a secure sandbox against malicious code.

Use the dashboard and testing utilities only with trusted code. LLM-generated scores are model judgements and should not replace human security reviews or verified test suites.

## Team

- Raghav Budhur
- P. Jaya Surya
- Sreyaesh Peruri
- Purvik V. Gowda

**Institution:** PES University  
**Programme:** B.Tech CSE (AI & ML)  
**Course:** Prompt Engineering and Optimization for Generative AI  
**Academic Year:** 2024–2028
