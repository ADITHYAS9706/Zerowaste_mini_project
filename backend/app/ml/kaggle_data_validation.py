
from pathlib import Path
import pandas as pd

# Project paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "processed" / "kaggle_grocery_cleaned.csv"
OUTPUT_DIR = BASE_DIR / "processed"

REPORT_PATH = OUTPUT_DIR / "kaggle_data_validation_report.csv"
MISSING_DATES_PATH = OUTPUT_DIR / "kaggle_missing_dates.csv"


def main():
    print("\n========== KAGGLE DATA VALIDATION ==========\n")

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    required_columns = [
        "sale_date",
        "store_id",
        "product_id",
        "quantity_sold"
    ]

    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df["sale_date"] = pd.to_datetime(
        df["sale_date"], errors="coerce"
    )

    checks = []

    def add_check(name, passed, details):
        checks.append({
            "validation_check": name,
            "status": "PASS" if passed else "FAIL",
            "details": str(details)
        })

        print(f"{'PASS' if passed else 'FAIL'}: {name}")
        print(f"     {details}\n")

    # 1. Total records
    add_check(
        "Total records",
        len(df) > 0,
        f"{len(df)} records found"
    )

    # 2. Missing values
    missing_values = int(df.isnull().sum().sum())

    add_check(
        "Missing values",
        missing_values == 0,
        f"{missing_values} missing values"
    )

    # 3. Invalid dates
    invalid_dates = int(df["sale_date"].isna().sum())

    add_check(
        "Date validity",
        invalid_dates == 0,
        f"{invalid_dates} invalid dates"
    )

    # 4. Duplicate store-product-date records
    valid_keys = df.dropna(
        subset=["sale_date", "store_id", "product_id"]
    )

    duplicate_count = int(
        valid_keys.duplicated(
            subset=["sale_date", "store_id", "product_id"]
        ).sum()
    )

    add_check(
        "Duplicate store-product-date records",
        duplicate_count == 0,
        f"{duplicate_count} duplicate records"
    )

    # 5. Store-product combinations
    combinations = df[
        ["store_id", "product_id"]
    ].drop_duplicates()

    combination_count = len(combinations)

    add_check(
        "Store-product combinations",
        combination_count > 0,
        f"{combination_count} unique combinations"
    )

    # 6. Date continuity
    missing_dates = []

    if invalid_dates == 0 and not df.empty:
        global_dates = pd.date_range(
            df["sale_date"].min(),
            df["sale_date"].max(),
            freq="D"
        )

        for _, group in valid_keys.groupby(
            ["store_id", "product_id"]
        ):
            existing_dates = pd.DatetimeIndex(
                group["sale_date"].drop_duplicates()
            )

            absent_dates = global_dates.difference(existing_dates)

            if len(absent_dates) > 0:
                store_id = group["store_id"].iloc[0]
                product_id = group["product_id"].iloc[0]

                for date in absent_dates:
                    missing_dates.append({
                        "store_id": store_id,
                        "product_id": product_id,
                        "missing_date": date.strftime("%Y-%m-%d")
                    })

    missing_dates_df = pd.DataFrame(
        missing_dates,
        columns=["store_id", "product_id", "missing_date"]
    )

    missing_dates_df.to_csv(
        MISSING_DATES_PATH, index=False
    )

    add_check(
        "Date continuity",
        len(missing_dates_df) == 0,
        f"{len(missing_dates_df)} missing store-product dates"
    )

    # 7. Negative sales
    negative_sales = int(
        (pd.to_numeric(
            df["quantity_sold"], errors="coerce"
        ) < 0).sum()
    )

    add_check(
        "Negative sales quantities",
        negative_sales == 0,
        f"{negative_sales} negative values"
    )

    # 8. Negative inventory, if available
    if "inventory_level" in df.columns:
        inventory = pd.to_numeric(
            df["inventory_level"], errors="coerce"
        )

        negative_inventory = int((inventory < 0).sum())

        add_check(
            "Negative inventory values",
            negative_inventory == 0,
            f"{negative_inventory} negative values"
        )

    # Save validation report
    report = pd.DataFrame(checks)

    report.to_csv(REPORT_PATH, index=False)

    print("\n========== VALIDATION SUMMARY ==========")
    print(f"Total checks: {len(report)}")
    print(f"Passed: {(report['status'] == 'PASS').sum()}")
    print(f"Failed: {(report['status'] == 'FAIL').sum()}")

    print(f"\nReport saved: {REPORT_PATH}")
    print(f"Missing dates saved: {MISSING_DATES_PATH}")

    if (report["status"] == "FAIL").any():
        print("\nWARNING: Some validation checks failed.")
    else:
        print("\nALL VALIDATION CHECKS PASSED!")


if __name__ == "__main__":
    main()
