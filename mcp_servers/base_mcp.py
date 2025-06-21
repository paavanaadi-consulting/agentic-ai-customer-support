"""
Base MCP interface for all MCP integrations.
"""
from abc import ABC, abstractmethod

class BaseMCP(ABC):
    """Abstract base class for MCP integrations."""

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def send(self, data):
        pass

    @abstractmethod
    def receive(self):
        pass

    @abstractmethod
    def close(self):
        pass
