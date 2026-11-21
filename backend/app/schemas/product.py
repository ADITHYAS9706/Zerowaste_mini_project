
from pydantic import BaseModel, Field
from typing import Optional


class ProductCreate(BaseModel):
    product_name: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    unit: str = Field(..., min_length=1)
    base_daily_demand: Optional[int] = Field(default=None, ge=0)
    unit_price: Optional[float] = Field(default=0, ge=0)


class ProductResponse(BaseModel):
    product_id: str
    product_name: str
    category: str
    unit: str
    base_daily_demand: Optional[int] = None
    unit_price: Optional[float] = 0
