
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database import engine
from app.schemas.product import ProductCreate

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/")
def create_product(product: ProductCreate):
    try:
        with engine.begin() as connection:

            # Generate a unique product ID
            next_id = connection.execute(
                text("SELECT nextval('public.product_id_seq')")
            ).scalar_one()

            product_id = f"P{next_id:03d}"

            # Insert product into Supabase
            connection.execute(
                text("""
                    INSERT INTO public.products
                    (
                        product_id,
                        product_name,
                        category,
                        unit,
                        base_daily_demand,
                        unit_price
                    )
                    VALUES
                    (
                        :product_id,
                        :product_name,
                        :category,
                        :unit,
                        :base_daily_demand,
                        :unit_price
                    )
                """),
                {
                    "product_id": product_id,
                    "product_name": product.product_name,
                    "category": product.category,
                    "unit": product.unit,
                    "base_daily_demand": product.base_daily_demand,
                    "unit_price": product.unit_price
                }
            )

        return {
            "message": "Product registered successfully",
            "product_id": product_id,
            "product_name": product.product_name
        }

    except Exception as error:
        print("Product registration error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Unable to register product"
        )


@router.get("/")
def get_products():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT
                        product_id,
                        product_name,
                        category,
                        unit,
                        base_daily_demand,
                        unit_price
                    FROM public.products
                    ORDER BY product_id
                """)
            )

            products = [
                dict(row)
                for row in result.mappings().all()
            ]

        return products

    except Exception as error:
        print("Get products error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve products"
        )
