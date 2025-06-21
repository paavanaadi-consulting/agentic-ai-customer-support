from data_sources.pdf_processor import PDFProcessor
import pytest

@pytest.mark.asyncio
async def test_pdf_processor_init():
    processor = PDFProcessor()
    await processor.initialize()
    assert hasattr(processor, 'initialize')
