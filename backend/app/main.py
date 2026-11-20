from fastapi import FastAPI

app = FastAPI(
    title="ZeroWasteNet API",
    description="Smart Grocery Inventory Redistribution System",
    version="1.0"
)

@app.get("/")
def home():
    return {
        "message": "Welcome to ZeroWasteNet",
        "status": "Backend running successfully"
    }