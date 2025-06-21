"""
Server manager for handling multiple MCP server instances.
"""

class ServerManager:
    def __init__(self):
        self.servers = {}

    def add_server(self, name, server):
        self.servers[name] = server

    def get_server(self, name):
        return self.servers.get(name)

    def remove_server(self, name):
        if name in self.servers:
            del self.servers[name]

    def list_servers(self):
        return list(self.servers.keys())
