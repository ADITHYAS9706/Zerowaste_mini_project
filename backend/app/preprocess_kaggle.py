

import pandas as pd
from pathlib import Path

# ----------------------------------
# 1. Define project paths
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "kaggle" / "sales_data.csv"

OUTPUT_DIR = BASE_DIR / "processed"

OUTPUT_FILE = OUTPUT_DIR / "kaggle_grocery_cleaned.csv"


# ----------------------------------
# 2. Create output directory
# ----------------------------------

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------
# 3. Load Kaggle dataset
# ----------------------------------

print("Loading Kaggle dataset...")

df = pd.read_csv(INPUT_FILE)

print("Original dataset shape:", df.shape)


# ----------------------------------
# 4. Filter grocery records
# ----------------------------------

df = df[df["Category"] == "Groceries"].copy()

print("Grocery records:", len(df))


# ----------------------------------
# 5. Rename columns
# ----------------------------------

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


# ----------------------------------
# 6. Convert data types
# ----------------------------------

df["sale_date"] = pd.to_datetime(
    df["sale_date"],
    errors="coerce"
)

df["quantity_sold"] = pd.to_numeric(
    df["quantity_sold"],
    errors="coerce"
)


# ----------------------------------
# 7. Handle missing values
# ----------------------------------

df.dropna(
    subset=[
        "sale_date",
        "store_id",
        "product_id",
        "quantity_sold"
    ],
    inplace=True
)


# ----------------------------------
# 8. Sort dataset chronologically
# ----------------------------------

df.sort_values(
    by=["store_id", "product_id", "sale_date"],
    inplace=True
)

df.reset_index(drop=True, inplace=True)


# ----------------------------------
# 9. Check duplicate records
# ----------------------------------

duplicates = df.duplicated(
    subset=["store_id", "product_id", "sale_date"]
).sum()

print("Duplicate store-product-date records:", duplicates)


# ----------------------------------
# 10. Save cleaned dataset
# ----------------------------------

df.to_csv(OUTPUT_FILE, index=False)


# ----------------------------------
# 11. Display final information
# ----------------------------------

print("\n========== KAGGLE PREPROCESSING COMPLETED ==========")

print("Cleaned dataset shape:", df.shape)

print("Date range:",
      df["sale_date"].min(),
      "to",
      df["sale_date"].max())

print("Number of stores:", df["store_id"].nunique())

print("Number of grocery products:", df["product_id"].nunique())

print("Missing values:\n", df.isnull().sum())

print("\nSaved successfully to:")
print(OUTPUT_FILE)
