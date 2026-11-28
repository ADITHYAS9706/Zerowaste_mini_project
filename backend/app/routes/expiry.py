from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from app.database import engine

router = APIRouter(prefix="/expiry", tags=["Expiry Management"])


@router.get("/")
def get_expiry_records(status: str = Query(default="all", pattern="^(all|expired|near|safe)$")):
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text("""
                    SELECT
                        b.batch_id, b.batch_code, b.store_id, st.store_name,
                        b.product_id, p.product_name, p.unit,
                        b.quantity_received, b.quantity_remaining,
                        b.manufacturing_date, b.expiry_date,
                        (b.expiry_date - CURRENT_DATE) AS days_to_expiry
                    FROM public.inventory_batches b
                    LEFT JOIN public.products p ON p.product_id = b.product_id
                    LEFT JOIN public.stores st ON st.store_id = b.store_id
                    WHERE b.quantity_remaining > 0
                    ORDER BY b.expiry_date ASC, b.batch_id ASC
                """
                )
            ).mappings().all()

        result = []
        for row in rows:
            item = dict(row)
            days = int(item["days_to_expiry"])
            item["expiry_status"] = "expired" if days < 0 else ("near" if days <= 7 else "safe")
            if status == "all" or item["expiry_status"] == status:
                result.append(item)
        return result
    except Exception as error:
        print("Expiry records error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to retrieve expiry records")
