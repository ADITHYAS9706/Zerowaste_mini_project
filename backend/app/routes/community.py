from typing import Literal
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.database import engine

router = APIRouter(prefix="/community", tags=["Store Community"])


class OfferCreate(BaseModel):
    store_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    quantity_available: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    pickup_deadline: date | None = None
    notes: str | None = None


class RequestCreate(BaseModel):
    requesting_store_id: str = Field(min_length=1)
    quantity_requested: int = Field(gt=0)
    message: str | None = None


class RequestDecision(BaseModel):
    status: Literal["accepted", "rejected"]


@router.get("/offers")
def get_offers():
    try:
        with engine.connect() as connection:
            rows = connection.execute(text("""
                SELECT o.offer_id, o.store_id, st.store_name,
                       o.product_id, p.product_name, p.unit,
                       o.batch_id, o.quantity_available, o.unit_price,
                       o.expiry_date, o.pickup_deadline, o.notes, o.status, o.created_at,
                       COALESCE((SELECT COUNT(*) FROM public.community_requests r WHERE r.offer_id = o.offer_id), 0) AS request_count
                FROM public.community_offers o
                LEFT JOIN public.stores st ON st.store_id = o.store_id
                LEFT JOIN public.products p ON p.product_id = o.product_id
                ORDER BY o.created_at DESC
            """)).mappings().all()
        return [dict(row) for row in rows]
    except Exception as error:
        print("Community offers error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to retrieve offers. Apply manager_modules.sql first.")


@router.get("/requests")
def get_requests():
    try:
        with engine.connect() as connection:
            rows = connection.execute(text("""
                SELECT r.request_id, r.offer_id, r.requesting_store_id,
                       requester.store_name AS requesting_store_name,
                       requester.address AS requesting_store_address,
                       requester.phone AS requesting_store_phone,
                       r.quantity_requested, r.message, r.status, r.created_at,
                       o.store_id AS offering_store_id,
                       offering.store_name AS offering_store_name,
                       offering.address AS offering_store_address,
                       offering.phone AS offering_store_phone,
                       p.product_name, p.unit
                FROM public.community_requests r
                JOIN public.community_offers o ON o.offer_id = r.offer_id
                LEFT JOIN public.stores requester ON requester.store_id = r.requesting_store_id
                LEFT JOIN public.stores offering ON offering.store_id = o.store_id
                LEFT JOIN public.products p ON p.product_id = o.product_id
                ORDER BY r.created_at DESC
            """)).mappings().all()
        return [dict(row) for row in rows]
    except Exception as error:
        print("Community requests error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to retrieve requests. Apply manager_modules.sql first.")


@router.post("/offers", status_code=201)
def create_offer(offer: OfferCreate):
    try:
        with engine.begin() as connection:
            batch = connection.execute(text("""
                SELECT product_id, store_id, quantity_remaining, expiry_date
                FROM public.inventory_batches
                WHERE batch_id = :batch_id
                  AND expiry_date >= CURRENT_DATE
                FOR UPDATE
            """), {"batch_id": offer.batch_id}).mappings().first()
            if not batch:
                raise HTTPException(status_code=404, detail="Batch was not found")
            if str(batch["store_id"]) != offer.store_id or str(batch["product_id"]) != offer.product_id:
                raise HTTPException(status_code=400, detail="The selected batch does not belong to this store and product")
            already_offered = connection.execute(text("""
                SELECT COALESCE(SUM(quantity_available), 0)
                FROM public.community_offers
                WHERE batch_id = :batch_id AND status = 'open'
            """), {"batch_id": offer.batch_id}).scalar_one()
            unoffered_quantity = int(batch["quantity_remaining"] or 0) - int(already_offered or 0)
            if unoffered_quantity < offer.quantity_available:
                raise HTTPException(status_code=409, detail=f"Only {max(0, unoffered_quantity)} units are not already offered from this batch")
            result = connection.execute(text("""
                INSERT INTO public.community_offers
                    (store_id, product_id, batch_id, quantity_available, unit_price,
                     expiry_date, pickup_deadline, notes, status, created_at)
                VALUES
                    (:store_id, :product_id, :batch_id, :quantity_available, :unit_price,
                     :expiry_date, :pickup_deadline, :notes, 'open', NOW())
                RETURNING offer_id
            """), {
                **offer.model_dump(),
                "expiry_date": batch["expiry_date"],
            }).mappings().first()
        return {"message": "Community offer published", "offer_id": result["offer_id"]}
    except HTTPException:
        raise
    except Exception as error:
        print("Create community offer error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to publish offer. Apply manager_modules.sql first.")


@router.post("/offers/{offer_id}/requests", status_code=201)
def create_request(offer_id: int, request: RequestCreate):
    try:
        with engine.begin() as connection:
            offer = connection.execute(text("""
                SELECT store_id, quantity_available, status
                FROM public.community_offers WHERE offer_id = :offer_id FOR UPDATE
            """), {"offer_id": offer_id}).mappings().first()
            if not offer:
                raise HTTPException(status_code=404, detail="Offer was not found")
            if offer["status"] != "open" or int(offer["quantity_available"]) <= 0:
                raise HTTPException(status_code=409, detail="This offer is no longer available")
            if str(offer["store_id"]) == request.requesting_store_id:
                raise HTTPException(status_code=400, detail="A store cannot request its own offer")
            if request.quantity_requested > int(offer["quantity_available"]):
                raise HTTPException(status_code=409, detail="Requested quantity exceeds the available offer quantity")
            result = connection.execute(text("""
                INSERT INTO public.community_requests
                    (offer_id, requesting_store_id, quantity_requested, message, status, created_at)
                VALUES (:offer_id, :requesting_store_id, :quantity_requested, :message, 'pending', NOW())
                RETURNING request_id
            """), {"offer_id": offer_id, **request.model_dump()}).mappings().first()
        return {"message": "Purchase request submitted", "request_id": result["request_id"]}
    except HTTPException:
        raise
    except Exception as error:
        print("Create community request error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to submit request. Apply manager_modules.sql first.")


@router.patch("/requests/{request_id}")
def decide_request(request_id: int, decision: RequestDecision):
    try:
        with engine.begin() as connection:
            request = connection.execute(text("""
                SELECT r.offer_id, r.requesting_store_id, r.quantity_requested, r.status,
                       o.quantity_available, o.status AS offer_status,
                       o.batch_id, o.product_id, o.store_id AS offering_store_id
                FROM public.community_requests r
                JOIN public.community_offers o ON o.offer_id = r.offer_id
                WHERE r.request_id = :request_id
                FOR UPDATE OF r, o
            """), {"request_id": request_id}).mappings().first()
            if not request:
                raise HTTPException(status_code=404, detail="Request was not found")
            if request["status"] != "pending":
                raise HTTPException(status_code=409, detail="This request has already been reviewed")
            if decision.status == "accepted":
                requested_quantity = int(request["quantity_requested"])
                if request["offer_status"] != "open" or int(request["quantity_available"]) < requested_quantity:
                    raise HTTPException(status_code=409, detail="Not enough offer quantity remains to accept this request")

                source_batch = connection.execute(text("""
                    SELECT batch_id, batch_code, store_id, product_id, quantity_remaining,
                           manufacturing_date, expiry_date
                    FROM public.inventory_batches
                    WHERE batch_id = :batch_id
                    FOR UPDATE
                """), {"batch_id": request["batch_id"]}).mappings().first()
                if not source_batch or int(source_batch["quantity_remaining"] or 0) < requested_quantity:
                    raise HTTPException(status_code=409, detail="The source batch no longer has enough stock")
                if source_batch["expiry_date"] < date.today():
                    raise HTTPException(status_code=409, detail="Expired stock cannot be transferred to another store")

                connection.execute(text("""
                    UPDATE public.inventory_batches
                    SET quantity_remaining = quantity_remaining - :quantity
                    WHERE batch_id = :batch_id
                """), {"quantity": requested_quantity, "batch_id": request["batch_id"]})

                next_batch_number = connection.execute(
                    text("SELECT nextval('public.batch_id_seq')")
                ).scalar_one()
                transferred_batch_id = f"B{int(next_batch_number):05d}"
                connection.execute(text("""
                    INSERT INTO public.inventory_batches
                        (batch_id, store_id, product_id, batch_code, quantity_received,
                         quantity_remaining, manufacturing_date, expiry_date)
                    VALUES
                        (:batch_id, :store_id, :product_id, :batch_code, :quantity_received,
                         :quantity_remaining, :manufacturing_date, :expiry_date)
                """), {
                    "batch_id": transferred_batch_id,
                    "store_id": request["requesting_store_id"],
                    "product_id": request["product_id"],
                    "batch_code": f"COMM-{request_id}",
                    "quantity_received": requested_quantity,
                    "quantity_remaining": requested_quantity,
                    "manufacturing_date": source_batch["manufacturing_date"],
                    "expiry_date": source_batch["expiry_date"],
                })

                new_quantity = int(request["quantity_available"]) - requested_quantity
                connection.execute(text("""
                    UPDATE public.community_offers
                    SET quantity_available = :quantity,
                        status = CASE WHEN :quantity = 0 THEN 'closed' ELSE 'open' END
                    WHERE offer_id = :offer_id
                """), {"quantity": new_quantity, "offer_id": request["offer_id"]})
            connection.execute(text("""
                UPDATE public.community_requests SET status = :status WHERE request_id = :request_id
            """), {"status": decision.status, "request_id": request_id})
        return {"message": f"Request {decision.status}", "request_id": request_id, "status": decision.status}
    except HTTPException:
        raise
    except Exception as error:
        print("Community decision error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to update request")
