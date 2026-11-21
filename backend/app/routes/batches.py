
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database import engine
from app.schemas.batch import BatchCreate

router = APIRouter(prefix="/batches", tags=["Batches"])


@router.post("/")
def create_batch(batch: BatchCreate):
    try:
        with engine.begin() as connection:

            # Generate the next batch ID
            next_id = connection.execute(
                text("SELECT nextval('public.batch_id_seq')")
            ).scalar_one()

            batch_id = f"B{next_id:05d}"

            # Insert batch into Supabase
            connection.execute(
                text("""
                    INSERT INTO public.inventory_batches
                    (
                        batch_id, store_id, product_id, batch_code,
                        quantity_received, quantity_remaining,
                        manufacturing_date, expiry_date
                    )
                    VALUES
                    (
                        :batch_id, :store_id, :product_id, :batch_code,
                        :quantity_received, :quantity_remaining,
                        :manufacturing_date, :expiry_date
                    )
                """),
                {
                    "batch_id": batch_id,
                    "store_id": batch.store_id,
                    "product_id": batch.product_id,
                    "batch_code": batch.batch_code,
                    "quantity_received": batch.quantity_received,
                    "quantity_remaining": batch.quantity_remaining,
                    "manufacturing_date": batch.manufacturing_date,
                    "expiry_date": batch.expiry_date
                }
            )

        return {
            "message": "Batch registered successfully",
            "batch_id": batch_id,
            "batch_code": batch.batch_code
        }

    except Exception as error:
        print("Batch registration error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Unable to register batch"
        )


@router.get("/")
def get_batches():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT *
                    FROM public.inventory_batches
                    ORDER BY batch_id
                """)
            )

            return [dict(row) for row in result.mappings().all()]

    except Exception as error:
        print("Get batches error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve batches"
        )
