from fastapi import APIRouter, HTTPException
from schemas import MenuCategoryCreate, MenuCategoryUpdate
from database import connection

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


@router.get("/")
def get_categories():
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name
                    FROM menu_categories
                    ORDER BY name
                """)
                rows = cur.fetchall()

        return [
            {"id": row[0], "name": row[1]}
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve categories"
        ) from e


@router.post("/")
def create_category(category: MenuCategoryCreate):
    name = category.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Category name cannot be empty"
        )

    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO menu_categories (name)
                    VALUES (%s)
                    RETURNING id, name
                """, (name,))
                row = cur.fetchone()

        return {"id": row[0], "name": row[1]}

    except Exception as e:
        if getattr(e, "sqlstate", None) == "23505":
            raise HTTPException(
                status_code=409,
                detail="A category with this name already exists"
            ) from e

        raise HTTPException(
            status_code=500,
            detail="Failed to create category"
        ) from e


@router.patch("/{category_id}")
def update_category(
    category_id: int,
    category: MenuCategoryUpdate
):
    updates = category.model_dump(exclude_unset=True)

    if "name" not in updates:
        raise HTTPException(
            status_code=400,
            detail="Provide a category name to update"
        )

    name = updates["name"].strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Category name cannot be empty"
        )

    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE menu_categories
                    SET name = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, name
                """, (name, category_id))

                row = cur.fetchone()

                if row is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Category not found"
                    )

        return {"id": row[0], "name": row[1]}

    except HTTPException:
        raise
    except Exception as e:
        if getattr(e, "sqlstate", None) == "23505":
            raise HTTPException(
                status_code=409,
                detail="A category with this name already exists"
            ) from e

        raise HTTPException(
            status_code=500,
            detail="Failed to update category"
        ) from e


@router.delete("/{category_id}")
def delete_category(category_id: int):
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM menu_categories
                    WHERE id = %s
                    RETURNING id, name
                """, (category_id,))

                row = cur.fetchone()

                if row is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Category not found"
                    )

        return {
            "message": "Category deleted successfully",
            "id": row[0],
            "name": row[1]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete category"
        ) from e