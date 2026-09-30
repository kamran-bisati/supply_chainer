import pandas as pd
import numpy as np

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)
from sklearn.ensemble import GradientBoostingRegressor

import joblib
import os


# ============================================================
# SUPPLYCHAINER MULTI-QUANTILE ML MODEL
# P50 / P85 / P95
# ============================================================

print("=" * 70)
print("SUPPLYCHAINER MULTI-QUANTILE ML MODEL TRAINING")
print("=" * 70)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\n--- Loading Data ---")

DATA_PATH = "Super_Supply_Chain_Data_Fixed.csv"
MODEL_DIR = "Execution"

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH}"
    )

df = pd.read_csv(
    DATA_PATH,
    encoding="latin1"
)

df = df.dropna(
    subset=["Transport_Mode"]
)

print(
    f"Data ready. Total rows: {df.shape[0]}"
)


# ============================================================
# 2. CATEGORICAL ENCODING
# ============================================================

print("\n--- Categorical Encoding ---")

le_dict = {}

categorical_cols = [
    "Leg_Type",
    "Origin_Node",
    "Destination_Node",
    "Transport_Mode",
    "Condition_Flag"
]

for col in categorical_cols:

    if col not in df.columns:
        raise ValueError(
            f"Required column missing: {col}"
        )

    le = LabelEncoder()

    df[col] = le.fit_transform(
        df[col].astype(str)
    )

    le_dict[col] = le

    print(
        f"  Encoded {col}: "
        f"{len(le.classes_)} classes"
    )

print(
    "Text features successfully converted "
    "to numeric matrices."
)


# ============================================================
# 3. FEATURES / TARGET
# ============================================================

print("\n--- Preparing Features and Target ---")

if "Delay_Hours" not in df.columns:
    raise ValueError(
        "Required target column 'Delay_Hours' is missing."
    )

X = df.drop(
    ["Delay_Hours"],
    axis=1
)

y = df["Delay_Hours"]

# Delays cannot be negative.
y = np.maximum(
    0,
    y
)


# ============================================================
# 4. TRAIN / TEST SPLIT
# ============================================================

print(
    "\n--- Splitting Data for Training & Testing ---"
)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

print(
    f"Training on {X_train.shape[0]} scenarios, "
    f"Testing on {X_test.shape[0]} scenarios."
)


# ============================================================
# 5. QUANTILES
# ============================================================

QUANTILES = {
    "p50": 0.50,
    "p85": 0.85,
    "p95": 0.95
}

models = {}
predictions = {}


# ============================================================
# 6. TRAIN THREE QUANTILE MODELS
# ============================================================

print("\n--- Training P50 / P85 / P95 Models ---")

for quantile_name, alpha in QUANTILES.items():

    print("\n" + "-" * 70)

    print(
        f"Training {quantile_name.upper()} "
        f"(alpha={alpha})"
    )

    model = GradientBoostingRegressor(
        loss="quantile",
        alpha=alpha,
        n_estimators=250,
        learning_rate=0.1,
        max_depth=6,
        random_state=42
    )

    model.fit(
        X_train,
        y_train
    )

    models[quantile_name] = model

    print(
        f"{quantile_name.upper()} model trained successfully."
    )


# ============================================================
# 7. BLIND TEST
# ============================================================

print("\n" + "=" * 70)
print("MODEL PERFORMANCE")
print("=" * 70)

for quantile_name, model in models.items():

    y_pred = model.predict(
        X_test
    )

    y_pred = np.maximum(
        0,
        y_pred
    )

    predictions[quantile_name] = y_pred

    mae = mean_absolute_error(
        y_test,
        y_pred
    )

    mse = mean_squared_error(
        y_test,
        y_pred
    )

    rmse = np.sqrt(
        mse
    )

    r2 = r2_score(
        y_test,
        y_pred
    )

    print(
        f"\n{quantile_name.upper()}"
    )

    print(
        f"  MAE : {mae:.2f} hours"
    )

    print(
        f"  RMSE: {rmse:.2f} hours"
    )

    print(
        f"  R2  : {r2:.4f}"
    )


# ============================================================
# 8. PREDICTION TABLE
# ============================================================

results_df = pd.DataFrame({
    "Actual Delay (Hours)": y_test.values[:10],

    "AI Predicted P50 (Hours)": np.round(
        predictions["p50"][:10],
        2
    ),

    "AI Predicted P85 (Hours)": np.round(
        predictions["p85"][:10],
        2
    ),

    "AI Predicted P95 (Hours)": np.round(
        predictions["p95"][:10],
        2
    )
})

print(
    "\n--- Prediction Analysis Table ---"
)

print(
    results_df
)


# ============================================================
# 9. CREATE EXECUTION DIRECTORY
# ============================================================

if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)


# ============================================================
# 10. SAVE P50 / P85 / P95
# ============================================================

print("\n--- Exporting Production Models ---")

for quantile_name, model in models.items():

    output_path = os.path.join(
        MODEL_DIR,
        f"risk_model_{quantile_name}.pkl"
    )

    joblib.dump(
        model,
        output_path
    )

    print(
        f"[SAVED] {output_path}"
    )


# ============================================================
# 11. BACKWARD COMPATIBILITY
# ============================================================

# Existing Supplychainer code expects:
#
#     Execution/risk_model.pkl
#
# Keep this file as P85 until the backend has been migrated
# completely to the three-model predictor.

legacy_model_path = os.path.join(
    MODEL_DIR,
    "risk_model.pkl"
)

joblib.dump(
    models["p85"],
    legacy_model_path
)

print(
    f"[SAVED] {legacy_model_path}"
)

print(
    "[INFO] risk_model.pkl remains the P85 compatibility model."
)


# ============================================================
# 12. SAVE ENCODERS
# ============================================================

encoder_path = os.path.join(
    MODEL_DIR,
    "label_encoders.pkl"
)

joblib.dump(
    le_dict,
    encoder_path
)

print(
    f"[SAVED] {encoder_path}"
)


# ============================================================
# 13. SANITY CHECK
# ============================================================

print("\n" + "=" * 70)
print("MULTI-QUANTILE SANITY CHECK")
print("=" * 70)

sample_count = min(
    5,
    len(X_test)
)

for index in range(sample_count):

    row = X_test.iloc[
        index:index + 1
    ]

    p50 = max(
        0.0,
        float(
            models["p50"].predict(row)[0]
        )
    )

    p85 = max(
        0.0,
        float(
            models["p85"].predict(row)[0]
        )
    )

    p95 = max(
        0.0,
        float(
            models["p95"].predict(row)[0]
        )
    )

    print(
        f"Sample {index + 1}: "
        f"P50={p50:.2f}h | "
        f"P85={p85:.2f}h | "
        f"P95={p95:.2f}h"
    )


# ============================================================
# 14. FINAL
# ============================================================

print("\n" + "=" * 70)
print("MULTI-QUANTILE TRAINING COMPLETE")
print("=" * 70)

print("\nGenerated:")

print(
    "  Execution/risk_model_p50.pkl"
)

print(
    "  Execution/risk_model_p85.pkl"
)

print(
    "  Execution/risk_model_p95.pkl"
)

print(
    "  Execution/risk_model.pkl"
)

print(
    "  Execution/label_encoders.pkl"
)

print("\nP50 / P85 / P95 models are ready.")