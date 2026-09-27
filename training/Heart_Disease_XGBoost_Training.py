import os, sys, subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pandas", "numpy", "scikit-learn", "xgboost", "joblib", "matplotlib"])

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, classification_report, confusion_matrix,
    ConfusionMatrixDisplay, roc_curve, precision_recall_curve, auc, make_scorer)
from xgboost import XGBClassifier

N_ESTIMATORS=100
RANDOM_STATE=42
MODEL_FILE="heart_disease_xgboost_pipeline.pkl"

# Find the uploaded Heart Disease CSV
names=["Heart_Disease.csv","heart_disease.csv","Heart Disease.csv","heart disease.csv"]
DATASET=next((f for f in names if os.path.exists(f)),None)
if DATASET is None:
    csvs=[f for f in os.listdir(".") if f.lower().endswith(".csv")]
    heart=[f for f in csvs if "heart" in f.lower()]
    DATASET=heart[0] if heart else (csvs[0] if len(csvs)==1 else None)
if DATASET is None:
    raise FileNotFoundError("Upload your Heart Disease CSV first.")

print("="*75)
print("             HEART DISEASE - XGBOOST TRAINING")
print("="*75)
print("Dataset:",DATASET)

df=pd.read_csv(DATASET)
df.columns=df.columns.astype(str).str.strip().str.replace(r"\s+","_",regex=True)
print("\nShape:",df.shape)
print("\nColumns:",list(df.columns))
print("\nFirst 5 rows:\n",df.head())

# Find target
target=None
for c in df.columns:
    n=c.lower().replace("_"," ").strip()
    if n in ["heart disease","heart_disease","target","diagnosis","output","condition"]:
        target=c; break
if target is None:
    raise ValueError("Heart Disease target column not found. Columns: "+str(list(df.columns)))

print("\nTarget column:",target)
df=df.dropna(axis=0,how="all").dropna(axis=1,how="all")
df=df.drop(columns=[c for c in df.columns if c.lower().startswith("unnamed")],errors="ignore")
df[target]=df[target].astype(str).str.strip()
df=df[(df[target]!="")&(df[target].str.lower()!="nan")].copy()
print("\nTarget distribution:\n",df[target].value_counts())

X=df.drop(columns=[target]).copy()
y_text=df[target].copy()

idcols=[c for c in X.columns if c.lower().strip() in ["id","patient_id","patientid"]]
if idcols: X=X.drop(columns=idcols)

for c in X.columns:
    if not pd.api.types.is_numeric_dtype(X[c]):
        X[c]=X[c].astype("category").cat.codes.replace(-1,np.nan)
    else:
        X[c]=pd.to_numeric(X[c],errors="coerce")
X=X.drop(columns=X.columns[X.isna().all()].tolist())

le=LabelEncoder()
y=le.fit_transform(y_text)
classes=le.classes_.tolist()
if len(classes)!=2:
    raise ValueError(f"Expected 2 target classes, found {classes}")

print("\nClasses:",classes)
X_train,X_test,y_train,y_test=train_test_split(
    X,y,test_size=.20,random_state=RANDOM_STATE,stratify=y)

prep=Pipeline([("imputer",SimpleImputer(strategy="median")),
               ("scaler",StandardScaler())])
Xtr=prep.fit_transform(X_train)
Xte=prep.transform(X_test)

model=XGBClassifier(n_estimators=100,max_depth=3,learning_rate=.05,
    subsample=.85,colsample_bytree=.85,objective="binary:logistic",
    eval_metric="logloss",random_state=RANDOM_STATE,n_jobs=-1)

print("\nTraining 100 boosting rounds...")
model.fit(Xtr,y_train,eval_set=[(Xtr,y_train),(Xte,y_test)],verbose=False)
res=model.evals_result()
train_loss=np.array(res["validation_0"]["logloss"])
val_loss=np.array(res["validation_1"]["logloss"])

train_acc=[]; val_acc=[]
print("\n"+"="*75)
print("             BOOSTING ROUND 1/100 -> 100/100")
print("="*75)
for r in range(1,101):
    pt=model.predict_proba(Xtr,iteration_range=(0,r))[:,1]
    pv=model.predict_proba(Xte,iteration_range=(0,r))[:,1]
    at=accuracy_score(y_train,(pt>=.5).astype(int))
    av=accuracy_score(y_test,(pv>=.5).astype(int))
    train_acc.append(at); val_acc.append(av)
    print(f"Boosting Round {r}/100 | Train Accuracy: {at*100:.2f}% | Validation Accuracy: {av*100:.2f}%")

rounds=np.arange(1,101)

plt.figure(figsize=(9,6)); plt.plot(rounds,train_acc,label="Training Accuracy"); plt.plot(rounds,val_acc,label="Validation Accuracy")
plt.xlabel("Boosting Round"); plt.ylabel("Accuracy"); plt.title("Heart Disease - Training vs Validation Accuracy")
plt.legend(); plt.grid(True,alpha=.3); plt.tight_layout()
plt.savefig("heart_disease_training_validation_accuracy.png",dpi=200); plt.show()

plt.figure(figsize=(9,6)); plt.plot(rounds,train_loss,label="Training Loss"); plt.plot(rounds,val_loss,label="Validation Loss")
plt.xlabel("Boosting Round"); plt.ylabel("Log Loss"); plt.title("Heart Disease - Training vs Validation Loss")
plt.legend(); plt.grid(True,alpha=.3); plt.tight_layout()
plt.savefig("heart_disease_training_validation_loss.png",dpi=200); plt.show()

prob=model.predict_proba(Xte)[:,1]
pred=(prob>=.5).astype(int)
accuracy=accuracy_score(y_test,pred)
precision=precision_score(y_test,pred,zero_division=0)
recall=recall_score(y_test,pred,zero_division=0)
f1=f1_score(y_test,pred,zero_division=0)
rocauc=roc_auc_score(y_test,prob)
prauc=average_precision_score(y_test,prob)

print("\n"+"="*75)
print("FINAL TEST METRICS")
print("="*75)
print(f"Accuracy : {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1       : {f1:.4f}")
print(f"ROC-AUC  : {rocauc:.4f}")
print(f"PR-AUC   : {prauc:.4f}")
print("\nClassification Report:\n",classification_report(y_test,pred,target_names=classes,zero_division=0))

cm=confusion_matrix(y_test,pred)
ConfusionMatrixDisplay(cm,display_labels=classes).plot(cmap="Blues",colorbar=False)
plt.title("Heart Disease - XGBoost Confusion Matrix"); plt.tight_layout()
plt.savefig("heart_disease_confusion_matrix.png",dpi=200,bbox_inches="tight"); plt.show()

fpr,tpr,_=roc_curve(y_test,prob)
plt.figure(figsize=(8,7)); plt.plot(fpr,tpr,label=f"XGBoost (AUC={auc(fpr,tpr):.3f})")
plt.plot([0,1],[0,1],"--",label="Random"); plt.xlabel("False Positive Rate"); plt.ylabel("True Positive Rate")
plt.title("Heart Disease - ROC Curve"); plt.legend(); plt.grid(True,alpha=.3); plt.tight_layout()
plt.savefig("heart_disease_roc_curve.png",dpi=200); plt.show()

prp,prr,_=precision_recall_curve(y_test,prob)
plt.figure(figsize=(8,7)); plt.plot(prr,prp,label=f"XGBoost (AP={prauc:.3f})")
plt.xlabel("Recall"); plt.ylabel("Precision"); plt.title("Heart Disease - Precision-Recall Curve")
plt.legend(); plt.grid(True,alpha=.3); plt.tight_layout()
plt.savefig("heart_disease_pr_curve.png",dpi=200); plt.show()

pd.DataFrame({"Boosting_Round":rounds,"Training_Accuracy":train_acc,
              "Validation_Accuracy":val_acc,"Training_Loss":train_loss,
              "Validation_Loss":val_loss}).to_csv("heart_disease_training_history.csv",index=False)

print("\n"+"="*75)
print("5-FOLD CROSS-VALIDATION")
print("="*75)
cvmodel=XGBClassifier(n_estimators=100,max_depth=3,learning_rate=.05,subsample=.85,
    colsample_bytree=.85,objective="binary:logistic",eval_metric="logloss",
    random_state=RANDOM_STATE,n_jobs=-1)
cvpipe=Pipeline([("preprocessor",prep),("model",cvmodel)])
cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=RANDOM_STATE)
scoring={"accuracy":"accuracy",
 "precision":make_scorer(precision_score,zero_division=0),
 "recall":make_scorer(recall_score,zero_division=0),
 "f1":make_scorer(f1_score,zero_division=0),
 "roc_auc":"roc_auc",
 "pr_auc":make_scorer(average_precision_score,response_method="predict_proba")}
scores=cross_validate(cvpipe,X_train,y_train,cv=cv,scoring=scoring,n_jobs=-1)
print("\n5-Fold Cross-Validation Mean Scores:")
for m in scoring:
    print(f"{m.upper():10s}: {scores['test_'+m].mean():.4f} ± {scores['test_'+m].std():.4f}")

joblib.dump({"preprocessor":prep,"model":model,"label_encoder":le,
             "class_names":classes,"feature_names":list(X.columns)},MODEL_FILE)

pd.DataFrame([{"Accuracy":accuracy,"Precision":precision,"Recall":recall,
"F1":f1,"ROC_AUC":rocauc,"PR_AUC":prauc,"Training_samples":len(X_train),
"Testing_samples":len(X_test),"Features":X.shape[1],"Boosting_rounds":100}]
).to_csv("heart_disease_final_metrics.csv",index=False)

print("\n"+"="*75)
print("MODEL SAVED")
print("="*75)
for f in [MODEL_FILE,"heart_disease_training_validation_accuracy.png",
"heart_disease_training_validation_loss.png","heart_disease_confusion_matrix.png",
"heart_disease_roc_curve.png","heart_disease_pr_curve.png",
"heart_disease_training_history.csv","heart_disease_final_metrics.csv"]:
    if os.path.exists(f): print("✓",f)
print("\n"+"="*75)
print("HEART DISEASE TRAINING COMPLETED SUCCESSFULLY")
print("="*75)
