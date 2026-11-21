
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load cleaned datasets
sales = pd.read_csv(BASE_DIR / "sales_cleaned.csv")
products = pd.read_csv(BASE_DIR / "products_cleaned.csv")

# Convert date
sales["sale_date"] = pd.to_datetime(sales["sale_date"])

# Sort records chronologically
sales = sales.sort_values(
    ["store_id", "product_id", "sale_date"]
).copy()

# Calendar features
sales["day_of_week"] = sales["sale_date"].dt.dayofweek
sales["month"] = sales["sale_date"].dt.month

sales["is_weekend"] = (
    sales["day_of_week"] >= 5
).astype(int)

# Group by store and product
group = sales.groupby(
    ["store_id", "product_id"]
)["quantity_sold"]

# Historical sales features
sales["lag_1"] = group.shift(1)
sales["lag_7"] = group.shift(7)
sales["lag_14"] = group.shift(14)

# Rolling averages (exclude current day's sales)
sales["rolling_mean_7"] = group.transform(
    lambda x: x.shift(1).rolling(7).mean()
)

sales["rolling_mean_14"] = group.transform(
    lambda x: x.shift(1).rolling(14).mean()
)

# Add product baseline demand
sales = sales.merge(
    products[["product_id", "base_daily_demand"]],
    on="product_id",
    how="left"
)

# Remove rows without sufficient historical data
sales = sales.dropna(
    subset=[
        "lag_1",
        "lag_7",
        "lag_14",
        "rolling_mean_7",
        "rolling_mean_14"
    ]
).copy()

# Save ML dataset
sales.to_csv(
    BASE_DIR / "ml_features.csv",
    index=False
)

print("\n===== FEATURE ENGINEERING COMPLETED =====")

print("Total ML records:", len(sales))

print("\nML feature columns:")
print(sales.columns.tolist())

print("\nSample ML records:")
print(sales.head())

print("\nMissing values:")
print(sales.isnull().sum())
