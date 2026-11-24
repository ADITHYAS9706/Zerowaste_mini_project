
import pandas as pd
from pathlib import Path

# ----------------------------------
# 1. Define paths
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "processed" / "kaggle_grocery_cleaned.csv"

OUTPUT_FILE = BASE_DIR / "processed" / "kaggle_ml_features.csv"


# ----------------------------------
# 2. Load cleaned dataset
# ----------------------------------

print("Loading cleaned Kaggle dataset...")

df = pd.read_csv(INPUT_FILE)

df["sale_date"] = pd.to_datetime(df["sale_date"])

df = df.sort_values(
    ["store_id", "product_id", "sale_date"]
).copy()


# ----------------------------------
# 3. Calendar features
# ----------------------------------

print("Creating calendar features...")

df["day_of_week"] = df["sale_date"].dt.dayofweek

df["month"] = df["sale_date"].dt.month

df["is_weekend"] = (
    df["day_of_week"] >= 5
).astype(int)


# ----------------------------------
# 4. Historical sales features
# ----------------------------------

print("Creating lag features...")

group = df.groupby(
    ["store_id", "product_id"]
)["quantity_sold"]

# Previous day sales
df["lag_1"] = group.shift(1)

# Sales seven days earlier
df["lag_7"] = group.shift(7)

# Sales fourteen days earlier
df["lag_14"] = group.shift(14)


# ----------------------------------
# 5. Rolling average features
# ----------------------------------

print("Creating rolling averages...")

df["rolling_mean_7"] = group.transform(
    lambda x: x.shift(1).rolling(7).mean()
)

df["rolling_mean_14"] = group.transform(
    lambda x: x.shift(1).rolling(14).mean()
)


# ----------------------------------
# 6. Remove rows without history
# ----------------------------------

df.dropna(
    subset=[
        "lag_1",
        "lag_7",
        "lag_14",
        "rolling_mean_7",
        "rolling_mean_14"
    ],
    inplace=True
)


# ----------------------------------
# 7. Reset index
# ----------------------------------

df.reset_index(drop=True, inplace=True)


# ----------------------------------
# 8. Save feature dataset
# ----------------------------------

df.to_csv(OUTPUT_FILE, index=False)


# ----------------------------------
# 9. Display results
# ----------------------------------

print("\n========== FEATURE ENGINEERING COMPLETED ==========")

print("Final dataset shape:", df.shape)

print("\nFeatures created:")

print([
    "day_of_week",
    "month",
    "is_weekend",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
    "rolling_mean_14"
])

print("\nMissing values in selected features:")

print(
    df[
        [
            "lag_1",
            "lag_7",
            "lag_14",
            "rolling_mean_7",
            "rolling_mean_14"
        ]
    ].isnull().sum()
)

print("\nSaved feature dataset to:")

print(OUTPUT_FILE)
