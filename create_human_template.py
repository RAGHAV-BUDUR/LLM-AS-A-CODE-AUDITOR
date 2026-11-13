
import csv
import os

INPUT_FILE = "data/submissions.csv"
OUTPUT_FILE = "data/human_annotations.csv"

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as file:

    submissions = list(csv.DictReader(file))

fields = [
    "submission_id",
    "problem_id",
    "problem_description",
    "annotator_id",
    "correctness_score",
    "security_score",
    "readability_score",
    "efficiency_score",
    "comments"
]

# Two independent human reviews per submission.
# Replace Annotator_1 and Annotator_2 with team member IDs.

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as file:

    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()

    for submission in submissions:

        for annotator in ["Annotator_1", "Annotator_2"]:

            writer.writerow({
                "submission_id": submission["submission_id"],
                "problem_id": submission["problem_id"],
                "problem_description": submission["problem_description"],
                "annotator_id": annotator,
                "correctness_score": "",
                "security_score": "",
                "readability_score": "",
                "efficiency_score": "",
                "comments": ""
            })

print("Human annotation template created!")
print("Total submissions:", len(submissions))
print("Independent reviews per submission: 2")
print("Total annotation rows:", len(submissions) * 2)
print("Saved to:", OUTPUT_FILE)
import pandas as pd

INPUT_FILE = "data/submissions.csv"
OUTPUT_FILE = "data/human_annotations.csv"

# Read generated submissions
df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

annotations = []

for _, row in df.iterrows():
    for annotator in ["Annotator_1", "Annotator_2"]:
        annotations.append({
            "submission_id": row["submission_id"],
            "problem_id": row["problem_id"],
            "problem_description": row["problem_description"],
            "annotator_id": annotator,
            "correctness_score": "",
            "security_score": "",
            "readability_score": "",
            "efficiency_score": "",
            "comments": ""
            })

human_df = pd.DataFrame(annotations)

human_df.to_csv(OUTPUT_FILE, index=False)

print("HUMAN ANNOTATION TEMPLATE CREATED")
print("Total annotation rows:", len(human_df))
print("Saved to:", OUTPUT_FILE)