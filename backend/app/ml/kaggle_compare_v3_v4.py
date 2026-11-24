
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "processed" / "kaggle_ml_features.csv"

OUTPUT_PATH = (
    BASE_DIR / "processed" / "kaggle_fair_v3_v4_comparison.csv"
)


# --------------------------------------------------
# 2. Load dataset
# --------------------------------------------------

df = pd.read_csv(DATA_PATH)

df.columns = df.columns.str.strip().str.lower()

# Dataset date column is sale_date
df["sale_date"] = pd.to_datetime(df["sale_date"])

df = df.sort_values("sale_date").reset_index(drop=True)


# --------------------------------------------------
# 3. Define feature sets
# --------------------------------------------------

# Historical-only features (V4)
v4_numeric = [
    "day_of_week",
    "month",
    "is_weekend",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
    "rolling_mean_14",
]

v4_categorical = [
    "store_id",
    "product_id",
]


# Historical + additional features (V3)
v3_numeric = [
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
    "competitor_pricing",
]

v3_categorical = [
    "store_id",
    "product_id",
    "weather_condition",
    "promotion",
    "seasonality",
    "epidemic",
]


target = "quantity_sold"


# --------------------------------------------------
# 4. Validate required columns
# --------------------------------------------------

required = list(set(
    v3_numeric
    + v3_categorical
    + [target, "sale_date"]
))

missing = [col for col in required if col not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

# Use exactly the same rows for both models
df = df.dropna(subset=required).copy()


# --------------------------------------------------
# 5. Identical chronological split
# --------------------------------------------------

unique_dates = sorted(df["sale_date"].unique())

split_index = int(len(unique_dates) * 0.80)
split_date = unique_dates[split_index]

train = df[df["sale_date"] < split_date].copy()
test = df[df["sale_date"] >= split_date].copy()

print("\n========== COMMON DATA SPLIT ==========")
print("Total records:", len(df))
print("Training records:", len(train))
print("Testing records:", len(test))
print("Training ends:", train["sale_date"].max().date())
print("Testing starts:", test["sale_date"].min().date())


# --------------------------------------------------
# 6. Model evaluation function
# --------------------------------------------------

def train_and_evaluate(
    name,
    numeric_features,
    categorical_features,
):

    features = numeric_features + categorical_features

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
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

    model.fit(
        train[features],
        train[target],
    )

    predictions = model.predict(test[features])

    return {
        "Model": name,
        "MAE": mean_absolute_error(
            test[target], predictions
        ),
        "RMSE": np.sqrt(
            mean_squared_error(test[target], predictions)
        ),
        "R2": r2_score(
            test[target], predictions
        ),
    }


# --------------------------------------------------
# 7. Train both models
# --------------------------------------------------

print("\nTraining V3 enhanced-feature model...")

v3_result = train_and_evaluate(
    "V3 - Enhanced Features",
    v3_numeric,
    v3_categorical,
)

print("Training V4 historical-only model...")

v4_result = train_and_evaluate(
    "V4 - Historical Only",
    v4_numeric,
    v4_categorical,
)


# --------------------------------------------------
# 8. Seasonal-naive baseline
# --------------------------------------------------

baseline_predictions = test["lag_7"]

baseline_result = {
    "Model": "Seasonal Naive Baseline",
    "MAE": mean_absolute_error(
        test[target], baseline_predictions
    ),
    "RMSE": np.sqrt(
        mean_squared_error(test[target], baseline_predictions)
    ),
    "R2": r2_score(
        test[target], baseline_predictions
    ),
}


# --------------------------------------------------
# 9. Display comparison
# --------------------------------------------------

comparison = pd.DataFrame([
    v3_result,
    v4_result,
    baseline_result,
])

print("\n========== FAIR V3 vs V4 COMPARISON ==========")

print(
    comparison.to_string(
        index=False,
        formatters={
            "MAE": "{:.4f}".format,
            "RMSE": "{:.4f}".format,
            "R2": "{:.4f}".format,
        },
    )
)

comparison.to_csv(OUTPUT_PATH, index=False)

print("\nComparison saved:")
print(OUTPUT_PATH)
