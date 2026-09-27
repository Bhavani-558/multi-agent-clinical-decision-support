"""
DIABETES - XGBOOST COMPLETE TRAINING
====================================

Expected input:
    diabetes_prediction_dataset.csv

Run in Google Colab:
    !python Diabetes_XGBoost_Training.py

Includes:
- Dataset reading/preparation
- XGBoost training
- Epoch / boosting round 1/100 -> 100/100
- Training/validation accuracy graph
- Training/validation loss graph
- Accuracy, Precision, Recall, F1
- ROC-AUC and PR-AUC
- Confusion matrix
- ROC curve
- Precision-Recall curve
- 5-fold cross-validation
- Saved .pkl model
- Training history CSV
- Final metrics CSV
"""

import os
import sys
import subprocess

subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q",
    "pandas", "numpy", "scikit-learn", "xgboost", "joblib", "matplotlib"
])

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay, roc_curve,
    precision_recall_curve, auc, make_scorer
)
from xgboost import XGBClassifier

DATASET = "diabetes_prediction_dataset.csv"
MODEL_FILE = "diabetes_xgboost_pipeline.pkl"
N_ESTIMATORS = 100
RANDOM_STATE = 42

print("=" * 75)
print("                 DIABETES - XGBOOST TRAINING")
print("=" * 75)

if not os.path.exists(DATASET):
    raise FileNotFoundError(
        "diabetes_prediction_dataset.csv was not found. "
        "Upload the CSV to Colab first."
    )

df = pd.read_csv(DATASET)

df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.replace(r"\s+", "_", regex=True)
)

print("\nDataset loaded successfully.")
print("Dataset shape:", df.shape)
print("\nColumns:")
print(list(df.columns))
print("\nFirst 5 rows:")
print(df.head())

# ------------------------------------------------------------
# Find target column
# ------------------------------------------------------------

target_candidates = [
    "diabetes", "Outcome", "outcome", "target", "Target",
    "label", "Label", "diagnosis", "Diagnosis"
]

target_col = None

for candidate in target_candidates:
    for col in df.columns:
        if col.lower().strip() == candidate.lower().strip():
            target_col = col
            break
    if target_col is not None:
        break

if target_col is None:
    raise ValueError(
        "Could not automatically find the diabetes target column. "
        f"Columns found: {list(df.columns)}"
    )

print("\nTarget column:", target_col)

# ------------------------------------------------------------
# Clean dataset
# ------------------------------------------------------------

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

print("\nTarget distribution:")
print(df[target_col].value_counts())

X = df.drop(columns=[target_col]).copy()
y_text = df[target_col].copy()

# Remove obvious ID columns.
id_cols = [
    c for c in X.columns
    if str(c).strip().lower() in [
        "id", "patient_id", "patientid", "user_id", "userid"
    ]
]

if id_cols:
    print("\nRemoving identifier column(s):", id_cols)
    X = X.drop(columns=id_cols)

# Convert categorical predictors to numeric codes.
# This keeps common datasets such as gender/smoking/history usable.
for col in X.columns:
    if not pd.api.types.is_numeric_dtype(X[col]):
        X[col] = X[col].astype("category").cat.codes.replace(-1, np.nan)
    else:
        X[col] = pd.to_numeric(X[col], errors="coerce")

all_missing_cols = X.columns[X.isna().all()].tolist()
if all_missing_cols:
    X = X.drop(columns=all_missing_cols)

# Encode target.
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y_text)
class_names = label_encoder.classes_.tolist()
n_classes = len(class_names)

print("\nEncoded target classes:")
for i, name in enumerate(class_names):
    print(f"{i} = {name}")

print("\nSamples :", len(X))
print("Features:", X.shape[1])
print("Classes :", n_classes)

if n_classes != 2:
    raise ValueError(
        f"This script expects binary diabetes classification, "
        f"but found {n_classes} classes: {class_names}"
    )

# ------------------------------------------------------------
# Train/test split
# ------------------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=RANDOM_STATE,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples :", len(X_test))

# ------------------------------------------------------------
# Preprocessing
# ------------------------------------------------------------

preprocessor = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

X_train_p = preprocessor.fit_transform(X_train)
X_test_p = preprocessor.transform(X_test)

# ------------------------------------------------------------
# XGBoost
# ------------------------------------------------------------

model = XGBClassifier(
    n_estimators=N_ESTIMATORS,
    max_depth=3,
    learning_rate=0.05,
    subsample=0.85,
    colsample_bytree=0.85,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=RANDOM_STATE,
    n_jobs=-1
)

print("\nTotal epochs / boosting rounds:", N_ESTIMATORS)

# ------------------------------------------------------------
# Training
# ------------------------------------------------------------

print("\n" + "=" * 75)
print("                    XGBOOST TRAINING")
print("=" * 75)

model.fit(
    X_train_p,
    y_train,
    eval_set=[
        (X_train_p, y_train),
        (X_test_p, y_test)
    ],
    verbose=False
)

results = model.evals_result()

train_loss = np.array(results["validation_0"]["logloss"])
validation_loss = np.array(results["validation_1"]["logloss"])

# ------------------------------------------------------------
# Epoch-by-epoch accuracy
# ------------------------------------------------------------

train_accuracy = []
validation_accuracy = []

print("\n" + "=" * 75)
print("                 EPOCH 1/100 -> 100/100")
print("=" * 75)

for epoch in range(1, N_ESTIMATORS + 1):

    train_prob = model.predict_proba(
        X_train_p,
        iteration_range=(0, epoch)
    )[:, 1]

    validation_prob = model.predict_proba(
        X_test_p,
        iteration_range=(0, epoch)
    )[:, 1]

    train_pred = (train_prob >= 0.5).astype(int)
    validation_pred = (validation_prob >= 0.5).astype(int)

    train_acc = accuracy_score(y_train, train_pred)
    validation_acc = accuracy_score(y_test, validation_pred)

    train_accuracy.append(train_acc)
    validation_accuracy.append(validation_acc)

    print(
        f"Epoch {epoch}/100 | "
        f"Train Accuracy: {train_acc * 100:.2f}% | "
        f"Validation Accuracy: {validation_acc * 100:.2f}%"
    )

epochs = np.arange(1, N_ESTIMATORS + 1)

# ------------------------------------------------------------
# Accuracy graph
# ------------------------------------------------------------

plt.figure(figsize=(9, 6))
plt.plot(epochs, train_accuracy, label="Training Accuracy")
plt.plot(epochs, validation_accuracy, label="Validation Accuracy")
plt.xlabel("Epoch / Boosting Round")
plt.ylabel("Accuracy")
plt.title("Diabetes - Training vs Validation Accuracy")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    "diabetes_training_validation_accuracy.png",
    dpi=200
)
plt.show()

# ------------------------------------------------------------
# Loss graph
# ------------------------------------------------------------

plt.figure(figsize=(9, 6))
plt.plot(epochs, train_loss, label="Training Loss")
plt.plot(epochs, validation_loss, label="Validation Loss")
plt.xlabel("Epoch / Boosting Round")
plt.ylabel("Log Loss")
plt.title("Diabetes - Training vs Validation Loss")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    "diabetes_training_validation_loss.png",
    dpi=200
)
plt.show()

# ------------------------------------------------------------
# Final metrics
# ------------------------------------------------------------

y_probability = model.predict_proba(X_test_p)[:, 1]
y_pred = (y_probability >= 0.5).astype(int)

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)
roc_auc = roc_auc_score(y_test, y_probability)
pr_auc = average_precision_score(y_test, y_probability)

print("\n" + "=" * 75)
print("                 FINAL TEST METRICS")
print("=" * 75)

print(f"Accuracy : {accuracy:.4f} ({accuracy * 100:.2f}%)")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1       : {f1:.4f}")
print(f"ROC-AUC  : {roc_auc:.4f}")
print(f"PR-AUC   : {pr_auc:.4f}")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=class_names,
        zero_division=0
    )
)

# ------------------------------------------------------------
# Confusion matrix
# ------------------------------------------------------------

cm = confusion_matrix(y_test, y_pred)

print("\nConfusion Matrix:")
print(cm)

fig, ax = plt.subplots(figsize=(7, 6))

ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=class_names
).plot(
    ax=ax,
    cmap="Blues",
    colorbar=False
)

plt.title("Diabetes - XGBoost Confusion Matrix")
plt.tight_layout()
plt.savefig(
    "diabetes_confusion_matrix.png",
    dpi=200,
    bbox_inches="tight"
)
plt.show()

# ------------------------------------------------------------
# ROC curve
# ------------------------------------------------------------

fpr, tpr, _ = roc_curve(y_test, y_probability)
roc_curve_auc = auc(fpr, tpr)

plt.figure(figsize=(8, 7))
plt.plot(
    fpr,
    tpr,
    label=f"XGBoost (AUC = {roc_curve_auc:.3f})"
)
plt.plot(
    [0, 1],
    [0, 1],
    linestyle="--",
    label="Random"
)
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("Diabetes - ROC Curve")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    "diabetes_roc_curve.png",
    dpi=200
)
plt.show()

# ------------------------------------------------------------
# Precision-Recall curve
# ------------------------------------------------------------

precision_curve, recall_curve, _ = precision_recall_curve(
    y_test,
    y_probability
)

plt.figure(figsize=(8, 7))
plt.plot(
    recall_curve,
    precision_curve,
    label=f"XGBoost (AP = {pr_auc:.3f})"
)
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Diabetes - Precision-Recall Curve")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    "diabetes_pr_curve.png",
    dpi=200
)
plt.show()

# ------------------------------------------------------------
# Training history CSV
# ------------------------------------------------------------

pd.DataFrame({
    "Epoch": epochs,
    "Training_Accuracy": train_accuracy,
    "Validation_Accuracy": validation_accuracy,
    "Training_Loss": train_loss,
    "Validation_Loss": validation_loss
}).to_csv(
    "diabetes_training_history.csv",
    index=False
)

# ------------------------------------------------------------
# 5-fold cross-validation
# ------------------------------------------------------------

print("\n" + "=" * 75)
print("                 5-FOLD CROSS-VALIDATION")
print("=" * 75)

cv_model = XGBClassifier(
    n_estimators=N_ESTIMATORS,
    max_depth=3,
    learning_rate=0.05,
    subsample=0.85,
    colsample_bytree=0.85,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=RANDOM_STATE,
    n_jobs=-1
)

cv_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", cv_model)
])

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=RANDOM_STATE
)

scoring = {
    "accuracy": "accuracy",
    "precision": make_scorer(
        precision_score,
        zero_division=0
    ),
    "recall": make_scorer(
        recall_score,
        zero_division=0
    ),
    "f1": make_scorer(
        f1_score,
        zero_division=0
    ),
    "roc_auc": "roc_auc",
    "pr_auc": make_scorer(
        average_precision_score,
        response_method="predict_proba"
    )
}

cv_scores = cross_validate(
    cv_pipeline,
    X_train,
    y_train,
    cv=cv,
    scoring=scoring,
    n_jobs=-1
)

print("\n5-Fold Cross-Validation Mean Scores:")

for metric in scoring:
    mean_score = cv_scores[f"test_{metric}"].mean()
    std_score = cv_scores[f"test_{metric}"].std()

    print(
        f"{metric.upper():10s}: "
        f"{mean_score:.4f} ± {std_score:.4f}"
    )

# ------------------------------------------------------------
# Save complete model
# ------------------------------------------------------------

complete_model = {
    "preprocessor": preprocessor,
    "model": model,
    "label_encoder": label_encoder,
    "class_names": class_names,
    "feature_names": list(X.columns)
}

joblib.dump(
    complete_model,
    MODEL_FILE
)

# ------------------------------------------------------------
# Final metrics CSV
# ------------------------------------------------------------

pd.DataFrame([{
    "Accuracy": accuracy,
    "Precision": precision,
    "Recall": recall,
    "F1": f1,
    "ROC_AUC": roc_auc,
    "PR_AUC": pr_auc,
    "Training_samples": len(X_train),
    "Testing_samples": len(X_test),
    "Features": X.shape[1]
}]).to_csv(
    "diabetes_final_metrics.csv",
    index=False
)

# ------------------------------------------------------------
# Output files
# ------------------------------------------------------------

print("\n" + "=" * 75)
print("                       MODEL SAVED")
print("=" * 75)

output_files = [
    MODEL_FILE,
    "diabetes_training_validation_accuracy.png",
    "diabetes_training_validation_loss.png",
    "diabetes_confusion_matrix.png",
    "diabetes_roc_curve.png",
    "diabetes_pr_curve.png",
    "diabetes_training_history.csv",
    "diabetes_final_metrics.csv"
]

for filename in output_files:
    if os.path.exists(filename):
        print("✓", filename)

print("\n" + "=" * 75)
print("             DIABETES TRAINING COMPLETED SUCCESSFULLY")
print("=" * 75)

print(
    "\nThis model is for an ML project and is not a clinical "
    "diagnostic tool."
)
