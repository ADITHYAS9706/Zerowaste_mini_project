
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


# ==================================================
# 1. PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "processed" / "kaggle_ml_features.csv"

MODEL_PATH = BASE_DIR / "models" / "kaggle_random_forest_v3.pkl"

OUTPUT_PATH = (
    BASE_DIR / "processed" / "kaggle_seven_day_forecast_v3.csv"
)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. FEATURE DEFINITIONS
# Keep exactly the same features used during V3 training
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
# 3. LOAD DATA AND MODEL
# ==================================================

print("Loading Kaggle feature dataset...")

df = pd.read_csv(DATA_PATH)

df.columns = df.columns.str.strip().str.lower()

df["sale_date"] = pd.to_datetime(df["sale_date"])

df = df.sort_values(
    ["store_id", "product_id", "sale_date"]
).reset_index(drop=True)

print("Dataset shape:", df.shape)

print("Loading trained Random Forest V3 model...")

model = joblib.load(MODEL_PATH)


# ==================================================
# 4. CHECK REQUIRED COLUMNS
# ==================================================

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
        f"Missing required dataset columns: {missing}"
    )


# ==================================================
# 5. GENERATE SEVEN-DAY FORECAST
# ==================================================

forecast_results = []

groups = df.groupby(
    ["store_id", "product_id"],
    sort=True
)

print("\nGenerating V3 seven-day forecasts...")


for (store_id, product_id), group in groups:

    group = group.sort_values("sale_date").copy()

    if len(group) < 14:
        print(
            f"Skipping {store_id}-{product_id}: "
            "insufficient sales history"
        )
        continue

    # ----------------------------------------------
    # Latest historical record
    # ----------------------------------------------

    latest = group.iloc[-1]

    last_date = pd.Timestamp(latest["sale_date"])

    # Historical sales
    sales_history = (
        group["quantity_sold"]
        .astype(float)
        .tolist()
    )

    # ----------------------------------------------
    # Inventory tracking
    # ----------------------------------------------

    current_inventory = max(
        0.0,
        float(latest["inventory_level"])
    )

    # Keep inventory input constant for model prediction.
    # Track projected inventory separately.

    model_inventory = current_inventory

    projected_inventory = current_inventory

    # ----------------------------------------------
    # Latest known external information
    # ----------------------------------------------

    current_price = float(latest["price"])

    current_discount = float(latest["discount"])

    current_competitor_price = float(
        latest["competitor_pricing"]
    )

    current_weather = latest["weather_condition"]

    current_promotion = latest["promotion"]

    current_seasonality = latest["seasonality"]

    current_epidemic = latest["epidemic"]

    # ----------------------------------------------
    # Recursive seven-day forecasting
    # ----------------------------------------------

    for forecast_day in range(1, 8):

        forecast_date = (
            last_date + pd.Timedelta(days=forecast_day)
        )

        # Calendar features
        day_of_week = forecast_date.dayofweek

        month = forecast_date.month

        is_weekend = int(day_of_week >= 5)

        # Historical and predicted sales features
        lag_1 = sales_history[-1]

        lag_7 = sales_history[-7]

        lag_14 = sales_history[-14]

        rolling_mean_7 = np.mean(sales_history[-7:])

        rolling_mean_14 = np.mean(sales_history[-14:])

        # ------------------------------------------
        # Prepare V3 model input
        # ------------------------------------------

        input_data = pd.DataFrame([{
            "day_of_week": day_of_week,
            "month": month,
            "is_weekend": is_weekend,

            "lag_1": lag_1,
            "lag_7": lag_7,
            "lag_14": lag_14,

            "rolling_mean_7": rolling_mean_7,
            "rolling_mean_14": rolling_mean_14,

            # Constant model inventory input
            "inventory_level": model_inventory,

            "discount": current_discount,
            "price": current_price,
            "competitor_pricing": current_competitor_price,

            "store_id": store_id,
            "product_id": product_id,

            "weather_condition": current_weather,
            "promotion": current_promotion,
            "seasonality": current_seasonality,
            "epidemic": current_epidemic,
        }])

        input_data = input_data[FEATURES]

        # ------------------------------------------
        # Predict demand
        # ------------------------------------------

        prediction = float(model.predict(input_data)[0])

        prediction = max(0.0, prediction)

        # ------------------------------------------
        # Calculate fulfillable sales and stock
        # ------------------------------------------

        estimated_fulfillable_sales = min(
            prediction,
            projected_inventory
        )

        projected_closing_inventory = max(
            0.0,
            projected_inventory - estimated_fulfillable_sales
        )

        # ------------------------------------------
        # Record forecast
        # ------------------------------------------

        forecast_results.append({

            "forecast_origin": last_date,

            "forecast_date": forecast_date,

            "forecast_day": forecast_day,

            "store_id": store_id,

            "product_id": product_id,

            "predicted_demand": round(prediction, 2),

            "estimated_fulfillable_sales": round(
                estimated_fulfillable_sales, 2
            ),

            "assumed_inventory_at_start": round(
                projected_inventory, 2
            ),

            "projected_closing_inventory": round(
                projected_closing_inventory, 2
            ),

            "potential_stockout": (
                projected_closing_inventory == 0
            ),

            "price_used": current_price,

            "discount_used": current_discount,

            "competitor_price_used": current_competitor_price,

            "weather_used": current_weather,

            "promotion_used": current_promotion,

            "seasonality_used": current_seasonality,

            "epidemic_used": current_epidemic,

            "external_inputs_assumption": (
                "Latest known values held constant"
            ),
        })

        # ------------------------------------------
        # Update projected inventory only
        # ------------------------------------------

        projected_inventory = projected_closing_inventory

        # ------------------------------------------
        # Update sales history recursively
        # ------------------------------------------

        sales_history.append(prediction)


# ==================================================
# 6. SAVE FORECAST
# ==================================================

forecast_df = pd.DataFrame(forecast_results)

if forecast_df.empty:
    raise ValueError("No forecasts generated.")

forecast_df.to_csv(OUTPUT_PATH, index=False)


# ==================================================
# 7. DISPLAY RESULTS
# ==================================================

print("\n========== V3 SEVEN-DAY FORECAST ==========")

print(
    forecast_df.head(20).to_string(index=False)
)

print("\nTotal forecast records:", len(forecast_df))

print(
    "Forecast origin:",
    forecast_df["forecast_origin"].min()
)

print(
    "Forecast dates:",
    forecast_df["forecast_date"].min(),
    "to",
    forecast_df["forecast_date"].max()
)

print(
    "\nUnique store-product combinations:",
    forecast_df.groupby(
        ["store_id", "product_id"]
    ).ngroups
)

print("\nForecast saved successfully:")
print(OUTPUT_PATH)

print(
    "\nNOTE: Predicted demand uses constant latest-known "
    "inventory and external inputs. Projected inventory "
    "is tracked separately, assuming no replenishment. "
    "Fulfillable sales are limited by projected stock."
)
