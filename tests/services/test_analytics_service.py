"""
Comprehensive test suite for AnalyticsService.
Tests all analytics, metrics collection, and reporting functionality.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List

from src.services.analytics_service import AnalyticsService
from src.services.query_service import QueryService
from src.services.ticket_service import TicketService
from src.services.customer_service import CustomerService
from src.services.feedback_service import FeedbackService
from src.api.schemas import AnalyticsResponse
from src.mcp.postgres_mcp_client import OptimizedPostgreSQLMCPClient, MCPClientError


class TestAnalyticsService:
    """Test cases for AnalyticsService class."""

    @pytest.fixture
    def mock_mcp_client(self):
        """Create a mocked MCP client."""
        mock_client = AsyncMock(spec=OptimizedPostgreSQLMCPClient)
        return mock_client

    @pytest.fixture
    def mock_query_service(self):
        """Create a mocked QueryService."""
        mock_service = Mock(spec=QueryService)
        mock_service.get_query_count.return_value = 100
        mock_service.get_average_processing_time.return_value = 2.5
        mock_service.get_queries_by_type.return_value = {
            "technical": 40,
            "billing": 30,
            "general": 20,
            "account": 10
        }
        return mock_service

    @pytest.fixture
    def mock_ticket_service(self):
        """Create a mocked TicketService."""
        mock_service = Mock(spec=TicketService)
        mock_service.get_ticket_count.return_value = 50
        mock_service.get_tickets_by_status.return_value = {
            "open": 20,
            "in_progress": 15,
            "resolved": 10,
            "closed": 5
        }
        mock_service.get_tickets_by_priority.return_value = {
            "high": 10,
            "medium": 25,
            "low": 15
        }
        return mock_service

    @pytest.fixture
    def mock_customer_service(self):
        """Create a mocked CustomerService."""
        mock_service = Mock(spec=CustomerService)
        mock_service.get_customer_count.return_value = 75
        mock_service.get_customers_by_tier.return_value = {
            "standard": 60,
            "enterprise": 15
        }
        return mock_service

    @pytest.fixture
    def mock_feedback_service(self):
        """Create a mocked FeedbackService."""
        mock_service = Mock(spec=FeedbackService)
        mock_service.get_feedback_count.return_value = 80
        mock_service.get_average_rating.return_value = 4.2
        return mock_service

    @pytest.fixture
    def analytics_service(self, mock_query_service, mock_ticket_service, 
                         mock_customer_service, mock_feedback_service):
        """Create an AnalyticsService instance with mocked dependencies."""
        return AnalyticsService(
            query_service=mock_query_service,
            ticket_service=mock_ticket_service,
            customer_service=mock_customer_service,
            feedback_service=mock_feedback_service
        )

    @pytest.fixture
    def analytics_service_with_mcp(self, mock_query_service, mock_mcp_client):
        """Create an AnalyticsService instance with MCP client."""
        return AnalyticsService(
            query_service=mock_query_service,
            mcp_client=mock_mcp_client
        )

    @pytest.fixture
    def sample_mcp_analytics(self):
        """Create sample analytics data from MCP client."""
        return {
            "total_tickets": 45,
            "total_customers": 68,
            "avg_resolution_hours": 3.2,
            "avg_satisfaction": 4.1,
            "open_tickets": 18,
            "resolved_tickets": 22,
            "high_priority": 8
        }


class TestSystemAnalytics:
    """Test system analytics functionality."""

    @pytest.mark.asyncio
    async def test_get_system_analytics_with_services(self, analytics_service, mock_query_service,
                                                     mock_ticket_service, mock_customer_service,
                                                     mock_feedback_service):
        """Test getting system analytics with service aggregation."""
        with patch.object(analytics_service, '_calculate_satisfaction_rate', return_value=0.87), \
             patch.object(analytics_service, '_calculate_resolution_rate', return_value=0.82), \
             patch.object(analytics_service, '_get_additional_metrics', return_value={}):
            
            result = await analytics_service.get_system_analytics()
            
            assert isinstance(result, AnalyticsResponse)
            assert result.total_queries == 100
            assert result.total_tickets == 50
            assert result.total_customers == 75
            assert result.avg_response_time == 2.5
            assert result.avg_rating == 4.2
            assert result.customer_satisfaction_rate == 0.87
            assert result.resolution_rate == 0.82
            
            # Verify tickets by status
            assert result.tickets_by_status["open"] == 20
            assert result.tickets_by_status["resolved"] == 10
            
            # Verify queries by type
            assert result.queries_by_type["technical"] == 40
            assert result.queries_by_type["billing"] == 30

    @pytest.mark.asyncio
    async def test_get_system_analytics_with_mcp(self, analytics_service_with_mcp, mock_mcp_client,
                                                sample_mcp_analytics):
        """Test getting system analytics with MCP client."""
        mock_mcp_client.get_analytics.return_value = sample_mcp_analytics
        
        result = await analytics_service_with_mcp.get_system_analytics()
        
        assert isinstance(result, AnalyticsResponse)
        assert result.total_tickets == 45
        assert result.total_customers == 68
        assert result.avg_response_time == 3.2
        assert result.avg_rating == 4.1
        assert result.tickets_by_status["open"] == 18
        assert result.tickets_by_status["resolved"] == 22
        mock_mcp_client.get_analytics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_system_analytics_mcp_fallback(self, analytics_service_with_mcp, mock_mcp_client,
                                                    mock_query_service):
        """Test fallback to service aggregation when MCP fails."""
        mock_mcp_client.get_analytics.side_effect = MCPClientError("Connection failed")
        
        # Should fall back to service aggregation
        result = await analytics_service_with_mcp.get_system_analytics()
        
        assert isinstance(result, AnalyticsResponse)
        assert result.total_queries == 100  # From mock query service

    @pytest.mark.asyncio
    async def test_get_system_analytics_includes_timestamps(self, analytics_service):
        """Test that system analytics includes generation timestamp."""
        with patch.object(analytics_service, '_calculate_satisfaction_rate', return_value=0.87), \
             patch.object(analytics_service, '_calculate_resolution_rate', return_value=0.82), \
             patch.object(analytics_service, '_get_additional_metrics', return_value={}):
            
            before_time = datetime.utcnow()
            result = await analytics_service.get_system_analytics()
            after_time = datetime.utcnow()
            
            assert result.generated_at is not None
            assert before_time <= result.generated_at <= after_time


class TestPerformanceMetrics:
    """Test performance metrics functionality."""

    @pytest.mark.asyncio
    async def test_get_performance_metrics_complete(self, analytics_service):
        """Test getting complete performance metrics."""
        with patch.object(analytics_service, '_calculate_response_time_percentiles', 
                         return_value={"p50": 2.0, "p95": 5.0, "p99": 8.0}), \
             patch.object(analytics_service, '_calculate_satisfaction_rate', return_value=0.87), \
             patch.object(analytics_service, '_calculate_nps_score', return_value=65), \
             patch.object(analytics_service, '_calculate_resolution_rate', return_value=0.82), \
             patch.object(analytics_service, '_calculate_fcr_rate', return_value=0.75), \
             patch.object(analytics_service, '_calculate_agent_utilization', return_value=0.88), \
             patch.object(analytics_service, '_calculate_queries_per_hour', return_value=12.5), \
             patch.object(analytics_service, '_calculate_tickets_per_day', return_value=8.3), \
             patch.object(analytics_service, '_identify_peak_hours', 
                         return_value={"9": 15, "14": 12, "16": 10}):
            
            result = await analytics_service.get_performance_metrics()
            
            assert "response_time_metrics" in result
            assert "customer_satisfaction" in result
            assert "operational_efficiency" in result
            assert "volume_metrics" in result
            
            # Response time metrics
            assert result["response_time_metrics"]["average"] == 2.5
            assert result["response_time_metrics"]["percentiles"]["p95"] == 5.0
            
            # Customer satisfaction
            assert result["customer_satisfaction"]["average_rating"] == 4.2
            assert result["customer_satisfaction"]["satisfaction_rate"] == 0.87
            assert result["customer_satisfaction"]["nps_score"] == 65
            
            # Operational efficiency
            assert result["operational_efficiency"]["resolution_rate"] == 0.82
            assert result["operational_efficiency"]["first_contact_resolution"] == 0.75
            assert result["operational_efficiency"]["agent_utilization"] == 0.88
            
            # Volume metrics
            assert result["volume_metrics"]["queries_per_hour"] == 12.5
            assert result["volume_metrics"]["tickets_per_day"] == 8.3
            assert result["volume_metrics"]["peak_hours"]["9"] == 15

    @pytest.mark.asyncio
    async def test_get_performance_metrics_response_times(self, analytics_service, mock_query_service,
                                                         mock_feedback_service):
        """Test response time performance metrics."""
        mock_query_service.get_average_processing_time.return_value = 3.2
        mock_feedback_service.get_average_rating.return_value = 4.5
        
        with patch.object(analytics_service, '_calculate_response_time_percentiles',
                         return_value={"p50": 2.8, "p90": 6.2, "p95": 8.1, "p99": 12.5}):
            
            result = await analytics_service.get_performance_metrics()
            
            response_metrics = result["response_time_metrics"]
            assert response_metrics["average"] == 3.2
            assert response_metrics["percentiles"]["p50"] == 2.8
            assert response_metrics["percentiles"]["p99"] == 12.5


class TestCustomerInsights:
    """Test customer insights functionality."""

    @pytest.mark.asyncio
    async def test_get_customer_insights_complete(self, analytics_service, mock_customer_service,
                                                 mock_ticket_service, mock_feedback_service):
        """Test getting complete customer insights."""
        mock_customer_service.get_customers_by_tier.return_value = {
            "standard": 45,
            "premium": 20,
            "enterprise": 10
        }
        mock_ticket_service.get_tickets_by_priority.return_value = {
            "high": 8,
            "medium": 22,
            "low": 20
        }
        
        # Mock feedback analytics
        mock_feedback_analytics = {
            "sentiment_distribution": {
                "positive": 50,
                "neutral": 20,
                "negative": 10
            },
            "category_distribution": {
                "praise": 30,
                "suggestion": 25,
                "complaint": 15,
                "neutral": 10
            }
        }
        mock_feedback_service.get_feedback_analytics.return_value = mock_feedback_analytics
        
        with patch.object(analytics_service, '_segment_customers_by_activity',
                         return_value={"active": 60, "inactive": 15}), \
             patch.object(analytics_service, '_segment_customers_by_satisfaction',
                         return_value={"satisfied": 65, "neutral": 8, "dissatisfied": 2}), \
             patch.object(analytics_service, '_identify_common_issues',
                         return_value=["login_problems", "billing_questions", "feature_requests"]):
            
            result = await analytics_service.get_customer_insights()
            
            assert "customer_segmentation" in result
            assert "support_patterns" in result
            
            # Customer segmentation
            segmentation = result["customer_segmentation"]
            assert segmentation["by_tier"]["enterprise"] == 10
            assert segmentation["by_activity"]["active"] == 60
            assert segmentation["by_satisfaction"]["satisfied"] == 65
            
            # Support patterns
            patterns = result["support_patterns"]
            assert patterns["tickets_by_priority"]["high"] == 8
            assert "login_problems" in patterns["common_issues"]

    @pytest.mark.asyncio
    async def test_get_customer_insights_segmentation(self, analytics_service, mock_customer_service):
        """Test customer segmentation analysis."""
        mock_customer_service.get_customers_by_tier.return_value = {
            "standard": 100,
            "premium": 30,
            "enterprise": 15
        }
        
        with patch.object(analytics_service, '_segment_customers_by_activity',
                         return_value={"high_activity": 40, "medium_activity": 70, "low_activity": 35}), \
             patch.object(analytics_service, '_segment_customers_by_satisfaction',
                         return_value={"promoters": 90, "passives": 40, "detractors": 15}):
            
            result = await analytics_service.get_customer_insights()
            
            segmentation = result["customer_segmentation"]
            
            # Tier distribution
            assert segmentation["by_tier"]["standard"] == 100
            assert segmentation["by_tier"]["premium"] == 30
            assert segmentation["by_tier"]["enterprise"] == 15
            
            # Activity segmentation
            assert segmentation["by_activity"]["high_activity"] == 40
            assert segmentation["by_activity"]["medium_activity"] == 70
            
            # Satisfaction segmentation (NPS-style)
            assert segmentation["by_satisfaction"]["promoters"] == 90
            assert segmentation["by_satisfaction"]["detractors"] == 15


class TestAnalyticsCalculations:
    """Test analytics calculation methods."""

    def test_calculate_satisfaction_rate(self, analytics_service, mock_feedback_service):
        """Test customer satisfaction rate calculation."""
        # Mock feedback data for satisfaction calculation
        with patch.object(analytics_service.feedback_service, 'feedback_db', {
            "f1": {"rating": 5, "customer_id": "c1"},
            "f2": {"rating": 4, "customer_id": "c2"},
            "f3": {"rating": 3, "customer_id": "c3"},
            "f4": {"rating": 2, "customer_id": "c4"},
            "f5": {"rating": 1, "customer_id": "c5"}
        }):
            satisfaction_rate = analytics_service._calculate_satisfaction_rate()
            
            # Ratings 4 and 5 are considered satisfied (2 out of 5 = 0.4)
            assert satisfaction_rate == 0.4

    def test_calculate_satisfaction_rate_no_feedback(self, analytics_service):
        """Test satisfaction rate calculation with no feedback."""
        with patch.object(analytics_service.feedback_service, 'feedback_db', {}):
            satisfaction_rate = analytics_service._calculate_satisfaction_rate()
            assert satisfaction_rate == 0.0

    def test_calculate_resolution_rate(self, analytics_service, mock_ticket_service):
        """Test ticket resolution rate calculation."""
        # Mock ticket data for resolution calculation
        with patch.object(analytics_service.ticket_service, 'tickets_db', {
            "t1": {"status": "resolved", "ticket_id": "t1"},
            "t2": {"status": "closed", "ticket_id": "t2"},
            "t3": {"status": "open", "ticket_id": "t3"},
            "t4": {"status": "in_progress", "ticket_id": "t4"},
            "t5": {"status": "resolved", "ticket_id": "t5"}
        }):
            resolution_rate = analytics_service._calculate_resolution_rate()
            
            # 3 resolved/closed out of 5 total = 0.6
            assert resolution_rate == 0.6

    def test_calculate_resolution_rate_no_tickets(self, analytics_service):
        """Test resolution rate calculation with no tickets."""
        with patch.object(analytics_service.ticket_service, 'tickets_db', {}):
            resolution_rate = analytics_service._calculate_resolution_rate()
            assert resolution_rate == 0.0

    def test_calculate_nps_score(self, analytics_service):
        """Test Net Promoter Score calculation."""
        # Mock feedback with ratings distribution
        feedback_data = {
            "f1": {"rating": 5, "customer_id": "c1"},  # Promoter
            "f2": {"rating": 5, "customer_id": "c2"},  # Promoter
            "f3": {"rating": 4, "customer_id": "c3"},  # Promoter
            "f4": {"rating": 4, "customer_id": "c4"},  # Promoter
            "f5": {"rating": 3, "customer_id": "c5"},  # Passive
            "f6": {"rating": 3, "customer_id": "c6"},  # Passive
            "f7": {"rating": 2, "customer_id": "c7"},  # Detractor
            "f8": {"rating": 1, "customer_id": "c8"},  # Detractor
            "f9": {"rating": 1, "customer_id": "c9"},  # Detractor
            "f10": {"rating": 2, "customer_id": "c10"}  # Detractor
        }
        
        with patch.object(analytics_service.feedback_service, 'feedback_db', feedback_data):
            nps_score = analytics_service._calculate_nps_score()
            
            # Promoters (4-5): 4, Detractors (1-2): 4, Total: 10
            # NPS = (4-4)/10 * 100 = 0
            assert nps_score == 0

    def test_calculate_fcr_rate(self, analytics_service):
        """Test First Contact Resolution rate calculation."""
        # Mock query and ticket data
        query_data = {
            "q1": {"customer_id": "c1", "success": True, "confidence": 0.9},
            "q2": {"customer_id": "c2", "success": True, "confidence": 0.8},
            "q3": {"customer_id": "c3", "success": False, "confidence": 0.5},
            "q4": {"customer_id": "c4", "success": True, "confidence": 0.95}
        }
        
        ticket_data = {
            "t1": {"customer_id": "c3", "status": "open"},  # Customer c3 needed a ticket
        }
        
        with patch.object(analytics_service.query_service, 'queries_db', query_data), \
             patch.object(analytics_service.ticket_service, 'tickets_db', ticket_data):
            
            fcr_rate = analytics_service._calculate_fcr_rate()
            
            # 3 customers resolved on first contact out of 4 = 0.75
            assert fcr_rate == 0.75

    def test_calculate_agent_utilization(self, analytics_service):
        """Test agent utilization calculation."""
        # Mock agent assignment data in tickets
        ticket_data = {
            "t1": {"assigned_agent": "agent_1", "status": "in_progress"},
            "t2": {"assigned_agent": "agent_1", "status": "resolved"},
            "t3": {"assigned_agent": "agent_2", "status": "open"},
            "t4": {"assigned_agent": "agent_3", "status": "closed"},
            "t5": {"assigned_agent": None, "status": "open"}  # Unassigned
        }
        
        with patch.object(analytics_service.ticket_service, 'tickets_db', ticket_data):
            utilization = analytics_service._calculate_agent_utilization()
            
            # 4 tickets assigned to agents out of 5 total = 0.8
            assert utilization == 0.8


class TestAnalyticsTimeBasedMetrics:
    """Test time-based analytics metrics."""

    def test_calculate_queries_per_hour(self, analytics_service):
        """Test queries per hour calculation."""
        base_time = datetime.utcnow()
        query_data = {
            f"q{i}": {
                "timestamp": base_time - timedelta(hours=i),
                "customer_id": f"c{i}"
            } for i in range(24)  # 24 queries over 24 hours
        }
        
        with patch.object(analytics_service.query_service, 'queries_db', query_data):
            queries_per_hour = analytics_service._calculate_queries_per_hour()
            
            # 24 queries over 24 hours = 1.0 queries per hour
            assert queries_per_hour == 1.0

    def test_calculate_tickets_per_day(self, analytics_service):
        """Test tickets per day calculation."""
        base_time = datetime.utcnow()
        ticket_data = {
            f"t{i}": {
                "created_at": base_time - timedelta(days=i),
                "customer_id": f"c{i}"
            } for i in range(7)  # 7 tickets over 7 days
        }
        
        with patch.object(analytics_service.ticket_service, 'tickets_db', ticket_data):
            tickets_per_day = analytics_service._calculate_tickets_per_day()
            
            # 7 tickets over 7 days = 1.0 tickets per day
            assert tickets_per_day == 1.0

    def test_identify_peak_hours(self, analytics_service):
        """Test peak hours identification."""
        base_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Create queries with specific hour distribution
        query_data = {}
        hour_distribution = {9: 5, 10: 3, 14: 8, 15: 6, 16: 4}  # Peak at 14:00
        
        query_id = 0
        for hour, count in hour_distribution.items():
            for i in range(count):
                query_data[f"q{query_id}"] = {
                    "timestamp": base_time.replace(hour=hour),
                    "customer_id": f"c{query_id}"
                }
                query_id += 1
        
        with patch.object(analytics_service.query_service, 'queries_db', query_data):
            peak_hours = analytics_service._identify_peak_hours()
            
            assert peak_hours["14"] == 8  # Highest count
            assert peak_hours["9"] == 5
            assert peak_hours["16"] == 4


class TestAnalyticsCustomerSegmentation:
    """Test customer segmentation methods."""

    def test_segment_customers_by_activity(self, analytics_service):
        """Test customer activity segmentation."""
        base_time = datetime.utcnow()
        
        # Mock customer data with different activity levels
        customer_data = {
            "c1": {"last_interaction": base_time - timedelta(days=1)},  # High activity
            "c2": {"last_interaction": base_time - timedelta(days=5)},  # Medium activity
            "c3": {"last_interaction": base_time - timedelta(days=15)}, # Low activity
            "c4": {"last_interaction": base_time - timedelta(days=35)}, # Inactive
            "c5": {"last_interaction": None}  # Never interacted
        }
        
        with patch.object(analytics_service.customer_service, 'customers_db', customer_data):
            segmentation = analytics_service._segment_customers_by_activity()
            
            assert segmentation["high"] == 1  # Last 7 days
            assert segmentation["medium"] == 1  # 7-30 days
            assert segmentation["low"] == 1   # 30+ days
            assert segmentation["inactive"] == 2  # No recent interaction

    def test_segment_customers_by_satisfaction(self, analytics_service):
        """Test customer satisfaction segmentation."""
        # Mock customer feedback data
        feedback_data = {
            "f1": {"customer_id": "c1", "rating": 5},  # Promoter
            "f2": {"customer_id": "c2", "rating": 4},  # Promoter
            "f3": {"customer_id": "c3", "rating": 3},  # Passive
            "f4": {"customer_id": "c4", "rating": 2},  # Detractor
            "f5": {"customer_id": "c5", "rating": 1},  # Detractor
        }
        
        with patch.object(analytics_service.feedback_service, 'feedback_db', feedback_data):
            segmentation = analytics_service._segment_customers_by_satisfaction()
            
            assert segmentation["promoters"] == 2    # Ratings 4-5
            assert segmentation["passives"] == 1     # Rating 3
            assert segmentation["detractors"] == 2   # Ratings 1-2

    def test_identify_common_issues(self, analytics_service):
        """Test identification of common issues."""
        # Mock ticket data with categories
        ticket_data = {
            "t1": {"category": "technical", "title": "Login issue"},
            "t2": {"category": "technical", "title": "Password reset"},
            "t3": {"category": "billing", "title": "Invoice question"},
            "t4": {"category": "technical", "title": "Account locked"},
            "t5": {"category": "billing", "title": "Payment failed"},
            "t6": {"category": "general", "title": "General inquiry"}
        }
        
        with patch.object(analytics_service.ticket_service, 'tickets_db', ticket_data):
            common_issues = analytics_service._identify_common_issues()
            
            # Should identify technical issues as most common
            assert "technical_issues" in common_issues
            assert "billing_questions" in common_issues


class TestAnalyticsServicePerformance:
    """Test AnalyticsService performance characteristics."""

    @pytest.mark.asyncio
    async def test_analytics_calculation_performance(self, analytics_service):
        """Test performance of analytics calculations with large datasets."""
        # Mock large datasets
        large_query_data = {f"q{i}": {"customer_id": f"c{i}", "timestamp": datetime.utcnow()} 
                           for i in range(1000)}
        large_ticket_data = {f"t{i}": {"customer_id": f"c{i}", "status": "open"} 
                            for i in range(500)}
        large_feedback_data = {f"f{i}": {"customer_id": f"c{i}", "rating": (i % 5) + 1} 
                              for i in range(800)}
        
        with patch.object(analytics_service.query_service, 'queries_db', large_query_data), \
             patch.object(analytics_service.ticket_service, 'tickets_db', large_ticket_data), \
             patch.object(analytics_service.feedback_service, 'feedback_db', large_feedback_data), \
             patch.object(analytics_service, '_get_additional_metrics', return_value={}):
            
            import time
            start_time = time.time()
            
            result = await analytics_service.get_system_analytics()
            
            end_time = time.time()
            calculation_time = end_time - start_time
            
            # Should complete within reasonable time (under 1 second for this test)
            assert calculation_time < 1.0
            assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_analytics_requests(self, analytics_service):
        """Test handling of concurrent analytics requests."""
        import asyncio
        
        with patch.object(analytics_service, '_calculate_satisfaction_rate', return_value=0.85), \
             patch.object(analytics_service, '_calculate_resolution_rate', return_value=0.78), \
             patch.object(analytics_service, '_get_additional_metrics', return_value={}):
            
            # Make multiple concurrent requests
            tasks = [analytics_service.get_system_analytics() for _ in range(5)]
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert len(results) == 5
            assert all(isinstance(result, AnalyticsResponse) for result in results)
            assert all(result.total_queries == 100 for result in results)


class TestAnalyticsServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_analytics_with_empty_data(self, analytics_service):
        """Test analytics calculation with empty datasets."""
        # Mock empty datasets
        with patch.object(analytics_service.query_service, 'queries_db', {}), \
             patch.object(analytics_service.ticket_service, 'tickets_db', {}), \
             patch.object(analytics_service.feedback_service, 'feedback_db', {}), \
             patch.object(analytics_service.query_service, 'get_query_count', return_value=0), \
             patch.object(analytics_service.ticket_service, 'get_ticket_count', return_value=0), \
             patch.object(analytics_service.customer_service, 'get_customer_count', return_value=0), \
             patch.object(analytics_service.feedback_service, 'get_feedback_count', return_value=0), \
             patch.object(analytics_service.query_service, 'get_average_processing_time', return_value=0.0), \
             patch.object(analytics_service.feedback_service, 'get_average_rating', return_value=0.0), \
             patch.object(analytics_service.ticket_service, 'get_tickets_by_status', return_value={}), \
             patch.object(analytics_service.query_service, 'get_queries_by_type', return_value={}), \
             patch.object(analytics_service, '_get_additional_metrics', return_value={}):
            
            result = await analytics_service.get_system_analytics()
            
            # Should handle gracefully with zero values
            assert result.total_queries == 0
            assert result.total_tickets == 0
            assert result.total_customers == 0
            assert result.avg_response_time == 0.0
            assert result.avg_rating == 0.0
            assert result.customer_satisfaction_rate == 0.0
            assert result.resolution_rate == 0.0

    @pytest.mark.asyncio
    async def test_analytics_with_partial_service_failures(self, analytics_service):
        """Test analytics when some services fail."""
        # Mock one service to fail
        with patch.object(analytics_service.ticket_service, 'get_ticket_count', 
                         side_effect=Exception("Ticket service error")), \
             patch.object(analytics_service, '_calculate_satisfaction_rate', return_value=0.85), \
             patch.object(analytics_service, '_calculate_resolution_rate', return_value=0.78), \
             patch.object(analytics_service, '_get_additional_metrics', return_value={}):
            
            # Should still complete but might have some missing data
            result = await analytics_service.get_system_analytics()
            
            assert result is not None
            assert result.total_queries == 100  # From working service
            # total_tickets might be 0 due to service failure

    def test_analytics_calculation_division_by_zero(self, analytics_service):
        """Test analytics calculations that might involve division by zero."""
        # Test satisfaction rate with no feedback
        with patch.object(analytics_service.feedback_service, 'feedback_db', {}):
            satisfaction_rate = analytics_service._calculate_satisfaction_rate()
            assert satisfaction_rate == 0.0  # Should handle gracefully
        
        # Test resolution rate with no tickets
        with patch.object(analytics_service.ticket_service, 'tickets_db', {}):
            resolution_rate = analytics_service._calculate_resolution_rate()
            assert resolution_rate == 0.0  # Should handle gracefully

    @pytest.mark.asyncio
    async def test_analytics_with_malformed_data(self, analytics_service):
        """Test analytics with malformed or inconsistent data."""
        # Mock data with missing fields
        malformed_feedback = {
            "f1": {"rating": 5},  # Missing customer_id
            "f2": {"customer_id": "c2"},  # Missing rating
            "f3": {"customer_id": "c3", "rating": "invalid"},  # Invalid rating type
        }
        
        with patch.object(analytics_service.feedback_service, 'feedback_db', malformed_feedback), \
             patch.object(analytics_service, '_calculate_resolution_rate', return_value=0.75), \
             patch.object(analytics_service, '_get_additional_metrics', return_value={}):
            
            # Should handle malformed data gracefully
            satisfaction_rate = analytics_service._calculate_satisfaction_rate()
            assert isinstance(satisfaction_rate, float)
            assert 0.0 <= satisfaction_rate <= 1.0


class TestAnalyticsServiceIntegration:
    """Test integration scenarios for AnalyticsService."""

    @pytest.mark.asyncio
    async def test_full_analytics_workflow(self, analytics_service):
        """Test complete analytics workflow with all components."""
        with patch.object(analytics_service, '_calculate_satisfaction_rate', return_value=0.87), \
             patch.object(analytics_service, '_calculate_resolution_rate', return_value=0.82), \
             patch.object(analytics_service, '_get_additional_metrics', return_value={
                 "custom_metric_1": 25.5,
                 "custom_metric_2": "excellent"
             }):
            
            # Get system analytics
            system_analytics = await analytics_service.get_system_analytics()
            assert isinstance(system_analytics, AnalyticsResponse)
            
            # Get performance metrics
            performance_metrics = await analytics_service.get_performance_metrics()
            assert "response_time_metrics" in performance_metrics
            
            # Get customer insights
            customer_insights = await analytics_service.get_customer_insights()
            assert "customer_segmentation" in customer_insights
            
            # All should be consistent and complete
            assert system_analytics.total_queries == 100
            assert performance_metrics["response_time_metrics"]["average"] == 2.5
            assert customer_insights["customer_segmentation"]["by_tier"]["enterprise"] == 15

    @pytest.mark.asyncio
    async def test_analytics_data_consistency(self, analytics_service):
        """Test that analytics data is consistent across different method calls."""
        with patch.object(analytics_service, '_calculate_satisfaction_rate', return_value=0.87), \
             patch.object(analytics_service, '_calculate_resolution_rate', return_value=0.82), \
             patch.object(analytics_service, '_get_additional_metrics', return_value={}):
            
            # Call analytics multiple times
            result1 = await analytics_service.get_system_analytics()
            result2 = await analytics_service.get_system_analytics()
            
            # Results should be consistent
            assert result1.total_queries == result2.total_queries
            assert result1.avg_response_time == result2.avg_response_time
            assert result1.customer_satisfaction_rate == result2.customer_satisfaction_rate
