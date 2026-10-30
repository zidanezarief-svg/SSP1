
from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
)
from schemas import MenuItemCreate, MenuItemUpdate
from database import connection

from storage import storage_bucket
from uuid import uuid4


router = APIRouter (
    prefix = "/products",
    tags = ["Products"]
)


@router.get("/")
def get_product():
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, price, patty_count, image_path
                    FROM menu_items
                    WHERE is_available = TRUE
                    ORDER BY id
                """)
                rows = cur.fetchall()

        return [
            {
                    "id": row[0],
                    "name": row[1],
                    "price": str(row[2]),
                    "patty_count": row[3],
                    "image_path": row[4],
                    "image_url": (
                        storage_bucket.get_public_url(row[4])
                        if row[4]
                        else None
                    )
            }
            for row in rows
]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve products"
        ) from e


@router.get("/manage")
def get_all_products():
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id,
                        name,
                        price,
                        patty_count,
                        category_id,
                        image_path,
                        is_available
                    FROM menu_items
                    ORDER BY id
                """)
                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "name": row[1],
                "price": str(row[2]),
                "patty_count": row[3],
                "category_id": row[4],
                "image_path": row[5],
                "is_available": row[6],
            }
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve products"
        ) from e


@router.post("/")
def create_product(product: MenuItemCreate):
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO menu_items (name, price, patty_count, category_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, name, price, patty_count, category_id
                    """,
                    (
                       product.name,
                       product.price,
                       product.patty_count,
                       product.category_id,
                    )
                )
                new_product = cur.fetchone()

        return {
            "id": new_product[0],
            "name": new_product[1],
            "price": str(new_product[2]),
            "patty_count": new_product[3],
            "category_id": new_product[4],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) from e

@router.patch("/{product_id}")
def update_product(product_id: int, product: MenuItemUpdate):
    updates = product.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="At least one field must be provided"
        )

    allowed_fields = {"name", "price", "patty_count"}

    if not set(updates).issubset(allowed_fields):
        raise HTTPException(
            status_code=400,
            detail="Invalid fields provided"
        )

    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE menu_items
                    SET
                        name = COALESCE(%s, name),
                        price = COALESCE(%s, price),
                        patty_count = COALESCE(%s, patty_count),
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, name, price, patty_count
                    """,
                    (
                        updates.get("name"),
                        updates.get("price"),
                        updates.get("patty_count"),
                        product_id,
                    )
                )

                updated_product = cur.fetchone()

                if updated_product is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Product not found"
                    )

        return {
            "message": "Product updated successfully",
            "product": {
                "id": updated_product[0],
                "name": updated_product[1],
                "price": str(updated_product[2]),
                "patty_count": updated_product[3],
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to update product"
        ) from e
    
@router.delete("/{product_id}")
def delete_product(product_id: int):
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE menu_items
                    SET is_available = FALSE,
                        updated_at = NOW()
                    WHERE id = %s
                      AND is_available = TRUE
                    RETURNING id, name
                    """,
                    (product_id,)
                )

                deleted_product = cur.fetchone()

                if deleted_product is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Product not found or already deleted"
                    )

        return {
            "message": "Product deleted successfully",
            "id": deleted_product[0],
            "name": deleted_product[1]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete product"
        ) from e


@router.patch("/{product_id}/enable")
def enable_product(product_id: int):
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE menu_items
                    SET is_available = TRUE
                    WHERE id = %s
                    RETURNING id, name, price, is_available
                    """,
                    (product_id,)
                )
                product = cur.fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return {
            "id": product[0],
            "name": product[1],
            "price": float(product[2]),
            "is_available": product[3]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to enable product"
        ) from e


@router.post("/{product_id}/image")
def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
):
    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, and WebP images are allowed",
        )

    try:
        # Read at most 5 MB + 1 byte to enforce the size limit.
        image_data = file.file.read(5 * 1024 * 1024 + 1)

        if not image_data:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty",
            )

        if len(image_data) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Image must be 5 MB or smaller",
            )

        # Confirm that the product exists.
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM menu_items WHERE id = %s",
                    (product_id,),
                )
                if cur.fetchone() is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Product not found",
                    )

        extension = allowed_types[file.content_type]
        image_path = f"products/{product_id}/{uuid4().hex}{extension}"

        # Upload to Supabase Storage.
        storage_bucket.upload(
            image_path,
            image_data,
            file_options={
                "content-type": file.content_type,
                "upsert": "false",
            },
        )

        # Save the image path in the existing database column.
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE menu_items
                    SET image_path = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (image_path, product_id),
                )

        image_url = storage_bucket.get_public_url(image_path)

        return {
            "message": "Product image uploaded successfully",
            "product_id": product_id,
            "image_path": image_path,
            "image_url": image_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to upload product image",
        ) from e
    finally:
        file.file.close()
