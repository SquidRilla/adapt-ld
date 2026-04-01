"""
ADAPT-LD — ML Training Pipeline
================================
Trains, evaluates, and saves a Random Forest classifier for LD risk classification.

Steps:
  1. Load & validate data
  2. Feature engineering
  3. Preprocessing (scaling, SMOTE balancing)
  4. Train RandomForest + compare baseline models
  5. Hyperparameter tuning (GridSearchCV)
  6. Full evaluation: accuracy, classification report, confusion matrix
  7. Feature importance plot
  8. Save model artefacts
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    roc_auc_score, ConfusionMatrixDisplay
)
from sklearn.pipeline import Pipeline
from sklearn.inspection import permutation_importance

try:
    from imblearn.over_sampling import SMOTE
    HAS_SMOTE = True
except ImportError:
    HAS_SMOTE = False

# ── Paths ────────────────────────────────────────────
BASE   = Path(__file__).parent
DATA   = BASE / "data" / "student_assessments.csv"
MODELS = BASE / "models"
PLOTS  = BASE / "plots"
MODELS.mkdir(exist_ok=True)
PLOTS.mkdir(exist_ok=True)

LABEL_MAP = {0: "No Risk", 1: "Mild Risk", 2: "Moderate Risk", 3: "High Risk"}
COLORS     = ["#02C39A", "#F9A825", "#E87722", "#C0392B"]

# ────────────────────────────────────────────────────
# 1. Load Data
# ────────────────────────────────────────────────────
print("=" * 60)
print("  ADAPT-LD  |  ML Training Pipeline")
print("=" * 60)

df = pd.read_csv(DATA)
print(f"\n[1/7] Data loaded  →  {df.shape[0]} rows, {df.shape[1]} cols")
print(f"      Class distribution:\n{df['risk_level'].value_counts().sort_index()}\n")

# ────────────────────────────────────────────────────
# 2. Feature Engineering
# ────────────────────────────────────────────────────
df["academic_composite"]  = (df["reading_accuracy"] + df["writing_coherence"] + df["math_accuracy"]) / 3
df["processing_speed"]    = 1 / (df["attention_response_ms"] / 1000 + 1e-6)   # higher = faster
df["error_rate_norm"]     = df["repeated_errors"] / (df["assessment_duration_s"] / 60)  # errors per minute

FEATURES = [
    "reading_accuracy", "writing_coherence", "math_accuracy", "speech_fluency",
    "attention_response_ms", "age", "repeated_errors", "assessment_duration_s",
    "academic_composite", "processing_speed", "error_rate_norm",
]

X = df[FEATURES]
y = df["risk_level"]
print(f"[2/7] Feature engineering done  →  {len(FEATURES)} features")

# ────────────────────────────────────────────────────
# 3. Train / Test Split
# ────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

# Optional SMOTE balancing
if HAS_SMOTE:
    sm = SMOTE(random_state=42)
    X_train_sc, y_train_sm = sm.fit_resample(X_train_sc, y_train)
    y_train = y_train_sm
    print(f"[3/7] SMOTE applied  →  training set: {X_train_sc.shape[0]} samples")
else:
    print("[3/7] Train/test split  →  train:", X_train_sc.shape[0], " test:", X_test_sc.shape[0])

# ────────────────────────────────────────────────────
# 4. Baseline Model Comparison
# ────────────────────────────────────────────────────
print("\n[4/7] Baseline model comparison (5-fold CV)...")
baselines = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "SVM":                 SVC(kernel="rbf", random_state=42, probability=True),
    "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=42),
    "Gradient Boosting":   GradientBoostingClassifier(n_estimators=100, random_state=42),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
baseline_results = {}
for name, clf in baselines.items():
    scores = cross_val_score(clf, X_train_sc, y_train, cv=cv, scoring="accuracy", n_jobs=-1)
    baseline_results[name] = scores
    print(f"    {name:25s}  mean={scores.mean():.4f}  std={scores.std():.4f}")

# ── Plot baseline comparison ──
fig, ax = plt.subplots(figsize=(9, 4))
names  = list(baseline_results.keys())
means  = [v.mean() for v in baseline_results.values()]
stds   = [v.std()  for v in baseline_results.values()]
bars = ax.barh(names, means, xerr=stds, color=["#028090","#02C39A","#1A2B4A","#F9A825"],
               capsize=4, edgecolor="white", height=0.55)
ax.set_xlabel("CV Accuracy", fontsize=11)
ax.set_title("Baseline Model Comparison (5-fold CV)", fontsize=13, fontweight="bold")
ax.set_xlim(0, 1.05)
for bar, mean in zip(bars, means):
    ax.text(mean + 0.01, bar.get_y() + bar.get_height()/2,
            f"{mean:.3f}", va="center", fontsize=10)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
plt.savefig(PLOTS / "01_baseline_comparison.png", dpi=150)
plt.close()

# ────────────────────────────────────────────────────
# 5. Hyperparameter Tuning (Random Forest)
# ────────────────────────────────────────────────────
print("\n[5/7] Hyperparameter tuning (RandomForest + GridSearchCV)...")
param_grid = {
    "n_estimators":      [100, 200, 300],
    "max_depth":         [6, 8, 10, None],
    "min_samples_split": [2, 5],
    "max_features":      ["sqrt", "log2"],
}
rf_base = RandomForestClassifier(random_state=42, n_jobs=-1)
gs = GridSearchCV(rf_base, param_grid, cv=cv, scoring="accuracy", n_jobs=-1, verbose=0)
gs.fit(X_train_sc, y_train)
best_params = gs.best_params_
print(f"    Best params: {best_params}")
print(f"    Best CV accuracy: {gs.best_score_:.4f}")

# ────────────────────────────────────────────────────
# 6. Final Model Evaluation
# ────────────────────────────────────────────────────
print("\n[6/7] Evaluating final model on held-out test set...")
model = gs.best_estimator_
y_pred  = model.predict(X_test_sc)
y_proba = model.predict_proba(X_test_sc)

acc = accuracy_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="macro")

print(f"\n    Accuracy : {acc:.4f}  ({acc*100:.1f}%)")
print(f"    ROC-AUC  : {auc:.4f}  (macro OvR)")
print(f"\n    Classification Report:")
print(classification_report(y_test, y_pred,
      target_names=[LABEL_MAP[i] for i in range(4)], digits=4))

# ── Confusion Matrix ──
cm  = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots(figsize=(7, 5.5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=[LABEL_MAP[i] for i in range(4)],
            yticklabels=[LABEL_MAP[i] for i in range(4)],
            linewidths=0.5, linecolor="white", ax=ax,
            annot_kws={"size": 13, "weight": "bold"})
ax.set_xlabel("Predicted Label", fontsize=11, labelpad=10)
ax.set_ylabel("True Label",      fontsize=11, labelpad=10)
ax.set_title("Confusion Matrix — ADAPT-LD Classifier", fontsize=13, fontweight="bold", pad=14)
plt.tight_layout()
plt.savefig(PLOTS / "02_confusion_matrix.png", dpi=150)
plt.close()

# ── Per-class accuracy bars ──
report = classification_report(y_test, y_pred,
         target_names=[LABEL_MAP[i] for i in range(4)],
         output_dict=True)
classes = [LABEL_MAP[i] for i in range(4)]
f1s  = [report[c]["f1-score"]  for c in classes]
prec = [report[c]["precision"] for c in classes]
rec  = [report[c]["recall"]    for c in classes]

x = np.arange(len(classes))
w = 0.26
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(x - w, prec, w, label="Precision", color="#028090", edgecolor="white")
ax.bar(x,     rec,  w, label="Recall",    color="#02C39A", edgecolor="white")
ax.bar(x + w, f1s,  w, label="F1-Score",  color="#1A2B4A", edgecolor="white")
ax.set_xticks(x); ax.set_xticklabels(classes, fontsize=10)
ax.set_ylim(0, 1.12); ax.set_ylabel("Score", fontsize=11)
ax.set_title("Per-Class Precision / Recall / F1", fontsize=13, fontweight="bold")
ax.legend(fontsize=10); ax.spines[["top","right"]].set_visible(False)
for bar in ax.patches:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.015,
            f"{bar.get_height():.2f}", ha="center", fontsize=8, color="#333")
plt.tight_layout()
plt.savefig(PLOTS / "03_per_class_metrics.png", dpi=150)
plt.close()

# ────────────────────────────────────────────────────
# 7. Feature Importance
# ────────────────────────────────────────────────────
print("[7/7] Computing feature importance...")
importances = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(8, 5))
colors_fi = ["#C0392B" if v >= importances.nlargest(3).min() else "#028090" for v in importances]
bars = ax.barh(importances.index, importances.values, color=colors_fi, edgecolor="white", height=0.65)
ax.set_xlabel("Mean Decrease in Impurity", fontsize=11)
ax.set_title("Feature Importance — ADAPT-LD Random Forest", fontsize=13, fontweight="bold")
ax.spines[["top","right"]].set_visible(False)
for bar, val in zip(bars, importances.values):
    ax.text(val + 0.002, bar.get_y() + bar.get_height()/2,
            f"{val:.3f}", va="center", fontsize=9)
plt.tight_layout()
plt.savefig(PLOTS / "04_feature_importance.png", dpi=150)
plt.close()

# ── Risk distribution in test set ──
pred_labels = [LABEL_MAP[p] for p in y_pred]
dist = pd.Series(pred_labels).value_counts().reindex([LABEL_MAP[i] for i in range(4)]).fillna(0)
fig, ax = plt.subplots(figsize=(7, 4))
wedges, texts, autotexts = ax.pie(
    dist, labels=dist.index, autopct="%1.1f%%",
    colors=COLORS, startangle=140,
    wedgeprops={"edgecolor": "white", "linewidth": 2},
    textprops={"fontsize": 11}
)
for at in autotexts: at.set_fontsize(10); at.set_color("white"); at.set_fontweight("bold")
ax.set_title("Predicted Risk Distribution (Test Set)", fontsize=13, fontweight="bold", pad=16)
plt.tight_layout()
plt.savefig(PLOTS / "05_risk_distribution.png", dpi=150)
plt.close()

# ────────────────────────────────────────────────────
# Save Model Artefacts
# ────────────────────────────────────────────────────
joblib.dump(model,  MODELS / "adapt_ld_rf_model.pkl")
joblib.dump(scaler, MODELS / "adapt_ld_scaler.pkl")

feature_meta = {"features": FEATURES, "label_map": LABEL_MAP, "best_params": best_params}
import json
with open(MODELS / "adapt_ld_metadata.json", "w") as f:
    json.dump(feature_meta, f, indent=2)

print(f"\n{'='*60}")
print("  TRAINING COMPLETE")
print(f"{'='*60}")
print(f"  Model     → {MODELS / 'adapt_ld_rf_model.pkl'}")
print(f"  Scaler    → {MODELS / 'adapt_ld_scaler.pkl'}")
print(f"  Metadata  → {MODELS / 'adapt_ld_metadata.json'}")
print(f"  Plots     → {PLOTS}/")
print(f"\n  Final Accuracy : {acc*100:.1f}%")
print(f"  Final ROC-AUC  : {auc:.4f}")
print(f"{'='*60}\n")
