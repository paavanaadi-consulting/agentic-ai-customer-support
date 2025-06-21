"""
API routes for customer support system.
"""
from fastapi import APIRouter, Depends
from .schemas import QueryRequest, QueryResponse

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    # Call agent logic here (stub)
    return QueryResponse(result="Query processed", success=True)
