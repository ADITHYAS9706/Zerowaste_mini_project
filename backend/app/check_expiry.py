
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

inventory = pd.read_csv(
    BASE_DIR / "inventory_cleaned.csv"
)

inventory["expiry_date"] = pd.to_datetime(
    inventory["expiry_date"]
)

analysis_date = pd.Timestamp("2026-11-21")

inventory["days_to_expiry"] = (
    inventory["expiry_date"] - analysis_date
).dt.days

print("\n===== EXPIRY DATE INSPECTION =====")

print("\nExpiry date range:")
print("Earliest:", inventory["expiry_date"].min())
print("Latest:", inventory["expiry_date"].max())

print("\nDays until expiry:")
print(inventory["days_to_expiry"].describe())

print("\nExpiry categories:")

print(
    pd.cut(
        inventory["days_to_expiry"],
        bins=[-float("inf"), 0, 2, 5, 7, 14, 30, float("inf")],
        labels=[
            "Expired",
            "1-2 days",
            "3-5 days",
            "6-7 days",
            "8-14 days",
            "15-30 days",
            "Above 30 days"
        ]
    ).value_counts().sort_index()
)

print("\n===== INSPECTION COMPLETED =====")
