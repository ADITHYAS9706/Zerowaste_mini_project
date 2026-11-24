
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "processed" / "kaggle_grocery_cleaned.csv"
MODEL_PATH = BASE_DIR / "models" / "kaggle_random_forest_v4.pkl"

OUTPUT_PATH = (
    BASE_DIR / "processed" / "kaggle_v4_seven_day_backtest.csv"
)

FEATURES = [
    "day_of_week",
    "month",
    "is_weekend",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
    "rolling_mean_14",
    "store_id",
    "product_id",
]


# Load data and model
df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip().str.lower()
df["sale_date"] = pd.to_datetime(df["sale_date"])

df = df.sort_values(
    ["store_id", "product_id", "sale_date"]
).reset_index(drop=True)

model = joblib.load(MODEL_PATH)


# Use the same chronological test boundary as V4
unique_dates = sorted(df["sale_date"].unique())
split_index = int(len(unique_dates) * 0.80)
test_start = pd.Timestamp(unique_dates[split_index])

all_results = []

# Start with the day before the test period.
# Evaluate separate, non-overlapping seven-day windows.
origins = []
origin = test_start - pd.Timedelta(days=1)
last_date = df["sale_date"].max()

while origin + pd.Timedelta(days=7) <= last_date:
    origins.append(origin)
    origin += pd.Timedelta(days=7)


print("Test period starts:", test_start.date())
print("Backtesting origins:", len(origins))


for origin in origins:

    print("Testing forecast origin:", origin.date())

    for (store_id, product_id), group in df.groupby(
        ["store_id", "product_id"]
    ):

        group = group.sort_values("sale_date")

        history = group[
            group["sale_date"] <= origin
        ]["quantity_sold"].astype(float).tolist()

        actual_group = group.set_index("sale_date")

        if len(history) < 14:
            continue

        # Forecast seven days recursively
        for day in range(1, 8):

            forecast_date = origin + pd.Timedelta(days=day)

            if forecast_date not in actual_group.index:
                break

            day_of_week = forecast_date.dayofweek

            features = pd.DataFrame([{
                "day_of_week": day_of_week,
                "month": forecast_date.month,
                "is_weekend": int(day_of_week >= 5),
                "lag_1": history[-1],
                "lag_7": history[-7],
                "lag_14": history[-14],
                "rolling_mean_7": np.mean(history[-7:]),
                "rolling_mean_14": np.mean(history[-14:]),
                "store_id": store_id,
                "product_id": product_id,
            }])

            prediction = float(
                model.predict(features[FEATURES])[0]
            )

            prediction = max(0.0, prediction)

            # Recursive seasonal-naive baseline
            baseline_prediction = max(0.0, history[-7])

            actual = float(
                actual_group.loc[forecast_date, "quantity_sold"]
            )

            all_results.append({
                "forecast_origin": origin,
                "forecast_date": forecast_date,
                "forecast_day": day,
                "store_id": store_id,
                "product_id": product_id,
                "actual_sales": actual,
                "predicted_sales": prediction,
                "baseline_sales": baseline_prediction,
            })

            # Add model prediction to history, not actual sales
            history.append(prediction)


# Save results
results = pd.DataFrame(all_results)

if results.empty:
    raise ValueError("No backtesting results generated.")

results.to_csv(OUTPUT_PATH, index=False)


# Overall metrics
actual = results["actual_sales"]
predicted = results["predicted_sales"]
baseline = results["baseline_sales"]

print("\n========== SEVEN-DAY BACKTEST RESULTS ==========")

print("Total predictions:", len(results))
print("Forecast origins:", results["forecast_origin"].nunique())

print("\nRandom Forest V4:")
print("MAE :", round(mean_absolute_error(actual, predicted), 4))
print(
    "RMSE:",
    round(np.sqrt(mean_squared_error(actual, predicted)), 4)
)
print("R2  :", round(r2_score(actual, predicted), 4))

print("\nSeasonal Naive Baseline:")
print("MAE :", round(mean_absolute_error(actual, baseline), 4))
print(
    "RMSE:",
    round(np.sqrt(mean_squared_error(actual, baseline)), 4)
)


# Accuracy by forecast horizon
print("\n========== DAY-WISE MAE ==========")

for day, group in results.groupby("forecast_day"):
    day_mae = mean_absolute_error(
        group["actual_sales"],
        group["predicted_sales"]
    )

    print(f"Day {day}: MAE = {day_mae:.4f}")


print("\nBacktesting results saved:")
print(OUTPUT_PATH)
