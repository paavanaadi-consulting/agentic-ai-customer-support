"""
Data Sources Test Suite

This module contains comprehensive tests for all data source components
in the Agentic AI Customer Support system.

Test Coverage:
- PDFProcessor: Document processing and search functionality
- VectorDBClient: Semantic search with Qdrant vector database
- KafkaConsumer: Real-time event stream processing  
- EnhancedRDBMSConnector: PostgreSQL database operations

Test Categories:
- Unit Tests: Individual component functionality
- Integration Tests: Component interaction with mocked dependencies
- Performance Tests: Throughput and response time validation
"""

import sys
import os

# Add the project root to the Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

__all__ = [
    'test_pdf_processor',
    'test_vector_db_client', 
    'test_kafka_consumer',
    'test_rdbms_connector'
]
