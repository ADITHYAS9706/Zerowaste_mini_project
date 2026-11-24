
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import ParameterGrid, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "processed" / "kaggle_ml_features.csv"

MODEL_PATH = (
    BASE_DIR / "models" / "kaggle_random_forest_v4_tuned.pkl"
)

PREDICTIONS_PATH = (
    BASE_DIR / "processed" / "kaggle_model_predictions_v4_tuned.csv"
)

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Load data
# --------------------------------------------------

df = pd.read_csv(DATA_PATH)

df.columns = df.columns.str.strip().str.lower()

df["sale_date"] = pd.to_datetime(df["sale_date"])

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
    numeric_features
    + categorical_features
    + [target, "sale_date"]
)

missing = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing:
    raise ValueError(f"Missing columns: {missing}")

df = df.dropna(subset=required_columns).copy()

df = df.sort_values("sale_date").reset_index(drop=True)


# --------------------------------------------------
# 3. Chronological train-test split
# --------------------------------------------------

unique_dates = np.array(sorted(df["sale_date"].unique()))

split_index = int(len(unique_dates) * 0.80)

split_date = unique_dates[split_index]

train = df[df["sale_date"] < split_date].copy()

test = df[df["sale_date"] >= split_date].copy()

feature_columns = numeric_features + categorical_features

X_train = train[feature_columns]
y_train = train[target]

X_test = test[feature_columns]
y_test = test[target]

print("\n========== DATA SPLIT ==========")
print("Total records:", len(df))
print("Training records:", len(train))
print("Testing records:", len(test))
print("Training ends:", train["sale_date"].max().date())
print("Testing starts:", test["sale_date"].min().date())


# --------------------------------------------------
# 4. Model creation function
# --------------------------------------------------

def create_model(parameters):

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
            (
                "numerical",
                "passthrough",
                numeric_features,
            ),
        ]
    )

    random_forest = RandomForestRegressor(
        random_state=42,
        n_jobs=-1,
        **parameters,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", random_forest),
        ]
    )


# --------------------------------------------------
# 5. Hyperparameter search
# --------------------------------------------------

parameter_grid = {
    "n_estimators": [300, 500],
    "max_depth": [10, 15, None],
    "min_samples_split": [2, 5],
    "min_samples_leaf": [2, 4],
    "max_features": [0.8, 1.0],
}

all_parameters = list(ParameterGrid(parameter_grid))

# Cross-validation is performed on training dates only.
training_dates = np.array(sorted(train["sale_date"].unique()))

time_split = TimeSeriesSplit(n_splits=3)

best_score = float("inf")
best_parameters = None

print("\n========== HYPERPARAMETER TUNING ==========")
print("Configurations:", len(all_parameters))
print("Chronological folds:", time_split.get_n_splits())

for parameter_number, parameters in enumerate(
    all_parameters, start=1
):

    fold_scores = []

    for fold_number, (train_indices, val_indices) in enumerate(
        time_split.split(training_dates), start=1
    ):

        fold_train_dates = training_dates[train_indices]
        fold_val_dates = training_dates[val_indices]

        fold_train = train[
            train["sale_date"].isin(fold_train_dates)
        ]

        fold_val = train[
            train["sale_date"].isin(fold_val_dates)
        ]

        fold_model = create_model(parameters)

        fold_model.fit(
            fold_train[feature_columns],
            fold_train[target],
        )

        fold_predictions = fold_model.predict(
            fold_val[feature_columns]
        )

        fold_mae = mean_absolute_error(
            fold_val[target],
            fold_predictions,
        )

        fold_scores.append(fold_mae)

    average_mae = float(np.mean(fold_scores))

    if average_mae < best_score:
        best_score = average_mae
        best_parameters = parameters.copy()

    if parameter_number % 5 == 0:
        print(
            f"Tested {parameter_number}/{len(all_parameters)} "
            f"| Current best CV MAE: {best_score:.4f}"
        )


print("\n========== BEST PARAMETERS ==========")
print(best_parameters)
print("Best cross-validation MAE:", round(best_score, 4))


# --------------------------------------------------
# 6. Train final tuned model
# --------------------------------------------------

print("\nTraining final tuned V4 model...")

tuned_model = create_model(best_parameters)

tuned_model.fit(X_train, y_train)

predictions = tuned_model.predict(X_test)


# --------------------------------------------------
# 7. Evaluate final test performance
# --------------------------------------------------

mae = mean_absolute_error(y_test, predictions)

rmse = np.sqrt(
    mean_squared_error(y_test, predictions)
)

r2 = r2_score(y_test, predictions)

baseline_predictions = test["lag_7"]

baseline_mae = mean_absolute_error(
    y_test,
    baseline_predictions,
)

baseline_rmse = np.sqrt(
    mean_squared_error(y_test, baseline_predictions)
)


print("\n========== TUNED V4 RESULTS ==========")

print("Training records:", len(train))
print("Testing records:", len(test))

print("\nRandom Forest V4 Tuned:")
print(f"MAE  : {mae:.4f}")
print(f"RMSE : {rmse:.4f}")
print(f"R2   : {r2:.4f}")

print("\nSeasonal Naive Baseline:")
print(f"MAE  : {baseline_mae:.4f}")
print(f"RMSE : {baseline_rmse:.4f}")


# --------------------------------------------------
# 8. Compare against previous V4
# --------------------------------------------------

old_model_path = (
    BASE_DIR / "models" / "kaggle_random_forest_v4.pkl"
)

if old_model_path.exists():

    old_model = joblib.load(old_model_path)

    old_predictions = old_model.predict(X_test)

    old_mae = mean_absolute_error(
        y_test, old_predictions
    )

    old_rmse = np.sqrt(
        mean_squared_error(y_test, old_predictions)
    )

    old_r2 = r2_score(y_test, old_predictions)

    print("\n========== OLD V4 vs TUNED V4 ==========")

    print(
        f"Old V4: "
        f"MAE={old_mae:.4f}, "
        f"RMSE={old_rmse:.4f}, "
        f"R2={old_r2:.4f}"
    )

    print(
        f"Tuned V4: "
        f"MAE={mae:.4f}, "
        f"RMSE={rmse:.4f}, "
        f"R2={r2:.4f}"
    )

    if mae < old_mae:
        print("\nTuned V4 improved MAE.")
    else:
        print("\nTuned V4 did not improve MAE.")


# --------------------------------------------------
# 9. Save predictions and model
# --------------------------------------------------

test_results = test.copy()

test_results["actual_sales"] = y_test.values
test_results["predicted_sales"] = predictions
test_results["baseline_sales"] = baseline_predictions.values

test_results.to_csv(PREDICTIONS_PATH, index=False)

joblib.dump(tuned_model, MODEL_PATH)

print("\nModel saved:", MODEL_PATH)
print("Predictions saved:", PREDICTIONS_PATH)

print("\nTuned V4 training completed.")

