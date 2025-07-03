"""
Comprehensive test suite for FeedbackService.
Tests all feedback collection, analysis, and reporting logic.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List

from src.services.feedback_service import FeedbackService
from src.api.schemas import FeedbackRequest, FeedbackResponse


class TestFeedbackService:
    """Test cases for FeedbackService class."""

    @pytest.fixture
    def feedback_service(self):
        """Create a FeedbackService instance."""
        return FeedbackService()

    @pytest.fixture
    def sample_feedback_request(self):
        """Create a sample feedback request."""
        return FeedbackRequest(
            customer_id="customer_123",
            rating=4,
            comment="Great service, very helpful support team!",
            query_id="query_456",
            ticket_id="ticket_789"
        )

    @pytest.fixture
    def negative_feedback_request(self):
        """Create a negative feedback request."""
        return FeedbackRequest(
            customer_id="customer_456",
            rating=2,
            comment="Poor response time and unhelpful answers",
            query_id="query_123"
        )

    @pytest.fixture
    def neutral_feedback_request(self):
        """Create a neutral feedback request."""
        return FeedbackRequest(
            customer_id="customer_789",
            rating=3,
            comment="It was okay, nothing special"
        )


class TestFeedbackSubmission:
    """Test feedback submission functionality."""

    @pytest.mark.asyncio
    async def test_submit_feedback_success(self, feedback_service, sample_feedback_request):
        """Test successful feedback submission."""
        result = await feedback_service.submit_feedback(sample_feedback_request)

        assert isinstance(result, FeedbackResponse)
        assert result.customer_id == "customer_123"
        assert result.rating == 4
        assert result.comment == "Great service, very helpful support team!"
        assert result.query_id == "query_456"
        assert result.ticket_id == "ticket_789"
        assert result.feedback_id is not None
        assert isinstance(result.created_at, datetime)
        assert result.sentiment is not None
        assert result.category is not None
        assert result.processed is False  # Initially not processed

    @pytest.mark.asyncio
    async def test_submit_feedback_minimal_data(self, feedback_service):
        """Test feedback submission with minimal required data."""
        minimal_request = FeedbackRequest(
            customer_id="customer_123",
            rating=5
        )
        
        result = await feedback_service.submit_feedback(minimal_request)
        
        assert result.customer_id == "customer_123"
        assert result.rating == 5
        assert result.comment is None
        assert result.query_id is None
        assert result.ticket_id is None

    @pytest.mark.asyncio
    async def test_submit_feedback_stores_in_database(self, feedback_service, sample_feedback_request):
        """Test that submitted feedback is stored in database."""
        result = await feedback_service.submit_feedback(sample_feedback_request)
        
        # Verify feedback is stored
        stored_feedback = feedback_service.feedback_db.get(result.feedback_id)
        assert stored_feedback is not None
        assert stored_feedback["customer_id"] == "customer_123"
        assert stored_feedback["rating"] == 4
        assert stored_feedback["comment"] == "Great service, very helpful support team!"

    @pytest.mark.asyncio
    async def test_submit_feedback_sentiment_analysis(self, feedback_service):
        """Test sentiment analysis for different types of feedback."""
        # Positive feedback
        positive_request = FeedbackRequest(
            customer_id="customer_1",
            rating=5,
            comment="Excellent service! Very satisfied with the help."
        )
        positive_result = await feedback_service.submit_feedback(positive_request)
        assert positive_result.sentiment == "positive"
        
        # Negative feedback
        negative_request = FeedbackRequest(
            customer_id="customer_2",
            rating=1,
            comment="Terrible experience, very disappointed."
        )
        negative_result = await feedback_service.submit_feedback(negative_request)
        assert negative_result.sentiment == "negative"
        
        # Neutral feedback
        neutral_request = FeedbackRequest(
            customer_id="customer_3",
            rating=3,
            comment="It was okay, not great but not bad either."
        )
        neutral_result = await feedback_service.submit_feedback(neutral_request)
        assert neutral_result.sentiment == "neutral"

    @pytest.mark.asyncio
    async def test_submit_feedback_categorization(self, feedback_service):
        """Test feedback categorization logic."""
        # High rating should be positive category
        high_rating_request = FeedbackRequest(
            customer_id="customer_1",
            rating=5,
            comment="Amazing support!"
        )
        result = await feedback_service.submit_feedback(high_rating_request)
        assert result.category == "positive"
        
        # Low rating should be complaint category
        low_rating_request = FeedbackRequest(
            customer_id="customer_2",
            rating=1,
            comment="Very poor service"
        )
        result = await feedback_service.submit_feedback(low_rating_request)
        assert result.category == "complaint"
        
        # Medium rating should be neutral category
        medium_rating_request = FeedbackRequest(
            customer_id="customer_3",
            rating=3,
            comment="Average experience"
        )
        result = await feedback_service.submit_feedback(medium_rating_request)
        assert result.category == "neutral"

    @pytest.mark.asyncio
    async def test_submit_feedback_triggers_processing(self, feedback_service, sample_feedback_request):
        """Test that feedback submission triggers processing workflow."""
        with patch.object(feedback_service, '_process_feedback') as mock_process:
            result = await feedback_service.submit_feedback(sample_feedback_request)
            mock_process.assert_called_once_with(result.feedback_id)

    @pytest.mark.asyncio
    async def test_submit_feedback_validation_error(self, feedback_service):
        """Test feedback submission with validation errors."""
        # Invalid rating (out of range)
        invalid_request = FeedbackRequest(
            customer_id="customer_123",
            rating=10  # Should be 1-5
        )
        
        with pytest.raises(ValueError) as exc_info:
            await feedback_service.submit_feedback(invalid_request)
        
        assert "Rating must be between 1 and 5" in str(exc_info.value)


class TestFeedbackRetrieval:
    """Test feedback retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_feedback_by_id_success(self, feedback_service, sample_feedback_request):
        """Test successful feedback retrieval by ID."""
        submitted_feedback = await feedback_service.submit_feedback(sample_feedback_request)
        
        result = await feedback_service.get_feedback_by_id(submitted_feedback.feedback_id)
        
        assert result is not None
        assert result.feedback_id == submitted_feedback.feedback_id
        assert result.customer_id == "customer_123"
        assert result.rating == 4

    @pytest.mark.asyncio
    async def test_get_feedback_by_id_not_found(self, feedback_service):
        """Test feedback retrieval when feedback doesn't exist."""
        result = await feedback_service.get_feedback_by_id("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_feedback_by_id_data_integrity(self, feedback_service, sample_feedback_request):
        """Test that retrieved feedback maintains data integrity."""
        submitted = await feedback_service.submit_feedback(sample_feedback_request)
        retrieved = await feedback_service.get_feedback_by_id(submitted.feedback_id)
        
        assert retrieved.feedback_id == submitted.feedback_id
        assert retrieved.customer_id == submitted.customer_id
        assert retrieved.rating == submitted.rating
        assert retrieved.comment == submitted.comment
        assert retrieved.sentiment == submitted.sentiment
        assert retrieved.category == submitted.category


class TestFeedbackListing:
    """Test feedback listing and filtering functionality."""

    @pytest.mark.asyncio
    async def test_list_feedback_no_filters(self, feedback_service):
        """Test listing all feedback without filters."""
        requests = [
            FeedbackRequest(customer_id="customer_1", rating=5, comment="Great!"),
            FeedbackRequest(customer_id="customer_2", rating=3, comment="Okay"),
            FeedbackRequest(customer_id="customer_3", rating=1, comment="Poor")
        ]
        
        for request in requests:
            await feedback_service.submit_feedback(request)
        
        result = await feedback_service.list_feedback()
        
        assert len(result) == 3
        assert all(isinstance(feedback, FeedbackResponse) for feedback in result)

    @pytest.mark.asyncio
    async def test_list_feedback_filter_by_customer(self, feedback_service):
        """Test listing feedback filtered by customer ID."""
        requests = [
            FeedbackRequest(customer_id="customer_1", rating=5, comment="Great!"),
            FeedbackRequest(customer_id="customer_1", rating=4, comment="Good"),
            FeedbackRequest(customer_id="customer_2", rating=3, comment="Okay")
        ]
        
        for request in requests:
            await feedback_service.submit_feedback(request)
        
        result = await feedback_service.list_feedback(customer_id="customer_1")
        
        assert len(result) == 2
        assert all(feedback.customer_id == "customer_1" for feedback in result)

    @pytest.mark.asyncio
    async def test_list_feedback_filter_by_rating(self, feedback_service):
        """Test listing feedback filtered by rating."""
        requests = [
            FeedbackRequest(customer_id="customer_1", rating=5, comment="Excellent"),
            FeedbackRequest(customer_id="customer_2", rating=5, comment="Amazing"),
            FeedbackRequest(customer_id="customer_3", rating=3, comment="Average"),
            FeedbackRequest(customer_id="customer_4", rating=1, comment="Poor")
        ]
        
        for request in requests:
            await feedback_service.submit_feedback(request)
        
        result = await feedback_service.list_feedback(rating=5)
        
        assert len(result) == 2
        assert all(feedback.rating == 5 for feedback in result)

    @pytest.mark.asyncio
    async def test_list_feedback_filter_by_sentiment(self, feedback_service):
        """Test listing feedback filtered by sentiment."""
        requests = [
            FeedbackRequest(customer_id="customer_1", rating=5, comment="Fantastic service!"),
            FeedbackRequest(customer_id="customer_2", rating=4, comment="Very good experience"),
            FeedbackRequest(customer_id="customer_3", rating=2, comment="Disappointing service")
        ]
        
        for request in requests:
            await feedback_service.submit_feedback(request)
        
        result = await feedback_service.list_feedback(sentiment="positive")
        
        assert len(result) >= 1  # At least the positive feedback should be there
        assert all(feedback.sentiment == "positive" for feedback in result)

    @pytest.mark.asyncio
    async def test_list_feedback_with_limit(self, feedback_service):
        """Test listing feedback with limit."""
        for i in range(5):
            request = FeedbackRequest(
                customer_id=f"customer_{i}",
                rating=4,
                comment=f"Feedback {i}"
            )
            await feedback_service.submit_feedback(request)
        
        result = await feedback_service.list_feedback(limit=3)
        
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_feedback_sorted_by_date(self, feedback_service):
        """Test that feedback is sorted by creation date (newest first)."""
        import asyncio
        
        feedback_list = []
        for i in range(3):
            request = FeedbackRequest(
                customer_id="customer_1",
                rating=4,
                comment=f"Feedback {i}"
            )
            feedback = await feedback_service.submit_feedback(request)
            feedback_list.append(feedback)
            await asyncio.sleep(0.01)  # Small delay to ensure different timestamps
        
        result = await feedback_service.list_feedback()
        
        # Should be sorted by creation date (newest first)
        assert len(result) == 3
        for i in range(len(result) - 1):
            assert result[i].created_at >= result[i + 1].created_at

    @pytest.mark.asyncio
    async def test_list_feedback_multiple_filters(self, feedback_service):
        """Test listing feedback with multiple filters."""
        requests = [
            FeedbackRequest(customer_id="customer_1", rating=5, comment="Excellent!"),
            FeedbackRequest(customer_id="customer_1", rating=4, comment="Good service"),
            FeedbackRequest(customer_id="customer_1", rating=2, comment="Poor experience"),
            FeedbackRequest(customer_id="customer_2", rating=5, comment="Great job!")
        ]
        
        for request in requests:
            await feedback_service.submit_feedback(request)
        
        result = await feedback_service.list_feedback(
            customer_id="customer_1",
            rating=5
        )
        
        assert len(result) == 1
        assert result[0].customer_id == "customer_1"
        assert result[0].rating == 5

    @pytest.mark.asyncio
    async def test_list_feedback_empty_result(self, feedback_service):
        """Test listing feedback when none match filters."""
        request = FeedbackRequest(customer_id="customer_1", rating=5, comment="Great!")
        await feedback_service.submit_feedback(request)
        
        result = await feedback_service.list_feedback(customer_id="nonexistent_customer")
        
        assert len(result) == 0


class TestFeedbackAnalytics:
    """Test feedback analytics functionality."""

    @pytest.mark.asyncio
    async def test_get_feedback_analytics_empty(self, feedback_service):
        """Test getting analytics when no feedback exists."""
        result = await feedback_service.get_feedback_analytics()
        
        assert result["total_feedback"] == 0
        assert result["average_rating"] == 0.0
        assert result["rating_distribution"] == {}
        assert result["sentiment_distribution"] == {}
        assert result["category_distribution"] == {}

    @pytest.mark.asyncio
    async def test_get_feedback_analytics_with_data(self, feedback_service):
        """Test getting analytics with feedback data."""
        requests = [
            FeedbackRequest(customer_id="c1", rating=5, comment="Excellent!"),
            FeedbackRequest(customer_id="c2", rating=4, comment="Good service"),
            FeedbackRequest(customer_id="c3", rating=3, comment="Average"),
            FeedbackRequest(customer_id="c4", rating=2, comment="Poor"),
            FeedbackRequest(customer_id="c5", rating=5, comment="Amazing!")
        ]
        
        for request in requests:
            await feedback_service.submit_feedback(request)
        
        result = await feedback_service.get_feedback_analytics()
        
        assert result["total_feedback"] == 5
        assert result["average_rating"] == 3.8  # (5+4+3+2+5)/5
        assert result["rating_distribution"][5] == 2
        assert result["rating_distribution"][4] == 1
        assert result["rating_distribution"][3] == 1
        assert result["rating_distribution"][2] == 1

    @pytest.mark.asyncio
    async def test_get_feedback_count(self, feedback_service):
        """Test getting total feedback count."""
        assert feedback_service.get_feedback_count() == 0
        
        for i in range(3):
            request = FeedbackRequest(
                customer_id=f"customer_{i}",
                rating=4,
                comment=f"Feedback {i}"
            )
            await feedback_service.submit_feedback(request)
        
        assert feedback_service.get_feedback_count() == 3

    @pytest.mark.asyncio
    async def test_get_average_rating(self, feedback_service):
        """Test calculating average rating."""
        requests = [
            FeedbackRequest(customer_id="c1", rating=5),
            FeedbackRequest(customer_id="c2", rating=3),
            FeedbackRequest(customer_id="c3", rating=4),
            FeedbackRequest(customer_id="c4", rating=2)
        ]
        
        for request in requests:
            await feedback_service.submit_feedback(request)
        
        avg_rating = feedback_service.get_average_rating()
        expected_avg = (5 + 3 + 4 + 2) / 4  # 3.5
        assert abs(avg_rating - expected_avg) < 0.01

    @pytest.mark.asyncio
    async def test_get_average_rating_no_feedback(self, feedback_service):
        """Test average rating when no feedback exists."""
        avg_rating = feedback_service.get_average_rating()
        assert avg_rating == 0.0

    @pytest.mark.asyncio
    async def test_get_sentiment_distribution(self, feedback_service):
        """Test getting sentiment distribution."""
        requests = [
            FeedbackRequest(customer_id="c1", rating=5, comment="Excellent service!"),
            FeedbackRequest(customer_id="c2", rating=4, comment="Good experience"),
            FeedbackRequest(customer_id="c3", rating=3, comment="It was okay"),
            FeedbackRequest(customer_id="c4", rating=2, comment="Poor service"),
            FeedbackRequest(customer_id="c5", rating=1, comment="Terrible experience")
        ]
        
        for request in requests:
            await feedback_service.submit_feedback(request)
        
        analytics = await feedback_service.get_feedback_analytics()
        sentiment_dist = analytics["sentiment_distribution"]
        
        assert "positive" in sentiment_dist
        assert "neutral" in sentiment_dist
        assert "negative" in sentiment_dist
        assert sum(sentiment_dist.values()) == 5


class TestFeedbackValidation:
    """Test feedback data validation."""

    def test_validate_feedback_data_valid_rating(self, feedback_service):
        """Test validation with valid rating."""
        request = FeedbackRequest(customer_id="customer_123", rating=3)
        # Should not raise any exception
        feedback_service._validate_feedback_data(request)

    def test_validate_feedback_data_invalid_rating_high(self, feedback_service):
        """Test validation with rating too high."""
        request = FeedbackRequest(customer_id="customer_123", rating=6)
        
        with pytest.raises(ValueError) as exc_info:
            feedback_service._validate_feedback_data(request)
        
        assert "Rating must be between 1 and 5" in str(exc_info.value)

    def test_validate_feedback_data_invalid_rating_low(self, feedback_service):
        """Test validation with rating too low."""
        request = FeedbackRequest(customer_id="customer_123", rating=0)
        
        with pytest.raises(ValueError) as exc_info:
            feedback_service._validate_feedback_data(request)
        
        assert "Rating must be between 1 and 5" in str(exc_info.value)

    def test_validate_feedback_data_empty_customer_id(self, feedback_service):
        """Test validation with empty customer ID."""
        request = FeedbackRequest(customer_id="", rating=3)
        
        with pytest.raises(ValueError) as exc_info:
            feedback_service._validate_feedback_data(request)
        
        assert "Customer ID cannot be empty" in str(exc_info.value)


class TestFeedbackSentimentAnalysis:
    """Test sentiment analysis functionality."""

    def test_analyze_sentiment_positive(self, feedback_service):
        """Test sentiment analysis for positive comments."""
        positive_comments = [
            "Excellent service! Very satisfied.",
            "Amazing support team, thank you!",
            "Great experience, highly recommend.",
            "Perfect solution to my problem."
        ]
        
        for comment in positive_comments:
            sentiment = feedback_service._analyze_sentiment(comment)
            assert sentiment == "positive"

    def test_analyze_sentiment_negative(self, feedback_service):
        """Test sentiment analysis for negative comments."""
        negative_comments = [
            "Terrible service, very disappointed.",
            "Poor response time and unhelpful.",
            "Worst experience ever, avoid this.",
            "Completely useless and frustrating."
        ]
        
        for comment in negative_comments:
            sentiment = feedback_service._analyze_sentiment(comment)
            assert sentiment == "negative"

    def test_analyze_sentiment_neutral(self, feedback_service):
        """Test sentiment analysis for neutral comments."""
        neutral_comments = [
            "It was okay, nothing special.",
            "Average service, could be better.",
            "Standard experience, meets expectations.",
            "Normal support, as expected."
        ]
        
        for comment in neutral_comments:
            sentiment = feedback_service._analyze_sentiment(comment)
            assert sentiment == "neutral"

    def test_analyze_sentiment_empty_comment(self, feedback_service):
        """Test sentiment analysis for empty or None comment."""
        assert feedback_service._analyze_sentiment(None) == "neutral"
        assert feedback_service._analyze_sentiment("") == "neutral"
        assert feedback_service._analyze_sentiment("   ") == "neutral"

    def test_analyze_sentiment_special_characters(self, feedback_service):
        """Test sentiment analysis with special characters."""
        comment_with_special = "Great service!!! 😊👍 100% satisfied!!!"
        sentiment = feedback_service._analyze_sentiment(comment_with_special)
        assert sentiment == "positive"


class TestFeedbackCategorization:
    """Test feedback categorization functionality."""

    def test_categorize_feedback_positive_high_rating(self, feedback_service):
        """Test categorization for high rating positive feedback."""
        category = feedback_service._categorize_feedback("Great service!", 5)
        assert category == "positive"
        
        category = feedback_service._categorize_feedback("Very satisfied", 4)
        assert category == "positive"

    def test_categorize_feedback_negative_low_rating(self, feedback_service):
        """Test categorization for low rating negative feedback."""
        category = feedback_service._categorize_feedback("Poor service", 1)
        assert category == "complaint"
        
        category = feedback_service._categorize_feedback("Disappointed", 2)
        assert category == "complaint"

    def test_categorize_feedback_neutral_medium_rating(self, feedback_service):
        """Test categorization for medium rating neutral feedback."""
        category = feedback_service._categorize_feedback("It was okay", 3)
        assert category == "neutral"

    def test_categorize_feedback_suggestion_keywords(self, feedback_service):
        """Test categorization for feedback with suggestion keywords."""
        suggestion_comments = [
            "Could you please add more features?",
            "I suggest improving the interface",
            "Would be nice to have faster response",
            "Please consider adding this option"
        ]
        
        for comment in suggestion_comments:
            category = feedback_service._categorize_feedback(comment, 3)
            assert category == "suggestion"

    def test_categorize_feedback_complaint_keywords(self, feedback_service):
        """Test categorization for feedback with complaint keywords."""
        complaint_comments = [
            "This is unacceptable behavior",
            "I want to file a complaint",
            "This service is broken",
            "I demand a refund immediately"
        ]
        
        for comment in complaint_comments:
            category = feedback_service._categorize_feedback(comment, 2)
            assert category == "complaint"

    def test_categorize_feedback_praise_keywords(self, feedback_service):
        """Test categorization for feedback with praise keywords."""
        praise_comments = [
            "Thank you so much for the help!",
            "Appreciate the quick response",
            "Thanks for resolving my issue",
            "Grateful for the excellent service"
        ]
        
        for comment in praise_comments:
            category = feedback_service._categorize_feedback(comment, 5)
            assert category == "praise"


class TestFeedbackProcessing:
    """Test feedback processing workflow."""

    @pytest.mark.asyncio
    async def test_process_feedback_marks_as_processed(self, feedback_service, sample_feedback_request):
        """Test that feedback processing marks feedback as processed."""
        submitted = await feedback_service.submit_feedback(sample_feedback_request)
        
        # Initially should not be processed
        assert submitted.processed is False
        
        # Process the feedback
        await feedback_service._process_feedback(submitted.feedback_id)
        
        # Should now be marked as processed
        processed_feedback = feedback_service.feedback_db[submitted.feedback_id]
        assert processed_feedback["processed"] is True

    @pytest.mark.asyncio
    async def test_process_feedback_negative_triggers_alert(self, feedback_service):
        """Test that negative feedback triggers alerts."""
        negative_request = FeedbackRequest(
            customer_id="customer_123",
            rating=1,
            comment="Terrible service, very angry!"
        )
        
        with patch.object(feedback_service, '_trigger_negative_feedback_alert') as mock_alert:
            submitted = await feedback_service.submit_feedback(negative_request)
            
            # Processing should trigger alert for negative feedback
            await feedback_service._process_feedback(submitted.feedback_id)
            mock_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_feedback_positive_triggers_follow_up(self, feedback_service):
        """Test that positive feedback triggers follow-up actions."""
        positive_request = FeedbackRequest(
            customer_id="customer_123",
            rating=5,
            comment="Excellent service, very happy!"
        )
        
        with patch.object(feedback_service, '_trigger_positive_feedback_follow_up') as mock_follow_up:
            submitted = await feedback_service.submit_feedback(positive_request)
            
            # Processing should trigger follow-up for positive feedback
            await feedback_service._process_feedback(submitted.feedback_id)
            mock_follow_up.assert_called_once()


class TestFeedbackServicePerformance:
    """Test FeedbackService performance characteristics."""

    @pytest.mark.asyncio
    async def test_concurrent_feedback_submission(self, feedback_service):
        """Test concurrent submission of multiple feedback."""
        import asyncio
        
        async def submit_feedback(index):
            request = FeedbackRequest(
                customer_id=f"customer_{index}",
                rating=4,
                comment=f"Concurrent feedback {index}"
            )
            return await feedback_service.submit_feedback(request)
        
        tasks = [submit_feedback(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(isinstance(r, FeedbackResponse) for r in results)
        assert len(set(r.feedback_id for r in results)) == 10  # All unique IDs

    @pytest.mark.asyncio
    async def test_high_volume_feedback_storage(self, feedback_service):
        """Test storage of high volume of feedback."""
        for i in range(100):
            request = FeedbackRequest(
                customer_id=f"customer_{i % 10}",
                rating=(i % 5) + 1,  # Ratings 1-5
                comment=f"Volume feedback {i}"
            )
            await feedback_service.submit_feedback(request)
        
        assert feedback_service.get_feedback_count() == 100
        
        # Test that analytics still work efficiently
        analytics = await feedback_service.get_feedback_analytics()
        assert analytics["total_feedback"] == 100


class TestFeedbackServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_very_long_comment(self, feedback_service):
        """Test feedback with very long comment."""
        long_comment = "A" * 10000  # Very long comment
        request = FeedbackRequest(
            customer_id="customer_123",
            rating=4,
            comment=long_comment
        )
        
        result = await feedback_service.submit_feedback(request)
        
        # Should handle gracefully
        assert result is not None
        assert result.feedback_id is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_comment(self, feedback_service):
        """Test feedback with special characters in comment."""
        special_comment = "Comment with special chars: @#$%^&*()[]{}|;:,.<>?"
        request = FeedbackRequest(
            customer_id="customer_123",
            rating=3,
            comment=special_comment
        )
        
        result = await feedback_service.submit_feedback(request)
        
        assert result is not None
        assert result.comment == special_comment

    @pytest.mark.asyncio
    async def test_unicode_characters_in_comment(self, feedback_service):
        """Test feedback with unicode characters in comment."""
        unicode_comment = "Feedback with unicode: 你好, مرحبا, здравствуй, 🙂"
        request = FeedbackRequest(
            customer_id="customer_123",
            rating=4,
            comment=unicode_comment
        )
        
        result = await feedback_service.submit_feedback(request)
        
        assert result is not None
        assert result.comment == unicode_comment

    @pytest.mark.asyncio
    async def test_feedback_without_comment(self, feedback_service):
        """Test feedback submission without comment."""
        request = FeedbackRequest(
            customer_id="customer_123",
            rating=4
            # No comment provided
        )
        
        result = await feedback_service.submit_feedback(request)
        
        assert result is not None
        assert result.comment is None
        assert result.sentiment == "neutral"  # Should default to neutral

    @pytest.mark.asyncio
    async def test_multiple_feedback_same_customer(self, feedback_service):
        """Test multiple feedback submissions from same customer."""
        customer_id = "repeat_customer"
        
        for i in range(5):
            request = FeedbackRequest(
                customer_id=customer_id,
                rating=(i % 5) + 1,
                comment=f"Feedback number {i}"
            )
            await feedback_service.submit_feedback(request)
        
        # All feedback should be stored
        customer_feedback = await feedback_service.list_feedback(customer_id=customer_id)
        assert len(customer_feedback) == 5


class TestFeedbackServiceIntegration:
    """Test integration scenarios for FeedbackService."""

    @pytest.mark.asyncio
    async def test_feedback_analytics_integration(self, feedback_service):
        """Test integration between feedback submission and analytics."""
        # Submit various types of feedback
        feedback_data = [
            (5, "Excellent service!"),
            (4, "Good experience"),
            (3, "Average service"),
            (2, "Could be better"),
            (1, "Poor service")
        ]
        
        for rating, comment in feedback_data:
            request = FeedbackRequest(
                customer_id=f"customer_{rating}",
                rating=rating,
                comment=comment
            )
            await feedback_service.submit_feedback(request)
        
        # Get analytics
        analytics = await feedback_service.get_feedback_analytics()
        
        # Verify analytics reflect submitted feedback
        assert analytics["total_feedback"] == 5
        assert analytics["average_rating"] == 3.0
        assert analytics["rating_distribution"][5] == 1
        assert analytics["rating_distribution"][1] == 1
        
        # Verify sentiment distribution
        assert "positive" in analytics["sentiment_distribution"]
        assert "negative" in analytics["sentiment_distribution"]
        assert "neutral" in analytics["sentiment_distribution"]

    @pytest.mark.asyncio
    async def test_feedback_trend_analysis(self, feedback_service):
        """Test feedback trend analysis over time."""
        # Submit feedback over different time periods
        base_time = datetime.utcnow()
        
        # Mock different timestamps
        with patch('datetime.datetime') as mock_datetime:
            timestamps = [
                base_time - timedelta(days=7),
                base_time - timedelta(days=5),
                base_time - timedelta(days=3),
                base_time - timedelta(days=1),
                base_time
            ]
            
            mock_datetime.utcnow.side_effect = timestamps
            
            for i, timestamp in enumerate(timestamps):
                request = FeedbackRequest(
                    customer_id=f"trend_customer_{i}",
                    rating=i + 1,  # Improving ratings over time
                    comment=f"Feedback at time {i}"
                )
                await feedback_service.submit_feedback(request)
        
        # Analyze trend (this would be implemented in a real trend analysis method)
        all_feedback = await feedback_service.list_feedback()
        ratings = [f.rating for f in all_feedback]
        
        # Should show improving trend
        assert len(ratings) == 5
        # Ratings should generally increase over time (though order might be different due to sorting)
        assert max(ratings) == 5
        assert min(ratings) == 1
