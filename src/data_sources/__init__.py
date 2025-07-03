"""
Data Sources Package

This package provides abstraction layers for various data sources used in the 
Agentic AI Customer Support system.

Available Components:
- PDFProcessor: Document processing and search capabilities
- VectorDBClient: Semantic search using Qdrant vector database
- KafkaConsumer: Real-time event stream processing
- EnhancedRDBMSConnector: PostgreSQL database operations

Note: MCP-based data access is now handled by the src.mcp package.
"""

from .pdf_processor import PDFProcessor
from .vector_db_client import VectorDBClient
from .kafka_consumer import KafkaConsumer
from .rdbms_connector import EnhancedRDBMSConnector

__all__ = [
    'PDFProcessor',
    'VectorDBClient', 
    'KafkaConsumer',
    'EnhancedRDBMSConnector'
]
