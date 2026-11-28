import csv
import math
from datetime import date, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.database import engine

router = APIRouter(prefix="/redistribution", tags=["Redistribution"])
BACKEND_DIR = Path(__file__).resolve().parents[2]
FORECAST_FILE = BACKEND_DIR / "seven_day_forecast.csv"


class TransferRequest(BaseModel):
    product_id: str = Field(min_length=1)
    from_store: str = Field(min_length=1)
    to_store: str = Field(min_length=1)
    transfer_quantity: int = Field(gt=0)
    notes: str | None = None


@router.get("/recommendations")
def get_recommendations():
    try:
        today = date.today()
        future_forecast = {}
        if FORECAST_FILE.exists():
            with FORECAST_FILE.open("r", encoding="utf-8-sig", newline="") as file:
                for row in csv.DictReader(file):
                    forecast_date = date.fromisoformat(str(row.get("forecast_date", ""))[:10])
                    if today <= forecast_date <= today + timedelta(days=6):
                        key = (str(row.get("store_id")), str(row.get("product_id")))
                        future_forecast[key] = future_forecast.get(key, 0.0) + float(row.get("predicted_units") or row.get("predicted_demand") or 0)

        with engine.connect() as connection:
            stock_rows = connection.execute(text("""
                SELECT b.store_id, b.product_id,
                       SUM(b.quantity_remaining) AS available_stock,
                       MAX(p.product_name) AS product_name,
                       MAX(p.base_daily_demand) AS base_daily_demand,
                       MAX(st.store_name) AS store_name
                FROM public.inventory_batches b
                JOIN public.products p ON p.product_id = b.product_id
                LEFT JOIN public.stores st ON st.store_id = b.store_id
                WHERE b.quantity_remaining > 0 AND b.expiry_date >= CURRENT_DATE
                  AND b.store_id IS NOT NULL
                GROUP BY b.store_id, b.product_id
            """)).mappings().all()
            sales_rows = connection.execute(text("""
                SELECT store_id, product_id, SUM(quantity_sold) AS sold_units
                FROM public.sales
                WHERE sale_date >= CURRENT_DATE - INTERVAL '14 days'
                GROUP BY store_id, product_id
            """)).mappings().all()
            product_rows = connection.execute(text("""
                SELECT product_id, product_name, base_daily_demand
                FROM public.products
            """)).mappings().all()
            store_rows = connection.execute(text("""
                SELECT store_id, store_name FROM public.stores
            """)).mappings().all()

        sales_map = {(str(r["store_id"]), str(r["product_id"])): float(r["sold_units"] or 0) for r in sales_rows}
        stock_map = {(str(r["store_id"]), str(r["product_id"])): dict(r) for r in stock_rows}
        records = []
        for product in product_rows:
            for store in store_rows:
                key = (str(store["store_id"]), str(product["product_id"]))
                stock_record = stock_map.get(key, {})
                if key in future_forecast:
                    demand = future_forecast[key]
                    basis = "7-day model forecast"
                elif key in sales_map:
                    demand = sales_map[key] / 2.0
                    basis = "recent 14-day sales estimate"
                else:
                    demand = float(product["base_daily_demand"] or 0) * 7
                    basis = "product baseline demand"
                available_stock = int(stock_record.get("available_stock") or 0)
                seven_day_demand = max(0, float(demand))
                reserve_stock = math.ceil(seven_day_demand * 1.2)
                records.append({
                    "store_id": key[0],
                    "store_name": store["store_name"],
                    "product_id": key[1],
                    "product_name": product["product_name"],
                    "available_stock": available_stock,
                    "seven_day_demand": seven_day_demand,
                    "reserve_stock": reserve_stock,
                    "shortage_quantity": max(0, reserve_stock - available_stock),
                    "surplus_quantity": max(0, available_stock - reserve_stock),
                    "demand_basis": basis,
                })

        remaining_surplus = {(r["store_id"], r["product_id"]): r["surplus_quantity"] for r in records}
        recommendations = []
        shortages = sorted((r for r in records if r["shortage_quantity"] > 0), key=lambda x: x["shortage_quantity"], reverse=True)
        for receiver in shortages:
            shortage = receiver["shortage_quantity"]
            donors = sorted(
                (r for r in records if r["product_id"] == receiver["product_id"] and r["store_id"] != receiver["store_id"]),
                key=lambda x: remaining_surplus.get((x["store_id"], x["product_id"]), 0), reverse=True,
            )
            for donor in donors:
                if shortage <= 0:
                    break
                donor_key = (donor["store_id"], donor["product_id"])
                transferable = remaining_surplus.get(donor_key, 0)
                if transferable <= 0:
                    continue
                quantity = min(shortage, transferable)
                recommendations.append({
                    "product_id": receiver["product_id"],
                    "product_name": receiver["product_name"],
                    "from_store": donor["store_id"],
                    "from_store_name": donor["store_name"],
                    "to_store": receiver["store_id"],
                    "to_store_name": receiver["store_name"],
                    "transfer_quantity": int(quantity),
                    "transfer_type": "INTERNAL",
                    "demand_basis": receiver["demand_basis"],
                })
                remaining_surplus[donor_key] -= quantity
                shortage -= quantity
            if shortage > 0:
                recommendations.append({
                    "product_id": receiver["product_id"],
                    "product_name": receiver["product_name"],
                    "from_store": "EXTERNAL_SUPPLIER",
                    "from_store_name": "External supplier",
                    "to_store": receiver["store_id"],
                    "to_store_name": receiver["store_name"],
                    "transfer_quantity": int(shortage),
                    "transfer_type": "PURCHASE",
                    "demand_basis": receiver["demand_basis"],
                })

        return {
            "recommendations": recommendations,
            "inventory_positions": len(records),
            "computed_at": date.today().isoformat(),
            "basis": "Uses current 7-day model forecast when available; otherwise recent 14-day sales, then product baseline demand. Applies a 20% reserve.",
        }
    except Exception as error:
        print("Redistribution recommendations error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to calculate redistribution recommendations")


@router.post("/transfers", status_code=201)
def create_transfer_request(transfer: TransferRequest):
    if transfer.from_store == transfer.to_store:
        raise HTTPException(status_code=400, detail="Source and destination stores must be different")
    if transfer.from_store == "EXTERNAL_SUPPLIER":
        raise HTTPException(status_code=400, detail="External purchases are not internal transfer requests")
    try:
        with engine.begin() as connection:
            valid_product = connection.execute(
                text("SELECT 1 FROM public.products WHERE product_id = :product_id"),
                {"product_id": transfer.product_id},
            ).first()
            valid_stores = connection.execute(text("""
                SELECT COUNT(*) FROM public.stores
                WHERE store_id IN (:from_store, :to_store)
            """), {"from_store": transfer.from_store, "to_store": transfer.to_store}).scalar_one()
            if not valid_product or int(valid_stores) != 2:
                raise HTTPException(status_code=404, detail="The selected product or store was not found")
            available = connection.execute(text("""
                SELECT COALESCE(SUM(quantity_remaining), 0)
                FROM public.inventory_batches
                WHERE store_id = :from_store AND product_id = :product_id
                  AND expiry_date >= CURRENT_DATE AND quantity_remaining > 0
            """), {"from_store": transfer.from_store, "product_id": transfer.product_id}).scalar_one()
            if int(available or 0) < transfer.transfer_quantity:
                raise HTTPException(status_code=409, detail=f"Source store currently has only {int(available or 0)} unexpired units")
            result = connection.execute(text("""
                INSERT INTO public.redistribution_transfers
                    (product_id, from_store, to_store, transfer_quantity, status, notes, created_at)
                VALUES (:product_id, :from_store, :to_store, :transfer_quantity, 'requested', :notes, NOW())
                RETURNING transfer_id
            """), transfer.model_dump()).mappings().first()
        return {"message": "Transfer request created", "transfer_id": result["transfer_id"], "status": "requested"}
    except Exception as error:
        print("Create transfer request error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to create transfer request. Apply manager_modules.sql first.")


@router.get("/transfers")
def get_transfer_requests():
    try:
        with engine.connect() as connection:
            rows = connection.execute(text("""
                SELECT t.transfer_id, t.product_id, p.product_name,
                       t.from_store, sf.store_name AS from_store_name,
                       t.to_store, st.store_name AS to_store_name,
                       t.transfer_quantity, t.status, t.notes, t.created_at
                FROM public.redistribution_transfers t
                LEFT JOIN public.products p ON p.product_id = t.product_id
                LEFT JOIN public.stores sf ON sf.store_id = t.from_store
                LEFT JOIN public.stores st ON st.store_id = t.to_store
                ORDER BY t.created_at DESC
            """)).mappings().all()
        return [dict(row) for row in rows]
    except Exception as error:
        print("Transfer requests error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to retrieve transfer requests. Apply manager_modules.sql first.")
