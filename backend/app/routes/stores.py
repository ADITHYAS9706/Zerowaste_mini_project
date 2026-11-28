
import math
import os

from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from supabase import create_client


# -----------------------------------------
# Load backend environment variables
# -----------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("========== SUPABASE CONFIGURATION ==========")
print("Environment file:", ENV_FILE)
print("Environment file exists:", ENV_FILE.exists())
print("Supabase URL loaded:", bool(SUPABASE_URL))
print("Service role key loaded:", bool(SUPABASE_SERVICE_ROLE_KEY))
print("============================================")


# Import database engine after loading environment variables
from app.database import engine


router = APIRouter(prefix="/stores", tags=["Stores"])


# -----------------------------------------
# Registration request schema
# -----------------------------------------

class StoreRegistration(BaseModel):
    store_name: str = Field(min_length=2, max_length=150)
    full_name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    address: str = Field(min_length=3, max_length=500)
    phone: str = Field(min_length=7, max_length=20)

    @field_validator("store_name", "full_name", "email", "address", "phone")
    @classmethod
    def strip_values(cls, value):
        return value.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Enter a valid email address")

        return value.lower()


# -----------------------------------------
# Calculate distance using Haversine formula
# -----------------------------------------

def calculate_distance(lat1, lon1, lat2, lon2):

    earth_radius = 6371

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
# Register store and manager
# -----------------------------------------

@router.post("/register", status_code=201)
def register_store(registration: StoreRegistration):

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=500,
            detail="Supabase backend configuration is missing"
        )

    supabase = create_client(
        SUPABASE_URL,
        SUPABASE_SERVICE_ROLE_KEY
    )

    auth_user_id = None

    try:

        # 1. Create manager authentication account
        auth_response = supabase.auth.admin.create_user({
            "email": registration.email,
            "password": registration.password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": registration.full_name
            }
        })

        if not auth_response.user:
            raise Exception("Supabase did not return a user")

        auth_user_id = str(auth_response.user.id)

        # 2. Create store and manager profile
        with engine.begin() as connection:

            # Generate store ID
            next_id = connection.execute(
                text("SELECT nextval('public.store_id_seq')")
            ).scalar_one()

            store_id = f"S{next_id:03d}"

            # Insert store record
            connection.execute(
                text("""
                    INSERT INTO public.stores (
                        store_id,
                        store_name,
                        address,
                        phone,
                        latitude,
                        longitude,
                        registration_status,
                        registration_source,
                        rejection_reason,
                        registration_submitted_at
                    )
                    VALUES (
                        :store_id,
                        :store_name,
                        :address,
                        :phone,
                        NULL,
                        NULL,
                        'approved',
                        'website',
                        NULL,
                        NOW()
                    )
                """),
                {
                    "store_id": store_id,
                    "store_name": registration.store_name,
                    "address": registration.address,
                    "phone": registration.phone
                }
            )

            # Insert manager profile
            connection.execute(
                text("""
                    INSERT INTO public.profiles (
                        user_id,
                        full_name,
                        role,
                        store_id,
                        is_active
                    )
                    VALUES (
                        :user_id,
                        :full_name,
                        'manager',
                        :store_id,
                        TRUE
                    )
                """),
                {
                    "user_id": auth_user_id,
                    "full_name": registration.full_name,
                    "store_id": store_id
                }
            )

        return {
            "message": "Store registered successfully",
            "store_id": store_id,
            "store_name": registration.store_name,
            "manager_name": registration.full_name,
            "role": "manager"
        }

    except Exception as error:

        print("========== STORE REGISTRATION ERROR ==========")
        print(repr(error))
        print("===============================================")

        # If database creation fails, remove the Auth account
        # so an unlinked account is not left behind.
        if auth_user_id:

            try:
                supabase.auth.admin.delete_user(auth_user_id)

            except Exception as cleanup_error:
                print("AUTH CLEANUP ERROR:", repr(cleanup_error))

        raise HTTPException(
            status_code=400,
            detail="Registration failed. Check the backend terminal for the actual error."
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
# Find nearby stores
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
