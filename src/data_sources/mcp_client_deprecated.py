"""
DEPRECATED: Legacy MCP client - Use src.mcp.postgres_mcp_client instead

This module is kept for backward compatibility only.
For new code, use OptimizedPostgreSQLMCPClient from src.mcp.postgres_mcp_client
"""
import warnings
from typing import Any


class MCPClientError(Exception):
    """Custom exception for MCP client errors."""
    pass


def deprecated_warning():
    """Issue deprecation warning."""
    warnings.warn(
        "src.data_sources.mcp_client is deprecated. "
        "Use src.mcp.postgres_mcp_client.OptimizedPostgreSQLMCPClient instead.",
        DeprecationWarning,
        stacklevel=3
    )


class PostgreSQLMCPClient:
    """
    DEPRECATED: Legacy PostgreSQL MCP client.
    
    Use src.mcp.optimized_postgres_mcp_client.OptimizedPostgreSQLMCPClient instead
    for better performance and features.
    """
    
    def __init__(self, *args, **kwargs):
        deprecated_warning()
        raise NotImplementedError(
            "Legacy PostgreSQLMCPClient is no longer supported. "
            "Use OptimizedPostgreSQLMCPClient from src.mcp.postgres_mcp_client"
        )


async def get_mcp_client(*args, **kwargs):
    """
    DEPRECATED: Use get_optimized_mcp_client instead.
    
    Raises:
        NotImplementedError: This function is deprecated
    """
    deprecated_warning()
    raise NotImplementedError(
        "get_mcp_client is deprecated. "
        "Use get_optimized_mcp_client from src.mcp.postgres_mcp_client"
    )


async def close_mcp_client(*args, **kwargs):
    """
    DEPRECATED: Use close_optimized_mcp_client instead.
    
    Raises:
        NotImplementedError: This function is deprecated
    """
    deprecated_warning()
    raise NotImplementedError(
        "close_mcp_client is deprecated. "
        "Use close_optimized_mcp_client from src.mcp.postgres_mcp_client"
    )
