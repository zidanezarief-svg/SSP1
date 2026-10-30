
from fastapi import APIRouter, HTTPException
from database import connection

router = APIRouter (
    prefix = "/inventory",
    tags = ["Inventory"]
)


@router.get("/")
def get_inventory():
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, ingredient_name, stock_quantity, unit
                    FROM inventory
                    ORDER BY ingredient_name
                """)
                rows = cur.fetchall()

        return [
    {
        "id": row[0],
        "ingredient_name": row[1],
        "stock_quantity": row[2],
        "unit": row[3]
    }
    for row in rows
    ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve inventory"
        ) from e


@router.get("/{inventory_id}")
def get_inventory_item(inventory_id: int):
    return {"message": "View one inventory item"}

@router.post("/")
def create_inventory():
    return{"message": "Add a new inventory item"}

from pydantic import BaseModel, Field

class StockUpdate(BaseModel):
    stock_quantity: int = Field(ge=0)

class IncomingStock(BaseModel):
    quantity: int = Field(gt=0)



@router.patch("/{inventory_id}")
def update_inventory(inventory_id: int, stock: StockUpdate):
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                # 1. Get the current stock
                cur.execute(
                    """
                    SELECT id, ingredient_name, stock_quantity, unit
                    FROM inventory
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (inventory_id,)
                )

                old_row = cur.fetchone()

                if old_row is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Inventory item not found"
                    )

                old_quantity = old_row[2]
                new_quantity = stock.stock_quantity
                quantity_change = new_quantity - old_quantity

                # 2. Update the stock quantity
                cur.execute(
                    """
                    UPDATE inventory
                    SET stock_quantity = %s
                    WHERE id = %s
                    RETURNING id, ingredient_name, stock_quantity, unit
                    """,
                    (new_quantity, inventory_id)
                )

                row = cur.fetchone()

                # 3. Record the adjustment only if stock changed
                if quantity_change != 0:
                    cur.execute(
                        """
                        INSERT INTO inventory_movements (
                            ingredient_name,
                            movement_type,
                            quantity_change,
                            stock_after,
                            notes
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            row[1],
                            "adjustment",
                            quantity_change,
                            row[2],
                            "Manual stock adjustment"
                        )
                    )

        return {
            "message": "Stock updated successfully",
            "id": row[0],
            "ingredient_name": row[1],
            "stock_quantity": row[2],
            "unit": row[3],
            "quantity_change": quantity_change
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to update inventory"
        ) from e


@router.delete("/{inventory_id}")
def delete_inventory(inventory_id: int):
    return{
        "message": "Inventory item deleted successfully",
        "inventory_id": inventory_id
    }


@router.get("/movements/history")
def get_inventory_movements():
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        ingredient_name,
                        movement_type,
                        quantity_change,
                        stock_after,
                        notes,
                        created_at
                    FROM inventory_movements
                    ORDER BY created_at DESC, id DESC
                    LIMIT 100
                    """
                )

                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "ingredient_name": row[1],
                "movement_type": row[2],
                "quantity_change": row[3],
                "stock_after": row[4],
                "notes": row[5],
                "created_at": row[6].isoformat()
                    if row[6] else None
            }
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve inventory movements"
        ) from e
