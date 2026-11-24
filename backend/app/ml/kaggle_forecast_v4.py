
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


# --------------------------------------------------
# 1. File paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "processed" / "kaggle_grocery_cleaned.csv"
MODEL_PATH = BASE_DIR / "models" / "kaggle_random_forest_v4.pkl"

OUTPUT_PATH = (
    BASE_DIR / "processed" / "kaggle_seven_day_forecast_v4.csv"
)


# --------------------------------------------------
# 2. Load historical data and trained model
# --------------------------------------------------

print("Loading historical sales data...")

df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip().str.lower()

# The cleaned dataset uses sale_date
df["sale_date"] = pd.to_datetime(df["sale_date"])

df = df.sort_values(
    ["store_id", "product_id", "sale_date"]
).reset_index(drop=True)

print("Loading trained V4 model...")

model = joblib.load(MODEL_PATH)


# --------------------------------------------------
# 3. Define model features
# --------------------------------------------------

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


# --------------------------------------------------
# 4. Forecast next seven days
# --------------------------------------------------

forecast_results = []

groups = df.groupby(["store_id", "product_id"])

print("\nGenerating seven-day forecasts...")


for (store_id, product_id), group in groups:

    group = group.sort_values("sale_date").copy()

    # Historical sales values
    sales_history = group["quantity_sold"].astype(float).tolist()

    # Latest date for this store-product combination
    last_date = group["sale_date"].max()

    if len(sales_history) < 14:
        print(
            f"Skipping {store_id} - {product_id}: "
            "insufficient history"
        )
        continue

    for day in range(1, 8):

        forecast_date = last_date + pd.Timedelta(days=day)

        # Calendar features
        day_of_week = forecast_date.dayofweek
        month = forecast_date.month
        is_weekend = int(day_of_week >= 5)

        # Historical and recursively predicted lag features
        lag_1 = sales_history[-1]
        lag_7 = sales_history[-7]
        lag_14 = sales_history[-14]

        rolling_mean_7 = np.mean(sales_history[-7:])
        rolling_mean_14 = np.mean(sales_history[-14:])

        # Prepare model input
        input_data = pd.DataFrame([{
            "day_of_week": day_of_week,
            "month": month,
            "is_weekend": is_weekend,
            "lag_1": lag_1,
            "lag_7": lag_7,
            "lag_14": lag_14,
            "rolling_mean_7": rolling_mean_7,
            "rolling_mean_14": rolling_mean_14,
            "store_id": store_id,
            "product_id": product_id,
        }])

        # Predict sales
        prediction = float(model.predict(input_data[FEATURES])[0])

        # Sales cannot be negative
        prediction = max(0.0, prediction)

        # Save prediction
        forecast_results.append({
            "forecast_date": forecast_date,
            "store_id": store_id,
            "product_id": product_id,
            "predicted_sales": round(prediction, 2),
            "forecast_day": day,
        })

        # Add prediction to history for next iteration
        sales_history.append(prediction)


# --------------------------------------------------
# 5. Save forecast
# --------------------------------------------------

forecast_df = pd.DataFrame(forecast_results)

if forecast_df.empty:
    raise ValueError("No forecasts generated. Check the input data.")

forecast_df.to_csv(OUTPUT_PATH, index=False)

print("\n========== SEVEN-DAY FORECAST ==========")

print(forecast_df.head(15).to_string(index=False))

print("\nTotal forecast records:", len(forecast_df))
print("Forecast dates:")
print(forecast_df["forecast_date"].min())
print("to")
print(forecast_df["forecast_date"].max())

print("\nForecast saved successfully:")
print(OUTPUT_PATH)
