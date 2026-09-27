"""
Extraction script for Chronic Liver Disease Model categorical feature mappings.
Reproduces the exact cleaning and encoding logic (whitespace strip, lowercasing, .astype("category").cat.codes)
from training/Chronic_Liver_XGBoost_Training (1).py on data/raw/indian_liver_patient.csv.
"""

import os
import pandas as pd
import numpy as np

csv_path = r"d:\MultiAgent_CDSS\data\raw\indian_liver_patient.csv"

if not os.path.exists(csv_path):
    raise FileNotFoundError(f"Dataset not found at {csv_path}")

df = pd.read_csv(csv_path)

df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.replace(r"\s+", "_", regex=True)
)

# Find target column following training script logic
target_col = None
for col in df.columns:
    normalized = col.lower().replace("_", " ").strip()
    if normalized in [
        "dataset", "class", "target", "diagnosis",
        "liver disease", "liver_disease"
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

# Extract mapping for Gender following training script logic (lines 135-145)
target_feature = "Gender"
mappings = {}

if target_feature in X.columns:
    cleaned = X[target_feature].astype(str).str.strip().str.lower()
    cat_series = cleaned.astype("category")
    categories = list(cat_series.cat.categories)
    code_map = {cat: idx for idx, cat in enumerate(categories)}
    mappings[target_feature] = {
        "num_unique": len(categories),
        "categories": categories,
        "code_map": code_map
    }

print("\n" + "=" * 75)
print("       CHRONIC LIVER MODEL CATEGORICAL MAPPING EXTRACTION")
print("=" * 75)

for col, data in mappings.items():
    print(f"\nFeature: {col}")
    print(f"Number of Unique Categories: {data['num_unique']}")
    print("Category (Cleaned & Lowercased) -> Numeric Code Mappings:")
    for cat, code in data["code_map"].items():
        print(f"  '{cat}' -> {code}")
