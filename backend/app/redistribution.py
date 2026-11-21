
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load inventory analysis
inventory = pd.read_csv(
    BASE_DIR / "inventory_status.csv"
)

# Work on a separate copy
inventory["available_stock"] = pd.to_numeric(
    inventory["available_stock"], errors="coerce"
).fillna(0)

inventory["seven_day_demand"] = pd.to_numeric(
    inventory["seven_day_demand"], errors="coerce"
).fillna(0)

inventory["shortage_quantity"] = pd.to_numeric(
    inventory["shortage_quantity"], errors="coerce"
).fillna(0)

recommendations = []

# Track available stock after each proposed transfer
remaining_stock = {}

for _, row in inventory.iterrows():
    key = (row["store_id"], row["product_id"])
    demand = row["seven_day_demand"]

    # Reserve forecast demand plus 20% safety stock
    reserve = demand * 1.20

    remaining_stock[key] = max(
        0,
        row["available_stock"] - reserve
    )

# Process products with shortages
receivers = inventory[
    inventory["shortage_quantity"] > 0
].copy()

for _, receiver in receivers.iterrows():

    product_id = receiver["product_id"]
    receiver_store = receiver["store_id"]

    shortage = float(receiver["shortage_quantity"])

    # Find potential donors for the same product
    donors = inventory[
        (inventory["product_id"] == product_id) &
        (inventory["store_id"] != receiver_store)
    ].copy()

    # Prioritize stores with more transferable stock
    donors["transferable_stock"] = donors.apply(
        lambda row: remaining_stock[
            (row["store_id"], row["product_id"])
        ],
        axis=1
    )

    donors = donors.sort_values(
        "transferable_stock",
        ascending=False
    )

    # Try internal redistribution
    for _, donor in donors.iterrows():

        if shortage <= 0:
            break

        donor_key = (
            donor["store_id"],
            donor["product_id"]
        )

        transferable = remaining_stock[donor_key]

        if transferable <= 0:
            continue

        quantity = min(
            shortage,
            transferable
        )

        recommendations.append({
            "product_id": product_id,
            "product_name": receiver["product_name"],
            "from_store": donor["store_id"],
            "to_store": receiver_store,
            "transfer_quantity": int(quantity),
            "transfer_type": "INTERNAL"
        })

        # Update donor and receiver
        remaining_stock[donor_key] -= quantity
        shortage -= quantity

    # Remaining quantity must come from supplier
    if shortage > 0:
        purchase_quantity = int(shortage)

        if purchase_quantity > 0:
            recommendations.append({
                "product_id": product_id,
                "product_name": receiver["product_name"],
                "from_store": "EXTERNAL_SUPPLIER",
                "to_store": receiver_store,
                "transfer_quantity": purchase_quantity,
                "transfer_type": "PURCHASE"
            })

# Save results
result = pd.DataFrame(recommendations)

output_path = BASE_DIR / "redistribution_recommendations.csv"

result.to_csv(output_path, index=False)

print("\n===== SMART REDISTRIBUTION RESULTS =====")

if not result.empty:

    print("\nTransfer recommendations:")
    print(result.to_string(index=False))

    print("\nTransfer summary:")
    print(
        result.groupby("transfer_type")[
            "transfer_quantity"
        ].sum()
    )

    print(
        "\nTotal recommended units:",
        result["transfer_quantity"].sum()
    )

    print(
        "\nInternal transfers:",
        len(result[result["transfer_type"] == "INTERNAL"])
    )

    print(
        "\nExternal purchase recommendations:",
        len(result[result["transfer_type"] == "PURCHASE"])
    )

else:
    print("No recommendations generated.")

print("\nSaved:", output_path)
print("\n===== REDISTRIBUTION COMPLETED =====")
