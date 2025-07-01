"""
MCP Client Migration Example
Shows how to migrate from legacy to optimized MCP client
"""
import asyncio
import warnings
import sys
import os

# Add the parent directory to the path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def demonstrate_migration():
    """Demonstrate migration from legacy to optimized MCP client."""
    
    print("🔄 MCP Client Migration Demonstration")
    print("=" * 50)
    
    # Show migration guide
    from src.mcp.migration_helper import MigrationGuide
    MigrationGuide.print_migration_guide()
    
    print("\n🧪 STEP 1: Legacy Client Usage (with warnings)")
    print("-" * 50)
    
    # Catch deprecation warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Legacy client usage
        from src.data_sources.mcp_client import get_mcp_client
        legacy_client = await get_mcp_client()
        
        if w:
            print(f"⚠️  Deprecation warning: {w[0].message}")
        
        print("✅ Legacy client created (with deprecation warning)")
    
    print("\n🚀 STEP 2: Optimized Client Usage")
    print("-" * 50)
    
    # Optimized client usage
    from src.mcp.postgres_mcp_client import get_optimized_mcp_client
    
    optimized_client = await get_optimized_mcp_client(
        connection_string=None,  # Would be real connection string in production
        mcp_server_url="http://localhost:8001",
        use_direct_connection=False  # Would be True with real connection string
    )
    
    print("✅ Optimized client created (no warnings)")
    
    print("\n📊 STEP 3: Performance Comparison")
    print("-" * 50)
    
    from src.mcp.migration_helper import get_client_performance_info
    
    legacy_info = get_client_performance_info(legacy_client)
    optimized_info = get_client_performance_info(optimized_client)
    
    print(f"Legacy client:    {legacy_info['performance_level']} performance")
    print(f"Optimized client: {optimized_info['performance_level']} performance")
    print(f"Caching:          {'❌' if not optimized_info['has_caching'] else '✅'}")
    print(f"Direct conn:      {'❌' if not optimized_info['has_direct_connection'] else '✅'}")
    
    print(f"\n💡 Recommendation: {optimized_info['recommendation']}")
    
    print("\n🔧 STEP 4: Service Factory Migration")
    print("-" * 50)
    
    # Legacy service factory
    print("Legacy approach:")
    print("  from src.services.service_factory import initialize_service_factory_with_mcp")
    print("  service_factory = await initialize_service_factory_with_mcp()")
    
    print("\nOptimized approach:")
    print("  from src.services.service_factory import initialize_service_factory_with_optimized_mcp")
    print("  service_factory = await initialize_service_factory_with_optimized_mcp(")
    print("      connection_string='postgresql://...',")
    print("      use_direct_connection=True")
    print("  )")
    
    print("\n✅ STEP 5: Migration Validation")
    print("-" * 50)
    
    from src.mcp.migration_helper import MigrationGuide
    success = MigrationGuide.validate_migration(legacy_client, optimized_client)
    
    if success:
        print("🎉 Migration demonstration completed successfully!")
    else:
        print("❌ Migration demonstration had issues")
    
    # Cleanup
    try:
        await legacy_client.close()
        await optimized_client.disconnect()
    except:
        pass
    
    print("\n📚 Next Steps:")
    print("1. Update your imports to use optimized client")
    print("2. Add PostgreSQL connection string for direct connection")
    print("3. Enable caching for better performance")
    print("4. Test with your actual workload")
    print("5. Monitor performance improvements")


if __name__ == "__main__":
    asyncio.run(demonstrate_migration())
