
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database import engine

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/")
def get_inventory():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT
                        store_id,
                        product_id,
                        SUM(quantity_remaining) AS available_quantity
                    FROM public.inventory_batches
                    GROUP BY store_id, product_id
                    ORDER BY store_id, product_id
                """)
            )

            inventory = [
                dict(row)
                for row in result.mappings().all()
            ]

        return inventory

    except Exception as error:
        print("Get inventory error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve inventory"
        )
