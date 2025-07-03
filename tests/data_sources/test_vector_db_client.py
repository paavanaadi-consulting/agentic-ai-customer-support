"""
Comprehensive tests for VectorDBClient data source component.
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from src.data_sources.vector_db_client import VectorDBClient


class TestVectorDBClient:
    """Test VectorDBClient functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for vector database."""
        return {
            'host': 'localhost',
            'port': 6333,
            'collection_name': 'test_collection'
        }

    @pytest.fixture
    def vector_client(self, mock_config):
        """Create VectorDBClient instance with mock config."""
        return VectorDBClient(mock_config)

    def test_vector_client_initialization(self, vector_client, mock_config):
        """Test VectorDBClient initialization."""
        assert vector_client.config == mock_config
        assert vector_client.client is None  # Before connection
        assert vector_client.encoder is None  # Before connection
        assert vector_client.collection_name == 'test_collection'
        assert vector_client.connected is False

    @pytest.mark.asyncio
    async def test_connect_success(self, vector_client):
        """Test successful connection to vector database."""
        with patch('src.data_sources.vector_db_client.QdrantClient') as mock_qdrant:
            with patch('src.data_sources.vector_db_client.SentenceTransformer') as mock_encoder:
                with patch.object(vector_client, '_ensure_collection_exists', new_callable=AsyncMock):
                    
                    await vector_client.connect()
                    
                    assert vector_client.connected is True
                    mock_qdrant.assert_called_once()
                    mock_encoder.assert_called_once_with('all-MiniLM-L6-v2')

    @pytest.mark.asyncio
    async def test_connect_failure(self, vector_client):
        """Test connection failure handling."""
        with patch('src.data_sources.vector_db_client.QdrantClient', side_effect=Exception("Connection failed")):
            
            with pytest.raises(Exception, match="Connection failed"):
                await vector_client.connect()
            
            assert vector_client.connected is False

    @pytest.mark.asyncio
    async def test_add_documents(self, vector_client):
        """Test adding documents to vector database."""
        # Mock successful connection
        vector_client.connected = True
        vector_client.client = Mock()
        vector_client.encoder = Mock()
        vector_client.encoder.encode.return_value = [[0.1, 0.2, 0.3]]  # Mock embedding
        
        documents = [
            {"id": "doc1", "text": "This is a test document", "metadata": {"type": "test"}}
        ]
        
        result = await vector_client.add_documents(documents)
        
        assert result is True
        vector_client.encoder.encode.assert_called_once_with(["This is a test document"])

    @pytest.mark.asyncio
    async def test_add_documents_not_connected(self, vector_client):
        """Test adding documents when not connected."""
        documents = [{"id": "doc1", "text": "test"}]
        
        result = await vector_client.add_documents(documents)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_search_documents(self, vector_client):
        """Test searching documents in vector database."""
        # Mock successful connection and search
        vector_client.connected = True
        vector_client.client = Mock()
        vector_client.encoder = Mock()
        vector_client.encoder.encode.return_value = [0.1, 0.2, 0.3]  # Mock query embedding
        
        # Mock search results
        mock_search_result = Mock()
        mock_search_result.id = "doc1"
        mock_search_result.score = 0.95
        mock_search_result.payload = {"text": "Test document", "metadata": {"type": "test"}}
        
        vector_client.client.search.return_value = [mock_search_result]
        
        results = await vector_client.search("test query", limit=5)
        
        assert len(results) == 1
        assert results[0]["id"] == "doc1"
        assert results[0]["score"] == 0.95
        assert "text" in results[0]

    @pytest.mark.asyncio
    async def test_search_not_connected(self, vector_client):
        """Test searching when not connected."""
        results = await vector_client.search("test query")
        
        assert results == []

    @pytest.mark.asyncio
    async def test_get_collection_info(self, vector_client):
        """Test getting collection information."""
        vector_client.connected = True
        vector_client.client = Mock()
        
        # Mock collection info
        mock_info = Mock()
        mock_info.points_count = 100
        mock_info.vectors_count = 100
        vector_client.client.get_collection.return_value = mock_info
        
        info = await vector_client.get_collection_info()
        
        assert info["points_count"] == 100
        assert info["vectors_count"] == 100

    @pytest.mark.asyncio
    async def test_delete_documents(self, vector_client):
        """Test deleting documents from vector database."""
        vector_client.connected = True
        vector_client.client = Mock()
        
        result = await vector_client.delete_documents(["doc1", "doc2"])
        
        assert result is True
        vector_client.client.delete.assert_called_once()

    def test_config_validation(self):
        """Test configuration validation."""
        # Missing required fields
        invalid_config = {'host': 'localhost'}
        
        client = VectorDBClient(invalid_config)
        # Should not raise exception during initialization
        assert client.config == invalid_config


@pytest.mark.integration
class TestVectorDBClientIntegration:
    """Integration tests for VectorDBClient."""

    @pytest.mark.asyncio
    async def test_full_workflow_mock(self):
        """Test complete workflow with mocked dependencies."""
        config = {
            'host': 'localhost',
            'port': 6333,
            'collection_name': 'integration_test'
        }
        
        client = VectorDBClient(config)
        
        with patch('src.data_sources.vector_db_client.QdrantClient'):
            with patch('src.data_sources.vector_db_client.SentenceTransformer'):
                with patch.object(client, '_ensure_collection_exists', new_callable=AsyncMock):
                    
                    # Test connection
                    await client.connect()
                    assert client.connected is True
                    
                    # Test document operations would go here
                    # (requires more detailed mocking of Qdrant responses)
