"""
Comprehensive tests for PDFProcessor data source component.
"""
import pytest
import tempfile
import os
from unittest.mock import patch, Mock, mock_open
from src.data_sources.pdf_processor import PDFProcessor


class TestPDFProcessor:
    """Test PDFProcessor functionality."""

    @pytest.fixture
    def temp_pdf_dir(self):
        """Create a temporary directory for PDF testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def pdf_processor(self, temp_pdf_dir):
        """Create PDFProcessor instance with temporary directory."""
        return PDFProcessor(pdf_directory=temp_pdf_dir)

    @pytest.mark.asyncio
    async def test_pdf_processor_initialization(self, pdf_processor):
        """Test basic PDFProcessor initialization."""
        assert pdf_processor.pdf_directory is not None
        assert isinstance(pdf_processor.documents, dict)
        assert isinstance(pdf_processor.document_chunks, list)
        assert pdf_processor.vectorizer is None  # Before initialization
        assert pdf_processor.tfidf_matrix is None  # Before initialization

    @pytest.mark.asyncio
    async def test_pdf_processor_initialize_empty_directory(self, pdf_processor):
        """Test initialization with empty PDF directory."""
        await pdf_processor.initialize()
        
        assert len(pdf_processor.documents) == 0
        assert len(pdf_processor.document_chunks) == 0

    @pytest.mark.asyncio
    async def test_pdf_directory_creation(self, temp_pdf_dir):
        """Test that PDF directory is created if it doesn't exist."""
        non_existent_dir = os.path.join(temp_pdf_dir, "new_pdf_dir")
        processor = PDFProcessor(pdf_directory=non_existent_dir)
        
        assert os.path.exists(non_existent_dir)

    @pytest.mark.asyncio 
    async def test_get_document_list(self, pdf_processor):
        """Test getting list of loaded documents."""
        await pdf_processor.initialize()
        doc_list = pdf_processor.get_document_list()
        
        assert isinstance(doc_list, list)
        assert len(doc_list) == 0  # Empty directory

    @pytest.mark.asyncio
    async def test_get_total_chunks(self, pdf_processor):
        """Test getting total number of document chunks."""
        await pdf_processor.initialize()
        total_chunks = pdf_processor.get_total_chunks()
        
        assert isinstance(total_chunks, int)
        assert total_chunks == 0  # Empty directory

    @pytest.mark.asyncio
    async def test_search_documents_empty_collection(self, pdf_processor):
        """Test searching documents with empty collection."""
        await pdf_processor.initialize()
        
        results = await pdf_processor.search_documents("test query")
        
        assert isinstance(results, dict)
        assert "results" in results
        assert len(results["results"]) == 0

    @pytest.mark.asyncio
    async def test_pdf_processor_with_mock_documents(self, pdf_processor):
        """Test PDF processor with mocked document loading."""
        # Mock document data
        mock_documents = {
            "test.pdf": {
                "content": "This is a test document about customer support.",
                "file_path": "/fake/path/test.pdf",
                "chunks": ["This is a test document", "about customer support."]
            }
        }
        
        # Patch the document loading
        with patch.object(pdf_processor, '_load_documents') as mock_load:
            with patch.object(pdf_processor, '_build_search_index') as mock_index:
                pdf_processor.documents = mock_documents
                pdf_processor.document_chunks = ["This is a test document", "about customer support."]
                
                await pdf_processor.initialize()
                
                mock_load.assert_called_once()
                mock_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_document_summary_nonexistent(self, pdf_processor):
        """Test getting summary for non-existent document."""
        await pdf_processor.initialize()
        
        summary = await pdf_processor.get_document_summary("nonexistent.pdf")
        
        assert summary is None

    def test_chunk_text_method(self, pdf_processor):
        """Test text chunking functionality."""
        # Test with a sample text that should be chunked
        long_text = " ".join(["This is sentence number {}.".format(i) for i in range(100)])
        
        chunks = pdf_processor._chunk_text(long_text)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        
        # Each chunk should be reasonably sized
        for chunk in chunks:
            assert len(chunk) <= 1500  # Assuming max chunk size


@pytest.mark.integration 
class TestPDFProcessorIntegration:
    """Integration tests for PDFProcessor with file system."""

    def test_pdf_processor_real_directory(self):
        """Test PDFProcessor with actual file system."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = PDFProcessor(pdf_directory=tmpdir)
            
            # Verify directory was created and processor initialized
            assert os.path.exists(tmpdir)
            assert processor.pdf_directory == tmpdir
