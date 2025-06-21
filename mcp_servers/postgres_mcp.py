"""
Postgres MCP integration.
"""
from .base_mcp import BaseMCP
import psycopg2

class PostgresMCP(BaseMCP):
    def __init__(self, config):
        self.config = config
        self.conn = None

    def connect(self):
        self.conn = psycopg2.connect(**self.config)

    def send(self, data):
        with self.conn.cursor() as cur:
            cur.execute(data)
            self.conn.commit()

    def receive(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM mcp_queue LIMIT 1;")
            return cur.fetchone()

    def close(self):
        if self.conn:
            self.conn.close()
