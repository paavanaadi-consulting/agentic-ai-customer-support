"""
API dependencies (e.g., authentication, DB session management).
"""
from fastapi import Depends, HTTPException

def get_current_user():
    # Stub for authentication dependency
    return {"user_id": "test_user"}
