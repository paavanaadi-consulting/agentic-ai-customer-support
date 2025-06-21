import pytest
from mcp_servers.postgres_mcp import PostgresMCP

class DummyConn:
    def __init__(self):
        self.connected = False
        self.closed = False
        self.last_query = None
    def cursor(self):
        class DummyCursor:
            def __enter__(self_): return self_
            def __exit__(self_, exc_type, exc_val, exc_tb): pass
            def execute(self_, data): self.last_query = data
            def fetchone(self_): return ("row",)
        return DummyCursor()
    def close(self): self.closed = True

def test_postgres_mcp_connect_and_send(monkeypatch):
    mcp = PostgresMCP({"host": "localhost"})
    mcp.conn = DummyConn()
    mcp.send("SELECT 1;")
    assert mcp.conn.last_query == "SELECT 1;"
    assert not mcp.conn.closed
    mcp.close()
    assert mcp.conn.closed
