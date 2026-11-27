
import math

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from app.database import engine
from app.schemas.store import StoreCreate


router = APIRouter(prefix="/stores", tags=["Stores"])


# -----------------------------------------
# Calculate distance using Haversine formula
# -----------------------------------------
def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371  # Kilometres

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


# -----------------------------------------
# Add a new store
# -----------------------------------------
@router.post("/")
def create_store(store: StoreCreate):
    try:
        with engine.begin() as connection:

            next_id = connection.execute(
                text("SELECT nextval('public.store_id_seq')")
            ).scalar_one()

            store_id = f"S{next_id:03d}"

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


# -----------------------------------------
# Get all registered stores
# -----------------------------------------
@router.get("/")
def get_stores():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT
                        store_id,
                        store_name,
                        address,
                        latitude,
                        longitude,
                        phone
                    FROM public.stores
                    ORDER BY store_id
                """)
            )

            stores = [
                dict(row)
                for row in result.mappings().all()
            ]

        return stores

    except Exception as error:
        print("Get stores error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve stores"
        )


# -----------------------------------------
# Find nearby stores using user location
# -----------------------------------------
@router.get("/nearby")
def get_nearby_stores(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, gt=0)
):
    try:
        query = text("""
            SELECT
                store_id,
                store_name,
                address,
                latitude,
                longitude,
                phone
            FROM public.stores
            WHERE latitude IS NOT NULL
              AND longitude IS NOT NULL
        """)

        with engine.connect() as connection:
            result = connection.execute(query).mappings().all()

        nearby_stores = []

        for store in result:

            distance = calculate_distance(
                latitude,
                longitude,
                float(store["latitude"]),
                float(store["longitude"])
            )

            if distance <= radius_km:
                nearby_stores.append({
                    "store_id": store["store_id"],
                    "store_name": store["store_name"],
                    "address": store["address"],
                    "latitude": float(store["latitude"]),
                    "longitude": float(store["longitude"]),
                    "phone": store["phone"],
                    "distance_km": round(distance, 2)
                })

        nearby_stores.sort(
            key=lambda store: store["distance_km"]
        )

        return {
            "count": len(nearby_stores),
            "radius_km": radius_km,
            "stores": nearby_stores
        }

    except Exception as error:
        print("Nearby stores error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Unable to find nearby stores"
        )
