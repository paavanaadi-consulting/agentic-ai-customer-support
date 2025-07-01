#!/usr/bin/env python3
"""
Startup script for the integrated API with MCP PostgreSQL server
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.service_factory import initialize_service_factory_with_mcp
from src.mcp.postgres_mcp_client import get_optimized_mcp_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp_integration():
    """Test MCP integration before starting API"""
    
    logger.info("Testing MCP server connection...")
    
    try:
        # Initialize MCP client
        mcp_client = await get_optimized_mcp_client()
        
        # Test basic connectivity
        customers = await mcp_client.get_customers(limit=1)
        logger.info(f"✅ MCP server connection successful")
        logger.info(f"   Found {len(customers)} customers in database")
        
        # Initialize service factory
        service_factory = await initialize_service_factory_with_mcp()
        logger.info("✅ Service factory initialized with MCP client")
        
        # Test services
        customer_service = service_factory.customer_service
        ticket_service = service_factory.ticket_service
        analytics_service = service_factory.analytics_service
        
        logger.info("✅ All services initialized successfully")
        logger.info("🚀 Ready to start API server!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP integration test failed: {e}")
        logger.error("   Make sure the PostgreSQL MCP server is running on port 8001")
        return False

def main():
    """Main startup function"""
    logger.info("Starting integrated API with MCP PostgreSQL server...")
    
    # Test MCP integration
    success = asyncio.run(test_mcp_integration())
    
    if success:
        logger.info("✅ Integration test passed - starting API server...")
        
        # Start the API server
        import uvicorn
        from src.api.api_main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0", 
            port=8000,
            log_level="info",
            reload=False
        )
    else:
        logger.error("❌ Integration test failed - cannot start API server")
        logger.error("   Please ensure:")
        logger.error("   1. PostgreSQL database is running")
        logger.error("   2. MCP PostgreSQL server is running on port 8001")
        logger.error("   3. Database schema is initialized")
        sys.exit(1)

if __name__ == "__main__":
    main()
