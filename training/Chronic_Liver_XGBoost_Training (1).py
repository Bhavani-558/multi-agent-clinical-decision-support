import os, sys, subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                       "pandas", "numpy", "scikit-learn", "xgboost", "joblib", "matplotlib"])

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
    classification_report, confusion_matrix, ConfusionMatrixDisplay,
    roc_auc_score, average_precision_score, roc_curve,
    precision_recall_curve, auc, make_scorer
)
from xgboost import XGBClassifier

# ============================================================
# CHRONIC LIVER DISEASE - XGBOOST TRAINING
# 100 BOOSTING ROUNDS + GRAPHS + METRICS + 5-FOLD CV
# ============================================================

RANDOM_STATE = 42
N_ESTIMATORS = 100
MODEL_FILE = "chronic_liver_xgboost_pipeline.pkl"

# Find uploaded CSV
preferred = [
    "indian_liver_patient.csv",
    "Indian_Liver_Patient.csv",
    "indian_liver_patient_data.csv",
    "liver.csv",
    "liver_disease.csv"
]

DATASET = next((f for f in preferred if os.path.exists(f)), None)

if DATASET is None:
    csv_files = [f for f in os.listdir(".") if f.lower().endswith(".csv")]
    liver_files = [
        f for f in csv_files
        if any(word in f.lower() for word in ["liver", "indian"])
    ]
    if len(liver_files) == 1:
        DATASET = liver_files[0]
    elif len(csv_files) == 1:
        DATASET = csv_files[0]

if DATASET is None:
    raise FileNotFoundError(
        "No Chronic Liver Disease CSV found. Upload the CSV first."
    )

print("=" * 75)
print("             CHRONIC LIVER DISEASE - XGBOOST")
print("=" * 75)
print("Dataset:", DATASET)

df = pd.read_csv(DATASET)

df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.replace(r"\s+", "_", regex=True)
)

print("\nDataset shape:", df.shape)
print("\nColumns:")
print(list(df.columns))
print("\nFirst 5 rows:")
print(df.head())

# ------------------------------------------------------------
# Target column: screenshot shows "Dataset"
# ------------------------------------------------------------
target_col = None

for col in df.columns:
    normalized = col.lower().replace("_", " ").strip()
    if normalized in [
        "dataset", "class", "target", "diagnosis",
        "liver disease", "liver_disease"
    ]:
        target_col = col
        break

if target_col is None:
    raise ValueError(
        "Target column was not found. "
        f"Available columns: {list(df.columns)}"
    )

print("\nTarget column:", target_col)

# ------------------------------------------------------------
# Clean data
# ------------------------------------------------------------
df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
df = df.drop(
    columns=[c for c in df.columns if c.lower().startswith("unnamed")],
    errors="ignore"
)

for col in df.columns:
    if df[col].dtype == "object":
        df[col] = df[col].astype(str).str.strip()

df = df[
    df[target_col].notna() &
    (df[target_col].astype(str).str.strip() != "")
].copy()

print("\nTarget distribution:")
print(df[target_col].value_counts())

X = df.drop(columns=[target_col]).copy()
y_text = df[target_col].copy()

# Remove ID columns if present
id_cols = [
    c for c in X.columns
    if c.lower().strip() in ["id", "patient_id", "patientid", "record_id"]
]
if id_cols:
    print("\nRemoving ID columns:", id_cols)
    X = X.drop(columns=id_cols)

# ------------------------------------------------------------
# Convert categorical/numeric features
# ------------------------------------------------------------
for col in X.columns:
    if pd.api.types.is_numeric_dtype(X[col]):
        X[col] = pd.to_numeric(X[col], errors="coerce")
    else:
        cleaned = X[col].astype(str).str.strip().str.lower()
        numeric = pd.to_numeric(cleaned, errors="coerce")

        if numeric.notna().mean() >= 0.80:
            X[col] = numeric
        else:
            X[col] = cleaned.astype("category").cat.codes.replace(-1, np.nan)

empty_cols = X.columns[X.isna().all()].tolist()
if empty_cols:
    print("\nRemoving empty columns:", empty_cols)
    X = X.drop(columns=empty_cols)

# ------------------------------------------------------------
# Encode target
# ------------------------------------------------------------
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y_text.astype(str).str.strip())
class_names = label_encoder.classes_.tolist()

if len(class_names) != 2:
    raise ValueError(
        f"Expected binary liver-disease target, found {class_names}"
    )

print("\nEncoded classes:")
for i, name in enumerate(class_names):
    print(f"{i} = {name}")

# ------------------------------------------------------------
# Train/test split
# ------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=RANDOM_STATE,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples :", len(X_test))
print("Features        :", X.shape[1])

# ------------------------------------------------------------
# Class balance
# ------------------------------------------------------------
class0 = int(np.sum(y_train == 0))
class1 = int(np.sum(y_train == 1))

imbalance_ratio = max(class0, class1) / max(1, min(class0, class1))

# scale_pos_weight only weights class 1.
# If class 1 is minority, balance it; otherwise leave at 1.
if class1 < class0 and class1 > 0 and imbalance_ratio >= 1.5:
    scale_pos_weight = class0 / class1
else:
    scale_pos_weight = 1.0

print("\nTraining class counts:")
print("Class 0:", class0)
print("Class 1:", class1)
print(f"Class imbalance ratio: {imbalance_ratio:.3f}")
print(f"scale_pos_weight used: {scale_pos_weight:.4f}")

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
    scale_pos_weight=scale_pos_weight,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=RANDOM_STATE,
    n_jobs=-1
)

print("\n" + "=" * 75)
print("             XGBOOST TRAINING - 100 ROUNDS")
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

eval_results = model.evals_result()
train_loss = np.array(eval_results["validation_0"]["logloss"])
validation_loss = np.array(eval_results["validation_1"]["logloss"])

# ------------------------------------------------------------
# Accuracy at every boosting round
# ------------------------------------------------------------
train_accuracy = []
validation_accuracy = []

print("\n" + "=" * 75)
print("             BOOSTING ROUND 1/100 -> 100/100")
print("=" * 75)

for round_no in range(1, 101):
    train_probability = model.predict_proba(
        X_train_p,
        iteration_range=(0, round_no)
    )[:, 1]

    validation_probability = model.predict_proba(
        X_test_p,
        iteration_range=(0, round_no)
    )[:, 1]

    train_prediction = (train_probability >= 0.5).astype(int)
    validation_prediction = (validation_probability >= 0.5).astype(int)

    train_acc = accuracy_score(y_train, train_prediction)
    validation_acc = accuracy_score(y_test, validation_prediction)

    train_accuracy.append(train_acc)
    validation_accuracy.append(validation_acc)

    print(
        f"Boosting Round {round_no}/100 | "
        f"Train Accuracy: {train_acc * 100:.2f}% | "
        f"Validation Accuracy: {validation_acc * 100:.2f}%"
    )

rounds = np.arange(1, 101)

# ------------------------------------------------------------
# Graph 1: Accuracy
# ------------------------------------------------------------
plt.figure(figsize=(9, 6))
plt.plot(rounds, train_accuracy, label="Training Accuracy")
plt.plot(rounds, validation_accuracy, label="Validation Accuracy")
plt.xlabel("Boosting Round")
plt.ylabel("Accuracy")
plt.title("Chronic Liver Disease - Training vs Validation Accuracy")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    "chronic_liver_training_validation_accuracy.png",
    dpi=200
)
plt.show()

# ------------------------------------------------------------
# Graph 2: Loss
# ------------------------------------------------------------
plt.figure(figsize=(9, 6))
plt.plot(rounds, train_loss, label="Training Loss")
plt.plot(rounds, validation_loss, label="Validation Loss")
plt.xlabel("Boosting Round")
plt.ylabel("Log Loss")
plt.title("Chronic Liver Disease - Training vs Validation Loss")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    "chronic_liver_training_validation_loss.png",
    dpi=200
)
plt.show()

# ------------------------------------------------------------
# Final test metrics
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
print("                    FINAL TEST METRICS")
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
# Graph 3: Confusion matrix
# ------------------------------------------------------------
cm = confusion_matrix(y_test, y_pred)

print("\nConfusion Matrix:")
print(cm)

ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=class_names
).plot(cmap="Blues", colorbar=False)

plt.title("Chronic Liver Disease - XGBoost Confusion Matrix")
plt.tight_layout()
plt.savefig(
    "chronic_liver_confusion_matrix.png",
    dpi=200,
    bbox_inches="tight"
)
plt.show()

# ------------------------------------------------------------
# Graph 4: ROC curve
# ------------------------------------------------------------
fpr, tpr, _ = roc_curve(y_test, y_probability)
roc_curve_auc = auc(fpr, tpr)

plt.figure(figsize=(8, 7))
plt.plot(
    fpr,
    tpr,
    label=f"XGBoost (AUC = {roc_curve_auc:.3f})"
)
plt.plot([0, 1], [0, 1], "--", label="Random")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("Chronic Liver Disease - ROC Curve")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    "chronic_liver_roc_curve.png",
    dpi=200
)
plt.show()

# ------------------------------------------------------------
# Graph 5: Precision-Recall curve
# ------------------------------------------------------------
pr_precision, pr_recall, _ = precision_recall_curve(
    y_test,
    y_probability
)

plt.figure(figsize=(8, 7))
plt.plot(
    pr_recall,
    pr_precision,
    label=f"XGBoost (AP = {pr_auc:.3f})"
)
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Chronic Liver Disease - Precision-Recall Curve")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    "chronic_liver_pr_curve.png",
    dpi=200
)
plt.show()

# ------------------------------------------------------------
# Training history CSV
# ------------------------------------------------------------
pd.DataFrame({
    "Boosting_Round": rounds,
    "Training_Accuracy": train_accuracy,
    "Validation_Accuracy": validation_accuracy,
    "Training_Loss": train_loss,
    "Validation_Loss": validation_loss
}).to_csv(
    "chronic_liver_training_history.csv",
    index=False
)

# ------------------------------------------------------------
# 5-Fold Cross-Validation
# ------------------------------------------------------------
print("\n" + "=" * 75)
print("                 5-FOLD CROSS-VALIDATION")
print("=" * 75)

def make_cv_model():
    return XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=scale_pos_weight,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

cv_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", make_cv_model())
])

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=RANDOM_STATE
)

scoring = {
    "accuracy": "accuracy",
    "precision": make_scorer(precision_score, zero_division=0),
    "recall": make_scorer(recall_score, zero_division=0),
    "f1": make_scorer(f1_score, zero_division=0),
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
    "feature_names": list(X.columns),
    "scale_pos_weight": scale_pos_weight
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
    "Features": X.shape[1],
    "Boosting_rounds": 100,
    "Scale_pos_weight": scale_pos_weight
}]).to_csv(
    "chronic_liver_final_metrics.csv",
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
    "chronic_liver_training_validation_accuracy.png",
    "chronic_liver_training_validation_loss.png",
    "chronic_liver_confusion_matrix.png",
    "chronic_liver_roc_curve.png",
    "chronic_liver_pr_curve.png",
    "chronic_liver_training_history.csv",
    "chronic_liver_final_metrics.csv"
]

for filename in output_files:
    if os.path.exists(filename):
        print("✓", filename)

print("\n" + "=" * 75)
print("       CHRONIC LIVER DISEASE TRAINING COMPLETED SUCCESSFULLY")
print("=" * 75)

print(
    "\nNote: This model is for an ML project and is not a clinical "
    "diagnostic tool."
)
