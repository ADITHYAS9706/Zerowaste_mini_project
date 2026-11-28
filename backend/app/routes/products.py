
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


@router.put("/{product_id}")
def update_product(product_id: str, product: ProductCreate):
    try:
        with engine.begin() as connection:
            result = connection.execute(text("""
                UPDATE public.products
                SET product_name = :product_name,
                    category = :category,
                    unit = :unit,
                    base_daily_demand = :base_daily_demand,
                    unit_price = :unit_price
                WHERE product_id = :product_id
            """), {**product.model_dump(), "product_id": product_id})
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product was not found")
        return {"message": "Product updated successfully", "product_id": product_id}
    except HTTPException:
        raise
    except Exception as error:
        print("Product update error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to update product")


@router.delete("/{product_id}")
def delete_product(product_id: str):
    try:
        with engine.begin() as connection:
            product = connection.execute(
                text("SELECT product_id FROM public.products WHERE product_id = :product_id"),
                {"product_id": product_id},
            ).first()
            if not product:
                raise HTTPException(status_code=404, detail="Product was not found")
            batch_count = connection.execute(
                text("SELECT COUNT(*) FROM public.inventory_batches WHERE product_id = :product_id"),
                {"product_id": product_id},
            ).scalar_one()
            sales_count = connection.execute(
                text("SELECT COUNT(*) FROM public.sales WHERE product_id = :product_id"),
                {"product_id": product_id},
            ).scalar_one()
            if batch_count or sales_count:
                raise HTTPException(
                    status_code=409,
                    detail="This product has batch or sales history and cannot be deleted. Keep it for audit history.",
                )
            connection.execute(
                text("DELETE FROM public.products WHERE product_id = :product_id"),
                {"product_id": product_id},
            )
        return {"message": "Product deleted successfully", "product_id": product_id}
    except HTTPException:
        raise
    except Exception as error:
        print("Product deletion error:", repr(error))
        raise HTTPException(status_code=500, detail="Unable to delete product")
