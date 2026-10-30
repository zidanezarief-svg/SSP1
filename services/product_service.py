from psycopg.rows import dict_row
from decimal import Decimal
from database import connection

def get_menu_items():
    with connection() as conn :
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, name, price, is_available
                FROM public.get_menu_items
                ORDER BY id
         """ )

            return cur.fetchall()

def get_menu_item(menu_item_id: int):
    with connection() as conn :
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                     SELECT id, name, price, is_available
                     FROM public_menu_items
                     WHERE id = %s
                     """,
                     (menu_item_id,)
                )

                return cur.fetchone()

def create_menu_item(name: str, price: Decimal):
    with connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO public.menu_items (name, price)
                VALUES (%s, %s)
                RETURNING id, name, price, is_available
                """,
                (name, price)
            )

            return cur.fetchone()
