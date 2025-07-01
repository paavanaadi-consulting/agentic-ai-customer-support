"""
Analytics service for handling system analytics and metrics.
"""
from datetime import datetime
from typing import Dict, Any, Optional

from .query_service import QueryService
from .ticket_service import TicketService
from .customer_service import CustomerService
from .feedback_service import FeedbackService
from ..api.schemas import AnalyticsResponse
from ..mcp.postgres_mcp_client import OptimizedPostgreSQLMCPClient, MCPClientError


class AnalyticsService:
    """Service class for handling analytics and metrics business logic."""
    
    def __init__(
        self,
        query_service: QueryService,
        ticket_service: Optional[TicketService] = None,
        customer_service: Optional[CustomerService] = None,
        feedback_service: Optional[FeedbackService] = None,
        mcp_client: Optional[OptimizedPostgreSQLMCPClient] = None
    ):
        self.query_service = query_service
        self.ticket_service = ticket_service
        self.customer_service = customer_service
        self.feedback_service = feedback_service
        self.mcp_client = mcp_client
    
    async def get_system_analytics(self) -> AnalyticsResponse:
        """
        Get comprehensive system analytics.
        
        Returns:
            AnalyticsResponse with system metrics
        """
        # Use MCP client for analytics if available
        if self.mcp_client:
            try:
                analytics = await self.mcp_client.get_analytics()
                
                # Build response from MCP data
                return AnalyticsResponse(
                    total_queries=0,  # Not available from MCP directly
                    total_tickets=analytics.get("total_tickets", 0),
                    total_customers=analytics.get("total_customers", 0),
                    total_feedback=0,  # Not available from MCP directly
                    avg_response_time=analytics.get("avg_resolution_hours", 0.0),
                    avg_rating=analytics.get("avg_satisfaction", 0.0),
                    tickets_by_status={
                        "open": analytics.get("open_tickets", 0),
                        "resolved": analytics.get("resolved_tickets", 0),
                        "high_priority": analytics.get("high_priority", 0)
                    },
                    queries_by_type={},  # Not available from MCP directly
                    customers_by_tier={},  # Not available from MCP directly
                    peak_hours={},  # Not available from MCP directly
                    satisfaction_trend=[],  # Not available from MCP directly
                    resolution_time_avg=analytics.get("avg_resolution_hours", 0.0),
                    generated_at=datetime.utcnow()
                )
                
            except MCPClientError as e:
                # Log error and fall back to service aggregation
                print(f"MCP error in get_system_analytics: {e}")
                pass
        
        # Fallback to aggregating from individual services
        # Get basic counts
        total_queries = self.query_service.get_query_count()
        total_tickets = self.ticket_service.get_ticket_count() if self.ticket_service else 0
        total_customers = self.customer_service.get_customer_count() if self.customer_service else 0
        total_feedback = self.feedback_service.get_feedback_count() if self.feedback_service else 0
        
        # Get performance metrics
        avg_response_time = self.query_service.get_average_processing_time()
        avg_rating = self.feedback_service.get_average_rating() if self.feedback_service else 0.0
        
        # Get distribution data
        tickets_by_status = self.ticket_service.get_tickets_by_status() if self.ticket_service else {}
        queries_by_type = self.query_service.get_queries_by_type()
        
        # Calculate additional metrics
        customer_satisfaction_rate = self._calculate_satisfaction_rate()
        resolution_rate = self._calculate_resolution_rate()
        
        return AnalyticsResponse(
            total_queries=total_queries,
            total_tickets=total_tickets,
            total_customers=total_customers,
            avg_response_time=avg_response_time,
            avg_rating=avg_rating,
            tickets_by_status=tickets_by_status,
            queries_by_type=queries_by_type,
            customer_satisfaction_rate=customer_satisfaction_rate,
            resolution_rate=resolution_rate,
            additional_metrics=await self._get_additional_metrics()
        )
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get detailed performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            "response_time_metrics": {
                "average": self.query_service.get_average_processing_time(),
                "percentiles": self._calculate_response_time_percentiles()
            },
            "customer_satisfaction": {
                "average_rating": self.feedback_service.get_average_rating(),
                "satisfaction_rate": self._calculate_satisfaction_rate(),
                "nps_score": self._calculate_nps_score()
            },
            "operational_efficiency": {
                "resolution_rate": self._calculate_resolution_rate(),
                "first_contact_resolution": self._calculate_fcr_rate(),
                "agent_utilization": self._calculate_agent_utilization()
            },
            "volume_metrics": {
                "queries_per_hour": self._calculate_queries_per_hour(),
                "tickets_per_day": self._calculate_tickets_per_day(),
                "peak_hours": self._identify_peak_hours()
            }
        }
    
    async def get_customer_insights(self) -> Dict[str, Any]:
        """
        Get customer-focused analytics and insights.
        
        Returns:
            Dictionary with customer insights
        """
        customers_by_tier = self.customer_service.get_customers_by_tier()
        tickets_by_priority = self.ticket_service.get_tickets_by_priority()
        feedback_analytics = await self.feedback_service.get_feedback_analytics()
        
        return {
            "customer_segmentation": {
                "by_tier": customers_by_tier,
                "by_activity": self._segment_customers_by_activity(),
                "by_satisfaction": self._segment_customers_by_satisfaction()
            },
            "support_patterns": {
                "tickets_by_priority": tickets_by_priority,
                "common_issues": self._identify_common_issues(),
                "escalation_patterns": self._analyze_escalation_patterns()
            },
            "feedback_insights": feedback_analytics,
            "retention_metrics": {
                "churn_risk": self._calculate_churn_risk(),
                "engagement_scores": self._calculate_engagement_scores()
            }
        }
    
    async def get_agent_performance(self) -> Dict[str, Any]:
        """
        Get agent performance analytics.
        
        Returns:
            Dictionary with agent performance metrics
        """
        return {
            "productivity_metrics": {
                "tickets_handled": self._get_tickets_per_agent(),
                "average_resolution_time": self._get_avg_resolution_time_per_agent(),
                "customer_satisfaction": self._get_satisfaction_per_agent()
            },
            "workload_distribution": {
                "tickets_by_agent": self._get_ticket_distribution(),
                "queue_status": self._get_agent_queue_status(),
                "availability": self._get_agent_availability()
            },
            "performance_trends": {
                "improvement_areas": self._identify_improvement_areas(),
                "top_performers": self._identify_top_performers(),
                "training_needs": self._identify_training_needs()
            }
        }
    
    def _calculate_satisfaction_rate(self) -> float:
        """Calculate customer satisfaction rate (ratings 4-5)."""
        feedback_list = list(self.feedback_service.feedback_db.values())
        if not feedback_list:
            return 0.0
        
        satisfied_count = len([f for f in feedback_list if f["rating"] >= 4])
        return (satisfied_count / len(feedback_list)) * 100
    
    def _calculate_resolution_rate(self) -> float:
        """Calculate ticket resolution rate."""
        tickets_by_status = self.ticket_service.get_tickets_by_status()
        total_tickets = sum(tickets_by_status.values())
        
        if total_tickets == 0:
            return 0.0
        
        resolved_tickets = (
            tickets_by_status.get("resolved", 0) + 
            tickets_by_status.get("closed", 0)
        )
        
        return (resolved_tickets / total_tickets) * 100
    
    def _calculate_nps_score(self) -> float:
        """Calculate Net Promoter Score."""
        feedback_list = list(self.feedback_service.feedback_db.values())
        if not feedback_list:
            return 0.0
        
        promoters = len([f for f in feedback_list if f["rating"] >= 4])
        detractors = len([f for f in feedback_list if f["rating"] <= 2])
        
        return ((promoters - detractors) / len(feedback_list)) * 100
    
    def _calculate_fcr_rate(self) -> float:
        """Calculate First Contact Resolution rate."""
        # Simplified calculation - in real implementation would track actual FCR
        tickets_by_status = self.ticket_service.get_tickets_by_status()
        total_tickets = sum(tickets_by_status.values())
        
        if total_tickets == 0:
            return 0.0
        
        # Assume resolved tickets are FCR for demo
        resolved_tickets = tickets_by_status.get("resolved", 0)
        return (resolved_tickets / total_tickets) * 100
    
    def _calculate_agent_utilization(self) -> float:
        """Calculate agent utilization rate."""
        # Simplified calculation - would need agent time tracking in real implementation
        tickets_by_status = self.ticket_service.get_tickets_by_status()
        active_tickets = (
            tickets_by_status.get("in_progress", 0) + 
            tickets_by_status.get("pending", 0)
        )
        
        # Assume 10 agents for demo
        total_agent_capacity = 10 * 8  # 8 tickets per agent per day
        
        if total_agent_capacity == 0:
            return 0.0
        
        return min(100.0, (active_tickets / total_agent_capacity) * 100)
    
    def _calculate_queries_per_hour(self) -> float:
        """Calculate average queries per hour."""
        total_queries = self.query_service.get_query_count()
        # Simplified - assume system running for 24 hours
        return total_queries / 24
    
    def _calculate_tickets_per_day(self) -> float:
        """Calculate average tickets per day."""
        total_tickets = self.ticket_service.get_ticket_count()
        # Simplified - assume system running for 1 day
        return total_tickets
    
    def _identify_peak_hours(self) -> list:
        """Identify peak usage hours."""
        # Simplified - would need timestamp analysis in real implementation
        return ["09:00-10:00", "14:00-15:00", "16:00-17:00"]
    
    def _calculate_response_time_percentiles(self) -> Dict[str, float]:
        """Calculate response time percentiles."""
        # Simplified calculation
        avg_time = self.query_service.get_average_processing_time()
        return {
            "p50": avg_time * 0.8,
            "p90": avg_time * 1.2,
            "p95": avg_time * 1.5,
            "p99": avg_time * 2.0
        }
    
    def _segment_customers_by_activity(self) -> Dict[str, int]:
        """Segment customers by activity level."""
        # Simplified segmentation
        total_customers = self.customer_service.get_customer_count()
        return {
            "high_activity": int(total_customers * 0.2),
            "medium_activity": int(total_customers * 0.5),
            "low_activity": int(total_customers * 0.3)
        }
    
    def _segment_customers_by_satisfaction(self) -> Dict[str, int]:
        """Segment customers by satisfaction level."""
        # Simplified segmentation
        total_customers = self.customer_service.get_customer_count()
        return {
            "highly_satisfied": int(total_customers * 0.6),
            "satisfied": int(total_customers * 0.3),
            "dissatisfied": int(total_customers * 0.1)
        }
    
    def _identify_common_issues(self) -> list:
        """Identify most common support issues."""
        queries_by_type = self.query_service.get_queries_by_type()
        sorted_issues = sorted(
            queries_by_type.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return [issue[0] for issue in sorted_issues[:5]]
    
    def _analyze_escalation_patterns(self) -> Dict[str, Any]:
        """Analyze ticket escalation patterns."""
        tickets_by_status = self.ticket_service.get_tickets_by_status()
        return {
            "escalation_rate": 15.0,  # Simplified
            "avg_escalation_time": 2.5,  # hours
            "common_escalation_reasons": [
                "Complex technical issue",
                "Billing dispute",
                "Customer dissatisfaction"
            ]
        }
    
    def _calculate_churn_risk(self) -> Dict[str, int]:
        """Calculate customer churn risk."""
        total_customers = self.customer_service.get_customer_count()
        return {
            "high_risk": int(total_customers * 0.1),
            "medium_risk": int(total_customers * 0.2),
            "low_risk": int(total_customers * 0.7)
        }
    
    def _calculate_engagement_scores(self) -> Dict[str, float]:
        """Calculate customer engagement scores."""
        return {
            "average_engagement": 0.72,
            "engagement_trend": "stable",
            "top_quartile": 0.95,
            "bottom_quartile": 0.35
        }
    
    def _get_tickets_per_agent(self) -> Dict[str, int]:
        """Get ticket count per agent."""
        # Simplified - would need actual agent assignment tracking
        return {
            "agent_001": 25,
            "agent_002": 30,
            "agent_003": 22,
            "agent_004": 28
        }
    
    def _get_avg_resolution_time_per_agent(self) -> Dict[str, float]:
        """Get average resolution time per agent."""
        return {
            "agent_001": 2.5,
            "agent_002": 3.1,
            "agent_003": 2.8,
            "agent_004": 2.2
        }
    
    def _get_satisfaction_per_agent(self) -> Dict[str, float]:
        """Get customer satisfaction per agent."""
        return {
            "agent_001": 4.2,
            "agent_002": 3.8,
            "agent_003": 4.5,
            "agent_004": 4.1
        }
    
    def _get_ticket_distribution(self) -> Dict[str, int]:
        """Get ticket distribution across agents."""
        return self._get_tickets_per_agent()
    
    def _get_agent_queue_status(self) -> Dict[str, int]:
        """Get current queue status per agent."""
        return {
            "agent_001": 3,
            "agent_002": 5,
            "agent_003": 2,
            "agent_004": 4
        }
    
    def _get_agent_availability(self) -> Dict[str, str]:
        """Get agent availability status."""
        return {
            "agent_001": "available",
            "agent_002": "busy",
            "agent_003": "available",
            "agent_004": "break"
        }
    
    def _identify_improvement_areas(self) -> list:
        """Identify areas for improvement."""
        return [
            "Response time optimization",
            "First contact resolution",
            "Customer satisfaction scores"
        ]
    
    def _identify_top_performers(self) -> list:
        """Identify top performing agents."""
        satisfaction_scores = self._get_satisfaction_per_agent()
        sorted_agents = sorted(
            satisfaction_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [agent[0] for agent in sorted_agents[:2]]
    
    def _identify_training_needs(self) -> list:
        """Identify training needs."""
        return [
            "Advanced technical troubleshooting",
            "Customer communication skills",
            "Product knowledge updates"
        ]
    
    async def _get_additional_metrics(self) -> Dict[str, Any]:
        """Get additional system metrics."""
        return {
            "system_uptime": "99.9%",
            "api_response_time": "125ms",
            "active_sessions": 45,
            "data_freshness": "real-time",
            "last_updated": datetime.utcnow()
        }
