
from datetime import date

from psycopg.rows import dict_row

from database import connection


def get_monthly_sales(year: int, month: int):
    with connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(total_price), 0) AS total_sales,
                    COUNT(*) AS total_orders
                FROM public.orders
                WHERE status = 'completed'
                  AND created_at >= make_date(%s, %s, 1)
                  AND created_at < (
                      make_date(%s, %s, 1) + INTERVAL '1 month'
                  )
                """,
                (year, month, year, month)
            )
            return cur.fetchone()


def get_daily_sales(sales_date: date):
    with connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(total_price), 0) AS total_sales,
                    COUNT(*) AS total_orders
                FROM public.orders
                WHERE status = 'completed'
                  AND created_at >= %s
                  AND created_at < %s + INTERVAL '1 day'
                """,
                (sales_date, sales_date)
            )
            return cur.fetchone()


def get_best_sellers(year: int, month: int):
    with connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    m.id AS menu_item_id,
                    m.name AS menu_item_name,
                    SUM(oi.quantity) AS quantity_sold,
                    SUM(oi.quantity * oi.unit_price) AS sales_revenue
                FROM public.order_items AS oi
                JOIN public.orders AS o
                    ON o.id = oi.order_id
                JOIN public.menu_items AS m
                    ON m.id = oi.menu_item_id
                WHERE o.status = 'completed'
                  AND o.created_at >= make_date(%s, %s, 1)
                  AND o.created_at < (
                      make_date(%s, %s, 1) + INTERVAL '1 month'
                  )
                GROUP BY m.id, m.name
                ORDER BY quantity_sold DESC
                """,
                (year, month, year, month)
            )
            return cur.fetchall()
