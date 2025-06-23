"""
Comprehensive unit tests for Database MCP Server
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from mcp.database_mcp_server import DatabaseMCPServer

class MockDBConnector:
    """Mock database connector for testing"""
    def __init__(self):
        self.connection = Mock()
        self.cursor_mock = Mock()
        self.connection.cursor.return_value.__enter__ = Mock(return_value=self.cursor_mock)
        self.connection.cursor.return_value.__exit__ = Mock(return_value=None)

class TestDatabaseMCPServer:
    """Test suite for Database MCP Server"""
    
    @pytest.fixture
    def mock_db_connector(self):
        return MockDBConnector()
    
    @pytest.fixture
    def db_mcp_server(self, mock_db_connector):
        return DatabaseMCPServer(mock_db_connector)
    
    @pytest.mark.asyncio
    async def test_initialization(self, db_mcp_server):
        """Test server initialization"""
        assert db_mcp_server.server_id == "mcp_database"
        assert db_mcp_server.name == "Database MCP Server"
        assert 'query_database' in db_mcp_server.tools
        assert 'get_customer_context' in db_mcp_server.tools
        assert 'db://customers' in db_mcp_server.resources
    
    @pytest.mark.asyncio
    async def test_start_server(self, db_mcp_server):
        """Test server startup"""
        await db_mcp_server.start()
        assert db_mcp_server.running is True
    
    @pytest.mark.asyncio
    async def test_query_database_tool(self, db_mcp_server, mock_db_connector):
        """Test query_database tool"""
        # Setup mock
        mock_db_connector.cursor_mock.fetchall.return_value = [
            {'id': 1, 'name': 'Test User'}
        ]
        
        # Test query
        result = await db_mcp_server.call_tool('query_database', {
            'query': 'SELECT * FROM users',
            'params': []
        })
        
        assert result['success'] is True
        assert len(result['data']) == 1
        assert result['data'][0]['name'] == 'Test User'
        mock_db_connector.cursor_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_database_without_query(self, db_mcp_server):
        """Test query_database tool without query parameter"""
        result = await db_mcp_server.call_tool('query_database', {})
        
        assert result['success'] is False
        assert 'Query parameter is required' in result['error']
    
    @pytest.mark.asyncio
    async def test_get_customer_context_tool(self, db_mcp_server, mock_db_connector):
        """Test get_customer_context tool"""
        # Setup mock
        mock_db_connector.cursor_mock.fetchone.return_value = {
            'customer_id': '123',
            'name': 'John Doe',
            'ticket_count': 5,
            'avg_satisfaction': 4.5
        }
        
        # Test customer context
        result = await db_mcp_server.call_tool('get_customer_context', {
            'customer_id': '123'
        })
        
        assert result['success'] is True
        assert result['customer_context']['customer_id'] == '123'
        assert result['customer_context']['ticket_count'] == 5
    
    @pytest.mark.asyncio
    async def test_search_knowledge_base_tool(self, db_mcp_server, mock_db_connector):
        """Test search_knowledge_base tool"""
        # Setup mock
        mock_db_connector.cursor_mock.fetchall.return_value = [
            {'id': 1, 'title': 'How to reset password', 'content': 'Steps to reset...'}
        ]
        
        # Test knowledge search
        result = await db_mcp_server.call_tool('search_knowledge_base', {
            'search_term': 'password',
            'limit': 10
        })
        
        assert result['success'] is True
        assert len(result['articles']) == 1
        assert 'password' in result['articles'][0]['title'].lower()
    
    @pytest.mark.asyncio
    async def test_save_interaction_tool(self, db_mcp_server, mock_db_connector):
        """Test save_interaction tool"""
        interaction_data = {
            'query_id': 'q123',
            'customer_id': 'c456',
            'query_text': 'How to reset password?',
            'agent_response': 'Here are the steps...',
            'created_at': '2025-06-23T10:00:00'
        }
        
        result = await db_mcp_server.call_tool('save_interaction', {
            'interaction_data': interaction_data
        })
        
        assert result['success'] is True
        assert 'saved successfully' in result['message']
        mock_db_connector.cursor_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_analytics_tool(self, db_mcp_server, mock_db_connector):
        """Test get_analytics tool"""
        # Setup mock
        mock_db_connector.cursor_mock.fetchone.return_value = {
            'total_queries': 100,
            'avg_satisfaction': 4.2,
            'unique_customers': 75
        }
        
        result = await db_mcp_server.call_tool('get_analytics', {
            'time_period': '7 days'
        })
        
        assert result['success'] is True
        assert result['analytics']['total_queries'] == 100
        assert result['analytics']['avg_satisfaction'] == 4.2
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self, db_mcp_server):
        """Test handling of unknown tools"""
        result = await db_mcp_server.call_tool('unknown_tool', {})
        
        assert result['success'] is False
        assert 'Unknown tool' in result['error']
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, db_mcp_server, mock_db_connector):
        """Test database error handling"""
        # Setup mock to raise exception
        mock_db_connector.cursor_mock.execute.side_effect = Exception("Database connection failed")
        
        result = await db_mcp_server.call_tool('query_database', {
            'query': 'SELECT * FROM users'
        })
        
        assert result['success'] is False
        assert 'Database connection failed' in result['error']
    
    @pytest.mark.asyncio
    async def test_get_resource_customers(self, db_mcp_server, mock_db_connector):
        """Test getting customers resource"""
        # Setup mock
        mock_db_connector.cursor_mock.fetchall.return_value = [
            {'id': 1, 'name': 'Customer 1'},
            {'id': 2, 'name': 'Customer 2'}
        ]
        
        result = await db_mcp_server.get_resource('db://customers')
        
        assert result['success'] is True
        assert len(result['contents']) == 1
        assert result['contents'][0]['mimeType'] == 'application/json'
    
    @pytest.mark.asyncio
    async def test_get_unknown_resource(self, db_mcp_server):
        """Test getting unknown resource"""
        result = await db_mcp_server.get_resource('db://unknown')
        
        assert result['success'] is False
        assert 'Unknown resource' in result['error']
    
    @pytest.mark.asyncio
    async def test_tool_definitions(self, db_mcp_server):
        """Test tool definitions"""
        query_def = await db_mcp_server._get_tool_definition('query_database')
        
        assert query_def is not None
        assert query_def['name'] == 'query_database'
        assert 'inputSchema' in query_def
        assert 'query' in query_def['inputSchema']['properties']
    
    @pytest.mark.asyncio
    async def test_no_database_connection(self):
        """Test behavior when no database connection is available"""
        server = DatabaseMCPServer(None)
        
        result = await server.call_tool('query_database', {'query': 'SELECT 1'})
        
        assert result['success'] is False
        assert 'Database connection not available' in result['error']
