"""
MCP client for interacting with MCP servers.
"""

class MCPClient:
    def __init__(self, mcp_impl):
        self.mcp = mcp_impl

    def connect(self):
        self.mcp.connect()

    def send(self, data):
        self.mcp.send(data)

    def receive(self):
        return self.mcp.receive()

    def close(self):
        self.mcp.close()
