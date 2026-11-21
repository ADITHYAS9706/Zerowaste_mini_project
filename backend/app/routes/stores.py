
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database import engine
from app.schemas.store import StoreCreate

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.post("/")
def create_store(store: StoreCreate):
    try:
        with engine.begin() as connection:

            # Generate a unique store ID
            next_id = connection.execute(
                text("SELECT nextval('public.store_id_seq')")
            ).scalar_one()

            store_id = f"S{next_id:03d}"

            # Insert store into Supabase
            connection.execute(
                text("""
                    INSERT INTO public.stores
                    (store_id, store_name, address, latitude, longitude, phone)
                    VALUES
                    (:store_id, :store_name, :address, :latitude, :longitude, :phone)
                """),
                {
                    "store_id": store_id,
                    "store_name": store.store_name,
                    "address": store.address,
                    "latitude": store.latitude,
                    "longitude": store.longitude,
                    "phone": store.phone
                }
            )

        return {
            "message": "Store registered successfully",
            "store_id": store_id,
            "store_name": store.store_name
        }

    except Exception as error:
        print("Store registration error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Unable to register store"
        )


@router.get("/")
def get_stores():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT store_id, store_name, address,
                           latitude, longitude, phone
                    FROM public.stores
                    ORDER BY store_id
                """)
            )

            stores = [dict(row) for row in result.mappings().all()]

        return stores

    except Exception as error:
        print("Get stores error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve stores"
        )
