"""
Initialize the PostgreSQL database schema for customer support.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", 5432),
    user=os.getenv("DB_USER", "admin"),
    password=os.getenv("DB_PASSWORD", "password"),
    dbname=os.getenv("DB_NAME", "customer_support")
)

schema_sql = """
-- Place your schema SQL here or import from a file
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    name VARCHAR(255),
    tier VARCHAR(50) DEFAULT 'standard',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

with conn.cursor() as cur:
    cur.execute(schema_sql)
    conn.commit()

print("Database initialized.")
