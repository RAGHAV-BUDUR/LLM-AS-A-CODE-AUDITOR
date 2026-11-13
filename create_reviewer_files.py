
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from pathlib import Path

INPUT_FILE = Path("data/submissions.csv")
OUTPUT_FOLDER = Path("data/human_review_files")

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

# Check the expected submission count
if len(df) != 60:
    raise ValueError(f"Expected 60 submissions, found {len(df)}")

reviewers = {
    "Member_1": range(1, 11),
    "Member_2": range(1, 11),
    "Member_3": range(11, 21),
    "Member_4": range(11, 21)
}

review_columns = [
    "submission_id",
    "problem_id",
    "problem_description",
    "variation",
    "code",
    "correctness_score",
    "security_score",
    "readability_score",
    "efficiency_score",
    "comments"
]

scoring_guide = [
    ["Dimension", "What to evaluate"],
    ["Correctness", "Does the code satisfy the complete problem requirements?"],
    ["Security", "Does the code avoid unsafe operations and security vulnerabilities?"],
    ["Readability", "Is the code understandable, organized and maintainable?"],
    ["Efficiency", "Does the code use reasonable time and memory?"],
    ["", ""],
    ["Score", "Meaning"],
    [1, "Very poor"],
    [2, "Very poor"],
    [3, "Poor"],
    [4, "Below average"],
    [5, "Average"],
    [6, "Average"],
    [7, "Good"],
    [8, "Very good"],
    [9, "Excellent"],
    [10, "Excellent"]
]

benchmark_rules = [
    ["Problem ID", "Benchmark convention"],
    ["P01", "Return Boolean indicating whether the number is prime."],
    ["P02", "Return the reversed string."],
    ["P03", "Return factorial value."],
    ["P04", "Palindrome checking is case-sensitive."],
    ["P05", "Return the list sorted in ascending order."],
    ["P06", "Return the largest element."],
    ["P07", "Return each duplicate element once."],
    ["P08", "Binary search returns index or -1."],
    ["P09", "Linear search returns index or -1."],
    ["P10", "Generate exactly n Fibonacci elements starting with 0; n=0 returns an empty list."],
    ["P11", "Return the number of vowels."],
    ["P12", "Anagram checking is case-insensitive."],
    ["P13", "Return non-negative GCD."],
    ["P14", "Remove duplicates while preserving original order."],
    ["P15", "Return the merged sorted list."],
    ["P16", "Validate correctly nested (), [] and {} brackets."],
    ["P17", "Return second distinct largest element or None."],
    ["P18", "Return word-frequency dictionary."],
    ["P19", "Return the matrix multiplication result."],
    ["P20", "Password requires at least 8 characters, uppercase, lowercase, digit and special character."]
]

for reviewer, problem_numbers in reviewers.items():

    selected = df[
        df["problem_id"].str.extract(r"P(\d+)")[0].astype(int).isin(problem_numbers)
    ].copy()

    selected = selected.sort_values(
        ["problem_id", "submission_id"]
    )

    selected["correctness_score"] = ""
    selected["security_score"] = ""
    selected["readability_score"] = ""
    selected["efficiency_score"] = ""
    selected["comments"] = ""

    selected = selected[review_columns]

    # Create workbook
    wb = Workbook()

    ws = wb.active
    ws.title = "Code Review"

    # Add title and instructions
    ws.append([f"Human Code Review - {reviewer}"])
    ws.append(["Evaluate each submission independently. Do not consult LLM scores."])
    ws.append(["Enter scores from 1 to 10. Add comments explaining important observations."])
    ws.append([])

    ws.append(review_columns)

    for row in selected.itertuples(index=False, name=None):
        ws.append(list(row))

    # Format code review sheet
    ws.freeze_panes = "A6"
    ws.auto_filter.ref = f"A5:J{ws.max_row}"

    widths = {
        "A": 18,
        "B": 12,
        "C": 38,
        "D": 12,
        "E": 85,
        "F": 18,
        "G": 16,
        "H": 19,
        "I": 17,
        "J": 45
    }

    for column, width in widths.items():
        ws.column_dimensions[column].width = width

    for cell in ws[5]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="244062")
        cell.alignment = Alignment(wrap_text=True, vertical="center")

    ws.row_dimensions[5].height = 30

    for row_num in range(6, ws.max_row + 1):

        ws.row_dimensions[row_num].height = 110

        for cell in ws[row_num]:
            cell.alignment = Alignment(
                wrap_text=True,
                vertical="top"
            )

        # Highlight score-entry columns
        for col_num in range(6, 11):
            ws.cell(row_num, col_num).fill = PatternFill(
                "solid",
                fgColor="FFF2CC"
            )

    ws.merge_cells("A1:J1")
    ws["A1"].font = Font(bold=True, size=16, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor="17365D")

    for row_num in [2, 3]:
        ws.merge_cells(
            start_row=row_num,
            start_column=1,
            end_row=row_num,
            end_column=10
        )
        ws.cell(row_num, 1).alignment = Alignment(wrap_text=True)

    # Scoring guide sheet
    guide = wb.create_sheet("Scoring Guide")

    for row in scoring_guide:
        guide.append(row)

    guide.append([])
    guide.append(["Important instructions"])
    guide.append(["Reviewers must work independently."])
    guide.append(["Do not view LLM evaluation scores or explanations."])
    guide.append(["Use the same scoring standards for every submission."])
    guide.append(["Do not change the original generated code."])

    guide.column_dimensions["A"].width = 25
    guide.column_dimensions["B"].width = 100

    for cell in guide[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="244062")

    for row in guide.iter_rows():
        for cell in row:
            cell.alignment = Alignment(
                wrap_text=True,
                vertical="top"
            )

    # Benchmark rules sheet
    rules = wb.create_sheet("Benchmark Rules")

    for row in benchmark_rules:
        rules.append(row)

    rules.column_dimensions["A"].width = 15
    rules.column_dimensions["B"].width = 110

    for cell in rules[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="244062")

    for row in rules.iter_rows():
        for cell in row:
            cell.alignment = Alignment(
                wrap_text=True,
                vertical="top"
            )

    # Save individual reviewer workbook
    output_file = OUTPUT_FOLDER / f"{reviewer}_Human_Review.xlsx"

    wb.save(output_file)

    print(f"Created: {output_file}")
    print(f"Submissions: {len(selected)}")


print("\nAll four reviewer workbooks created successfully.")
