
from pathlib import Path
import pandas as pd
import numpy as np


# =====================================================
# 1. PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "processed"

CLEANED_FILE = PROCESSED_DIR / "kaggle_grocery_cleaned.csv"
FEATURE_FILE = PROCESSED_DIR / "kaggle_ml_features.csv"
VALIDATION_FILE = PROCESSED_DIR / "kaggle_data_validation_report.csv"

HOLDOUT_FILE = PROCESSED_DIR / "kaggle_v3_holdout_evaluation.csv"
FIXED_BACKTEST_FILE = PROCESSED_DIR / "kaggle_v3_seven_day_backtest.csv"
FIXED_DAILY_FILE = PROCESSED_DIR / "kaggle_v3_backtest_by_day.csv"

ROLLING_PREDICTIONS_FILE = (
    PROCESSED_DIR / "kaggle_v3_rolling_origin_predictions.csv"
)
ROLLING_METRICS_FILE = (
    PROCESSED_DIR / "kaggle_v3_rolling_origin_metrics.csv"
)
ROLLING_DAILY_FILE = (
    PROCESSED_DIR / "kaggle_v3_rolling_origin_daily_metrics.csv"
)
STORE_PRODUCT_FILE = (
    PROCESSED_DIR / "kaggle_v3_store_product_analysis.csv"
)

REPORT_FILE = PROCESSED_DIR / "kaggle_ml_final_report.md"
SUMMARY_FILE = PROCESSED_DIR / "kaggle_ml_final_summary.csv"


# =====================================================
# 2. HELPER FUNCTIONS
# =====================================================

def load_csv(path, required=True):

    if not path.exists():

        if required:
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

        print(f"Optional file not found: {path.name}")
        return None

    return pd.read_csv(path)


def calculate_metrics(actual, predicted):

    actual = pd.to_numeric(actual, errors="coerce")
    predicted = pd.to_numeric(predicted, errors="coerce")

    valid = actual.notna() & predicted.notna()

    actual = actual[valid]
    predicted = predicted[valid]

    if len(actual) == 0:
        return {}

    return {
        "MAE": float(np.mean(np.abs(actual - predicted))),
        "RMSE": float(
            np.sqrt(np.mean((actual - predicted) ** 2))
        )
    }


def markdown_table(df):

    if df is None or df.empty:
        return "No data available."

    return df.to_markdown(index=False)


def add_summary_row(summary, category, metric, value):

    summary.append({
        "category": category,
        "metric": metric,
        "value": value
    })


# =====================================================
# 3. MAIN REPORT GENERATOR
# =====================================================

def main():

    print("\n========== ZERO WASTE ML FINAL REPORT ==========\n")

    summary = []
    report = []

    # -------------------------------------------------
    # A. DATASET INFORMATION
    # -------------------------------------------------

    cleaned = load_csv(CLEANED_FILE)
    features = load_csv(FEATURE_FILE)

    cleaned["sale_date"] = pd.to_datetime(
        cleaned["sale_date"], errors="coerce"
    )

    features["sale_date"] = pd.to_datetime(
        features["sale_date"], errors="coerce"
    )

    total_records = len(cleaned)
    feature_records = len(features)

    store_count = cleaned["store_id"].nunique()
    product_count = cleaned["product_id"].nunique()

    combination_count = cleaned[
        ["store_id", "product_id"]
    ].drop_duplicates().shape[0]

    start_date = cleaned["sale_date"].min().date()
    end_date = cleaned["sale_date"].max().date()

    add_summary_row(
        summary, "Dataset", "Cleaned records", total_records
    )
    add_summary_row(
        summary, "Dataset", "Feature records", feature_records
    )
    add_summary_row(
        summary, "Dataset", "Stores", store_count
    )
    add_summary_row(
        summary, "Dataset", "Products", product_count
    )
    add_summary_row(
        summary, "Dataset", "Store-product combinations",
        combination_count
    )

    report.append("# ZeroWasteNet - Final ML Pipeline Report\n")

    report.append(
        "## 1. Dataset Description\n"
    )

    report.append(
        f"- Cleaned grocery records: {total_records}\n"
        f"- Feature-engineered records: {feature_records}\n"
        f"- Unique stores: {store_count}\n"
        f"- Unique products: {product_count}\n"
        f"- Store-product combinations: {combination_count}\n"
        f"- Dataset date range: {start_date} to {end_date}\n"
    )

    # -------------------------------------------------
    # B. DATA VALIDATION
    # -------------------------------------------------

    validation = load_csv(
        VALIDATION_FILE, required=False
    )

    report.append("\n## 2. Data Validation\n")

    if validation is not None:

        passed = int(
            (validation["status"] == "PASS").sum()
        )

        failed = int(
            (validation["status"] == "FAIL").sum()
        )

        report.append(
            f"- Total validation checks: {len(validation)}\n"
            f"- Passed: {passed}\n"
            f"- Failed: {failed}\n"
        )

        report.append("\n### Validation Check Results\n")
        report.append(markdown_table(validation))

        add_summary_row(
            summary, "Validation", "Passed checks", passed
        )
        add_summary_row(
            summary, "Validation", "Failed checks", failed
        )

    else:
        report.append(
            "Validation report was not found.\n"
        )

    # -------------------------------------------------
    # C. FEATURE ENGINEERING
    # -------------------------------------------------

    report.append("\n## 3. Feature Engineering\n")

    report.append("""
The feature-engineering pipeline created historical sales,
calendar and inventory-related input features.

**Numerical features:**
- day_of_week
- month
- is_weekend
- lag_1
- lag_7
- lag_14
- rolling_mean_7
- rolling_mean_14
- inventory_level
- discount
- price
- competitor_pricing

**Categorical features:**
- store_id
- product_id
- weather_condition
- promotion
- seasonality
- epidemic

**Prediction target:** quantity_sold
""")

    # -------------------------------------------------
    # D. MODEL TRAINING
    # -------------------------------------------------

    report.append("\n## 4. Model Training\n")

    report.append("""
**Selected model:** Random Forest Regressor V3

**Configuration:**
- Number of estimators: 300
- Maximum depth: 15
- Minimum samples per leaf: 2
- Random state: 42
- OneHotEncoder with handle_unknown='ignore'
- Chronological training and testing split

The model was trained using a scikit-learn Pipeline
containing preprocessing and Random Forest regression.
""")

    # -------------------------------------------------
    # E. FIXED-MODEL HOLDOUT EVALUATION
    # -------------------------------------------------

    report.append("\n## 5. Fixed-Model Holdout Evaluation\n")

    holdout = load_csv(
        HOLDOUT_FILE, required=False
    )

    if holdout is not None:

        report.append(
            "Existing holdout evaluation results:\n\n"
        )

        report.append(markdown_table(holdout))

    else:

        report.append(
            "Holdout evaluation file was not found.\n"
        )

    # -------------------------------------------------
    # F. FIXED-MODEL SEVEN-DAY BACKTEST
    # -------------------------------------------------

    report.append("\n## 6. Fixed-Model Seven-Day Backtest\n")

    fixed = load_csv(
        FIXED_BACKTEST_FILE, required=False
    )

    if fixed is not None:

        fixed_v3 = calculate_metrics(
            fixed["actual_sales"],
            fixed["predicted_demand"]
        )

        fixed_naive = calculate_metrics(
            fixed["actual_sales"],
            fixed["seasonal_naive_prediction"]
        )

        report.append(
            f"- Total forecast records: {len(fixed)}\n"
            f"- V3 MAE: {fixed_v3['MAE']:.4f}\n"
            f"- V3 RMSE: {fixed_v3['RMSE']:.4f}\n"
            f"- Seasonal-naive MAE: {fixed_naive['MAE']:.4f}\n"
            f"- Seasonal-naive RMSE: {fixed_naive['RMSE']:.4f}\n"
        )

        add_summary_row(
            summary, "Fixed Backtest", "V3 MAE",
            fixed_v3["MAE"]
        )
        add_summary_row(
            summary, "Fixed Backtest", "V3 RMSE",
            fixed_v3["RMSE"]
        )
        add_summary_row(
            summary, "Fixed Backtest", "Naive MAE",
            fixed_naive["MAE"]
        )
        add_summary_row(
            summary, "Fixed Backtest", "Naive RMSE",
            fixed_naive["RMSE"]
        )

    # -------------------------------------------------
    # G. ROLLING-ORIGIN EVALUATION
    # -------------------------------------------------

    report.append("\n## 7. Rolling-Origin Validation\n")

    rolling_metrics = load_csv(
        ROLLING_METRICS_FILE
    )

    rolling_daily = load_csv(
        ROLLING_DAILY_FILE
    )

    rolling_predictions = load_csv(
        ROLLING_PREDICTIONS_FILE
    )

    report.append(
        f"- Total forecast records: {len(rolling_predictions)}\n"
        f"- Forecast origins: "
        f"{rolling_predictions['forecast_origin'].nunique()}\n"
    )

    report.append("\n### Overall Model Metrics\n")
    report.append(markdown_table(rolling_metrics))

    report.append("\n### Day-wise Model Metrics\n")
    report.append(markdown_table(rolling_daily))

    for _, row in rolling_metrics.iterrows():

        for metric in ["MAE", "RMSE", "R2"]:

            if metric in row.index:

                add_summary_row(
                    summary,
                    str(row["model"]),
                    metric,
                    row[metric]
                )

    # -------------------------------------------------
    # H. STORE-PRODUCT ANALYSIS
    # -------------------------------------------------

    report.append("\n## 8. Store-Product Performance Analysis\n")

    store_product = load_csv(
        STORE_PRODUCT_FILE, required=False
    )

    if store_product is not None:

        report.append(
            f"- Total combinations analysed: "
            f"{len(store_product)}\n"
        )

        report.append("\n### Highest Forecasting Errors\n")

        report.append(
            markdown_table(
                store_product.sort_values(
                    "MAE", ascending=False
                ).head(10)
            )
        )

        best = store_product.sort_values(
            "MAE", ascending=True
        ).iloc[0]

        worst = store_product.sort_values(
            "MAE", ascending=False
        ).iloc[0]

        report.append(
            f"\n- Best-performing combination: "
            f"{best['store_id']} / {best['product_id']} "
            f"(MAE: {best['MAE']:.4f})\n"
        )

        report.append(
            f"- Highest-error combination: "
            f"{worst['store_id']} / {worst['product_id']} "
            f"(MAE: {worst['MAE']:.4f})\n"
        )

    else:

        report.append(
            "Store-product analysis file was not found.\n"
        )

    # -------------------------------------------------
    # I. METHODOLOGY AND LIMITATIONS
    # -------------------------------------------------

    report.append("\n## 9. Forecasting Methodology\n")

    report.append("""
The seven-day forecast uses recursive prediction.

At each forecast step:
1. The model predicts the next day's demand.
2. The predicted value is appended to the sales history.
3. Lag and rolling features are updated.
4. The next day's prediction uses the updated history.

The rolling-origin experiment retrains a separate model
at each forecast origin using historical data available
up to that origin.

The seasonal-naive baseline independently uses the
corresponding previous-week sales value.
""")

    report.append("\n## 10. Limitations\n")

    report.append("""
1. The source dataset ends on 2024-01-30. The forecasts
   are historical experiments, not live 2026 forecasts.

2. Future external variables such as inventory, price,
   promotions and weather are held at their latest
   known values during the recursive forecast.

3. The target quantity_sold may be affected by stockouts,
   so it may not represent unconstrained customer demand.

4. The rolling-origin evaluation has negative R².
   Although V3 outperforms the seasonal-naive baseline
   on MAE and RMSE, forecasting errors remain substantial.

5. Model performance varies between store-product
   combinations.

6. The evaluation uses historical data and does not
   establish real-world operational performance.
""")

    # -------------------------------------------------
    # J. FINAL CONCLUSION
    # -------------------------------------------------

    report.append("\n## 11. Conclusion\n")

    report.append("""
The project implemented a complete baseline ML workflow
covering data preprocessing, data validation, feature
engineering, Random Forest training, model evaluation
and recursive seven-day forecasting.

The selected V3 model outperformed the seasonal-naive
baseline on MAE and RMSE in the rolling-origin experiment.

The generated forecasts and evaluation reports provide
a foundation for integrating demand estimates into
expiry monitoring, surplus inventory detection and
grocery redistribution workflows.

Further work is required to improve forecasting accuracy
and validate the system using operational data and
realistic future input variables.
""")

    # -------------------------------------------------
    # K. SAVE FINAL REPORT AND SUMMARY
    # -------------------------------------------------

    REPORT_FILE.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    summary_df = pd.DataFrame(summary)

    summary_df.to_csv(
        SUMMARY_FILE,
        index=False
    )

    print("\n========== REPORT GENERATION COMPLETED ==========")

    print("Report:", REPORT_FILE)
    print("Summary:", SUMMARY_FILE)

    print("\nSummary metrics:")
    print(summary_df.to_string(index=False))

    print("\nFINAL ML REPORT GENERATED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
