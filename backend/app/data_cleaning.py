
import pandas as pd
from pathlib import Path

# Locate backend folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load all datasets
stores = pd.read_csv(BASE_DIR / "stores.csv")
products = pd.read_csv(BASE_DIR / "products.csv")
inventory = pd.read_csv(BASE_DIR / "inventory_batches.csv")
sales = pd.read_csv(BASE_DIR / "sales.csv")


def inspect_data(name, df):

    print("\n================================")
    print("DATASET:", name)
    print("================================")

    print("Shape:", df.shape)

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nDuplicate rows:", df.duplicated().sum())

    print("\nData types:")
    print(df.dtypes)


# Inspect all datasets
inspect_data("STORES", stores)
inspect_data("PRODUCTS", products)
inspect_data("INVENTORY", inventory)
inspect_data("SALES", sales)


# Convert date columns
sales["sale_date"] = pd.to_datetime(
    sales["sale_date"], errors="coerce"
)

inventory["manufacturing_date"] = pd.to_datetime(
    inventory["manufacturing_date"], errors="coerce"
)

inventory["expiry_date"] = pd.to_datetime(
    inventory["expiry_date"], errors="coerce"
)


print("\nDATA INSPECTION COMPLETED!")
