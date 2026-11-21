
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load datasets
inventory = pd.read_csv(
    BASE_DIR / "inventory_cleaned.csv"
)

forecast = pd.read_csv(
    BASE_DIR / "seven_day_forecast.csv"
)

products = pd.read_csv(
    BASE_DIR / "products_cleaned.csv"
)

# Convert dates
inventory["expiry_date"] = pd.to_datetime(
    inventory["expiry_date"], errors="coerce"
)

forecast["forecast_date"] = pd.to_datetime(
    forecast["forecast_date"], errors="coerce"
)

# Use the forecast starting date as analysis date
analysis_date = forecast["forecast_date"].min()

# Remove already expired batches
inventory = inventory[
    inventory["expiry_date"] >= analysis_date
].copy()

# Merge product names
inventory = inventory.merge(
    products[["product_id", "product_name"]],
    on="product_id",
    how="left"
)

# Calculate days until expiry
inventory["days_to_expiry"] = (
    inventory["expiry_date"] - analysis_date
).dt.days

# Analyse each batch separately
results = []

for _, batch in inventory.iterrows():

    store_id = batch["store_id"]
    product_id = batch["product_id"]

    stock = float(batch["quantity_remaining"])

    days_left = int(batch["days_to_expiry"])

    # Get demand for this product and store
    future_sales = forecast[
        (forecast["store_id"] == store_id) &
        (forecast["product_id"] == product_id) &
        (forecast["forecast_date"] <= batch["expiry_date"])
    ]

    predicted_demand = float(
        future_sales["predicted_units"].sum()
    )

    # Estimate unsold stock
    estimated_waste = max(
        0,
        stock - predicted_demand
    )

    if days_left <= 2 and estimated_waste > 0:
        risk = "HIGH"

    elif days_left <= 5 and estimated_waste > 0:
        risk = "MEDIUM"

    elif estimated_waste > 0:
        risk = "LOW"

    else:
        risk = "SAFE"

    results.append({
        "batch_id": batch["batch_id"],
        "store_id": store_id,
        "product_id": product_id,
        "product_name": batch["product_name"],
        "expiry_date": batch["expiry_date"],
        "days_to_expiry": days_left,
        "available_stock": stock,
        "predicted_demand_before_expiry": predicted_demand,
        "estimated_waste": estimated_waste,
        "waste_risk": risk
    })

# Create output
result = pd.DataFrame(results)

output_path = BASE_DIR / "food_waste_risk.csv"

result.to_csv(output_path, index=False)

# Display results
print("\n===== ZEROWASTENET FOOD WASTE ANALYSIS =====")

if not result.empty:

    print("\nWaste risk summary:")
    print(result["waste_risk"].value_counts())

    print("\nHigh-risk batches:")

    high_risk = result[
        result["waste_risk"] == "HIGH"
    ]

    if high_risk.empty:
        print("No high-risk batches identified.")
    else:
        print(
            high_risk[
                ["store_id", "product_name",
                 "days_to_expiry", "available_stock",
                 "predicted_demand_before_expiry",
                 "estimated_waste"]
            ].to_string(index=False)
        )

    print(
        "\nTotal estimated waste:",
        result["estimated_waste"].sum()
    )

else:
    print("No valid inventory batches found.")

print("\nSaved food_waste_risk.csv")
print("\n===== FOOD WASTE ANALYSIS COMPLETED =====")
