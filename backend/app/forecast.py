
import pandas as pd
import numpy as np
import joblib

from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load validated model
model = joblib.load(
    BASE_DIR / "random_forest_validated.pkl"
)

# Load historical sales and product information
sales = pd.read_csv(BASE_DIR / "sales_cleaned.csv")
products = pd.read_csv(BASE_DIR / "products_cleaned.csv")

sales["sale_date"] = pd.to_datetime(sales["sale_date"])

# Sort historical data
sales = sales.sort_values("sale_date")

# Check historical data
if sales.empty:
    raise ValueError("No historical sales data found.")

# Define model features in the same order used during training
features = [
    "day_of_week",
    "month",
    "is_weekend",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
    "rolling_mean_14",
    "base_daily_demand"
]

# Add baseline product demand
sales = sales.merge(
    products[["product_id", "base_daily_demand"]],
    on="product_id",
    how="left"
)

if sales["base_daily_demand"].isnull().any():
    raise ValueError("Some products have no base daily demand.")

# Store historical demand for each store-product pair
history = {}

for (store_id, product_id), group in sales.groupby(
    ["store_id", "product_id"]
):
    group = group.sort_values("sale_date")

    history[(store_id, product_id)] = (
        group["quantity_sold"].astype(float).tolist()
    )

# Forecast starts after the latest historical date
last_date = sales["sale_date"].max()
forecast_start = last_date + pd.Timedelta(days=1)

# Store-product combinations
combinations = list(history.keys())

forecast_results = []

print("\n===== ZEROWASTENET 7-DAY FORECAST =====")
print("Last historical date:", last_date.date())
print("Forecast starts:", forecast_start.date())

# Generate forecasts recursively
for day in range(7):

    forecast_date = forecast_start + pd.Timedelta(days=day)

    daily_inputs = []

    for store_id, product_id in combinations:

        past = history[(store_id, product_id)]

        if len(past) < 14:
            continue

        # Calendar features
        day_of_week = forecast_date.dayofweek
        month = forecast_date.month
        is_weekend = int(day_of_week >= 5)

        # Historical features
        lag_1 = past[-1]
        lag_7 = past[-7]
        lag_14 = past[-14]

        rolling_mean_7 = np.mean(past[-7:])
        rolling_mean_14 = np.mean(past[-14:])

        base_daily_demand = float(
            products.loc[
                products["product_id"] == product_id,
                "base_daily_demand"
            ].iloc[0]
        )

        daily_inputs.append({
            "store_id": store_id,
            "product_id": product_id,
            "day_of_week": day_of_week,
            "month": month,
            "is_weekend": is_weekend,
            "lag_1": lag_1,
            "lag_7": lag_7,
            "lag_14": lag_14,
            "rolling_mean_7": rolling_mean_7,
            "rolling_mean_14": rolling_mean_14,
            "base_daily_demand": base_daily_demand
        })

    input_df = pd.DataFrame(daily_inputs)

    if input_df.empty:
        raise ValueError("Not enough historical data to forecast.")

    # Predict demand
    predictions = model.predict(input_df[features])

    # Keep predictions non-negative
    predictions = np.maximum(predictions, 0)

    # Save predictions and update history
    for i, row in input_df.iterrows():

        predicted_demand = float(predictions[i])

        forecast_results.append({
            "forecast_date": forecast_date,
            "store_id": row["store_id"],
            "product_id": row["product_id"],
            "predicted_demand": round(predicted_demand, 2),
            "predicted_units": int(round(predicted_demand))
        })

        # Use prediction as input for next day
        history[(row["store_id"], row["product_id"])].append(
            predicted_demand
        )

# Convert to DataFrame
forecast_df = pd.DataFrame(forecast_results)

# Save forecast
output_path = BASE_DIR / "seven_day_forecast.csv"

forecast_df.to_csv(output_path, index=False)

print("\n===== FORECAST COMPLETED =====")

print("Total predictions:", len(forecast_df))
print("Forecast days:", forecast_df["forecast_date"].nunique())

print("\nSample predictions:")
print(forecast_df.head(10).to_string(index=False))

print("\nTotal predicted demand:")
print(forecast_df["predicted_units"].sum())

print("\nSaved to:", output_path)
