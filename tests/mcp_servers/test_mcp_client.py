import pytest
from mcp_servers.mcp_client import MCPClient

class DummyMCP:
    def __init__(self):
        self.connected = False
        self.sent = None
        self.closed = False
    def connect(self):
        self.connected = True
    def send(self, data):
        self.sent = data
    def receive(self):
        return "dummy data"
    def close(self):
        self.closed = True

def test_mcp_client_basic():
    mcp = DummyMCP()
    client = MCPClient(mcp)
    client.connect()
    assert mcp.connected
    client.send("hello")
    assert mcp.sent == "hello"
    assert client.receive() == "dummy data"
    client.close()
    assert mcp.closed
