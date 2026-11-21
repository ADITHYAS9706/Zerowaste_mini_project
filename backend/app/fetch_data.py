
import pandas as pd
from sqlalchemy import text
from app.database import engine
from pathlib import Path


# Save CSV files in the backend folder
BASE_DIR = Path(__file__).resolve().parent.parent


def fetch_table(table_name):

    query = text(f"SELECT * FROM public.{table_name}")

    with engine.connect() as connection:
        df = pd.read_sql(query, connection)

    return df


if __name__ == "__main__":

    print("\n===== ZEROWASTENET DATA FETCH =====")

    tables = [
        "stores",
        "products",
        "inventory_batches",
        "sales"
    ]

    for table in tables:

        print(f"\nFetching {table}...")

        df = fetch_table(table)

        # Display first five records
        print("\nFirst 5 records:")
        print(df.head())

        # Display record count
        print("\nTotal records:", len(df))

        # Display column names
        print("\nColumns:", df.columns.tolist())

        # Save as CSV
        file_path = BASE_DIR / f"{table}.csv"

        df.to_csv(file_path, index=False)

        print(f"\n{table}.csv saved successfully!")

    print("\n===== DATA FETCH COMPLETED =====")
