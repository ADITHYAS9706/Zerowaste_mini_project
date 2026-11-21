
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

df = pd.read_csv(BASE_DIR / "inventory_status.csv")

print("\n===== PRODUCT-WISE INVENTORY CHECK =====")

for product, group in df.groupby("product_name"):

    donors = group[group["stock_status"] == "EXCESS"]
    receivers = group[group["stock_status"] == "SHORTAGE"]

    print(f"\nProduct: {product}")
    print("Excess stores:", donors["store_id"].tolist())
    print("Shortage stores:", receivers["store_id"].tolist())

    if len(donors) and len(receivers):
        print("Redistribution possible: YES")
    else:
        print("Redistribution possible: NO")

print("\n===== CHECK COMPLETED =====")
