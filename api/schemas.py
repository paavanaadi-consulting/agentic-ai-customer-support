"""
Pydantic schemas for API requests and responses.
"""
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    customer_id: str
    context: dict = {}

class QueryResponse(BaseModel):
    result: str
    success: bool
