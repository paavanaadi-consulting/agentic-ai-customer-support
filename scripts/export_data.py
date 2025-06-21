"""
Export documents from the vector database to a JSON file.
"""
import json
import asyncio
from config.settings import settings
from data_sources.vector_db_client import VectorDBClient

async def main():
    config = type('Config', (), {
        'host': settings.VECTOR_DB_HOST,
        'port': settings.VECTOR_DB_PORT,
        'collection_name': settings.VECTOR_DB_COLLECTION
    })()
    
    vector_db = VectorDBClient(config)
    await vector_db.connect()
    results = await vector_db.search("")  # Export all documents (or adjust as needed)
    with open('data/exported_documents.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Exported {len(results)} documents from vector DB.")

if __name__ == "__main__":
    asyncio.run(main())
