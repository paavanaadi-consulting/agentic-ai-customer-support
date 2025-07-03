"""
Comprehensive test suite for QueryService.
Tests all query processing logic and AI agent interactions.
"""
import pytest
import uuid
import time
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List

from src.services.query_service import QueryService
from src.api.schemas import QueryRequest, QueryResponse, QueryType, Priority


class TestQueryService:
    """Test cases for QueryService class."""

    @pytest.fixture
    def query_service(self):
        """Create a QueryService instance."""
        return QueryService()

    @pytest.fixture
    def sample_query_request(self):
        """Create a sample query request."""
        return QueryRequest(
            query="I can't log into my account",
            customer_id="customer_123",
            query_type=QueryType.TECHNICAL,
            priority=Priority.HIGH,
            context={"previous_attempts": 3, "error_code": "AUTH_FAILED"},
            metadata={"source": "web", "user_agent": "Chrome"}
        )

    @pytest.fixture
    def sample_billing_request(self):
        """Create a sample billing query request."""
        return QueryRequest(
            query="Why was I charged twice?",
            customer_id="customer_456",
            query_type=QueryType.BILLING,
            priority=Priority.MEDIUM
        )


class TestQueryProcessing:
    """Test query processing functionality."""

    @pytest.mark.asyncio
    async def test_process_query_technical_success(self, query_service, sample_query_request):
        """Test successful processing of technical query."""
        result = await query_service.process_query(sample_query_request)

        assert isinstance(result, QueryResponse)
        assert result.success is True
        assert result.agent_used == "technical_agent"
        assert result.confidence > 0.0
        assert result.processing_time > 0.0
        assert "Technical support response" in result.result
        assert result.query_id is not None
        assert isinstance(result.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_process_query_billing_success(self, query_service, sample_billing_request):
        """Test successful processing of billing query."""
        result = await query_service.process_query(sample_billing_request)

        assert isinstance(result, QueryResponse)
        assert result.success is True
        assert result.agent_used == "billing_agent"
        assert "Billing inquiry handled" in result.result

    @pytest.mark.asyncio
    async def test_process_query_all_types(self, query_service):
        """Test processing queries of all types."""
        query_types = [
            (QueryType.TECHNICAL, "technical_agent"),
            (QueryType.BILLING, "billing_agent"),
            (QueryType.ACCOUNT, "account_agent"),
            (QueryType.COMPLAINT, "response_agent"),
            (QueryType.GENERAL, "general_agent")
        ]

        for query_type, expected_agent in query_types:
            request = QueryRequest(
                query=f"Test {query_type.value} query",
                customer_id="test_customer",
                query_type=query_type
            )
            
            result = await query_service.process_query(request)
            
            assert result.agent_used == expected_agent
            assert result.success is True

    @pytest.mark.asyncio
    async def test_process_query_unknown_type(self, query_service):
        """Test processing query with unknown type falls back to general agent."""
        # Create request with None query_type (should default to general)
        request = QueryRequest(
            query="Unknown type query",
            customer_id="test_customer"
        )
        
        result = await query_service.process_query(request)
        
        assert result.agent_used == "general_agent"
        assert result.success is True

    @pytest.mark.asyncio
    async def test_process_query_stores_in_database(self, query_service, sample_query_request):
        """Test that processed queries are stored in database."""
        result = await query_service.process_query(sample_query_request)
        
        # Verify query is stored
        stored_query = query_service.queries_db.get(result.query_id)
        assert stored_query is not None
        assert stored_query["customer_id"] == "customer_123"
        assert stored_query["query"] == "I can't log into my account"
        assert stored_query["query_type"] == QueryType.TECHNICAL
        assert stored_query["priority"] == Priority.HIGH

    @pytest.mark.asyncio
    async def test_process_query_generates_suggestions(self, query_service, sample_query_request):
        """Test that query processing generates suggestions."""
        result = await query_service.process_query(sample_query_request)
        
        assert result.suggestions is not None
        assert isinstance(result.suggestions, list)
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_process_query_calculates_confidence(self, query_service, sample_query_request):
        """Test confidence calculation for queries."""
        result = await query_service.process_query(sample_query_request)
        
        assert 0.0 <= result.confidence <= 1.0
        # High priority technical queries should have higher confidence
        assert result.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_process_query_measures_processing_time(self, query_service, sample_query_request):
        """Test that processing time is accurately measured."""
        with patch('time.time', side_effect=[1000.0, 1001.5]):  # 1.5 second processing
            result = await query_service.process_query(sample_query_request)
            
            assert result.processing_time == 1.5

    @pytest.mark.asyncio
    async def test_process_query_error_handling(self, query_service):
        """Test query processing error handling."""
        # Create a request that might cause an error
        with patch.object(query_service, '_generate_suggestions', side_effect=Exception("Suggestion error")):
            with pytest.raises(Exception):
                request = QueryRequest(query="Error test", customer_id="test")
                await query_service.process_query(request)


class TestQueryRetrieval:
    """Test query retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_query_by_id_success(self, query_service, sample_query_request):
        """Test successful query retrieval by ID."""
        # First process a query
        processed = await query_service.process_query(sample_query_request)
        
        # Then retrieve it
        result = await query_service.get_query_by_id(processed.query_id)
        
        assert result is not None
        assert result.query_id == processed.query_id
        assert result.agent_used == processed.agent_used
        assert result.result == processed.result

    @pytest.mark.asyncio
    async def test_get_query_by_id_not_found(self, query_service):
        """Test query retrieval when query doesn't exist."""
        result = await query_service.get_query_by_id("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_query_by_id_maintains_data_integrity(self, query_service, sample_query_request):
        """Test that retrieved query maintains data integrity."""
        processed = await query_service.process_query(sample_query_request)
        retrieved = await query_service.get_query_by_id(processed.query_id)
        
        assert retrieved.query_id == processed.query_id
        assert retrieved.success == processed.success
        assert retrieved.agent_used == processed.agent_used
        # Note: suggestions might be empty in retrieved version (as per implementation)


class TestQueryListing:
    """Test query listing and filtering functionality."""

    @pytest.mark.asyncio
    async def test_list_queries_no_filters(self, query_service):
        """Test listing all queries without filters."""
        # Create multiple queries
        requests = [
            QueryRequest(query="Query 1", customer_id="customer_1", query_type=QueryType.TECHNICAL),
            QueryRequest(query="Query 2", customer_id="customer_2", query_type=QueryType.BILLING),
            QueryRequest(query="Query 3", customer_id="customer_1", query_type=QueryType.GENERAL)
        ]
        
        for request in requests:
            await query_service.process_query(request)
        
        result = await query_service.list_queries()
        
        assert len(result) == 3
        assert all(isinstance(query, QueryResponse) for query in result)

    @pytest.mark.asyncio
    async def test_list_queries_filter_by_customer(self, query_service):
        """Test listing queries filtered by customer ID."""
        # Create queries for different customers
        customer_1_requests = [
            QueryRequest(query="Query 1", customer_id="customer_1", query_type=QueryType.TECHNICAL),
            QueryRequest(query="Query 2", customer_id="customer_1", query_type=QueryType.BILLING)
        ]
        customer_2_request = QueryRequest(query="Query 3", customer_id="customer_2", query_type=QueryType.GENERAL)
        
        for request in customer_1_requests + [customer_2_request]:
            await query_service.process_query(request)
        
        result = await query_service.list_queries(customer_id="customer_1")
        
        assert len(result) == 2
        assert all(q.query_id for q in result)  # All should have valid IDs

    @pytest.mark.asyncio
    async def test_list_queries_filter_by_type(self, query_service):
        """Test listing queries filtered by query type."""
        requests = [
            QueryRequest(query="Tech Query 1", customer_id="customer_1", query_type=QueryType.TECHNICAL),
            QueryRequest(query="Tech Query 2", customer_id="customer_2", query_type=QueryType.TECHNICAL),
            QueryRequest(query="Billing Query", customer_id="customer_3", query_type=QueryType.BILLING)
        ]
        
        for request in requests:
            await query_service.process_query(request)
        
        result = await query_service.list_queries(query_type=QueryType.TECHNICAL)
        
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_queries_with_limit(self, query_service):
        """Test listing queries with limit."""
        # Create multiple queries
        for i in range(5):
            request = QueryRequest(
                query=f"Query {i}",
                customer_id=f"customer_{i}",
                query_type=QueryType.GENERAL
            )
            await query_service.process_query(request)
        
        result = await query_service.list_queries(limit=3)
        
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_queries_multiple_filters(self, query_service):
        """Test listing queries with multiple filters."""
        requests = [
            QueryRequest(query="Tech Query 1", customer_id="customer_1", query_type=QueryType.TECHNICAL),
            QueryRequest(query="Tech Query 2", customer_id="customer_1", query_type=QueryType.TECHNICAL),
            QueryRequest(query="Billing Query", customer_id="customer_1", query_type=QueryType.BILLING),
            QueryRequest(query="Tech Query 3", customer_id="customer_2", query_type=QueryType.TECHNICAL)
        ]
        
        for request in requests:
            await query_service.process_query(request)
        
        result = await query_service.list_queries(
            customer_id="customer_1",
            query_type=QueryType.TECHNICAL
        )
        
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_queries_empty_result(self, query_service):
        """Test listing queries when none match filters."""
        request = QueryRequest(query="Test", customer_id="customer_1", query_type=QueryType.TECHNICAL)
        await query_service.process_query(request)
        
        result = await query_service.list_queries(customer_id="nonexistent_customer")
        
        assert len(result) == 0


class TestQueryAnalytics:
    """Test query analytics functionality."""

    @pytest.mark.asyncio
    async def test_get_query_count(self, query_service):
        """Test getting total query count."""
        assert query_service.get_query_count() == 0
        
        # Process some queries
        for i in range(3):
            request = QueryRequest(query=f"Query {i}", customer_id=f"customer_{i}")
            await query_service.process_query(request)
        
        assert query_service.get_query_count() == 3

    @pytest.mark.asyncio
    async def test_get_queries_by_type(self, query_service):
        """Test getting queries grouped by type."""
        requests = [
            QueryRequest(query="Tech 1", customer_id="c1", query_type=QueryType.TECHNICAL),
            QueryRequest(query="Tech 2", customer_id="c2", query_type=QueryType.TECHNICAL),
            QueryRequest(query="Billing 1", customer_id="c3", query_type=QueryType.BILLING),
            QueryRequest(query="General 1", customer_id="c4", query_type=QueryType.GENERAL)
        ]
        
        for request in requests:
            await query_service.process_query(request)
        
        result = query_service.get_queries_by_type()
        
        assert result[QueryType.TECHNICAL] == 2
        assert result[QueryType.BILLING] == 1
        assert result[QueryType.GENERAL] == 1

    @pytest.mark.asyncio
    async def test_get_average_processing_time(self, query_service):
        """Test calculating average processing time."""
        # Mock processing times
        with patch('time.time', side_effect=[
            1000.0, 1001.0,  # First query: 1.0 second
            2000.0, 2002.0,  # Second query: 2.0 seconds
            3000.0, 3001.5   # Third query: 1.5 seconds
        ]):
            for i in range(3):
                request = QueryRequest(query=f"Query {i}", customer_id=f"customer_{i}")
                await query_service.process_query(request)
        
        avg_time = query_service.get_average_processing_time()
        expected_avg = (1.0 + 2.0 + 1.5) / 3
        assert abs(avg_time - expected_avg) < 0.01

    @pytest.mark.asyncio
    async def test_get_average_processing_time_no_queries(self, query_service):
        """Test average processing time when no queries exist."""
        avg_time = query_service.get_average_processing_time()
        assert avg_time == 0.0


class TestQuerySuggestions:
    """Test query suggestion generation."""

    def test_generate_suggestions_technical(self, query_service):
        """Test suggestion generation for technical queries."""
        suggestions = query_service._generate_suggestions(QueryType.TECHNICAL)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("troubleshooting" in s.lower() for s in suggestions)

    def test_generate_suggestions_billing(self, query_service):
        """Test suggestion generation for billing queries."""
        suggestions = query_service._generate_suggestions(QueryType.BILLING)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("billing" in s.lower() or "payment" in s.lower() for s in suggestions)

    def test_generate_suggestions_account(self, query_service):
        """Test suggestion generation for account queries."""
        suggestions = query_service._generate_suggestions(QueryType.ACCOUNT)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("account" in s.lower() or "profile" in s.lower() for s in suggestions)

    def test_generate_suggestions_complaint(self, query_service):
        """Test suggestion generation for complaint queries."""
        suggestions = query_service._generate_suggestions(QueryType.COMPLAINT)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("escalate" in s.lower() or "manager" in s.lower() for s in suggestions)

    def test_generate_suggestions_general(self, query_service):
        """Test suggestion generation for general queries."""
        suggestions = query_service._generate_suggestions(QueryType.GENERAL)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_generate_suggestions_unknown_type(self, query_service):
        """Test suggestion generation for unknown query type."""
        suggestions = query_service._generate_suggestions(None)
        
        assert isinstance(suggestions, list)
        # Should still return some default suggestions


class TestQueryConfidence:
    """Test query confidence calculation."""

    def test_calculate_confidence_high_priority_technical(self, query_service):
        """Test confidence calculation for high priority technical query."""
        request = QueryRequest(
            query="Critical system error",
            customer_id="customer_123",
            query_type=QueryType.TECHNICAL,
            priority=Priority.HIGH
        )
        
        confidence = query_service._calculate_confidence(request)
        
        assert confidence >= 0.85  # High priority technical should have high confidence

    def test_calculate_confidence_low_priority_general(self, query_service):
        """Test confidence calculation for low priority general query."""
        request = QueryRequest(
            query="General question",
            customer_id="customer_123",
            query_type=QueryType.GENERAL,
            priority=Priority.LOW
        )
        
        confidence = query_service._calculate_confidence(request)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence < 0.9  # Should be lower than high priority technical

    def test_calculate_confidence_with_context(self, query_service):
        """Test confidence calculation with additional context."""
        request_with_context = QueryRequest(
            query="Login issue",
            customer_id="customer_123",
            query_type=QueryType.TECHNICAL,
            priority=Priority.MEDIUM,
            context={"error_logs": "detailed error info", "steps_tried": ["reset", "clear_cache"]}
        )
        
        request_without_context = QueryRequest(
            query="Login issue",
            customer_id="customer_123",
            query_type=QueryType.TECHNICAL,
            priority=Priority.MEDIUM
        )
        
        confidence_with = query_service._calculate_confidence(request_with_context)
        confidence_without = query_service._calculate_confidence(request_without_context)
        
        # Context should increase confidence
        assert confidence_with >= confidence_without

    def test_calculate_confidence_query_length_factor(self, query_service):
        """Test that query length affects confidence calculation."""
        short_request = QueryRequest(
            query="Help",
            customer_id="customer_123",
            query_type=QueryType.GENERAL
        )
        
        detailed_request = QueryRequest(
            query="I am experiencing a specific issue with login functionality where after entering correct credentials, the system shows a timeout error",
            customer_id="customer_123",
            query_type=QueryType.TECHNICAL
        )
        
        short_confidence = query_service._calculate_confidence(short_request)
        detailed_confidence = query_service._calculate_confidence(detailed_request)
        
        # More detailed queries should have higher confidence
        assert detailed_confidence >= short_confidence


class TestQueryServicePerformance:
    """Test QueryService performance characteristics."""

    @pytest.mark.asyncio
    async def test_concurrent_query_processing(self, query_service):
        """Test concurrent processing of multiple queries."""
        import asyncio
        
        async def process_query(index):
            request = QueryRequest(
                query=f"Concurrent query {index}",
                customer_id=f"customer_{index}",
                query_type=QueryType.GENERAL
            )
            return await query_service.process_query(request)
        
        # Process queries concurrently
        tasks = [process_query(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 10
        assert all(r.success for r in results)
        assert len(set(r.query_id for r in results)) == 10  # All unique IDs

    @pytest.mark.asyncio
    async def test_high_volume_query_storage(self, query_service):
        """Test storage of high volume of queries."""
        # Process many queries
        for i in range(100):
            request = QueryRequest(
                query=f"Volume test query {i}",
                customer_id=f"customer_{i % 10}",  # 10 different customers
                query_type=QueryType.GENERAL
            )
            await query_service.process_query(request)
        
        assert query_service.get_query_count() == 100
        
        # Test that listing still works efficiently
        all_queries = await query_service.list_queries(limit=50)
        assert len(all_queries) == 50


class TestQueryServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_query_string(self, query_service):
        """Test processing query with empty string."""
        request = QueryRequest(
            query="",
            customer_id="customer_123",
            query_type=QueryType.GENERAL
        )
        
        result = await query_service.process_query(request)
        
        # Should still process but with lower confidence
        assert result.success is True
        assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_very_long_query_string(self, query_service):
        """Test processing very long query string."""
        long_query = "A" * 10000  # Very long query
        request = QueryRequest(
            query=long_query,
            customer_id="customer_123",
            query_type=QueryType.GENERAL
        )
        
        result = await query_service.process_query(request)
        
        # Should handle gracefully
        assert result.success is True
        # Result should be truncated appropriately
        assert len(result.result) < len(long_query)

    @pytest.mark.asyncio
    async def test_special_characters_in_query(self, query_service):
        """Test processing query with special characters."""
        special_query = "Query with special chars: @#$%^&*()[]{}|;:,.<>?"
        request = QueryRequest(
            query=special_query,
            customer_id="customer_123",
            query_type=QueryType.GENERAL
        )
        
        result = await query_service.process_query(request)
        
        assert result.success is True
        assert result.query_id is not None

    @pytest.mark.asyncio
    async def test_unicode_characters_in_query(self, query_service):
        """Test processing query with unicode characters."""
        unicode_query = "Query with unicode: 你好, مرحبا, здравствуй, 🙂"
        request = QueryRequest(
            query=unicode_query,
            customer_id="customer_123",
            query_type=QueryType.GENERAL
        )
        
        result = await query_service.process_query(request)
        
        assert result.success is True
        assert result.query_id is not None


class TestQueryServiceValidation:
    """Test input validation for QueryService."""

    @pytest.mark.asyncio
    async def test_invalid_customer_id_handling(self, query_service):
        """Test handling of invalid customer IDs."""
        request = QueryRequest(
            query="Test query",
            customer_id="",  # Empty customer ID
            query_type=QueryType.GENERAL
        )
        
        # Should still process (validation might be at API layer)
        result = await query_service.process_query(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_none_values_handling(self, query_service):
        """Test handling of None values in request."""
        request = QueryRequest(
            query="Test query",
            customer_id="customer_123"
            # Other fields are None/default
        )
        
        result = await query_service.process_query(request)
        assert result.success is True
        assert result.agent_used == "general_agent"  # Default agent
