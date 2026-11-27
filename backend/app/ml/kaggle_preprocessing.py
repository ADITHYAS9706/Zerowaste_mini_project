import pandas as pd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = "data/kaggle/sales_data.csv"
OUTPUT_DIR = BASE_DIR / "processed"
OUTPUT_FILE = OUTPUT_DIR / "kaggle_grocery_cleaned.csv"

# Create output folder if it does not exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load Kaggle dataset
df = pd.read_csv(INPUT_FILE)

print("Original dataset shape:", df.shape)

# Keep only grocery records
df = df[df["Category"] == "Groceries"].copy()

# Rename columns to consistent names
df.rename(columns={
    "Date": "sale_date",
    "Store ID": "store_id",
    "Product ID": "product_id",
    "Units Sold": "quantity_sold",
    "Inventory Level": "inventory_level",
    "Units Ordered": "units_ordered",
    "Price": "price",
    "Discount": "discount",
    "Weather Condition": "weather_condition",
    "Promotion": "promotion",
    "Competitor Pricing": "competitor_pricing",
    "Seasonality": "seasonality",
    "Epidemic": "epidemic"
}, inplace=True)

# Convert date column
df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")

# Remove invalid dates and missing essential values
df.dropna(
    subset=["sale_date", "store_id", "product_id", "quantity_sold"],
    inplace=True
)

# Sort chronologically by store and product
df.sort_values(
    ["store_id", "product_id", "sale_date"],
    inplace=True
)

# Save cleaned grocery dataset
df.to_csv(OUTPUT_FILE, index=False)

print("\nKaggle preprocessing completed!")
print("Cleaned dataset shape:", df.shape)
print("Date range:", df["sale_date"].min(), "to", df["sale_date"].max())
print("Stores:", df["store_id"].nunique())
print("Products:", df["product_id"].nunique())
print("Saved to:", OUTPUT_FILE)
