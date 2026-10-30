import psycopg
from config import settings

def connection():
    return psycopg.connect(settings.supabase_db_url)
