from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    batches,
    community,
    expiry,
    forecast,
    inventory,
    products,
    redistribution,
    sales,
    staff,
    stores,
)

app = FastAPI(
    title="ZeroWasteNet API",
    description="Smart Grocery Inventory Redistribution Platform",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stores.router)
app.include_router(products.router)
app.include_router(batches.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(expiry.router)
app.include_router(forecast.router)
app.include_router(redistribution.router)
app.include_router(community.router)
app.include_router(staff.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to ZeroWasteNet API", "version": "1.1.0"}
