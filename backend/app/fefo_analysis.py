
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

inventory = pd.read_csv(
    BASE_DIR / "inventory_cleaned.csv"
)

forecast = pd.read_csv(
    BASE_DIR / "seven_day_forecast.csv"
)

products = pd.read_csv(
    BASE_DIR / "products_cleaned.csv"
)

# Analysis date
analysis_date = pd.Timestamp("2026-11-21")

inventory["expiry_date"] = pd.to_datetime(
    inventory["expiry_date"]
)

forecast["forecast_date"] = pd.to_datetime(
    forecast["forecast_date"]
)

# Remove expired and empty batches
inventory = inventory[
    (inventory["expiry_date"] >= analysis_date) &
    (inventory["quantity_remaining"] > 0)
].copy()

inventory["days_to_expiry"] = (
    inventory["expiry_date"] - analysis_date
).dt.days

# Add product names
inventory = inventory.merge(
    products[["product_id", "product_name"]],
    on="product_id",
    how="left"
)

# Sort batches using FEFO
inventory = inventory.sort_values(
    ["store_id", "product_id", "expiry_date"]
)

results = []

# Process each store and product
for (store, product), batches in inventory.groupby(
    ["store_id", "product_id"]
):

    batches = batches.copy()

    future = forecast[
        (forecast["store_id"] == store) &
        (forecast["product_id"] == product)
    ]

    total_demand = float(
        future["predicted_units"].sum()
    )

    remaining_demand = total_demand

    # Allocate predicted demand to earliest expiry first
    for _, batch in batches.iterrows():

        stock = float(batch["quantity_remaining"])

        allocated_sales = min(
            stock,
            remaining_demand
        )

        remaining_stock = stock - allocated_sales

        remaining_demand -= allocated_sales

        days = int(batch["days_to_expiry"])

        # Initial risk classification
        if remaining_stock <= 0:
            risk = "SAFE"

        elif days <= 14:
            risk = "HIGH"

        elif days <= 30:
            risk = "MEDIUM"

        else:
            risk = "LOW"

        results.append({
            "batch_id": batch["batch_id"],
            "store_id": store,
            "product_id": product,
            "product_name": batch["product_name"],
            "expiry_date": batch["expiry_date"],
            "days_to_expiry": days,
            "initial_stock": stock,
            "predicted_sales_allocated": allocated_sales,
            "estimated_unsold_stock": remaining_stock,
            "waste_risk": risk,
            "fefo_priority": 1
        })

result = pd.DataFrame(results)

# Save FEFO analysis
result.to_csv(
    BASE_DIR / "fefo_analysis.csv",
    index=False
)

print("\n===== ZEROWASTENET FEFO ANALYSIS =====")

print("\nRisk summary:")

print(result["waste_risk"].value_counts())

print("\nHigh-risk batches:")

high = result[result["waste_risk"] == "HIGH"]

if high.empty:
    print("No high-risk batches found.")
else:
    print(
        high[
            ["store_id", "product_name",
             "days_to_expiry", "estimated_unsold_stock"]
        ].to_string(index=False)
    )

print(
    "\nTotal estimated unsold stock:",
    result["estimated_unsold_stock"].sum()
)

print("\nSaved fefo_analysis.csv")

print("\n===== FEFO ANALYSIS COMPLETED =====")
