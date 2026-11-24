
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ----------------------------------
# 1. Define paths
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "processed" / "kaggle_model_predictions.csv"

OUTPUT_DIR = BASE_DIR / "processed"

# ----------------------------------
# 2. Load predictions
# ----------------------------------

print("Loading Kaggle model predictions...")

df = pd.read_csv(INPUT_FILE)

actual = df["quantity_sold"]
predicted = df["random_forest_prediction"]

# ----------------------------------
# 3. Overall prediction analysis
# ----------------------------------

df["error"] = actual - predicted
df["absolute_error"] = df["error"].abs()

print("\n========== OVERALL ANALYSIS ==========")

print("\nActual sales:")
print(actual.describe())

print("\nPredicted sales:")
print(predicted.describe())

print("\nAverage actual sales:", round(actual.mean(), 2))
print("Average predicted sales:", round(predicted.mean(), 2))
print("Average absolute error:", round(df["absolute_error"].mean(), 2))

# ----------------------------------
# 4. Store-wise performance
# ----------------------------------

print("\n========== STORE-WISE PERFORMANCE ==========")

store_results = []

for store, group in df.groupby("store_id"):

    mae = mean_absolute_error(
        group["quantity_sold"],
        group["random_forest_prediction"]
    )

    rmse = np.sqrt(mean_squared_error(
        group["quantity_sold"],
        group["random_forest_prediction"]
    ))

    r2 = r2_score(
        group["quantity_sold"],
        group["random_forest_prediction"]
    )

    store_results.append({
        "store_id": store,
        "records": len(group),
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    })

store_df = pd.DataFrame(store_results)

print(store_df.round(3).to_string(index=False))

# ----------------------------------
# 5. Product-wise performance
# ----------------------------------

print("\n========== PRODUCT-WISE PERFORMANCE ==========")

product_results = []

for product, group in df.groupby("product_id"):

    mae = mean_absolute_error(
        group["quantity_sold"],
        group["random_forest_prediction"]
    )

    rmse = np.sqrt(mean_squared_error(
        group["quantity_sold"],
        group["random_forest_prediction"]
    ))

    r2 = r2_score(
        group["quantity_sold"],
        group["random_forest_prediction"]
    )

    product_results.append({
        "product_id": product,
        "records": len(group),
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    })

product_df = pd.DataFrame(product_results)

print(product_df.round(3).to_string(index=False))

# ----------------------------------
# 6. Save analysis reports
# ----------------------------------

store_df.to_csv(
    OUTPUT_DIR / "kaggle_store_performance.csv",
    index=False
)

product_df.to_csv(
    OUTPUT_DIR / "kaggle_product_performance.csv",
    index=False
)

print("\nAnalysis reports saved successfully!")
print("Store report: kaggle_store_performance.csv")
print("Product report: kaggle_product_performance.csv")
