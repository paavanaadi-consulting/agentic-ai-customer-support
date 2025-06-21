from data_sources.vector_db_client import VectorDBClient
import pytest

@pytest.mark.asyncio
async def test_vector_db_client_connect():
    client = VectorDBClient({"host": "localhost", "port": 6333, "collection": "test"})
    await client.connect()
    assert hasattr(client, 'connect')
