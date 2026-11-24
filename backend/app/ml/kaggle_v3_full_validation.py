
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


# ==================================================
# 1. PATHS AND SETTINGS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "processed" / "kaggle_ml_features.csv"

MODEL_PATH = BASE_DIR / "models" / "kaggle_random_forest_v3.pkl"

OUTPUT_DIR = BASE_DIR / "processed"

HOLDOUT_OUTPUT = (
    OUTPUT_DIR / "kaggle_v3_holdout_evaluation.csv"
)

BACKTEST_OUTPUT = (
    OUTPUT_DIR / "kaggle_v3_seven_day_backtest.csv"
)

HORIZON_OUTPUT = (
    OUTPUT_DIR / "kaggle_v3_backtest_by_day.csv"
)

CUTOFF_DATE = pd.Timestamp("2023-09-02")

FORECAST_HORIZON = 7

# One forecast origin every seven days.
ORIGIN_INTERVAL = 7

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. MODEL FEATURES
# ==================================================

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
    "competitor_pricing",
]

CATEGORICAL_FEATURES = [
    "store_id",
    "product_id",
    "weather_condition",
    "promotion",
    "seasonality",
    "epidemic",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


# ==================================================
# 3. METRIC FUNCTION
# ==================================================

def calculate_metrics(actual, predicted):

    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    return {
        "MAE": round(
            mean_absolute_error(actual, predicted), 4
        ),
        "RMSE": round(
            np.sqrt(mean_squared_error(actual, predicted)), 4
        ),
        "R2": round(
            r2_score(actual, predicted), 4
        ),
    }


# ==================================================
# 4. LOAD DATA AND MODEL
# ==================================================

print("Loading feature dataset...")

df = pd.read_csv(DATA_PATH)

df.columns = df.columns.str.strip().str.lower()

df["sale_date"] = pd.to_datetime(df["sale_date"])

df = df.sort_values(
    ["store_id", "product_id", "sale_date"]
).reset_index(drop=True)

required_columns = FEATURES + [
    "sale_date",
    "quantity_sold",
]

missing = [
    column for column in required_columns
    if column not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

print("Dataset shape:", df.shape)

print("Loading saved V3 model...")

model = joblib.load(MODEL_PATH)


# ==================================================
# 5. HOLDOUT MODEL EVALUATION
# ==================================================

print("\n==========================================")
print("V3 HOLDOUT MODEL EVALUATION")
print("==========================================")

train_df = df[
    df["sale_date"] <= CUTOFF_DATE
].copy()

test_df = df[
    df["sale_date"] > CUTOFF_DATE
].copy()

if train_df.empty or test_df.empty:
    raise ValueError(
        "Invalid chronological train/test split."
    )

print("Training records:", len(train_df))
print("Testing records:", len(test_df))

print(
    "Training ends:",
    train_df["sale_date"].max()
)

print(
    "Testing starts:",
    test_df["sale_date"].min()
)

# Evaluate using same-day features.
# This matches the original V3 holdout evaluation.

X_test = test_df[FEATURES]

y_test = test_df["quantity_sold"].astype(float)

v3_predictions = np.maximum(
    0,
    model.predict(X_test)
)

# Seasonal-naive baseline using previous week's sales.

baseline_predictions = np.maximum(
    0,
    test_df["lag_7"].astype(float).to_numpy()
)

v3_metrics = calculate_metrics(
    y_test,
    v3_predictions
)

baseline_metrics = calculate_metrics(
    y_test,
    baseline_predictions
)

holdout_summary = pd.DataFrame([
    {
        "model": "Random Forest V3",
        **v3_metrics,
    },
    {
        "model": "Seasonal Naive (lag_7)",
        **baseline_metrics,
    },
])

print("\nHOLDOUT RESULTS")

print(
    holdout_summary.to_string(index=False)
)

holdout_summary.to_csv(
    HOLDOUT_OUTPUT,
    index=False
)

print("\nHoldout results saved:")
print(HOLDOUT_OUTPUT)


# ==================================================
# 6. ROLLING SEVEN-DAY BACKTEST
# ==================================================

print("\n==========================================")
print("ROLLING SEVEN-DAY BACKTEST")
print("==========================================")

all_dates = sorted(df["sale_date"].unique())

max_date = pd.Timestamp(
    df["sale_date"].max()
)

origin_dates = [
    pd.Timestamp(date)
    for date in all_dates
    if (
        pd.Timestamp(date) >= CUTOFF_DATE
        and pd.Timestamp(date)
        <= max_date - pd.Timedelta(
            days=FORECAST_HORIZON
        )
    )
]

# Use non-overlapping seven-day forecast windows.

origin_dates = origin_dates[::ORIGIN_INTERVAL]

if not origin_dates:
    raise ValueError(
        "No valid forecast origins found."
    )

print("Forecast origins:", len(origin_dates))

print("First origin:", origin_dates[0])

print("Last origin:", origin_dates[-1])

backtest_results = []

groups = df.groupby(
    ["store_id", "product_id"],
    sort=True
)


# ==================================================
# 7. GENERATE RECURSIVE BACKTEST PREDICTIONS
# ==================================================

for origin_index, origin_date in enumerate(
    origin_dates,
    start=1
):

    print(
        f"\nBacktesting origin {origin_index}/"
        f"{len(origin_dates)}: {origin_date.date()}"
    )

    for (store_id, product_id), group in groups:

        group = group.sort_values(
            "sale_date"
        ).copy()

        history_df = group[
            group["sale_date"] <= origin_date
        ]

        future_df = group[
            (group["sale_date"] > origin_date)
            & (
                group["sale_date"]
                <= origin_date
                + pd.Timedelta(days=FORECAST_HORIZON)
            )
        ].sort_values("sale_date")

        if len(history_df) < 14:
            continue

        if len(future_df) != FORECAST_HORIZON:
            continue

        # Verify all seven future dates are consecutive.

        expected_dates = [
            origin_date + pd.Timedelta(days=day)
            for day in range(1, FORECAST_HORIZON + 1)
        ]

        actual_dates = future_df[
            "sale_date"
        ].tolist()

        if actual_dates != expected_dates:
            continue

        latest = history_df.iloc[-1]

        # ------------------------------------------
        # Historical sales at forecast origin
        # ------------------------------------------

        sales_history = (
            history_df["quantity_sold"]
            .astype(float)
            .tolist()
        )

        # IMPORTANT:
        # Keep an independent history for the
        # seasonal-naive baseline.

        naive_history = sales_history.copy()

        # ------------------------------------------
        # Latest known inventory and external inputs
        # ------------------------------------------

        model_inventory = max(
            0.0,
            float(latest["inventory_level"])
        )

        current_price = float(
            latest["price"]
        )

        current_discount = float(
            latest["discount"]
        )

        current_competitor_price = float(
            latest["competitor_pricing"]
        )

        current_weather = latest[
            "weather_condition"
        ]

        current_promotion = latest[
            "promotion"
        ]

        current_seasonality = latest[
            "seasonality"
        ]

        current_epidemic = latest[
            "epidemic"
        ]

        # ------------------------------------------
        # Recursive seven-day forecasting
        # ------------------------------------------

        for forecast_day in range(
            1,
            FORECAST_HORIZON + 1
        ):

            forecast_date = (
                origin_date
                + pd.Timedelta(days=forecast_day)
            )

            # Calendar features

            day_of_week = forecast_date.dayofweek

            month = forecast_date.month

            is_weekend = int(
                day_of_week >= 5
            )

            # --------------------------------------
            # V3 historical and predicted features
            # --------------------------------------

            lag_1 = sales_history[-1]

            lag_7 = sales_history[-7]

            lag_14 = sales_history[-14]

            rolling_mean_7 = np.mean(
                sales_history[-7:]
            )

            rolling_mean_14 = np.mean(
                sales_history[-14:]
            )

            # --------------------------------------
            # Prepare model input
            # --------------------------------------

            input_data = pd.DataFrame([{

                "day_of_week": day_of_week,

                "month": month,

                "is_weekend": is_weekend,

                "lag_1": lag_1,

                "lag_7": lag_7,

                "lag_14": lag_14,

                "rolling_mean_7": rolling_mean_7,

                "rolling_mean_14": rolling_mean_14,

                "inventory_level": model_inventory,

                "discount": current_discount,

                "price": current_price,

                "competitor_pricing": (
                    current_competitor_price
                ),

                "store_id": store_id,

                "product_id": product_id,

                "weather_condition": current_weather,

                "promotion": current_promotion,

                "seasonality": current_seasonality,

                "epidemic": current_epidemic,

            }])

            input_data = input_data[FEATURES]

            # --------------------------------------
            # Random Forest V3 prediction
            # --------------------------------------

            prediction = float(
                model.predict(input_data)[0]
            )

            prediction = max(
                0.0,
                prediction
            )

            # --------------------------------------
            # Seasonal-naive prediction
            # --------------------------------------
            # Use only the independent naive history.
            # Do not use V3 predictions here.

            naive_prediction = max(
                0.0,
                float(naive_history[-7])
            )

            # --------------------------------------
            # Retrieve actual future sales
            # --------------------------------------

            actual_row = future_df[
                future_df["sale_date"] == forecast_date
            ]

            actual_sales = float(
                actual_row.iloc[0]["quantity_sold"]
            )

            # --------------------------------------
            # Save backtest result
            # --------------------------------------

            backtest_results.append({

                "forecast_origin": origin_date,

                "forecast_date": forecast_date,

                "forecast_day": forecast_day,

                "store_id": store_id,

                "product_id": product_id,

                "predicted_demand": round(
                    prediction, 2
                ),

                "seasonal_naive_prediction": round(
                    naive_prediction, 2
                ),

                "actual_sales": round(
                    actual_sales, 2
                ),

                "absolute_error": round(
                    abs(actual_sales - prediction), 2
                ),

                "naive_absolute_error": round(
                    abs(actual_sales - naive_prediction), 2
                ),

                "inventory_assumption": round(
                    model_inventory, 2
                ),

                "external_inputs_assumption": (
                    "Latest known values at forecast origin held constant"
                ),
            })

            # --------------------------------------
            # Update both histories independently
            # --------------------------------------

            # V3 history receives V3 prediction.

            sales_history.append(prediction)

            # Seasonal-naive history receives
            # seasonal-naive prediction.

            naive_history.append(
                naive_prediction
            )


# ==================================================
# 8. SAVE BACKTEST PREDICTIONS
# ==================================================

backtest_df = pd.DataFrame(
    backtest_results
)

if backtest_df.empty:
    raise ValueError(
        "No backtest records generated. "
        "Check forecast origins and date coverage."
    )

backtest_df.to_csv(
    BACKTEST_OUTPUT,
    index=False
)

print(
    "\nBacktest prediction records:",
    len(backtest_df)
)

print("\nBacktest predictions saved:")
print(BACKTEST_OUTPUT)


# ==================================================
# 9. OVERALL BACKTEST METRICS
# ==================================================

overall_v3 = calculate_metrics(
    backtest_df["actual_sales"],
    backtest_df["predicted_demand"]
)

overall_naive = calculate_metrics(
    backtest_df["actual_sales"],
    backtest_df["seasonal_naive_prediction"]
)

overall_summary = pd.DataFrame([
    {
        "model": "Random Forest V3",
        **overall_v3,
    },
    {
        "model": "Seasonal Naive (lag_7)",
        **overall_naive,
    },
])

print("\n==========================================")
print("OVERALL SEVEN-DAY BACKTEST RESULTS")
print("==========================================")

print(
    overall_summary.to_string(index=False)
)


# ==================================================
# 10. DAY-WISE BACKTEST METRICS
# ==================================================

horizon_results = []

for day in range(
    1,
    FORECAST_HORIZON + 1
):

    day_df = backtest_df[
        backtest_df["forecast_day"] == day
    ]

    if day_df.empty:
        continue

    model_day_metrics = calculate_metrics(
        day_df["actual_sales"],
        day_df["predicted_demand"]
    )

    naive_day_metrics = calculate_metrics(
        day_df["actual_sales"],
        day_df["seasonal_naive_prediction"]
    )

    horizon_results.append({

        "forecast_day": day,

        "V3_MAE": model_day_metrics["MAE"],

        "V3_RMSE": model_day_metrics["RMSE"],

        "V3_R2": model_day_metrics["R2"],

        "Naive_MAE": naive_day_metrics["MAE"],

        "Naive_RMSE": naive_day_metrics["RMSE"],

        "Naive_R2": naive_day_metrics["R2"],

        "records": len(day_df),
    })

horizon_df = pd.DataFrame(
    horizon_results
)

horizon_df.to_csv(
    HORIZON_OUTPUT,
    index=False
)

print("\n==========================================")
print("DAY-WISE SEVEN-DAY BACKTEST RESULTS")
print("==========================================")

print(
    horizon_df.to_string(index=False)
)

print("\nDay-wise results saved:")
print(HORIZON_OUTPUT)


# ==================================================
# 11. FINAL SUMMARY
# ==================================================

print("\n==========================================")
print("VALIDATION COMPLETED")
print("==========================================")

print(
    "Holdout evaluation:",
    HOLDOUT_OUTPUT
)

print(
    "Seven-day predictions:",
    BACKTEST_OUTPUT
)

print(
    "Day-wise metrics:",
    HORIZON_OUTPUT
)

print(
    "\nForecast origins evaluated:",
    len(origin_dates)
)

print(
    "Unique store-product combinations:",
    backtest_df.groupby(
        ["store_id", "product_id"]
    ).ngroups
)

print(
    "Total backtest predictions:",
    len(backtest_df)
)

print(
    "\nIMPORTANT: Future inventory, price, discount, "
    "competitor price, weather, promotion, seasonality "
    "and epidemic inputs are held at their latest "
    "known forecast-origin values. This is a historical "
    "simulation, not a live-data forecast."
)

print(
    "\nNOTE: The saved V3 model is fixed during this "
    "backtest. It is not retrained at each forecast origin."
)
