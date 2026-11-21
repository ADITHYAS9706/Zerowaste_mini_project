
import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = Path(__file__).resolve().parent.parent

df = pd.read_csv(BASE_DIR / "ml_features.csv")
df["sale_date"] = pd.to_datetime(df["sale_date"])

features = [
    "day_of_week",
    "month",
    "is_weekend",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
    "rolling_mean_14",
    "base_daily_demand"
]

target = "quantity_sold"

# Split using unique dates, not individual rows
dates = sorted(df["sale_date"].dropna().unique())
cutoff = int(len(dates) * 0.8)
test_start = dates[cutoff]

train = df[df["sale_date"] < test_start].copy()
test = df[df["sale_date"] >= test_start].copy()

X_train = train[features]
y_train = train[target]

X_test = test[features]
y_test = test[target]

print("\n===== TIME-BASED MODEL VALIDATION =====")
print("Training records:", len(train))
print("Testing records:", len(test))
print("Training ends:", train["sale_date"].max())
print("Testing starts:", test["sale_date"].min())

# Train Random Forest
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=12,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

# Baseline: yesterday's sales
baseline_predictions = test["lag_1"].to_numpy()

def evaluate(name, actual, predicted):
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    r2 = r2_score(actual, predicted)

    print(f"\n{name}")
    print("MAE:", round(mae, 2))
    print("RMSE:", round(rmse, 2))
    print("R2:", round(r2, 4))

    return mae, rmse, r2

rf_metrics = evaluate("RANDOM FOREST", y_test, predictions)
baseline_metrics = evaluate(
    "LAG-1 BASELINE",
    y_test,
    baseline_predictions
)

# Save validated model separately
joblib.dump(
    model,
    BASE_DIR / "random_forest_validated.pkl"
)

# Save test predictions
results = test[
    ["sale_date", "store_id", "product_id"]
].copy()

results["actual"] = y_test.to_numpy()
results["random_forest_prediction"] = predictions
results["baseline_prediction"] = baseline_predictions

results.to_csv(
    BASE_DIR / "validated_predictions.csv",
    index=False
)

print("\nValidated model saved successfully!")
print("\n===== VALIDATION COMPLETED =====")
