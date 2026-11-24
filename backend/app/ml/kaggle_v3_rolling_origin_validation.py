
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# =====================================================
# 1. PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "processed" / "kaggle_ml_features.csv"

OUTPUT_DIR = BASE_DIR / "processed"

PREDICTIONS_FILE = (
    OUTPUT_DIR / "kaggle_v3_rolling_origin_predictions.csv"
)

METRICS_FILE = (
    OUTPUT_DIR / "kaggle_v3_rolling_origin_metrics.csv"
)

DAILY_METRICS_FILE = (
    OUTPUT_DIR / "kaggle_v3_rolling_origin_daily_metrics.csv"
)


# =====================================================
# 2. MODEL CONFIGURATION - SAME AS V3
# =====================================================

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

RANDOM_FOREST_CONFIG = {
    "n_estimators": 300,
    "max_depth": 15,
    "min_samples_leaf": 2,
    "random_state": 42,
    "n_jobs": -1
}


# =====================================================
# 3. CREATE MODEL
# =====================================================

def create_model():

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

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(**RANDOM_FOREST_CONFIG)
            )
        ]
    )

    return model


# =====================================================
# 4. CREATE FORECAST FEATURES
# =====================================================

def create_forecast_features(
    forecast_date,
    latest_row,
    sales_history
):

    features = {}

    # Calendar features
    features["day_of_week"] = forecast_date.weekday()
    features["month"] = forecast_date.month
    features["is_weekend"] = int(
        forecast_date.weekday() >= 5
    )

    # Historical sales features
    features["lag_1"] = sales_history[-1]
    features["lag_7"] = sales_history[-7]
    features["lag_14"] = sales_history[-14]

    features["rolling_mean_7"] = np.mean(
        sales_history[-7:]
    )

    features["rolling_mean_14"] = np.mean(
        sales_history[-14:]
    )

    # Hold latest known external values constant.
    for column in [
        "inventory_level",
        "discount",
        "price",
        "competitor_pricing"
    ]:
        features[column] = latest_row[column]

    for column in CATEGORICAL_FEATURES:
        if column in ["store_id", "product_id"]:
            features[column] = latest_row[column]
        else:
            features[column] = latest_row[column]

    return pd.DataFrame(
        [features],
        columns=FEATURES
    )


# =====================================================
# 5. LOAD DATA
# =====================================================

def main():

    print("\n========== V3 ROLLING-ORIGIN VALIDATION ==========\n")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_FILE)

    df["sale_date"] = pd.to_datetime(df["sale_date"])

    df = df.sort_values(
        ["store_id", "product_id", "sale_date"]
    ).reset_index(drop=True)

    required_columns = FEATURES + [
        "sale_date",
        TARGET
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    print("Dataset shape:", df.shape)

    # Group historical records by store and product.
    grouped_data = {
        key: group.reset_index(drop=True)
        for key, group in df.groupby(
            ["store_id", "product_id"]
        )
    }

    # Create actual sales lookup for scoring.
    actual_lookup = {}

    for key, group in grouped_data.items():

        actual_lookup[key] = {
            row.sale_date: float(getattr(row, TARGET))
            for row in group.itertuples(index=False)
        }

    # Same 21 weekly forecast origins as the
    # existing fixed-model backtest.
    forecast_origins = pd.date_range(
        start="2023-09-02",
        end="2024-01-20",
        freq="7D"
    )

    all_results = []

    print("Forecast origins:", len(forecast_origins))
    print("Store-product groups:", len(grouped_data))

    # =================================================
    # 6. ROLLING-ORIGIN TRAINING AND FORECASTING
    # =================================================

    for origin_number, origin in enumerate(
        forecast_origins, start=1
    ):

        origin = pd.Timestamp(origin)

        print(
            f"\nOrigin {origin_number}/{len(forecast_origins)}"
            f" | Date: {origin.date()}"
        )

        # Train only with data available on or before origin.
        train_df = df[df["sale_date"] <= origin].copy()

        if train_df.empty:
            raise ValueError(
                f"No training data available at {origin}"
            )

        X_train = train_df[FEATURES]
        y_train = train_df[TARGET]

        # Fresh model for this forecast origin.
        model = create_model()

        print("Training records:", len(train_df))

        model.fit(X_train, y_train)

        print("Model trained.")

        # =============================================
        # 7. FORECAST EACH STORE-PRODUCT COMBINATION
        # =============================================

        for key, group in grouped_data.items():

            store_id, product_id = key

            history_df = group[
                group["sale_date"] <= origin
            ].copy()

            if history_df.empty:
                continue

            latest_row = history_df.iloc[-1]

            # Require a complete history through origin.
            if latest_row["sale_date"] != origin:
                continue

            sales_history = (
                history_df[TARGET].astype(float).tolist()
            )

            # Independent history for seasonal-naive.
            naive_history = sales_history.copy()

            if len(sales_history) < 14:
                continue

            # Recursive seven-day forecast.
            for forecast_day in range(1, 8):

                forecast_date = (
                    origin + pd.Timedelta(days=forecast_day)
                )

                # Stop if actual data is unavailable.
                if forecast_date not in actual_lookup[key]:
                    continue

                X_future = create_forecast_features(
                    forecast_date,
                    latest_row,
                    sales_history
                )

                predicted_demand = float(
                    model.predict(X_future)[0]
                )

                predicted_demand = max(
                    0.0, predicted_demand
                )

                # Seasonal-naive uses its own history.
                seasonal_naive = max(
                    0.0,
                    float(naive_history[-7])
                )

                actual_sales = actual_lookup[key][
                    forecast_date
                ]

                all_results.append({
                    "forecast_origin": origin.date(),
                    "forecast_date": forecast_date.date(),
                    "forecast_day": forecast_day,
                    "store_id": store_id,
                    "product_id": product_id,
                    "predicted_demand": predicted_demand,
                    "seasonal_naive_prediction": seasonal_naive,
                    "actual_sales": actual_sales,
                    "absolute_error": abs(
                        actual_sales - predicted_demand
                    ),
                    "naive_absolute_error": abs(
                        actual_sales - seasonal_naive
                    )
                })

                # Append predictions, not actual future sales.
                sales_history.append(predicted_demand)
                naive_history.append(seasonal_naive)

        print("Forecast origin completed.")

    # =================================================
    # 8. SAVE PREDICTIONS
    # =================================================

    results = pd.DataFrame(all_results)

    if results.empty:
        raise ValueError("No forecast predictions generated.")

    results.to_csv(PREDICTIONS_FILE, index=False)

    print("\nPredictions saved:", PREDICTIONS_FILE)

    # =================================================
    # 9. OVERALL EVALUATION
    # =================================================

    actual = results["actual_sales"]
    predicted = results["predicted_demand"]
    naive = results["seasonal_naive_prediction"]

    v3_mae = mean_absolute_error(actual, predicted)
    v3_rmse = np.sqrt(mean_squared_error(actual, predicted))
    v3_r2 = r2_score(actual, predicted)

    naive_mae = mean_absolute_error(actual, naive)
    naive_rmse = np.sqrt(mean_squared_error(actual, naive))
    naive_r2 = r2_score(actual, naive)

    metrics = pd.DataFrame([
        {
            "model": "V3 Rolling-Origin",
            "MAE": v3_mae,
            "RMSE": v3_rmse,
            "R2": v3_r2
        },
        {
            "model": "Seasonal Naive",
            "MAE": naive_mae,
            "RMSE": naive_rmse,
            "R2": naive_r2
        }
    ])

    metrics.to_csv(METRICS_FILE, index=False)

    # =================================================
    # 10. DAY-WISE EVALUATION
    # =================================================

    daily_rows = []

    for day, day_df in results.groupby("forecast_day"):

        daily_rows.append({
            "forecast_day": day,
            "v3_mae": mean_absolute_error(
                day_df["actual_sales"],
                day_df["predicted_demand"]
            ),
            "naive_mae": mean_absolute_error(
                day_df["actual_sales"],
                day_df["seasonal_naive_prediction"]
            ),
            "v3_rmse": np.sqrt(
                mean_squared_error(
                    day_df["actual_sales"],
                    day_df["predicted_demand"]
                )
            ),
            "naive_rmse": np.sqrt(
                mean_squared_error(
                    day_df["actual_sales"],
                    day_df["seasonal_naive_prediction"]
                )
            ),
            "records": len(day_df)
        })

    daily_metrics = pd.DataFrame(daily_rows)

    daily_metrics.to_csv(
        DAILY_METRICS_FILE,
        index=False
    )

    # =================================================
    # 11. FINAL REPORT
    # =================================================

    print("\n========== ROLLING-ORIGIN RESULTS ==========")

    print("\nV3 Rolling-Origin:")
    print(f"MAE  : {v3_mae:.4f}")
    print(f"RMSE : {v3_rmse:.4f}")
    print(f"R2   : {v3_r2:.4f}")

    print("\nSeasonal Naive:")
    print(f"MAE  : {naive_mae:.4f}")
    print(f"RMSE : {naive_rmse:.4f}")
    print(f"R2   : {naive_r2:.4f}")

    print("\nTotal forecast records:", len(results))

    print("\nDay-wise results:")
    print(daily_metrics.to_string(index=False))

    print("\nMetrics saved:", METRICS_FILE)
    print("Daily metrics saved:", DAILY_METRICS_FILE)

    print("\nROLLING-ORIGIN VALIDATION COMPLETED!")


if __name__ == "__main__":
    main()
