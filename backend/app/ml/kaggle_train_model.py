
import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ----------------------------------
# 1. Define project paths
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "processed" / "kaggle_ml_features.csv"

MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = MODEL_DIR / "kaggle_random_forest_model.pkl"

PREDICTION_FILE = BASE_DIR / "processed" / "kaggle_model_predictions.csv"


# ----------------------------------
# 2. Load feature dataset
# ----------------------------------

print("Loading Kaggle feature dataset...")

df = pd.read_csv(INPUT_FILE)

df["sale_date"] = pd.to_datetime(df["sale_date"])

print("Dataset shape:", df.shape)


# ----------------------------------
# 3. Select input features and target
# ----------------------------------

FEATURES = [
    "day_of_week",
    "month",
    "is_weekend",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
    "rolling_mean_14"
]

TARGET = "quantity_sold"

X = df[FEATURES]
y = df[TARGET]


# ----------------------------------
# 4. Chronological train-test split
# ----------------------------------

print("\nSplitting dataset chronologically...")

unique_dates = sorted(df["sale_date"].unique())

split_index = int(len(unique_dates) * 0.80)

split_date = unique_dates[split_index]

train_mask = df["sale_date"] < split_date
test_mask = df["sale_date"] >= split_date

X_train = X.loc[train_mask]
X_test = X.loc[test_mask]

y_train = y.loc[train_mask]
y_test = y.loc[test_mask]

print("Training date range:",
      df.loc[train_mask, "sale_date"].min(),
      "to",
      df.loc[train_mask, "sale_date"].max())

print("Testing date range:",
      df.loc[test_mask, "sale_date"].min(),
      "to",
      df.loc[test_mask, "sale_date"].max())

print("Training records:", len(X_train))
print("Testing records:", len(X_test))


# ----------------------------------
# 5. Train Random Forest model
# ----------------------------------

print("\nTraining Kaggle Random Forest model...")

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("Model training completed!")


# ----------------------------------
# 6. Generate predictions
# ----------------------------------

print("\nGenerating test predictions...")

rf_predictions = model.predict(X_test)

# Seasonal-naive baseline:
# Predict today's sales using sales from 7 days earlier.
baseline_predictions = X_test["lag_7"].to_numpy()


# ----------------------------------
# 7. Evaluate both models
# ----------------------------------

def evaluate_model(actual, predicted, model_name):

    mae = mean_absolute_error(actual, predicted)

    rmse = np.sqrt(mean_squared_error(actual, predicted))

    r2 = r2_score(actual, predicted)

    print(f"\n{model_name}")
    print("-" * 40)
    print(f"MAE  : {mae:.4f}")
    print(f"RMSE : {rmse:.4f}")
    print(f"R2   : {r2:.4f}")

    return {
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    }


rf_metrics = evaluate_model(
    y_test,
    rf_predictions,
    "Random Forest"
)

baseline_metrics = evaluate_model(
    y_test,
    baseline_predictions,
    "Seasonal Naive Baseline"
)


# ----------------------------------
# 8. Save predictions
# ----------------------------------

results = df.loc[test_mask, [
    "sale_date",
    "store_id",
    "product_id",
    "quantity_sold"
]].copy()

results["random_forest_prediction"] = rf_predictions

results["seasonal_naive_prediction"] = baseline_predictions

results.to_csv(PREDICTION_FILE, index=False)


# ----------------------------------
# 9. Save trained model
# ----------------------------------

joblib.dump(model, MODEL_FILE)


# ----------------------------------
# 10. Display final results
# ----------------------------------

print("\n========== KAGGLE MODEL TRAINING COMPLETED ==========")

print("\nModel saved at:")
print(MODEL_FILE)

print("\nPredictions saved at:")
print(PREDICTION_FILE)

print("\nFeature importance:")

importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

print(importance.to_string(index=False))

print("\nTraining and evaluation completed successfully!")
