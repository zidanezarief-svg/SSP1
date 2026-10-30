from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from schemas import OrderRequest
from database import connection

router = APIRouter (
    prefix = "/orders",
    tags = ["Orders"]
)

class OrderStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(pending|preparing|completed|cancelled)$"
    )



@router.get("/")
def get_orders():
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
    o.id,
    o.total_price,
    o.status,
    o.created_at,
    o.customer_name,
                        oi.menu_item_id,
                        m.name,
                        oi.quantity,
                        oi.unit_price
                    FROM orders AS o
                    LEFT JOIN order_items AS oi
                        ON o.id = oi.order_id
                    LEFT JOIN menu_items AS m
                        ON oi.menu_item_id = m.id
                    ORDER BY o.created_at DESC, o.id DESC
                    """
                )

                rows = cur.fetchall()

                orders = {}

                for row in rows:
                    order_id = row[0]

                    if order_id not in orders:
                        orders[order_id] = {
                            "order_id": order_id,
                            "total_price": str(row[1]),
                            "status": row[2],
                            "created_at": row[3].isoformat(),
                            "customer_name": row[4] or "Walk-in Customer",
                            "items": [],
                        }

                    if row[4] is not None:
                        orders[order_id]["items"].append({
                            "menu_item_id": row[5],
                            "name": row[6],
                            "quantity": row[7],
                            "unit_price": str(row[8]),
                        })

                return list(orders.values())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve orders",
        ) from e

@router.get("/{order_id}")
def get_order(order_id: int):
    return {"message": "View one order"}



@router.post("/")
def create_orders(order: OrderRequest):
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                total_price = 0
                order_items = []

                # 1. Validate every burger and calculate the total
                for item in order.items:
                    cur.execute(
                        """
                        SELECT id, name, price, patty_count, is_available
                        FROM menu_items
                        WHERE id = %s
                        """,
                        (item.menu_item_id,),
                    )
                    product = cur.fetchone()

                    if product is None:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Burger ID {item.menu_item_id} not found",
                        )

                    if not product[4]:
                        raise HTTPException(
                            status_code=400,
                            detail=f"{product[1]} is unavailable",
                        )

                    patties_required = product[3] * item.quantity
                    total_price += product[2] * item.quantity

                    order_items.append({
                        "product": product,
                        "quantity": item.quantity,
                        "patties_required": patties_required,
                    })

                # 2. Lock the patty inventory row
                cur.execute(
                    """
                    SELECT stock_quantity
                    FROM inventory
                    WHERE ingredient_name = %s
                    FOR UPDATE
                    """,
                    ("Patty",),
                )
                inventory_row = cur.fetchone()

                if inventory_row is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Patty inventory not found",
                    )

                total_patties = sum(
                    item["patties_required"] for item in order_items
                )

                if total_patties > inventory_row[0]:
                    raise HTTPException(
                        status_code=400,
                        detail="Not enough patties in stock",
                    )

                # 3. Create one order for the whole cart
                cur.execute(
    """
    INSERT INTO orders (total_price, status, customer_name)
    VALUES (%s, %s, %s)
    RETURNING id
    """,
    (
        total_price,
        "pending",
        order.customer_name.strip() or "Walk-in Customer",
    ),
)
                order_id = cur.fetchone()[0]

                # 4. Save each burger under the same order ID
                for item in order_items:
                    product = item["product"]

                    cur.execute(
                        """
                        INSERT INTO order_items (
                            order_id,
                            menu_item_id,
                            quantity,
                            unit_price
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            order_id,
                            product[0],
                            item["quantity"],
                            product[2],
                        ),
                    )

                # 5. Deduct the total patty quantity
                cur.execute(
                    """
                    UPDATE inventory
                    SET stock_quantity = stock_quantity - %s
                    WHERE ingredient_name = %s
                    AND stock_quantity >= %s
                    """,
                    (total_patties, "Patty", total_patties),
                )

                if cur.rowcount == 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Not enough patties in stock",
                    )
                
                # 6. Record the stock movement
                cur.execute(
                    """
                    INSERT INTO inventory_movements (
                        ingredient_name,
                        movement_type,
                        quantity_change,
                        stock_after,
                        notes
                    )
                    SELECT
                        ingredient_name,
                        %s,
                        %s,
                        stock_quantity,
                        %s
                    FROM inventory
                    WHERE ingredient_name = %s
                    """,
                    (
                        "sold",
                        -total_patties,
                        f"Order #{order_id}",
                        "Patty",
                    ),
                )


                return {
                    "message": "Order placed successfully",
                    "order_id": order_id,
                    "total_price": str(total_price),
                    "total_patties": total_patties,
                    "items": [
                        {
                            "menu_item_id": item["product"][0],
                            "name": item["product"][1],
                            "quantity": item["quantity"],
                        }
                        for item in order_items
                    ],
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to process order",
        ) from e



@router.patch("/{id}")
def update_orders(id: int, update: OrderStatusUpdate):
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE orders
                    SET status = %s
                    WHERE id = %s
                    RETURNING id, status
                    """,
                    (update.status, id),
                )

                updated_order = cur.fetchone()

                if updated_order is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Order not found",
                    )

                return {
                    "message": "Order status updated",
                    "id": updated_order[0],
                    "status": updated_order[1],
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to update order status",
        ) from e

@router.delete("/{order_id}")
def delete_orders(order_id: int):
    return{
        "message": "Order deleted successfully",
        "order_id": order_id
    }