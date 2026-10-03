import os
import psycopg
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
