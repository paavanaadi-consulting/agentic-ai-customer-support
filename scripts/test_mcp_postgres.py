#!/usr/bin/env python3
"""
Test script for MCP PostgreSQL server
Tests all available tools and resources
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPPostgresTestClient:
    """Test client for MCP PostgreSQL server"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call an MCP tool"""
        if arguments is None:
            arguments = {}
            
        payload = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": f"test-{tool_name}-{int(time.time())}"
        }
        
        async with self.session.post(
            f"{self.base_url}/mcp/tools/call",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"HTTP {response.status}: {await response.text()}")
    
    async def read_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Read an MCP resource"""
        payload = {
            "method": "resources/read",
            "params": {
                "uri": resource_uri
            },
            "id": f"test-resource-{int(time.time())}"
        }
        
        async with self.session.post(
            f"{self.base_url}/mcp/resources/read",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"HTTP {response.status}: {await response.text()}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        async with self.session.get(f"{self.base_url}/health") as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"HTTP {response.status}: {await response.text()}")
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        async with self.session.get(f"{self.base_url}/mcp/tools/list") as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"HTTP {response.status}: {await response.text()}")
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources"""
        async with self.session.get(f"{self.base_url}/mcp/resources/list") as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"HTTP {response.status}: {await response.text()}")

async def run_tests():
    """Run comprehensive tests"""
    logger.info("Starting MCP PostgreSQL server tests...")
    
    async with MCPPostgresTestClient() as client:
        
        # 1. Health Check
        logger.info("1. Testing health check...")
        try:
            health = await client.health_check()
            logger.info(f"✅ Health check: {health['status']}")
            if health['status'] != 'healthy':
                logger.error(f"❌ Server not healthy: {health}")
                return False
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
        
        # 2. List Tools
        logger.info("2. Testing list tools...")
        try:
            tools = await client.list_tools()
            logger.info(f"✅ Found {len(tools['tools'])} tools")
            for tool in tools['tools']:
                logger.info(f"   - {tool['name']}")
        except Exception as e:
            logger.error(f"❌ List tools failed: {e}")
            return False
        
        # 3. List Resources
        logger.info("3. Testing list resources...")
        try:
            resources = await client.list_resources()
            logger.info(f"✅ Found {len(resources['resources'])} resources")
            for resource in resources['resources']:
                logger.info(f"   - {resource['uri']}")
        except Exception as e:
            logger.error(f"❌ List resources failed: {e}")
            return False
        
        # 4. Test get_customers tool
        logger.info("4. Testing get_customers tool...")
        try:
            result = await client.call_tool("get_customers", {"limit": 3})
            if result['result']['success']:
                customers = result['result']['customers']
                logger.info(f"✅ Retrieved {len(customers)} customers")
                for customer in customers[:1]:  # Show one example
                    logger.info(f"   - {customer['first_name']} {customer['last_name']} ({customer['tier']})")
            else:
                logger.error(f"❌ get_customers failed: {result['result']}")
        except Exception as e:
            logger.error(f"❌ get_customers failed: {e}")
            return False
        
        # 5. Test get_tickets tool
        logger.info("5. Testing get_tickets tool...")
        try:
            result = await client.call_tool("get_tickets", {"limit": 3})
            if result['result']['success']:
                tickets = result['result']['tickets']
                logger.info(f"✅ Retrieved {len(tickets)} tickets")
                for ticket in tickets[:1]:  # Show one example
                    logger.info(f"   - {ticket['subject']} ({ticket['status']})")
            else:
                logger.error(f"❌ get_tickets failed: {result['result']}")
        except Exception as e:
            logger.error(f"❌ get_tickets failed: {e}")
            return False
        
        # 6. Test search_knowledge_base tool
        logger.info("6. Testing search_knowledge_base tool...")
        try:
            result = await client.call_tool("search_knowledge_base", {"search_term": "password", "limit": 2})
            if result['result']['success']:
                articles = result['result']['articles']
                logger.info(f"✅ Found {len(articles)} knowledge articles")
                for article in articles[:1]:  # Show one example
                    logger.info(f"   - {article['title']}")
            else:
                logger.error(f"❌ search_knowledge_base failed: {result['result']}")
        except Exception as e:
            logger.error(f"❌ search_knowledge_base failed: {e}")
            return False
        
        # 7. Test get_analytics tool
        logger.info("7. Testing get_analytics tool...")
        try:
            result = await client.call_tool("get_analytics", {"days": 30})
            if result['result']['success']:
                analytics = result['result']['analytics']
                logger.info(f"✅ Analytics: {analytics['total_tickets']} tickets, {analytics['total_customers']} customers")
            else:
                logger.error(f"❌ get_analytics failed: {result['result']}")
        except Exception as e:
            logger.error(f"❌ get_analytics failed: {e}")
            return False
        
        # 8. Test query_database tool
        logger.info("8. Testing query_database tool...")
        try:
            result = await client.call_tool("query_database", {
                "query": "SELECT tier, COUNT(*) as count FROM customers GROUP BY tier ORDER BY count DESC",
                "params": []
            })
            if result['result']['success']:
                data = result['result']['data']
                logger.info(f"✅ Custom query returned {len(data)} rows")
                for row in data:
                    logger.info(f"   - {row['tier']}: {row['count']} customers")
            else:
                logger.error(f"❌ query_database failed: {result['result']}")
        except Exception as e:
            logger.error(f"❌ query_database failed: {e}")
            return False
        
        # 9. Test resources
        logger.info("9. Testing resources...")
        test_resources = [
            "postgresql://customers",
            "postgresql://tickets", 
            "postgresql://knowledge_articles",
            "postgresql://analytics"
        ]
        
        for resource_uri in test_resources:
            try:
                result = await client.read_resource(resource_uri)
                if result['result']:
                    logger.info(f"✅ Resource {resource_uri}: {json.dumps(result['result']['data'])}")
                else:
                    logger.error(f"❌ Resource {resource_uri} failed: {result}")
            except Exception as e:
                logger.error(f"❌ Resource {resource_uri} failed: {e}")
                return False
        
        # 10. Test error handling
        logger.info("10. Testing error handling...")
        try:
            result = await client.call_tool("nonexistent_tool", {})
            if result.get('error'):
                logger.info("✅ Error handling works for nonexistent tool")
            else:
                logger.warning("⚠️ Expected error for nonexistent tool")
        except Exception as e:
            logger.info(f"✅ Error handling works: {e}")
        
        logger.info("🎉 All MCP PostgreSQL server tests completed successfully!")
        return True

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    if not success:
        exit(1)
