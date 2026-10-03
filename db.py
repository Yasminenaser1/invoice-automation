import os
import psycopg
from psycopg.types.json import Jsonb
from dotenv import load_dotenv

load_dotenv()

# Connection details (not secret). Only the password comes from the environment.
DB_SETTINGS = {
    "host": "aws-0-us-east-1.pooler.supabase.com",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres.ewdlgtzekezffijlygju",
}

def get_connection():
    """Open a connection to the Supabase database."""
    password = os.environ.get("DB_PASSWORD")
    if not password:
        raise RuntimeError("DB_PASSWORD is not set. Add it to .env locally, or to secrets in the cloud.")
    return psycopg.connect(**DB_SETTINGS, password=password, sslmode="require")

def invoice_exists(conn, test_set, invoice_id):
    """True if this invoice is already saved in the database."""
    row = conn.execute(
        "select 1 from invoices where test_set = %s and invoice_id = %s",
        (test_set, invoice_id),
    ).fetchone()
    return row is not None

def save_invoice(conn, test_set, invoice_id, source_file, status, extracted, issues):
    """Insert a processed invoice. Returns True if saved, False if it already existed."""
    final_data = Jsonb(extracted) if status == "auto_approved" else None
    cursor = conn.execute(
        """
        insert into invoices (test_set, invoice_id, source_file, status, extracted, issues, final_data)
        values (%s, %s, %s, %s, %s, %s, %s)
        on conflict (test_set, invoice_id) do nothing
        """,
        (test_set, invoice_id, source_file, status, Jsonb(extracted), Jsonb(issues), final_data),
    )
    return cursor.rowcount == 1
