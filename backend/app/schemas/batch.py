
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class BatchCreate(BaseModel):
    store_id: Optional[str] = None
    product_id: Optional[str] = None
    batch_code: str = Field(..., min_length=1)
    quantity_received: int = Field(..., gt=0)
    quantity_remaining: int = Field(..., ge=0)
    manufacturing_date: Optional[date] = None
    expiry_date: date


class BatchResponse(BaseModel):
    batch_id: str
    store_id: Optional[str] = None
    product_id: Optional[str] = None
    batch_code: str
    quantity_received: int
    quantity_remaining: int
    manufacturing_date: Optional[date] = None
    expiry_date: date
