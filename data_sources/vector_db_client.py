"""
# FILE: data_sources/vector_db_client.py
Vector database client for semantic search capabilities
"""
import asyncio
from typing import Dict, Any, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import logging
import uuid

class VectorDBClient:
    """Qdrant vector database client for semantic search"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self.encoder = None
        self.collection_name = config.collection_name
        self.logger = logging.getLogger("VectorDBClient")
        self.connected = False
    
    async def connect(self):
        """Connect to vector database and initialize encoder"""
        try:
            # Initialize Qdrant client
            self.client = QdrantClient(
                host=self.config.host,
                port=self.config.port
            )
            
            # Initialize sentence transformer for embeddings
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Create collection if it doesn't exist
            await self._ensure_collection_exists()
            
            self.connected = True
            self.logger.info("Connected to vector database")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to vector database: {str(e)}")
            raise
    
    async def _ensure_collection_exists(self):
        """Ensure the collection exists in Qdrant"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # all-MiniLM-L6-v2 embedding size
                        distance=models.Distance.COSINE
                    )
                )
                self.logger.info(f"Created collection: {self.collection_name}")
            else:
                self.logger.info(f"Collection already exists: {self.collection_name}")
                
        except Exception as e:
            self.logger.error(f"Error ensuring collection exists: {str(e)}")
            raise
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector database"""
        try:
            points = []
            
            for doc in documents:
                # Generate embedding
                text = doc.get('content', '')
                if not text:
                    continue
                
                embedding = self.encoder.encode(text)
                
                # Create point
                point_id = str(uuid.uuid4())
                point = models.PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        'content': text,
                        'metadata': doc.get('metadata', {}),
                        'source': doc.get('source', 'unknown'),
                        'created_at': doc.get('created_at', ''),
                        'category': doc.get('category', ''),
                        'tags': doc.get('tags', [])
                    }
                )
                points.append(point)
            
            if points:
                # Upload points to Qdrant
                operation_info = self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                self.logger.info(f"Added {len(points)} documents to vector database")
                return True
            else:
                self.logger.warning("No valid documents to add")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding documents: {str(e)}")
            return False
    
    async def search(self, query: str, limit: int = 10, 
                   score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar documents using semantic similarity"""
        try:
            if not query.strip():
                return []
            
            # Generate query embedding
            query_embedding = self.encoder.encode(query)
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for scored_point in search_result:
                result = {
                    'content': scored_point.payload.get('content', ''),
                    'score': scored_point.score,
                    'metadata': scored_point.payload.get('metadata', {}),
                    'source': scored_point.payload.get('source', ''),
                    'category': scored_point.payload.get('category', ''),
                    'tags': scored_point.payload.get('tags', []),
                    'point_id': scored_point.id
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching vector database: {str(e)}")
            return []
    
    async def search_with_filter(self, query: str, filters: Dict[str, Any], 
                               limit: int = 10, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search with additional filters"""
        try:
            query_embedding = self.encoder.encode(query)
            
            # Build Qdrant filter
            filter_conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=value)
                        )
                    )
                else:
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
            
            search_filter = models.Filter(
                must=filter_conditions
            ) if filter_conditions else None
            
            # Search with filter
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for scored_point in search_result:
                result = {
                    'content': scored_point.payload.get('content', ''),
                    'score': scored_point.score,
                    'metadata': scored_point.payload.get('metadata', {}),
                    'source': scored_point.payload.get('source', ''),
                    'category': scored_point.payload.get('category', ''),
                    'tags': scored_point.payload.get('tags', []),
                    'point_id': scored_point.id
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching with filter: {str(e)}")
            return []
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                'name': collection_info.config.name,
                'vector_size': collection_info.config.params.vectors.size,
                'distance_metric': collection_info.config.params.vectors.distance,
                'points_count': collection_info.points_count,
                'indexed_vectors_count': collection_info.indexed_vectors_count,
                'status': collection_info.status
            }
            
        except Exception as e:
            self.logger.error(f"Error getting collection info: {str(e)}")
            return {}
    
    async def delete_points(self, point_ids: List[str]) -> bool:
        """Delete specific points from the collection"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=point_ids
                )
            )
            
            self.logger.info(f"Deleted {len(point_ids)} points from collection")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting points: {str(e)}")
            return False
    
    async def update_document(self, point_id: str, document: Dict[str, Any]) -> bool:
        """Update an existing document"""
        try:
            text = document.get('content', '')
            if not text:
                return False
            
            # Generate new embedding
            embedding = self.encoder.encode(text)
            
            # Update point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=embedding.tolist(),
                        payload={
                            'content': text,
                            'metadata': document.get('metadata', {}),
                            'source': document.get('source', 'unknown'),
                            'created_at': document.get('created_at', ''),
                            'category': document.get('category', ''),
                            'tags': document.get('tags', [])
                        }
                    )
                ]
            )
            
            self.logger.info(f"Updated document with point_id: {point_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating document: {str(e)}")
            return False