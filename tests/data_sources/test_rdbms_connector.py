"""
Comprehensive tests for EnhancedRDBMSConnector data source component.
"""
import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
from src.data_sources.rdbms_connector import EnhancedRDBMSConnector


class TestEnhancedRDBMSConnector:
    """Test EnhancedRDBMSConnector functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock database configuration."""
        return {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_customer_support',
            'user': 'test_user',
            'password': 'test_password'
        }

    @pytest.fixture
    def db_connector(self, mock_config):
        """Create EnhancedRDBMSConnector instance with mock config."""
        with patch('src.data_sources.rdbms_connector.psycopg2.connect'):
            connector = EnhancedRDBMSConnector()
            connector.config = mock_config
            return connector

    def test_connector_initialization(self, db_connector):
        """Test connector initialization."""
        assert db_connector.connection is None  # Before connect
        assert db_connector.connected is False
        assert hasattr(db_connector, 'logger')

    @pytest.mark.asyncio
    async def test_connect_success(self, db_connector):
        """Test successful database connection."""
        mock_connection = Mock()
        
        with patch('src.data_sources.rdbms_connector.psycopg2.connect', return_value=mock_connection):
            await db_connector.connect()
            
            assert db_connector.connected is True
            assert db_connector.connection == mock_connection

    @pytest.mark.asyncio
    async def test_connect_failure(self, db_connector):
        """Test database connection failure."""
        with patch('src.data_sources.rdbms_connector.psycopg2.connect', side_effect=Exception("Connection failed")):
            
            with pytest.raises(Exception, match="Connection failed"):
                await db_connector.connect()
            
            assert db_connector.connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self, db_connector):
        """Test database disconnection."""
        # Mock connected state
        mock_connection = Mock()
        db_connector.connection = mock_connection
        db_connector.connected = True
        
        await db_connector.disconnect()
        
        assert db_connector.connected is False
        mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_customer(self, db_connector):
        """Test creating a new customer."""
        # Mock connection and cursor
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'customer_id': 'CUST_123'}
        
        db_connector.connection = mock_connection
        db_connector.connected = True
        
        customer_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1234567890'
        }
        
        result = await db_connector.create_customer(customer_data)
        
        assert result == 'CUST_123'
        mock_cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_customer_by_id(self, db_connector):
        """Test retrieving customer by ID."""
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_customer_data = {
            'customer_id': 'CUST_123',
            'name': 'John Doe',
            'email': 'john@example.com',
            'created_at': datetime.now()
        }
        mock_cursor.fetchone.return_value = mock_customer_data
        
        db_connector.connection = mock_connection
        db_connector.connected = True
        
        result = await db_connector.get_customer_by_id('CUST_123')
        
        assert result == mock_customer_data
        mock_cursor.execute.assert_called_with(
            pytest.approx("SELECT * FROM customers WHERE customer_id = %s", abs=0),
            ('CUST_123',)
        )

    @pytest.mark.asyncio
    async def test_create_ticket(self, db_connector):
        """Test creating a support ticket."""
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'ticket_id': 'TKT_456'}
        
        db_connector.connection = mock_connection
        db_connector.connected = True
        
        ticket_data = {
            'customer_id': 'CUST_123',
            'title': 'Login Issue',
            'description': 'Cannot access my account',
            'priority': 'high'
        }
        
        result = await db_connector.create_ticket(ticket_data)
        
        assert result == 'TKT_456'
        mock_cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_update_ticket_status(self, db_connector):
        """Test updating ticket status."""
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        db_connector.connection = mock_connection
        db_connector.connected = True
        
        result = await db_connector.update_ticket_status('TKT_456', 'resolved')
        
        assert result is True
        mock_cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_search_knowledge_base(self, db_connector):
        """Test searching knowledge base."""
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_articles = [
            {
                'article_id': 'KB_001',
                'title': 'Password Reset Guide',
                'content': 'How to reset your password...',
                'relevance_score': 0.95
            }
        ]
        mock_cursor.fetchall.return_value = mock_articles
        
        db_connector.connection = mock_connection
        db_connector.connected = True
        
        results = await db_connector.search_knowledge_base('password reset', limit=10)
        
        assert len(results) == 1
        assert results[0]['article_id'] == 'KB_001'
        mock_cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_save_query_interaction(self, db_connector):
        """Test saving query interaction data."""
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'query_id': 'QRY_789'}
        
        db_connector.connection = mock_connection
        db_connector.connected = True
        
        interaction_data = {
            'query_text': 'How do I reset my password?',
            'customer_id': 'CUST_123',
            'query_type': 'question',
            'sentiment': 'neutral',
            'response_text': 'You can reset your password...'
        }
        
        result = await db_connector.save_query_interaction(interaction_data)
        
        assert result == 'QRY_789'
        mock_cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_save_agent_performance(self, db_connector):
        """Test saving agent performance metrics."""
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        db_connector.connection = mock_connection
        db_connector.connected = True
        
        performance_data = {
            'agent_id': 'agent_001',
            'agent_type': 'query',
            'fitness_score': 0.89,
            'success_rate': 0.95,
            'customer_satisfaction_avg': 4.2,
            'queries_processed': 150
        }
        
        result = await db_connector.save_agent_performance(performance_data)
        
        assert result is True
        mock_cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_system_analytics(self, db_connector):
        """Test getting system analytics."""
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock analytics data
        mock_ticket_metrics = {
            'total_tickets': 500,
            'resolved_tickets': 450,
            'avg_satisfaction': 4.1,
            'avg_resolution_hours': 24.5
        }
        
        mock_ai_performance = [
            {
                'agent_id': 'agent_001',
                'agent_type': 'query',
                'avg_fitness': 0.89,
                'avg_success_rate': 0.95
            }
        ]
        
        mock_cursor.fetchone.return_value = mock_ticket_metrics
        mock_cursor.fetchall.return_value = mock_ai_performance
        
        db_connector.connection = mock_connection
        db_connector.connected = True
        
        analytics = await db_connector.get_system_analytics(days=30)
        
        assert 'ticket_metrics' in analytics
        assert 'ai_performance' in analytics
        assert analytics['ticket_metrics']['total_tickets'] == 500

    @pytest.mark.asyncio
    async def test_get_trending_issues(self, db_connector):
        """Test getting trending issues."""
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_trending = [
            {
                'issue_category': 'login_problems',
                'ticket_count': 25,
                'trend_score': 0.85
            },
            {
                'issue_category': 'billing_questions',
                'ticket_count': 18,
                'trend_score': 0.72
            }
        ]
        mock_cursor.fetchall.return_value = mock_trending
        
        db_connector.connection = mock_connection
        db_connector.connected = True
        
        trends = await db_connector.get_trending_issues(days=7, limit=10)
        
        assert len(trends) == 2
        assert trends[0]['issue_category'] == 'login_problems'
        mock_cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_operation_not_connected(self, db_connector):
        """Test operations when not connected to database."""
        db_connector.connected = False
        
        # Test various operations
        customer_result = await db_connector.create_customer({'name': 'Test'})
        ticket_result = await db_connector.create_ticket({'title': 'Test'})
        
        assert customer_result is None
        assert ticket_result is None


@pytest.mark.integration
class TestEnhancedRDBMSConnectorIntegration:
    """Integration tests for EnhancedRDBMSConnector."""

    @pytest.mark.asyncio
    async def test_connection_workflow(self):
        """Test complete connection workflow with mocked database."""
        connector = EnhancedRDBMSConnector()
        
        with patch('src.data_sources.rdbms_connector.psycopg2.connect') as mock_connect:
            mock_connection = Mock()
            mock_connect.return_value = mock_connection
            
            # Test connection
            await connector.connect()
            assert connector.connected is True
            
            # Test disconnection
            await connector.disconnect()
            assert connector.connected is False

    @pytest.mark.asyncio
    async def test_customer_ticket_workflow(self):
        """Test customer and ticket creation workflow."""
        connector = EnhancedRDBMSConnector()
        
        with patch('src.data_sources.rdbms_connector.psycopg2.connect'):
            mock_cursor = Mock()
            mock_connection = Mock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            connector.connection = mock_connection
            connector.connected = True
            
            # Mock customer creation
            mock_cursor.fetchone.side_effect = [
                {'customer_id': 'CUST_123'},  # Customer creation
                {'ticket_id': 'TKT_456'}      # Ticket creation
            ]
            
            # Create customer
            customer_id = await connector.create_customer({
                'name': 'Test Customer',
                'email': 'test@example.com'
            })
            
            # Create ticket for customer
            ticket_id = await connector.create_ticket({
                'customer_id': customer_id,
                'title': 'Test Issue',
                'description': 'Test description'
            })
            
            assert customer_id == 'CUST_123'
            assert ticket_id == 'TKT_456'
            assert mock_cursor.execute.call_count == 2


@pytest.mark.performance
class TestEnhancedRDBMSConnectorPerformance:
    """Performance tests for EnhancedRDBMSConnector."""

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self):
        """Test performance of bulk database operations."""
        import time
        
        connector = EnhancedRDBMSConnector()
        
        with patch('src.data_sources.rdbms_connector.psycopg2.connect'):
            mock_cursor = Mock()
            mock_connection = Mock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            connector.connection = mock_connection
            connector.connected = True
            
            # Mock successful operations
            mock_cursor.fetchone.return_value = {'customer_id': 'CUST_123'}
            
            # Time bulk customer creation
            start_time = time.time()
            
            for i in range(100):
                await connector.create_customer({
                    'name': f'Customer {i}',
                    'email': f'customer{i}@example.com'
                })
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            assert processing_time < 5.0  # Should complete within 5 seconds
            assert mock_cursor.execute.call_count == 100
            
            operations_per_second = 100 / processing_time
            assert operations_per_second > 20  # At least 20 operations per second
