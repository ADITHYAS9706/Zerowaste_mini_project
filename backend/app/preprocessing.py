
import pandas as pd
from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load datasets
stores = pd.read_csv(BASE_DIR / "stores.csv")
products = pd.read_csv(BASE_DIR / "products.csv")
inventory = pd.read_csv(BASE_DIR / "inventory_batches.csv")
sales = pd.read_csv(BASE_DIR / "sales.csv")


print("\n===== ZEROWASTENET PREPROCESSING =====")


# 1. Convert sales date
sales["sale_date"] = pd.to_datetime(
    sales["sale_date"],
    errors="coerce"
)

sales["created_at"] = pd.to_datetime(
    sales["created_at"],
    errors="coerce"
)


# 2. Convert inventory dates
inventory["manufacturing_date"] = pd.to_datetime(
    inventory["manufacturing_date"],
    errors="coerce"
)

inventory["expiry_date"] = pd.to_datetime(
    inventory["expiry_date"],
    errors="coerce"
)

inventory["created_at"] = pd.to_datetime(
    inventory["created_at"],
    errors="coerce"
)


# 3. Remove duplicate records
stores = stores.drop_duplicates()
products = products.drop_duplicates()
inventory = inventory.drop_duplicates()
sales = sales.drop_duplicates()


# 4. Check invalid sales quantities
print("\nInvalid sales quantities:")

print(
    sales[sales["quantity_sold"] < 0]
)


# 5. Check invalid prices
print("\nInvalid selling prices:")

print(
    sales[sales["selling_price"] < 0]
)


# 6. Check invalid inventory quantities
print("\nInvalid inventory quantities:")

print(
    inventory[
        (inventory["quantity_remaining"] < 0) |
        (inventory["quantity_remaining"] >
         inventory["quantity_received"])
    ]
)


# 7. Save cleaned datasets
stores.to_csv(BASE_DIR / "stores_cleaned.csv", index=False)

products.to_csv(BASE_DIR / "products_cleaned.csv", index=False)

inventory.to_csv(
    BASE_DIR / "inventory_cleaned.csv",
    index=False
)

sales.to_csv(BASE_DIR / "sales_cleaned.csv", index=False)


print("\n===== PREPROCESSING COMPLETED =====")

print("Cleaned datasets saved successfully!")
print("Sales records:", len(sales))
print("Products:", len(products))
print("Inventory batches:", len(inventory))
print("Stores:", len(stores))
