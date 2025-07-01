"""
Feedback service for handling customer feedback business logic.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..api.schemas import FeedbackRequest, FeedbackResponse


class FeedbackService:
    """Service class for handling feedback-related business logic."""
    
    def __init__(self):
        # In-memory storage for demo purposes (replace with database in production)
        self.feedback_db = {}
    
    async def submit_feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        """
        Submit customer feedback.
        
        Args:
            request: FeedbackRequest containing feedback details
            
        Returns:
            FeedbackResponse with created feedback information
        """
        feedback_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Validate feedback data
        self._validate_feedback_data(request)
        
        feedback_data = {
            "feedback_id": feedback_id,
            "customer_id": request.customer_id,
            "rating": request.rating,
            "comment": request.comment,
            "query_id": request.query_id,
            "ticket_id": request.ticket_id,
            "created_at": now,
            "sentiment": self._analyze_sentiment(request.comment),
            "category": self._categorize_feedback(request.comment, request.rating),
            "processed": False
        }
        
        # Store feedback
        self.feedback_db[feedback_id] = feedback_data
        
        # Trigger feedback processing workflow
        await self._process_feedback(feedback_id)
        
        return FeedbackResponse(**feedback_data)
    
    async def get_feedback_by_id(self, feedback_id: str) -> Optional[FeedbackResponse]:
        """
        Retrieve feedback by its ID.
        
        Args:
            feedback_id: The unique feedback identifier
            
        Returns:
            FeedbackResponse if found, None otherwise
        """
        if feedback_id not in self.feedback_db:
            return None
        
        feedback = self.feedback_db[feedback_id]
        return FeedbackResponse(**feedback)
    
    async def list_feedback(
        self,
        customer_id: Optional[str] = None,
        rating: Optional[int] = None,
        sentiment: Optional[str] = None,
        limit: int = 10
    ) -> List[FeedbackResponse]:
        """
        List feedback with optional filtering.
        
        Args:
            customer_id: Filter by customer ID
            rating: Filter by rating
            sentiment: Filter by sentiment
            limit: Maximum number of results to return
            
        Returns:
            List of FeedbackResponse objects
        """
        filtered_feedback = list(self.feedback_db.values())
        
        # Apply filters
        if customer_id:
            filtered_feedback = [
                f for f in filtered_feedback 
                if f["customer_id"] == customer_id
            ]
        
        if rating is not None:
            filtered_feedback = [
                f for f in filtered_feedback 
                if f["rating"] == rating
            ]
        
        if sentiment:
            filtered_feedback = [
                f for f in filtered_feedback 
                if f.get("sentiment") == sentiment
            ]
        
        # Sort by creation date (newest first)
        filtered_feedback.sort(
            key=lambda x: x["created_at"], 
            reverse=True
        )
        
        # Apply limit
        filtered_feedback = filtered_feedback[:limit]
        
        return [FeedbackResponse(**feedback) for feedback in filtered_feedback]
    
    async def get_feedback_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive feedback analytics.
        
        Returns:
            Dictionary with feedback analytics
        """
        if not self.feedback_db:
            return {
                "total_feedback": 0,
                "average_rating": 0.0,
                "rating_distribution": {},
                "sentiment_distribution": {},
                "category_distribution": {}
            }
        
        feedback_list = list(self.feedback_db.values())
        
        # Calculate average rating
        total_rating = sum(f["rating"] for f in feedback_list)
        avg_rating = total_rating / len(feedback_list)
        
        # Rating distribution
        rating_distribution = {}
        for feedback in feedback_list:
            rating = feedback["rating"]
            rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
        
        # Sentiment distribution
        sentiment_distribution = {}
        for feedback in feedback_list:
            sentiment = feedback.get("sentiment", "unknown")
            sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
        
        # Category distribution
        category_distribution = {}
        for feedback in feedback_list:
            category = feedback.get("category", "uncategorized")
            category_distribution[category] = category_distribution.get(category, 0) + 1
        
        return {
            "total_feedback": len(feedback_list),
            "average_rating": round(avg_rating, 2),
            "rating_distribution": rating_distribution,
            "sentiment_distribution": sentiment_distribution,
            "category_distribution": category_distribution,
            "trends": self._calculate_trends()
        }
    
    async def get_customer_feedback_summary(
        self, 
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Get feedback summary for a specific customer.
        
        Args:
            customer_id: The unique customer identifier
            
        Returns:
            Dictionary with customer feedback summary
        """
        customer_feedback = [
            f for f in self.feedback_db.values() 
            if f["customer_id"] == customer_id
        ]
        
        if not customer_feedback:
            return {
                "customer_id": customer_id,
                "total_feedback": 0,
                "average_rating": 0.0,
                "latest_feedback": None
            }
        
        # Calculate metrics
        total_feedback = len(customer_feedback)
        avg_rating = sum(f["rating"] for f in customer_feedback) / total_feedback
        
        # Get latest feedback
        latest_feedback = max(customer_feedback, key=lambda x: x["created_at"])
        
        return {
            "customer_id": customer_id,
            "total_feedback": total_feedback,
            "average_rating": round(avg_rating, 2),
            "latest_feedback": {
                "rating": latest_feedback["rating"],
                "comment": latest_feedback["comment"],
                "created_at": latest_feedback["created_at"]
            },
            "satisfaction_trend": self._calculate_customer_satisfaction_trend(customer_id)
        }
    
    def _validate_feedback_data(self, request: FeedbackRequest) -> None:
        """
        Validate feedback data before creation.
        
        Args:
            request: FeedbackRequest to validate
            
        Raises:
            ValueError: If validation fails
        """
        # Validate rating range
        if not (1 <= request.rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
        
        # Validate comment length
        if request.comment and len(request.comment.strip()) > 1000:
            raise ValueError("Comment must be 1000 characters or less")
        
        # Ensure at least one reference (query_id or ticket_id)
        if not request.query_id and not request.ticket_id:
            raise ValueError("Feedback must reference either a query or ticket")
    
    def _analyze_sentiment(self, comment: Optional[str]) -> str:
        """
        Analyze sentiment of feedback comment.
        
        Args:
            comment: Feedback comment text
            
        Returns:
            Sentiment classification (positive, negative, neutral)
        """
        if not comment:
            return "neutral"
        
        comment_lower = comment.lower()
        
        # Simple keyword-based sentiment analysis
        positive_words = [
            "good", "great", "excellent", "amazing", "helpful",
            "satisfied", "pleased", "happy", "love", "perfect"
        ]
        
        negative_words = [
            "bad", "terrible", "awful", "horrible", "disappointed",
            "frustrated", "angry", "hate", "worst", "useless"
        ]
        
        positive_count = sum(1 for word in positive_words if word in comment_lower)
        negative_count = sum(1 for word in negative_words if word in comment_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _categorize_feedback(self, comment: Optional[str], rating: int) -> str:
        """
        Categorize feedback based on content and rating.
        
        Args:
            comment: Feedback comment text
            rating: Feedback rating
            
        Returns:
            Feedback category
        """
        if rating <= 2:
            return "complaint"
        elif rating >= 4:
            return "praise"
        else:
            return "suggestion"
        
        # Could be enhanced with keyword analysis of comment
    
    async def _process_feedback(self, feedback_id: str) -> None:
        """
        Process feedback for alerts and actions.
        
        Args:
            feedback_id: The unique feedback identifier
        """
        feedback = self.feedback_db[feedback_id]
        
        # Mark as processed
        feedback["processed"] = True
        
        # Trigger alerts for low ratings
        if feedback["rating"] <= 2:
            await self._trigger_low_rating_alert(feedback)
        
        # Trigger appreciation for high ratings
        if feedback["rating"] >= 4:
            await self._trigger_positive_feedback_action(feedback)
    
    async def _trigger_low_rating_alert(self, feedback: Dict[str, Any]) -> None:
        """
        Trigger alert for low rating feedback.
        
        Args:
            feedback: Feedback data
        """
        # In a real implementation, this would:
        # - Send notification to management
        # - Create follow-up task
        # - Escalate if necessary
        pass
    
    async def _trigger_positive_feedback_action(self, feedback: Dict[str, Any]) -> None:
        """
        Trigger action for positive feedback.
        
        Args:
            feedback: Feedback data
        """
        # In a real implementation, this would:
        # - Thank the customer
        # - Share with relevant team
        # - Update agent recognition
        pass
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate feedback trends over time."""
        # Simple trend calculation - could be enhanced with time-based analysis
        feedback_list = list(self.feedback_db.values())
        
        if len(feedback_list) < 2:
            return {"trend": "insufficient_data"}
        
        # Sort by date
        feedback_list.sort(key=lambda x: x["created_at"])
        
        # Compare recent vs older feedback
        mid_point = len(feedback_list) // 2
        older_feedback = feedback_list[:mid_point]
        recent_feedback = feedback_list[mid_point:]
        
        older_avg = sum(f["rating"] for f in older_feedback) / len(older_feedback)
        recent_avg = sum(f["rating"] for f in recent_feedback) / len(recent_feedback)
        
        if recent_avg > older_avg + 0.2:
            trend = "improving"
        elif recent_avg < older_avg - 0.2:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "older_average": round(older_avg, 2),
            "recent_average": round(recent_avg, 2)
        }
    
    def _calculate_customer_satisfaction_trend(self, customer_id: str) -> str:
        """Calculate satisfaction trend for specific customer."""
        customer_feedback = [
            f for f in self.feedback_db.values() 
            if f["customer_id"] == customer_id
        ]
        
        if len(customer_feedback) < 2:
            return "insufficient_data"
        
        # Sort by date and compare first vs last ratings
        customer_feedback.sort(key=lambda x: x["created_at"])
        first_rating = customer_feedback[0]["rating"]
        last_rating = customer_feedback[-1]["rating"]
        
        if last_rating > first_rating:
            return "improving"
        elif last_rating < first_rating:
            return "declining"
        else:
            return "stable"
    
    def get_feedback_count(self) -> int:
        """Get total number of feedback entries."""
        return len(self.feedback_db)
    
    def get_average_rating(self) -> float:
        """Calculate overall average rating."""
        if not self.feedback_db:
            return 0.0
        
        total_rating = sum(f["rating"] for f in self.feedback_db.values())
        return total_rating / len(self.feedback_db)
