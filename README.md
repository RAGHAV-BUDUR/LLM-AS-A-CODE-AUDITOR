# Evaluative Benchmarking of LLM-as-a-Judge for Automated Code Auditing

A research project evaluating the use of Large Language Models (LLMs) as automated judges for Python code auditing.

## Project Overview

This project investigates how effectively an LLM can evaluate generated Python code across four dimensions:

- Correctness
- Security
- Readability
- Efficiency

It compares pointwise and pairwise evaluation approaches and investigates potential evaluation biases, including position bias, verbosity bias, and self-enhancement bias.

The project also compares LLM evaluations with functional test outcomes and external human-preference annotations.

## Models Used

- **Qwen 2.5 Coder 3B:** Primary code-generation model.
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

The experiments use separate scripts and datasets to support reproducibility and analysis.

## Research Results

Key observations from the experiments include:

- Qwen generated submissions passed 245 out of 261 functional test cases (93.87%).
- Llama generated submissions passed 86 out of 87 functional test cases (98.85%).
- In the controlled position-reversal experiment, 127 out of 145 pairs changed preference (87.59%).
- Pairwise judge agreement with human-majority labels was 64 out of 145 pairs (44.14%).

These results describe the observed experimental setup and should not be interpreted as universal model-performance claims.

## Project Structure

```text
Prompt_mini_project/
|
|-- benchmarking/          # Benchmark-related resources
|-- bias_testing/          # Bias experiment resources
|-- dashboard/             # Streamlit dashboard
|-- data/                  # Research datasets and outputs
|-- generator/              # Code generation resources
|-- report/                 # Final research report
|-- results/                # Experiment results
|-- screenshots/            # Dashboard screenshots
|
|-- main.py                 # Main code auditing workflow
|-- generator.py            # Code generation
|-- evaluator.py            # Pointwise evaluation
|-- pairwise_evaluator.py   # Pairwise evaluation
|-- benchmark_config.py    # Benchmark configuration
|-- test_cases.py           # Functional test cases
|-- universal_test_runner.py
|-- requirements.txt        # Project dependencies
|-- dashboard-requirements.txt
|-- README.md
```

## Requirements

- Python 3.10 or newer
- Ollama installed and running locally
- `qwen2.5-coder:3b` model
- `llama3.2:3b` model

## Installation

Clone the repository:

```powershell
git clone https://github.com/Suryapurimetla/LLM-as-a-Judge-Code-Auditing.git
cd LLM-as-a-Judge-Code-Auditing
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

Ensure Ollama is running before executing model-based experiments.

## Running the Project

Run the main code auditing workflow:

```powershell
python main.py
```

Run the Streamlit dashboard:

```powershell
python -m streamlit run dashboard/app.py
```

The dashboard provides:

- Project overview
- Live code evaluation
- Functional testing
- Research result visualisations
- Experiment descriptions

Live evaluations are stored separately from historical research results in:

`data/live_evaluations/evaluations.jsonl`

## External Benchmark Dataset

Some pairwise and position-bias experiments depend on the external human-preference dataset.

The original external dataset files are not bundled in this repository. Obtain the dataset from its original source and review its licence and attribution requirements before use or redistribution.

Place the required files in:

`data/external_human_dataset/`

The relevant analysis scripts expect the dataset at that location.

## Execution Safety

The functional testing feature executes Python code in subprocesses with timeouts and reduced environments. These measures help limit accidental interference but do not provide a secure sandbox against malicious code.

Use the dashboard and testing utilities only with trusted code. Do not treat them as production-grade security isolation.

LLM-generated scores are model judgements and should not replace functional testing or human review.

## Reproducibility and Data Management

- Historical experiment datasets are maintained separately from live dashboard evaluations.
- Research analysis scripts are retained for reproducibility.
- Functional test outcomes provide an independent correctness signal.
- External dataset licensing and attribution must be respected.

## Team

- P. Jaya Surya
- Sreyaesh Peruri
- Purvik V. Gowda
- Raghav Budhur

**Institution:** PES University  
**Programme:** B.Tech CSE (AI & ML)  
**Course:** Prompt Engineering and Optimization for Generative AI  
**Academic Year:** 2024–2028


