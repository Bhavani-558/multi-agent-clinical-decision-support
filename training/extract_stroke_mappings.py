"""
Extraction script for Stroke Model categorical feature mappings.
Reproduces the exact pandas category encoding (.astype("category").cat.codes)
used in training/Stroke_Balanced_XGBoost_Training (1).py on data/raw/healthcare-dataset-stroke-data.csv.
"""

import os
import pandas as pd
import numpy as np

csv_path = r"d:\MultiAgent_CDSS\data\raw\healthcare-dataset-stroke-data.csv"

if not os.path.exists(csv_path):
    raise FileNotFoundError(f"Dataset not found at {csv_path}")

df = pd.read_csv(csv_path)

df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.replace(r"\s+", "_", regex=True)
)

# Identify target column following training script logic
target_col = None
for col in df.columns:
    normalized = col.lower().replace("_", " ").strip()
    if normalized in ["stroke", "target", "diagnosis", "output", "condition"]:
        target_col = col
        break

# Cleaning steps matching training script
df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
df = df.drop(
    columns=[c for c in df.columns if c.lower().startswith("unnamed")],
    errors="ignore"
)

if target_col and target_col in df.columns:
    df[target_col] = df[target_col].astype(str).str.strip()
    df = df[
        (df[target_col] != "") &
        (df[target_col].str.lower() != "nan")
    ].copy()
    X = df.drop(columns=[target_col]).copy()
else:
    X = df.copy()

# Remove identifier columns matching training script
id_cols = [
    c for c in X.columns
    if c.lower().strip() in ["id", "patient_id", "patientid"]
]
if id_cols:
    X = X.drop(columns=id_cols)

categorical_cols = ["gender", "ever_married", "work_type", "Residence_type", "smoking_status"]

mappings = {}

for col in categorical_cols:
    if col in X.columns:
        cat_series = X[col].astype("category")
        categories = list(cat_series.cat.categories)
        code_map = {cat: idx for idx, cat in enumerate(categories)}
        mappings[col] = {
            "num_unique": len(categories),
            "categories": categories,
            "code_map": code_map
        }

print("\n" + "=" * 75)
print("             STROKE MODEL CATEGORICAL MAPPING EXTRACTION")
print("=" * 75)

for col, data in mappings.items():
    print(f"\nFeature: {col}")
    print(f"Number of Unique Categories: {data['num_unique']}")
    print("Category -> Numeric Code Mappings:")
    for cat, code in data["code_map"].items():
        print(f"  '{cat}' -> {code}")
