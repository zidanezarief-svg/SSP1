
from psycopg.rows import dict_row

from database import connection


# 1. View all ingredients in the inventory
def get_inventory():
    with connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, ingredient_name, stock_quantity, unit, updated_at
                FROM public.inventory
                ORDER BY ingredient_name
            """)

            return cur.fetchall()


# 2. View one ingredient using its ID
def get_ingredient(ingredient_id: int):
    with connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, ingredient_name, stock_quantity, unit, updated_at
                FROM public.inventory
                WHERE id = %s
            """, (ingredient_id,))

            return cur.fetchone()


# 3. Add stock when new ingredients arrive
def add_stock(ingredient_id: int, quantity: int):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    with connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                UPDATE public.inventory
                SET stock_quantity = stock_quantity + %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, ingredient_name, stock_quantity, unit, updated_at
            """, (quantity, ingredient_id))

            return cur.fetchone()


# 4. Correct stock after a physical stock count
def set_stock_quantity(ingredient_id: int, quantity: int):
    if quantity < 0:
        raise ValueError("Stock quantity cannot be negative")

    with connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                UPDATE public.inventory
                SET stock_quantity = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, ingredient_name, stock_quantity, unit, updated_at
            """, (quantity, ingredient_id))

            return cur.fetchone()
