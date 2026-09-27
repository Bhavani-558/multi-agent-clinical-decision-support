import pandas as pd
import numpy as np

csv_path = r"D:\MultiAgent_CDSS\data\raw\diabetes_prediction_dataset.csv"

df = pd.read_csv(csv_path)

df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.replace(r"\s+", "_", regex=True)
)

target_col = "diabetes"

df = df.dropna(axis=0, how="all")
df = df.dropna(axis=1, how="all")

drop_cols = [
    c for c in df.columns
    if str(c).lower().startswith("unnamed")
]

if drop_cols:
    df = df.drop(columns=drop_cols)

df[target_col] = df[target_col].astype(str).str.strip()

df = df[
    df[target_col].notna()
    & (df[target_col].str.lower() != "nan")
    & (df[target_col] != "")
].copy()

X = df.drop(columns=[target_col]).copy()

mappings = {}

for col in ["gender", "smoking_history"]:
    if col in X.columns:
        cat_series = X[col].astype("category")
        categories = list(cat_series.cat.categories)

        code_map = {
            cat: idx
            for idx, cat in enumerate(categories)
        }

        mappings[col] = {
            "num_unique": len(categories),
            "categories": categories,
            "code_map": code_map
        }

print("\nEXTRACTED MAPPINGS:")

for col, data in mappings.items():
    print(f"\nFeature: {col}")
    print(f"Number of unique categories: {data['num_unique']}")
    print("Category -> Numeric Code Mappings:")

    for cat, code in data["code_map"].items():
        print(f"  '{cat}' -> {code}")