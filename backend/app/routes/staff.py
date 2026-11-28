import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from supabase import create_client

from app.database import engine

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

router = APIRouter(prefix="/staff", tags=["Staff Management"])


class StaffCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    store_id: str = Field(min_length=1)


class StaffStatusUpdate(BaseModel):
    is_active: bool


def get_admin_client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=503, detail="Supabase admin configuration is not available")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@router.get("/")
def get_staff():
    try:
        with engine.connect() as connection:
            rows = connection.execute(text("""
                SELECT user_id, full_name, role, store_id, is_active
                FROM public.profiles
                WHERE role = 'staff'
                ORDER BY full_name
            """)).mappings().all()
        return [dict(row) for row in rows]
    except Exception as error:
        print("Get staff error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to retrieve staff profiles")


@router.post("/", status_code=201)
def create_staff(staff: StaffCreate):
    supabase = get_admin_client()
    auth_user_id = None
    try:
        with engine.connect() as connection:
            exists = connection.execute(text("SELECT 1 FROM public.stores WHERE store_id = :store_id"), {"store_id": staff.store_id}).first()
        if not exists:
            raise HTTPException(status_code=404, detail="Selected store was not found")

        auth_result = supabase.auth.admin.create_user({
            "email": staff.email.strip().lower(),
            "password": staff.password,
            "email_confirm": True,
            "user_metadata": {"full_name": staff.full_name.strip()},
        })
        if not auth_result.user:
            raise RuntimeError("Supabase did not return a user")
        auth_user_id = str(auth_result.user.id)

        with engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO public.profiles (user_id, full_name, role, store_id, is_active)
                VALUES (:user_id, :full_name, 'staff', :store_id, TRUE)
            """), {
                "user_id": auth_user_id,
                "full_name": staff.full_name.strip(),
                "store_id": staff.store_id,
            })
        return {"message": "Staff account created", "user_id": auth_user_id, "store_id": staff.store_id}
    except HTTPException:
        raise
    except Exception as error:
        print("Create staff error:", repr(error))
        if auth_user_id:
            try:
                supabase.auth.admin.delete_user(auth_user_id)
            except Exception as cleanup_error:
                print("Staff Auth cleanup error:", repr(cleanup_error))
        raise HTTPException(status_code=400, detail="Unable to create staff account. Check the backend terminal for details.")


@router.patch("/{user_id}")
def update_staff_status(user_id: str, update: StaffStatusUpdate):
    try:
        with engine.begin() as connection:
            result = connection.execute(text("""
                UPDATE public.profiles SET is_active = :is_active
                WHERE user_id = :user_id AND role = 'staff'
            """), {"user_id": user_id, "is_active": update.is_active})
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Staff profile was not found")
        return {"message": "Staff status updated", "user_id": user_id, "is_active": update.is_active}
    except HTTPException:
        raise
    except Exception as error:
        print("Update staff status error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to update staff status")
