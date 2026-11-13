
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ============================================================
# PROJECT PATHS AND IMPORTS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.services import (
    DIMENSIONS,
    available_models,
    evaluate_live,
    matching_tasks,
    read_csv,
    run_functional,
)

st.set_page_config(
    page_title="Code Audit Research",
    page_icon="🧪",
    layout="wide",
)

# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown("""
<style>
[data-testid="stSidebar"] {
    min-width: 17rem;
}

[data-testid="stMainBlockContainer"] {
    width: 100%;
    max-width: 100%;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
}

.hero-box {
    padding: 2rem;
    margin-bottom: 1.5rem;
    border-radius: 18px;
    background: linear-gradient(
        120deg,
        #e8f1ff 0%,
        #ffffff 70%,
        #edf7ff 100%
    );
    box-shadow: 0 12px 30px rgba(15, 39, 74, 0.10);
}

.hero-box h1 {
    font-size: clamp(2rem, 4vw, 3rem);
    line-height: 1.15;
    overflow-wrap: anywhere;
}

.info-card {
    padding: 1rem;
    margin-bottom: 0.8rem;
    border: 1px solid #dce5f0;
    border-radius: 12px;
    background: rgba(255,255,255,0.65);
}

.metric-card {
    padding: 0.8rem;
    border: 1px solid #dce5f0;
    border-radius: 12px;
    background: rgba(255,255,255,0.65);
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("Code audit lab")
st.sidebar.caption("Evaluative benchmarking | local LLM research")

section = st.sidebar.radio(
    "Navigate",
    [
        "Project overview",
        "Code evaluation",
        "Functional testing",
        "Research results",
        "About the experiments",
    ],
)

st.sidebar.caption("Qwen 2.5 Coder | Llama 3.2 | Ollama")


# ============================================================
# REUSABLE FUNCTIONS
# ============================================================

def hero(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="hero-box">
            <p>AI CODE AUDIT | RESEARCH DASHBOARD</p>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(parent, label: str, value):
    st.markdown(
        '<div class="metric-card">',
        unsafe_allow_html=True
    )

    st.metric(label, value)

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


def numeric(df: pd.DataFrame, col: str):
    if col not in df.columns:
        return pd.Series(dtype=float)

    return pd.to_numeric(
        df[col],
        errors="coerce",
    ).dropna()


def show_cards(items, columns=4):
    cols = st.columns(columns)

    for index, (label, value) in enumerate(items):
        with cols[index % columns]:
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.caption(label)
            st.subheader(str(value))
            st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# PROJECT OVERVIEW
# ============================================================

if section == "Project overview":

    hero(
        "Evaluative Benchmarking of LLM-as-a-Judge",
        "A practical study of how language models review Python code "
        "and where those judgments can fall short.",
    )

    st.header("What this project investigates")

    st.write(
        "LLM-as-a-Judge uses a language model to assess a code submission "
        "against a task. This project compares those assessments with "
        "functional tests, human preferences, and controlled bias experiments."
    )

    st.write("")

    st.header("Project identity & team")

    with st.container():
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.caption("UNIVERSITY")
        st.title("PES UNIVERSITY")
        st.caption("PROJECT TITLE")
        st.subheader("Evaluative Benchmarking of LLM-as-a-Judge")
        st.markdown("</div>", unsafe_allow_html=True)

    identity_details = [
        ("Department", "Artificial Intelligence and Machine Learning (AIML)"),
        ("Degree", "Bachelor of Technology (BTech)"),
        ("Course", "Prompt Engineering"),
        ("Academic year", "2024–2028"),
    ]

    show_cards(identity_details, 4)

    st.subheader("Project team")

    team = [
        ("Team member 01", "P. Jaya Surya"),
        ("Team member 02", "Sreyaesh Peruri"),
        ("Team member 03", "Purvik V Gowda"),
        ("Team member 04", "Raghav Budhur"),
    ]

    show_cards(team, 4)

    st.subheader("Evaluation dimensions")

    dimensions = [
        ("Correctness", "Meets the stated requirements"),
        ("Security", "Avoids identifiable vulnerabilities"),
        ("Readability", "Clear and maintainable code"),
        ("Efficiency", "Reasonable time and space use"),
    ]

    cols = st.columns(4)

    for index, (name, desc) in enumerate(dimensions):
        with cols[index]:
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.subheader(name)
            st.write(desc)
            st.markdown("</div>", unsafe_allow_html=True)

    st.header("Models")

    model_cols = st.columns(2)

    with model_cols[0]:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.subheader("Qwen 2.5 Coder 3B")
        st.write("Primary code generation model")
        st.caption("Local inference through Ollama")
        st.markdown("</div>", unsafe_allow_html=True)

    with model_cols[1]:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.subheader("Llama 3.2 3B")
        st.write("LLM judge and secondary code generator")
        st.caption("Local inference through Ollama")
        st.markdown("</div>", unsafe_allow_html=True)

    evals = read_csv("evaluation_results.csv")
    tests = read_csv("correctness_results.csv")

    st.header("Existing benchmark snapshot")

    total_tests = numeric(tests, "total").sum()
    total_passed = numeric(tests, "passed").sum()

    if total_tests:
        rate = total_passed / total_tests * 100
        rate_text = f"{rate:.1f}%"
    else:
        rate_text = "Unavailable"

    snapshot = [
        ("Historical LLM evaluations", len(evals)),
        ("Functional submissions", len(tests)),
        ("Test pass rate", rate_text),
    ]

    show_cards(snapshot, 3)

    if evals.empty or tests.empty:
        st.info(
            "Some research CSV files are missing or empty. "
            "Available sections remain usable."
        )


# ============================================================
# CODE EVALUATION
# ============================================================

elif section == "Code evaluation":

    hero(
        "Code evaluation",
        "Score a fresh submission with the existing LLM judge pipeline.",
    )

    st.info(
        "Live scores are model-generated opinions, not proof of correctness. "
        "Ollama must be running locally with the selected model available."
    )

    try:
        models = available_models()

    except Exception as exc:
        models = []
        st.error(f"Could not connect to Ollama: {exc}")

    if not models:
        st.warning(
            "No Ollama models were detected. "
            "Start Ollama and confirm a model is installed."
        )
        selected_model = "llama3.2:3b"

    else:
        preferred = next(
            (m for m in models if m.startswith("llama3.2:3b")),
            models[0],
        )

        selected_model = st.selectbox(
            "Judge model",
            models,
            index=models.index(preferred),
        )

    problem = st.text_area(
        "Task description",
        height=180,
        placeholder="Describe what the code is intended to do...",
    )

    code = st.text_area(
        "Python code",
        height=420,
        placeholder="Paste a Python function or program...",
    )

    if st.button("Evaluate code", type="primary", use_container_width=True):

        if not problem.strip() or not code.strip():
            st.error("Enter both a task description and Python code.")

        else:
            with st.spinner(f"Evaluating with {selected_model}..."):

                try:
                    result = evaluate_live(
                        problem,
                        code,
                        selected_model,
                    )

                    st.subheader("Evaluation scores")

                    score_cols = st.columns(5)

                    for index, dim in enumerate(DIMENSIONS):
                        with score_cols[index]:
                            metric_card(
                                st,
                                dim.title(),
                                f"{result[dim]['score']}/10",
                            )

                    for dim in DIMENSIONS:
                        with st.expander(
                            f"{dim.title()} - {result[dim]['score']}/10",
                            expanded=True,
                        ):
                            st.write(result[dim]["explanation"])

                    st.success(
                        f"Overall score: {result['overall_score']}/10"
                    )

                    st.caption(
                        "Saved separately to "
                        "data/live_evaluations/evaluations.jsonl"
                    )

                except Exception as exc:
                    st.error(f"Evaluation failed: {exc}")
                    st.exception(exc)

# ============================================================
# FUNCTIONAL TESTING
# ============================================================

elif section == "Functional testing":

    hero(
        "Functional testing",
        "Run the project's existing cases for a recognized task.",
    )

    st.warning(
        "Submitted code runs in timed subprocesses with a temporary "
        "working directory. This is a limited local demonstration safeguard, "
        "not a hardened sandbox. Run only trusted code."
    )

    tasks = matching_tasks()

    if tasks.empty:

        st.warning(
            "Task catalog is missing or unavailable. "
            "No test suite can be selected."
        )

        st.text_input("Custom task description")

        st.text_area(
            "Python code",
            height=380,
            placeholder="Paste the function implementation...",
        )

        st.info(
            "Automated functional verification is unavailable because "
            "no predefined test suite could be loaded."
        )

    else:

        task_ids = tasks["problem_id"].tolist()

        selection = st.selectbox(
            "Task",
            ["Custom task", *task_ids],
            format_func=lambda pid: (
                "Custom task - no predefined test suite"
                if pid == "Custom task"
                else (
                    f"{pid} - "
                    f"{tasks.loc[tasks.problem_id == pid, 'problem_description'].iloc[0]}"
                )
            ),
        )

        if selection == "Custom task":
            st.text_input("Custom task description")

        code = st.text_area(
            "Python code",
            height=380,
            placeholder="Paste the function implementation...",
        )

        if st.button(
            "Run functional tests",
            type="primary",
            use_container_width=True,
        ):

            if selection == "Custom task":

                st.info(
                    "No predefined test suite matches this custom task. "
                    "Automated functional verification is unavailable."
                )

            else:

                try:
                    outcomes = run_functional(selection, code)

                    if not outcomes:
                        st.info(
                            "No configured test suite is available for this task."
                        )

                    else:
                        frame = pd.DataFrame(outcomes)

                        passed = int(
                            (frame.outcome == "PASSED").sum()
                        )

                        total = len(frame)

                        results = [
                            ("Passed tests", passed),
                            ("Failed tests", total - passed),
                            ("Total tests", total),
                            (
                                "Pass rate",
                                f"{passed / total * 100:.1f}%",
                            ),
                        ]

                        show_cards(results, 4)

                        st.subheader("Individual test outcomes")

                        st.dataframe(
                            frame,
                            use_container_width=True,
                            height=420,
                        )

                except SyntaxError as exc:
                    st.error(
                        f"Python syntax error at line {exc.lineno}: {exc.msg}"
                    )

                except Exception as exc:
                    st.error(f"Could not run tests: {exc}")


# ============================================================
# RESEARCH RESULTS
# ============================================================

elif section == "Research results":

    hero(
        "Research results",
        "Explore recorded experimental results. "
        "Charts use project CSV data; unavailable data is called out.",
    )

    st.header("Judge reliability")

    rel = read_csv("qwen_reliability_analysis.csv")

    if not rel.empty and "correctness" in rel.columns:

        st.subheader("LLM correctness score distribution")

        scores = numeric(rel, "correctness").value_counts().sort_index()

        st.bar_chart(scores, use_container_width=True)

    comparison = read_csv("llm_functional_comparison.csv")

    if (
        not comparison.empty
        and {"correctness", "accuracy_percent"}.issubset(comparison.columns)
    ):

        plot = comparison[
            ["correctness", "accuracy_percent"]
        ].apply(
            pd.to_numeric,
            errors="coerce",
        ).dropna()

        st.subheader("Judge correctness score vs functional accuracy")

        st.scatter_chart(
            plot,
            x="correctness",
            y="accuracy_percent",
            use_container_width=True,
        )

    else:
        st.info("LLM vs functional comparison data is not available.")

    # --------------------------------------------------------
    # HUMAN PREFERENCE ALIGNMENT
    # --------------------------------------------------------

    st.header("Preference and bias experiments")
    st.subheader("Human preference alignment")

    pair = read_csv(
        "external_human_dataset/pairwise_analysis_summary.csv"
    )

    if not pair.empty and "agreement_percentage" in pair.columns:

        pair_cols = st.columns(max(1, len(pair)))

        for index, (_, row) in enumerate(pair.iterrows()):

            with pair_cols[index % len(pair_cols)]:
                metric_card(
                    st,
                    str(row["human_reference"]),
                    f"{float(row['agreement_percentage']):.2f}%",
                )

        st.dataframe(
            pair,
            use_container_width=True,
        )

    else:
        st.info("Pairwise human alignment summary is not available.")

    # --------------------------------------------------------
    # POSITION BIAS
    # --------------------------------------------------------

    st.subheader("Controlled position sensitivity")

    position = read_csv(
        "external_human_dataset/controlled_position_bias_results.csv"
    )

    if not position.empty:

        st.dataframe(
            position["preference_changed"]
            .value_counts(dropna=False)
            .rename_axis("Preference changed")
            .to_frame("Pairs"),
            use_container_width=True,
        )

        if "first_position_selections" in position.columns:

            first_rate = (
                numeric(position, "first_position_selections").sum()
                / (2 * len(position))
            )

            metric_card(
                st,
                "First-position selection rate",
                f"{first_rate * 100:.2f}%",
            )

        elif "original_choice" in position.columns:

            first = (
                position.original_choice.astype(str)
                .str.upper()
                .eq("A")
                .mean()
            )

            metric_card(
                st,
                "First-position selection rate (A in original order)",
                f"{first * 100:.2f}%",
            )

    else:
        st.info("Controlled position results are unavailable.")

    # --------------------------------------------------------
    # VERBOSITY EXPERIMENT
    # --------------------------------------------------------

    st.subheader("Verbosity experiment")

    verbosity = read_csv(
        "controlled_verbosity_scoring_results.csv"
    )

    if (
        not verbosity.empty
        and {"original_score", "verbose_score"}.issubset(verbosity.columns)
    ):

        means = verbosity[
            ["original_score", "verbose_score"]
        ].apply(
            pd.to_numeric,
            errors="coerce",
        ).mean()

        means = means.rename(
            index={
                "original_score": "Original",
                "verbose_score": "With extra comments",
            }
        )

        st.subheader("Average score with added comments")
        st.bar_chart(means, use_container_width=True)

    elif not verbosity.empty:

        st.dataframe(
            verbosity,
            use_container_width=True,
        )

    else:
        st.info("Verbosity scoring results are unavailable.")

    # --------------------------------------------------------
    # SELF-ENHANCEMENT
    # --------------------------------------------------------

    st.subheader("Self-enhancement comparison")

    self_data = read_csv(
        "self_enhancement_pointwise_results.csv"
    )

    if (
        not self_data.empty
        and "solution_id" in self_data.columns
        and "overall" in self_data.columns
    ):

        self_data["overall"] = pd.to_numeric(
            self_data.overall,
            errors="coerce",
        )

        means = (
            self_data.assign(
                generator=self_data.solution_id.str.extract(
                    r"^(QWEN|LLAMA)",
                    expand=False,
                )
            )
            .groupby("generator")
            .overall.mean()
            .dropna()
        )

        st.subheader("Average pointwise score by generator")
        st.bar_chart(means, use_container_width=True)

    else:
        st.info(
            "Pointwise self-enhancement result data is unavailable."
        )

    # --------------------------------------------------------
    # FUNCTIONAL TEST PASS RATES
    # --------------------------------------------------------

    st.subheader("Functional test pass rates")

    qwen = read_csv("correctness_results.csv")
    llama = read_csv("llama_correctness_results.csv")

    rates = {}

    for name, frame in (
        ("Qwen", qwen),
        ("Llama", llama),
    ):

        passed_sum = numeric(frame, "passed").sum()
        total_sum = numeric(frame, "total").sum()

        if total_sum:
            rates[name] = passed_sum / total_sum * 100

    if rates:

        rate_cols = st.columns(len(rates))

        for index, (model_name, pass_rate) in enumerate(rates.items()):

            with rate_cols[index]:
                metric_card(
                    st,
                    f"{model_name} functional accuracy",
                    f"{pass_rate:.2f}%",
                )

        st.bar_chart(
            pd.Series(rates, name="Pass rate (%)"),
            use_container_width=True,
        )

    else:
        st.info("Functional test result files are unavailable.")


# ============================================================
# ABOUT THE EXPERIMENTS
# ============================================================

else:

    hero(
        "About the experiments",
        "Methods used to study judge quality, agreement and bias.",
    )

    topics = {
        "Pointwise evaluation": (
            "A judge scores one submission on correctness, security, "
            "readability and efficiency. Scores are model judgments "
            "and should be checked against evidence."
        ),

        "Pairwise evaluation": (
            "A judge compares two candidate solutions and selects one "
            "or a tie. Reversing candidate order helps reveal position effects."
        ),

        "Functional correctness testing": (
            "The submission's selected function is run on predefined inputs "
            "and its outputs are compared with expected values. "
            "This measures the tested cases, not every possible behavior."
        ),

        "Position bias": (
            "The experiment checks whether a judge changes its preference "
            "when the same two solutions swap positions."
        ),

        "Verbosity bias": (
            "The experiment compares judgments before and after adding "
            "comments or verbosity while keeping the solution's behavior fixed."
        ),

        "Self-enhancement bias": (
            "The experiment checks whether a judge favors solutions generated "
            "by its own model family over another model's solutions."
        ),

        "Human preference alignment": (
            "Judge choices are compared with human annotations or majority "
            "choices from the recorded preference dataset."
        ),
    }

    for title, body in topics.items():

        with st.expander(title):
            st.write(body)
