import csv
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from app.database import engine

router = APIRouter(prefix="/forecast", tags=["AI Forecast"])
BACKEND_DIR = Path(__file__).resolve().parents[2]
FORECAST_FILE = BACKEND_DIR / "seven_day_forecast.csv"


@router.get("/")
def get_forecast(store_id: str | None = Query(default=None)):
    if not FORECAST_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Forecast file was not found. Run the backend 7-day forecast pipeline first.",
        )

    try:
        with FORECAST_FILE.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))

        if not rows:
            return {"rows": [], "is_stale": True, "generated_through": None, "source": "seven_day_forecast.csv"}

        with engine.connect() as connection:
            products = connection.execute(text("SELECT product_id, product_name, unit FROM public.products")).mappings().all()
            stores = connection.execute(text("SELECT store_id, store_name FROM public.stores")).mappings().all()
        product_map = {str(row["product_id"]): dict(row) for row in products}
        store_map = {str(row["store_id"]): dict(row) for row in stores}

        parsed = []
        dates = []
        for row in rows:
            forecast_date = date.fromisoformat(str(row["forecast_date"])[:10])
            dates.append(forecast_date)
            store_key = str(row.get("store_id", ""))
            product_key = str(row.get("product_id", ""))
            product = product_map.get(product_key, {})
            store = store_map.get(store_key, {})
            if store_id and store_key != store_id:
                continue
            parsed.append({
                "forecast_date": forecast_date.isoformat(),
                "store_id": store_key,
                "store_name": store.get("store_name", store_key),
                "product_id": product_key,
                "product_name": product.get("product_name", product_key),
                "unit": product.get("unit", "units"),
                "predicted_demand": float(row.get("predicted_demand", 0) or 0),
                "predicted_units": int(float(row.get("predicted_units", 0) or 0)),
            })

        latest_date = max(dates) if dates else None
        is_stale = latest_date is None or latest_date < date.today()
        return {
            "rows": parsed,
            "is_stale": is_stale,
            "generated_through": latest_date.isoformat() if latest_date else None,
            "source": "seven_day_forecast.csv",
            "generated_at": datetime.fromtimestamp(FORECAST_FILE.stat().st_mtime).isoformat(timespec="seconds"),
        }
    except HTTPException:
        raise
    except Exception as error:
        print("Forecast read error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to read the 7-day forecast")
