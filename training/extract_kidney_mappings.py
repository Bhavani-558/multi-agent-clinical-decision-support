"""
Extraction script for Chronic Kidney Disease Model categorical feature mappings.
Reproduces the exact cleaning and conversion logic from training/Kidney_XGBoost_Training (1).py
on data/raw/Chronic_Kidney.csv for features Rbc and Htn.
"""

import os
import pandas as pd
import numpy as np

csv_path = r"d:\MultiAgent_CDSS\data\raw\Chronic_Kidney.csv"

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
    if normalized in [
        "class", "classification", "target",
        "diagnosis", "ckd", "chronic kidney disease"
    ]:
        target_col = col
        break

# Cleaning steps matching training script
df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
df = df.drop(
    columns=[c for c in df.columns if c.lower().startswith("unnamed")],
    errors="ignore"
)

for col in df.columns:
    if df[col].dtype == "object":
        df[col] = df[col].astype(str).str.strip()

if target_col and target_col in df.columns:
    df = df[
        df[target_col].notna() &
        (df[target_col].astype(str).str.strip() != "")
    ].copy()
    X = df.drop(columns=[target_col]).copy()
else:
    X = df.copy()

id_cols = [
    c for c in X.columns
    if c.lower().strip() in ["id", "patient_id", "patientid", "record_id"]
]
if id_cols:
    X = X.drop(columns=id_cols)

# Extract mappings for Rbc and Htn matching training script logic (lines 145-162)
target_features = ["Rbc", "Htn"]
mappings = {}

for col in target_features:
    if col in X.columns:
        if pd.api.types.is_numeric_dtype(X[col]):
            converted = pd.to_numeric(X[col], errors="coerce")
            unique_vals = sorted(list(converted.dropna().unique()))
            code_map = {val: val for val in unique_vals}
            is_native_numeric = True
        else:
            cleaned = X[col].astype(str).str.strip().str.lower()
            numeric = pd.to_numeric(cleaned, errors="coerce")
            if numeric.notna().mean() >= 0.80:
                converted = numeric
                unique_vals = sorted(list(converted.dropna().unique()))
                code_map = {val: val for val in unique_vals}
                is_native_numeric = True
            else:
                cat_series = cleaned.astype("category")
                categories = list(cat_series.cat.categories)
                code_map = {cat: idx for idx, cat in enumerate(categories)}
                is_native_numeric = False

        mappings[col] = {
            "num_unique": len(code_map),
            "code_map": code_map,
            "is_native_numeric": is_native_numeric
        }

print("\n" + "=" * 75)
print("          KIDNEY MODEL CATEGORICAL MAPPING EXTRACTION")
print("=" * 75)

for col, data in mappings.items():
    print(f"\nFeature: {col}")
    print(f"Is Native Numeric in CSV: {data['is_native_numeric']}")
    print(f"Number of Unique Categories/Values: {data['num_unique']}")
    print("Original Category/Value -> Numeric Code Mappings:")
    for val, code in data["code_map"].items():
        print(f"  {val} -> {code}")
