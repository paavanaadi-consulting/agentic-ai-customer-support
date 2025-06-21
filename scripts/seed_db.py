"""
Seed the database with sample customer support data.
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

sample_customers = [
    ("cust_001", "alice@example.com", "Alice", "premium"),
    ("cust_002", "bob@example.com", "Bob", "standard"),
]

with conn.cursor() as cur:
    for customer_id, email, name, tier in sample_customers:
        cur.execute(
            """
            INSERT INTO customers (customer_id, email, name, tier)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (customer_id) DO NOTHING;
            """,
            (customer_id, email, name, tier)
        )
    conn.commit()

print("Database seeded with sample data.")
