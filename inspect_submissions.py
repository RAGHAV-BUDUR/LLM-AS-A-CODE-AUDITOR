import pandas as pd

df = pd.read_csv(
    "data/submissions.csv",
    encoding="utf-8-sig"
)

print("COLUMN NAMES:")
print(df.columns.tolist())

print("\nFIRST SUBMISSION:")
print(df.iloc[0].to_dict())

print("\nTOTAL SUBMISSIONS:", len(df))