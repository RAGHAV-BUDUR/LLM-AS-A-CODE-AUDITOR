import gzip
import json
import pandas as pd
from collections import Counter

input_path = "data/external_human_dataset/human-preference-alignment.jsonl.gz"

rows = []

with gzip.open(input_path, "rt", encoding="utf-8") as file:
    for line in file:
        record = json.loads(line)

        annotations = record["annotations"]
        counts = Counter(annotations)

        if counts["codeA"] > counts["codeB"] and counts["codeA"] > counts["Tie"]:
            majority = "codeA"
        elif counts["codeB"] > counts["codeA"] and counts["codeB"] > counts["Tie"]:
            majority = "codeB"
        else:
            majority = "Tie"

        rows.append({
            "task_id": record["task_id"],
            "instruction": record["instruction"],
            "codeA": record["choices"][0],
            "codeB": record["choices"][1],
            "gt_choice": record["gt_choice"],
            "human_annotations": "|".join(annotations),
            "human_majority": majority,
            "human_codeA_votes": counts["codeA"],
            "human_codeB_votes": counts["codeB"],
            "human_tie_votes": counts["Tie"]
        })

df = pd.DataFrame(rows)

output_path = "data/external_human_dataset/cleaned_human_preferences.csv"
df.to_csv(output_path, index=False)

print("Dataset preparation completed!")
print("Total records:", len(df))
print("Human majority distribution:")
print(df["human_majority"].value_counts())
print("Saved:", output_path)