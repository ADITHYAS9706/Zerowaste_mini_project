
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "processed" / "kaggle_grocery_cleaned.csv"

df = pd.read_csv(INPUT_FILE)

print("Dataset shape:", df.shape)

# Numerical feature analysis
numeric_columns = [
    "quantity_sold",
    "inventory_level",
    "units_ordered",
    "price",
    "discount",
    "competitor_pricing"
]

print("\n========== NUMERICAL FEATURE CORRELATION ==========")

print(
    df[numeric_columns]
    .corr(numeric_only=True)["quantity_sold"]
    .sort_values(ascending=False)
)

# Categorical feature analysis
categorical_columns = [
    "weather_condition",
    "promotion",
    "seasonality",
    "epidemic"
]

print("\n========== CATEGORICAL FEATURE VALUES ==========")

for column in categorical_columns:

    print(f"\n{column}")

    print(df[column].value_counts(dropna=False))

# Inventory and sales relationship
print("\n========== INVENTORY ANALYSIS ==========")

print(
    df.groupby(
        pd.cut(
            df["inventory_level"],
            bins=5
        ),
        observed=False
    )["quantity_sold"].mean()
)

print("\nFeature analysis completed!")
