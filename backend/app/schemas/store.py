
from pydantic import BaseModel, Field
from typing import Optional


class StoreCreate(BaseModel):
    store_name: str = Field(..., min_length=2)
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
