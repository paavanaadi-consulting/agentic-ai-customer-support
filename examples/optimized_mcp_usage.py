"""
Example usage of the optimized PostgreSQL MCP client
Demonstrates the improved performance and features
"""
import asyncio
import os
from src.mcp.optimized_postgres_mcp_client import (
    OptimizedPostgreSQLMCPClient, 
    get_optimized_mcp_client,
    close_optimized_mcp_client
)
from src.services.service_factory import initialize_service_factory_with_optimized_mcp


async def main():
    """Example of using the optimized MCP client."""
    
    # Example 1: Direct usage of optimized client
    print("=== Example 1: Direct Optimized MCP Client ===")
    
    # Initialize with both direct and HTTP fallback capabilities
    connection_string = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
    
    client = OptimizedPostgreSQLMCPClient(
        connection_string=connection_string,
        mcp_server_url=mcp_server_url,
        use_direct_connection=True  # Prefer direct connection
    )
    
    try:
        # Connect (will try direct first, fallback to HTTP)
        connected = await client.connect()
        if not connected:
            print("❌ Failed to connect to MCP server")
            return
        
        print("✅ Connected to optimized MCP client")
        
        # Example customer operations
        customer_data = {
            "customer_id": "test-customer-123",
            "first_name": "John",
            "last_name": "Doe", 
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "company": "Acme Corp",
            "created_at": "2025-01-01T00:00:00Z",
            "tier": "premium",
            "status": "active"
        }
        
        # Create customer with optimized performance
        print("Creating customer...")
        try:
            created_customer = await client.create_customer(customer_data)
            print(f"✅ Customer created: {created_customer.get('customer_id')}")
        except Exception as e:
            print(f"❌ Customer creation failed: {e}")
        
        # Get customer with caching
        print("Retrieving customer (with caching)...")
        try:
            customer = await client.get_customer_by_id("test-customer-123")
            if customer:
                print(f"✅ Customer retrieved: {customer.get('first_name')} {customer.get('last_name')}")
            else:
                print("❌ Customer not found")
        except Exception as e:
            print(f"❌ Customer retrieval failed: {e}")
        
        # Search knowledge base with full-text search
        print("Searching knowledge base...")
        try:
            articles = await client.search_knowledge_base("troubleshooting", limit=5)
            print(f"✅ Found {len(articles)} knowledge articles")
        except Exception as e:
            print(f"❌ Knowledge base search failed: {e}")
        
        # Get analytics with caching
        print("Getting analytics (with caching)...")
        try:
            analytics = await client.get_analytics(days=7)
            print(f"✅ Analytics retrieved: {analytics}")
        except Exception as e:
            print(f"❌ Analytics retrieval failed: {e}")
        
    finally:
        await client.disconnect()
        print("✅ Disconnected from optimized MCP client")
    
    # Example 2: Using with service factory
    print("\\n=== Example 2: Service Factory with Optimized MCP ===")
    
    try:
        # Initialize service factory with optimized MCP client
        service_factory = await initialize_service_factory_with_optimized_mcp(
            connection_string=connection_string,
            mcp_server_url=mcp_server_url,
            use_direct_connection=True
        )
        
        print("✅ Service factory initialized with optimized MCP client")
        
        # Get services
        customer_service = service_factory.customer_service
        ticket_service = service_factory.ticket_service
        analytics_service = service_factory.analytics_service
        
        print("✅ All services created successfully")
        
        # Example service operations
        from src.api.schemas import CustomerRequest
        
        customer_request = CustomerRequest(
            name="Jane Smith",
            email="jane.smith@example.com",
            phone="+1-555-0456",
            company="Tech Corp",
            metadata={"source": "website"}
        )
        
        try:
            customer_response = await customer_service.create_customer(customer_request)
            print(f"✅ Customer created via service: {customer_response.customer_id}")
        except Exception as e:
            print(f"❌ Service customer creation failed: {e}")
        
    finally:
        await close_optimized_mcp_client()
        print("✅ Service factory cleaned up")
    
    # Example 3: Performance comparison
    print("\\n=== Example 3: Performance Comparison ===")
    
    # Test caching performance
    client = await get_optimized_mcp_client(
        connection_string=connection_string,
        mcp_server_url=mcp_server_url
    )
    
    try:
        import time
        
        # First call (no cache)
        start_time = time.time()
        analytics1 = await client.get_analytics(days=30)
        first_call_time = time.time() - start_time
        
        # Second call (with cache)
        start_time = time.time()
        analytics2 = await client.get_analytics(days=30)
        second_call_time = time.time() - start_time
        
        print(f"✅ First analytics call: {first_call_time:.3f}s")
        print(f"✅ Second analytics call (cached): {second_call_time:.3f}s")
        print(f"✅ Cache speedup: {first_call_time/second_call_time:.1f}x faster")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
    
    finally:
        await close_optimized_mcp_client()


if __name__ == "__main__":
    asyncio.run(main())
