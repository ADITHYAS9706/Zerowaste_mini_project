from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import inventory, batches, stores, products

app = FastAPI(
    title="ZeroWasteNet API",
    description="Smart Grocery Inventory Redistribution Platform",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allow the React development server to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(stores.router)
app.include_router(products.router)
app.include_router(batches.router)
app.include_router(inventory.router)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to ZeroWasteNet API"
    }
