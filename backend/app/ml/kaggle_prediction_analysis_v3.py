
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "processed" / "kaggle_model_predictions_v3.csv"

df = pd.read_csv(INPUT_FILE)

actual = df["quantity_sold"]
predicted = df["predicted_sales"]

# Prediction errors
df["error"] = actual - predicted
df["absolute_error"] = df["error"].abs()

print("\n========== V3 OVERALL ANALYSIS ==========")

print("Actual mean:", round(actual.mean(), 2))
print("Predicted mean:", round(predicted.mean(), 2))

print("Actual standard deviation:", round(actual.std(), 2))
print("Predicted standard deviation:", round(predicted.std(), 2))

print("MAE:", round(mean_absolute_error(actual, predicted), 4))

print("RMSE:", round(np.sqrt(mean_squared_error(actual, predicted)), 4))

print("R2:", round(r2_score(actual, predicted), 4))


# Store-wise analysis
print("\n========== STORE-WISE PERFORMANCE ==========")

for store, group in df.groupby("store_id"):

    mae = mean_absolute_error(
        group["quantity_sold"],
        group["predicted_sales"]
    )

    rmse = np.sqrt(mean_squared_error(
        group["quantity_sold"],
        group["predicted_sales"]
    ))

    r2 = r2_score(
        group["quantity_sold"],
        group["predicted_sales"]
    )

    print(
        f"{store} | Records: {len(group)} | "
        f"MAE: {mae:.2f} | RMSE: {rmse:.2f} | R2: {r2:.4f}"
    )


# Product-wise analysis
print("\n========== PRODUCT-WISE PERFORMANCE ==========")

for product, group in df.groupby("product_id"):

    mae = mean_absolute_error(
        group["quantity_sold"],
        group["predicted_sales"]
    )

    print(f"{product} | MAE: {mae:.2f}")


# Save detailed error analysis
OUTPUT_FILE = BASE_DIR / "processed" / "kaggle_v3_error_analysis.csv"

df.to_csv(OUTPUT_FILE, index=False)

print("\nV3 error analysis saved to:", OUTPUT_FILE)

