from app.routes import inventory
from app.routes import batches
from fastapi import FastAPI
from app.routes import stores, products

app = FastAPI(
    title="ZeroWasteNet API",
    description="Smart Grocery Inventory Redistribution Platform",
    version="1.0.0"
)

# Register Store routes
app.include_router(stores.router)

# Register Product routes
app.include_router(products.router)
app.include_router(batches.router)
app.include_router(inventory.router)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to ZeroWasteNet API"
    }
