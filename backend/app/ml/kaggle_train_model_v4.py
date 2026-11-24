
from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "processed" / "kaggle_ml_features.csv"
MODEL_PATH = BASE_DIR / "models" / "kaggle_random_forest_v4.pkl"
PREDICTIONS_PATH = (
    BASE_DIR / "processed" / "kaggle_model_predictions_v4.csv"
)

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Load data
# --------------------------------------------------

df = pd.read_csv(DATA_PATH)

# Standardize column names
df.columns = df.columns.str.strip().str.lower()

print("Dataset columns:", df.columns.tolist())

df["sale_date"] = pd.to_datetime(df["sale_date"])

# Standardize the date column name for the V4 script
df = df.rename(columns={"sale_date": "date"})

numeric_features = [
    "day_of_week",
    "month",
    "is_weekend",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
    "rolling_mean_14",
]

categorical_features = [
    "store_id",
    "product_id",
]

target = "quantity_sold"

required_columns = (
    numeric_features + categorical_features + [target, "date"]
)

missing = [col for col in required_columns if col not in df.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

df = df.dropna(subset=required_columns).copy()
df = df.sort_values("date").reset_index(drop=True)


# --------------------------------------------------
# 3. Chronological train-test split
# --------------------------------------------------

unique_dates = sorted(df["date"].unique())

split_index = int(len(unique_dates) * 0.80)
split_date = unique_dates[split_index]

train = df[df["date"] < split_date].copy()
test = df[df["date"] >= split_date].copy()

X_train = train[numeric_features + categorical_features]
y_train = train[target]

X_test = test[numeric_features + categorical_features]
y_test = test[target]


# --------------------------------------------------
# 4. Build model
# --------------------------------------------------

preprocessor = ColumnTransformer(
    transformers=[
        ("categorical", OneHotEncoder(handle_unknown="ignore"),
         categorical_features),
        ("numerical", "passthrough", numeric_features),
    ]
)

model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "regressor",
            RandomForestRegressor(
                n_estimators=300,
                max_depth=15,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ]
)


# --------------------------------------------------
# 5. Train
# --------------------------------------------------

print("Training V4 historical-only model...")

model.fit(X_train, y_train)

predictions = model.predict(X_test)


# --------------------------------------------------
# 6. Evaluate model
# --------------------------------------------------

mae = mean_absolute_error(y_test, predictions)
rmse = mean_squared_error(y_test, predictions) ** 0.5
r2 = r2_score(y_test, predictions)

# Seasonal-naive baseline: same weekday last week
baseline_predictions = test["lag_7"]

baseline_mae = mean_absolute_error(y_test, baseline_predictions)
baseline_rmse = mean_squared_error(
    y_test, baseline_predictions
) ** 0.5

print("\n========== V4 MODEL RESULTS ==========")
print(f"Training records : {len(train)}")
print(f"Testing records  : {len(test)}")
print(f"Training ends    : {train['date'].max().date()}")
print(f"Testing starts   : {test['date'].min().date()}")

print("\nRandom Forest V4:")
print(f"MAE  : {mae:.4f}")
print(f"RMSE : {rmse:.4f}")
print(f"R2   : {r2:.4f}")

print("\nSeasonal Naive Baseline:")
print(f"MAE  : {baseline_mae:.4f}")
print(f"RMSE : {baseline_rmse:.4f}")


# --------------------------------------------------
# 7. Save model and predictions
# --------------------------------------------------

test["actual_sales"] = y_test.values
test["predicted_sales"] = predictions
test["baseline_sales"] = baseline_predictions.values

test.to_csv(PREDICTIONS_PATH, index=False)
joblib.dump(model, MODEL_PATH)

print("\nModel saved:", MODEL_PATH)
print("Predictions saved:", PREDICTIONS_PATH)
print("\nV4 training and evaluation completed.")
