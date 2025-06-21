"""
Base agent interface for all customer support agents.
"""
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def process_input(self, input_data):
        pass

    @abstractmethod
    def set_chromosome(self, chromosome):
        pass
