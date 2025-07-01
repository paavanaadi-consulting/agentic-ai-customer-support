#!/usr/bin/env python3
"""
Test API integration with PostgreSQL MCP server
Tests the full API stack with MCP client integration
"""

import asyncio
import json
import logging
import sys
import aiohttp
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api_integration():
    """Test the API with MCP integration"""
    
    api_base_url = "http://localhost:8000"
    
    logger.info("Testing API integration with MCP server...")
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Test health check
        logger.info("1. Testing API health check...")
        try:
            async with session.get(f"{api_base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"✅ API Health: {health_data['status']}")
                    logger.info(f"   MCP Client: {health_data['services']['mcp_client']}")
                    logger.info(f"   Service Factory: {health_data['services']['service_factory']}")
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
        
        # 2. Test create customer
        logger.info("2. Testing create customer...")
        customer_data = {
            "name": "John Doe",
            "email": f"john.doe.{int(datetime.now().timestamp())}@example.com",
            "phone": "+1234567890",
            "company": "Test Corp",
            "metadata": {"source": "api_test"}
        }
        
        try:
            async with session.post(
                f"{api_base_url}/api/v1/customers",
                json=customer_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    customer = await response.json()
                    customer_id = customer['customer_id']
                    logger.info(f"✅ Created customer: {customer_id}")
                    logger.info(f"   Name: {customer['name']}")
                    logger.info(f"   Tier: {customer['tier']}")
                else:
                    logger.error(f"❌ Create customer failed: {response.status}")
                    error_text = await response.text()
                    logger.error(f"   Error: {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Create customer failed: {e}")
            return False
        
        # 3. Test get customer
        logger.info("3. Testing get customer...")
        try:
            async with session.get(f"{api_base_url}/api/v1/customers/{customer_id}") as response:
                if response.status == 200:
                    customer = await response.json()
                    logger.info(f"✅ Retrieved customer: {customer['name']}")
                else:
                    logger.error(f"❌ Get customer failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Get customer failed: {e}")
            return False
        
        # 4. Test create ticket
        logger.info("4. Testing create ticket...")
        ticket_data = {
            "title": "Test Ticket",
            "description": "This is a test ticket created via API",
            "customer_id": customer_id,
            "category": "technical",
            "priority": "medium",
            "tags": ["test", "api"]
        }
        
        try:
            async with session.post(
                f"{api_base_url}/api/v1/tickets",
                json=ticket_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    ticket = await response.json()
                    ticket_id = ticket['ticket_id']
                    logger.info(f"✅ Created ticket: {ticket_id}")
                    logger.info(f"   Title: {ticket['title']}")
                    logger.info(f"   Status: {ticket['status']}")
                else:
                    logger.error(f"❌ Create ticket failed: {response.status}")
                    error_text = await response.text()
                    logger.error(f"   Error: {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Create ticket failed: {e}")
            return False
        
        # 5. Test list tickets
        logger.info("5. Testing list tickets...")
        try:
            async with session.get(f"{api_base_url}/api/v1/tickets?limit=5") as response:
                if response.status == 200:
                    tickets = await response.json()
                    logger.info(f"✅ Retrieved {len(tickets)} tickets")
                    if tickets:
                        logger.info(f"   First ticket: {tickets[0]['title']}")
                else:
                    logger.error(f"❌ List tickets failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ List tickets failed: {e}")
            return False
        
        # 6. Test analytics
        logger.info("6. Testing analytics...")
        try:
            async with session.get(f"{api_base_url}/api/v1/analytics") as response:
                if response.status == 200:
                    analytics = await response.json()
                    logger.info(f"✅ Retrieved analytics")
                    logger.info(f"   Total tickets: {analytics['total_tickets']}")
                    logger.info(f"   Total customers: {analytics['total_customers']}")
                else:
                    logger.error(f"❌ Analytics failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Analytics failed: {e}")
            return False
        
        logger.info("🎉 All API integration tests passed!")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_api_integration())
    if not success:
        sys.exit(1)
