
import pandas as pd

df = pd.read_csv(
    "data/submissions.csv",
    encoding="utf-8-sig"
)

for submission_id in ["P01_S2", "P01_S3"]:

    row = df[df["submission_id"] == submission_id].iloc[0]

    print("\n" + "=" * 60)
    print("SUBMISSION:", submission_id)
    print("=" * 60)
    print(row["code"])
