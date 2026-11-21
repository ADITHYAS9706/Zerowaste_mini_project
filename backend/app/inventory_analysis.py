
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

# Forecast period
forecast_start = forecast["forecast_date"].min()
forecast_end = forecast["forecast_date"].max()

print("\n===== ZEROWASTENET INVENTORY ANALYSIS =====")

print("Forecast starts:", forecast_start.date())
print("Forecast ends:", forecast_end.date())

# 1. Calculate seven-day demand
demand = forecast.groupby(
    ["store_id", "product_id"]
)["predicted_units"].sum().reset_index()

demand.rename(
    columns={"predicted_units": "seven_day_demand"},
    inplace=True
)

# 2. Calculate current available stock
# Exclude expired batches and invalid quantities
inventory["quantity_remaining"] = pd.to_numeric(
    inventory["quantity_remaining"],
    errors="coerce"
).fillna(0)

expired = inventory[
    inventory["expiry_date"] < forecast_start
].copy()

active_inventory = inventory[
    (inventory["expiry_date"] >= forecast_start) &
    (inventory["quantity_remaining"] > 0)
].copy()

stock = active_inventory.groupby(
    ["store_id", "product_id"]
)["quantity_remaining"].sum().reset_index()

stock.rename(
    columns={"quantity_remaining": "available_stock"},
    inplace=True
)

# 3. Combine stock and predicted demand
analysis = demand.merge(
    stock,
    on=["store_id", "product_id"],
    how="left"
)

analysis["available_stock"] = (
    analysis["available_stock"].fillna(0)
)

# 4. Calculate stock balance
analysis["stock_balance"] = (
    analysis["available_stock"] -
    analysis["seven_day_demand"]
)

analysis["shortage_quantity"] = (
    analysis["seven_day_demand"] -
    analysis["available_stock"]
).clip(lower=0)

analysis["surplus_quantity"] = (
    analysis["available_stock"] -
    analysis["seven_day_demand"] * 1.5
).clip(lower=0)

# 5. Classify inventory
def classify_stock(row):
    if row["available_stock"] < row["seven_day_demand"]:
        return "SHORTAGE"
    elif row["available_stock"] > row["seven_day_demand"] * 1.5:
        return "EXCESS"
    else:
        return "ADEQUATE"

analysis["stock_status"] = analysis.apply(
    classify_stock,
    axis=1
)

# 6. Add product names
analysis = analysis.merge(
    products[["product_id", "product_name", "category"]],
    on="product_id",
    how="left"
)

# 7. Identify batches approaching expiry
near_expiry = active_inventory[
    (active_inventory["expiry_date"] >= forecast_start) &
    (active_inventory["expiry_date"] <= forecast_end)
].copy()

near_expiry = near_expiry.merge(
    products[["product_id", "product_name"]],
    on="product_id",
    how="left"
)

near_expiry["days_to_expiry"] = (
    near_expiry["expiry_date"] - forecast_start
).dt.days

# 8. Save results
analysis.to_csv(
    BASE_DIR / "inventory_status.csv",
    index=False
)

near_expiry.to_csv(
    BASE_DIR / "near_expiry_products.csv",
    index=False
)

expired.to_csv(
    BASE_DIR / "expired_inventory.csv",
    index=False
)

# 9. Display summary
print("\n===== INVENTORY STATUS SUMMARY =====")

print(
    analysis["stock_status"].value_counts()
)

print("\nShortage products:")
print(
    analysis[analysis["stock_status"] == "SHORTAGE"][
        ["store_id", "product_name",
         "available_stock", "seven_day_demand",
         "shortage_quantity"]
    ].to_string(index=False)
)

print("\nExcess inventory:")
print(
    analysis[analysis["stock_status"] == "EXCESS"][
        ["store_id", "product_name",
         "available_stock", "seven_day_demand",
         "surplus_quantity"]
    ].to_string(index=False)
)

print("\nNear-expiry batches:", len(near_expiry))
print("Already expired batches:", len(expired))

print("\n===== INVENTORY ANALYSIS COMPLETED =====")
print("Saved inventory_status.csv")
print("Saved near_expiry_products.csv")
print("Saved expired_inventory.csv")
