
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Locate backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load cleaned datasets
sales = pd.read_csv(BASE_DIR / "sales_cleaned.csv")
products = pd.read_csv(BASE_DIR / "products_cleaned.csv")
stores = pd.read_csv(BASE_DIR / "stores_cleaned.csv")

# Convert date
sales["sale_date"] = pd.to_datetime(sales["sale_date"])

print("\n===== ZEROWASTENET EDA =====")

# 1. Overall sales summary
print("\n1. OVERALL SALES SUMMARY")

print("Total sales records:", len(sales))
print("Total quantity sold:", sales["quantity_sold"].sum())
print("Total sales revenue:",
      sales["quantity_sold"].mul(
          sales["selling_price"]
      ).sum())

# 2. Product-wise sales
product_sales = sales.groupby(
    "product_id"
)["quantity_sold"].sum().reset_index()

product_sales = product_sales.merge(
    products[["product_id", "product_name", "category"]],
    on="product_id"
)

product_sales = product_sales.sort_values(
    "quantity_sold", ascending=False
)

print("\n2. TOP 10 SELLING PRODUCTS")
print(product_sales.head(10))

# 3. Store-wise sales
store_sales = sales.groupby(
    "store_id"
)["quantity_sold"].sum().reset_index()

store_sales = store_sales.merge(
    stores[["store_id", "store_name"]],
    on="store_id"
)

print("\n3. STORE-WISE SALES")
print(store_sales)

# 4. Category-wise sales
category_sales = sales.merge(
    products[["product_id", "category"]],
    on="product_id"
).groupby("category")["quantity_sold"].sum().sort_values(
    ascending=False
)

print("\n4. CATEGORY-WISE SALES")
print(category_sales)

# 5. Daily sales trend
daily_sales = sales.groupby(
    "sale_date"
)["quantity_sold"].sum()

plt.figure(figsize=(12, 5))
daily_sales.plot()
plt.title("ZeroWasteNet - Daily Grocery Sales")
plt.xlabel("Date")
plt.ylabel("Quantity Sold")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(BASE_DIR / "daily_sales_trend.png")
plt.show()

# 6. Top 10 products chart
plt.figure(figsize=(10, 5))

product_sales.head(10).plot(
    x="product_name",
    y="quantity_sold",
    kind="bar",
    legend=False
)

plt.title("Top 10 Selling Grocery Products")
plt.xlabel("Product")
plt.ylabel("Quantity Sold")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(BASE_DIR / "top_products.png")
plt.show()

print("\n===== EDA COMPLETED =====")
