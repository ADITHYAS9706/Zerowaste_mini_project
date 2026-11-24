
import pandas as pd
import numpy as np
import joblib

from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ----------------------------------
# 1. Paths
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "processed" / "kaggle_ml_features.csv"

MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = MODEL_DIR / "kaggle_random_forest_v3.pkl"

PREDICTION_FILE = BASE_DIR / "processed" / "kaggle_model_predictions_v3.csv"


# ----------------------------------
# 2. Load dataset
# ----------------------------------

print("Loading Kaggle feature dataset...")

df = pd.read_csv(INPUT_FILE)

df["sale_date"] = pd.to_datetime(df["sale_date"])

print("Dataset shape:", df.shape)


# ----------------------------------
# 3. Define features
# ----------------------------------

NUMERIC_FEATURES = [
    "day_of_week",
    "month",
    "is_weekend",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
    "rolling_mean_14",
    "inventory_level",
    "discount",
    "price",
    "competitor_pricing"
]

CATEGORICAL_FEATURES = [
    "store_id",
    "product_id",
    "weather_condition",
    "promotion",
    "seasonality",
    "epidemic"
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

TARGET = "quantity_sold"

X = df[FEATURES].copy()
y = df[TARGET]


# ----------------------------------
# 4. Chronological split
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

print("Training records:", len(X_train))
print("Testing records:", len(X_test))
print("Split date:", split_date)


# ----------------------------------
# 5. Preprocessing
# ----------------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            CATEGORICAL_FEATURES
        ),
        (
            "numerical",
            "passthrough",
            NUMERIC_FEATURES
        )
    ]
)


# ----------------------------------
# 6. Random Forest pipeline
# ----------------------------------

model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),

        ("regressor", RandomForestRegressor(
            n_estimators=300,
            max_depth=15,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ))
    ]
)


# ----------------------------------
# 7. Train
# ----------------------------------

print("\nTraining Random Forest V3...")

model.fit(X_train, y_train)

print("Training completed!")


# ----------------------------------
# 8. Predictions
# ----------------------------------

print("\nGenerating predictions...")

predictions = model.predict(X_test)


# ----------------------------------
# 9. Evaluation
# ----------------------------------

mae = mean_absolute_error(y_test, predictions)

rmse = np.sqrt(mean_squared_error(y_test, predictions))

r2 = r2_score(y_test, predictions)

print("\n========== RANDOM FOREST V3 RESULTS ==========")

print(f"MAE  : {mae:.4f}")
print(f"RMSE : {rmse:.4f}")
print(f"R2   : {r2:.4f}")


# ----------------------------------
# 10. Save predictions
# ----------------------------------

results = df.loc[test_mask, [
    "sale_date",
    "store_id",
    "product_id",
    "quantity_sold"
]].copy()

results["predicted_sales"] = predictions

results.to_csv(PREDICTION_FILE, index=False)


# ----------------------------------
# 11. Save model
# ----------------------------------

joblib.dump(model, MODEL_FILE)


# ----------------------------------
# 12. Feature importance
# ----------------------------------

rf = model.named_steps["regressor"]

encoded_names = (
    model.named_steps["preprocessor"]
    .get_feature_names_out()
)

importance = pd.DataFrame({
    "feature": encoded_names,
    "importance": rf.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

print("\nTop 15 feature importance values:")

print(importance.head(15).to_string(index=False))


# ----------------------------------
# 13. Prediction distribution
# ----------------------------------

print("\nActual sales standard deviation:",
      round(y_test.std(), 2))

print("Predicted sales standard deviation:",
      round(np.std(predictions), 2))


print("\nModel saved:", MODEL_FILE)

print("Predictions saved:", PREDICTION_FILE)

print("\nRandom Forest V3 completed successfully!")
