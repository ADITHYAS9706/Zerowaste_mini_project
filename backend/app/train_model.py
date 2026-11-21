
import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Load feature dataset
df = pd.read_csv(BASE_DIR / "ml_features.csv")

df["sale_date"] = pd.to_datetime(df["sale_date"])

# Sort chronologically
df = df.sort_values("sale_date").reset_index(drop=True)

# Select ML features
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

X = df[features]
y = df[target]

# Chronological 80:20 split
split_index = int(len(df) * 0.8)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

print("\n===== RANDOM FOREST TRAINING =====")

print("Training records:", len(X_train))
print("Testing records:", len(X_test))

# Create model
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=12,
    random_state=42,
    n_jobs=-1
)

# Train
model.fit(X_train, y_train)

# Predict
predictions = model.predict(X_test)

# Evaluate
mae = mean_absolute_error(y_test, predictions)

rmse = np.sqrt(
    mean_squared_error(y_test, predictions)
)

r2 = r2_score(y_test, predictions)

print("\n===== MODEL EVALUATION =====")

print("MAE:", round(mae, 2))
print("RMSE:", round(rmse, 2))
print("R2 Score:", round(r2, 4))

# Save model
model_path = BASE_DIR / "random_forest_model.pkl"

joblib.dump(model, model_path)

print("\nModel saved successfully!")
print("Location:", model_path)

# Save actual vs predicted values
results = pd.DataFrame({
    "Actual": y_test.values,
    "Predicted": predictions
})

results.to_csv(
    BASE_DIR / "model_predictions.csv",
    index=False
)

print("Predictions saved successfully!")

print("\n===== TRAINING COMPLETED =====")
