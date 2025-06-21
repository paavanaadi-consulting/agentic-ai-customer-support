"""
Import documents into the vector database from a JSON file.
"""
import json
import asyncio
from config.settings import settings
from data_sources.vector_db_client import VectorDBClient

async def main():
    with open('data/import_documents.json') as f:
        documents = json.load(f)
    
    config = type('Config', (), {
        'host': settings.VECTOR_DB_HOST,
        'port': settings.VECTOR_DB_PORT,
        'collection_name': settings.VECTOR_DB_COLLECTION
    })()
    
    vector_db = VectorDBClient(config)
    await vector_db.connect()
    await vector_db.add_documents(documents)
    print(f"Imported {len(documents)} documents to vector DB.")

if __name__ == "__main__":
    asyncio.run(main())
