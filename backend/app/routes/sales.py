from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.database import engine

router = APIRouter(prefix="/sales", tags=["Sales"])


class SaleCreate(BaseModel):
    store_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    quantity_sold: int = Field(gt=0)
    selling_price: float | None = Field(default=None, ge=0)


@router.get("/")
def get_sales(limit: int = 250):
    limit = min(max(limit, 1), 1000)
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text("""
                    SELECT
                        s.sale_id,
                        s.sale_date,
                        s.store_id,
                        st.store_name,
                        s.product_id,
                        p.product_name,
                        p.unit,
                        s.quantity_sold,
                        s.selling_price,
                        (s.quantity_sold * s.selling_price) AS total_amount,
                        s.created_at
                    FROM public.sales s
                    LEFT JOIN public.products p ON p.product_id = s.product_id
                    LEFT JOIN public.stores st ON st.store_id = s.store_id
                    ORDER BY s.sale_date DESC, s.created_at DESC
                    LIMIT :limit
                """), {"limit": limit}
            ).mappings().all()
        return [dict(row) for row in rows]
    except Exception as error:
        print("Get sales error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to retrieve sales")


@router.post("/", status_code=201)
def create_sale(sale: SaleCreate):
    try:
        with engine.begin() as connection:
            product = connection.execute(
                text("SELECT unit_price FROM public.products WHERE product_id = :product_id"),
                {"product_id": sale.product_id},
            ).mappings().first()
            if not product:
                raise HTTPException(status_code=404, detail="Product was not found")

            store_exists = connection.execute(
                text("SELECT 1 FROM public.stores WHERE store_id = :store_id"),
                {"store_id": sale.store_id},
            ).first()
            if not store_exists:
                raise HTTPException(status_code=404, detail="Store was not found")

            price = float(sale.selling_price if sale.selling_price is not None else product["unit_price"] or 0)
            batches = connection.execute(
                text("""
                    SELECT batch_id, quantity_remaining
                    FROM public.inventory_batches
                    WHERE store_id = :store_id
                      AND product_id = :product_id
                      AND quantity_remaining > 0
                      AND expiry_date >= CURRENT_DATE
                    ORDER BY expiry_date ASC, batch_id ASC
                    FOR UPDATE
                """),
                {"store_id": sale.store_id, "product_id": sale.product_id},
            ).mappings().all()

            available = sum(int(row["quantity_remaining"] or 0) for row in batches)
            if available < sale.quantity_sold:
                raise HTTPException(
                    status_code=409,
                    detail=f"Not enough unexpired stock. Available: {available} units.",
                )

            remaining_to_deduct = sale.quantity_sold
            for batch in batches:
                if remaining_to_deduct <= 0:
                    break
                batch_quantity = int(batch["quantity_remaining"] or 0)
                deduction = min(batch_quantity, remaining_to_deduct)
                connection.execute(
                    text("""
                        UPDATE public.inventory_batches
                        SET quantity_remaining = quantity_remaining - :deduction
                        WHERE batch_id = :batch_id
                    """),
                    {"deduction": deduction, "batch_id": batch["batch_id"]},
                )
                remaining_to_deduct -= deduction

            inserted = connection.execute(
                text("""
                    INSERT INTO public.sales
                        (sale_date, store_id, product_id, quantity_sold, selling_price, created_at)
                    VALUES
                        (:sale_date, :store_id, :product_id, :quantity_sold, :selling_price, NOW())
                    RETURNING sale_id
                """),
                {
                    "sale_date": date.today(),
                    "store_id": sale.store_id,
                    "product_id": sale.product_id,
                    "quantity_sold": sale.quantity_sold,
                    "selling_price": price,
                },
            ).mappings().first()

        return {
            "message": "Sale recorded and stock deducted using FEFO",
            "sale_id": inserted["sale_id"] if inserted else None,
            "quantity_sold": sale.quantity_sold,
            "selling_price": price,
            "total_amount": round(sale.quantity_sold * price, 2),
        }
    except HTTPException:
        raise
    except Exception as error:
        print("Create sale error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to record sale")
