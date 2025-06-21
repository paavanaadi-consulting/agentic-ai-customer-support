"""
Database setup and initialization script
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import CONFIG
from data_sources.enhanced_rdbms_connector import EnhancedRDBMSConnector

async def setup_database():
    """Set up the customer support database with schema and sample data"""
    
    print("🗄️ Setting up Customer Support Database...")
    
    # Initialize database connector
    db = EnhancedRDBMSConnector(CONFIG['database'])
    await db.connect()
    
    print("✅ Database connection established")
    
    # Read and execute schema file
    schema_file = Path(__file__).parent / "customer_support_schema.sql"
    
    if schema_file.exists():
        print("📄 Executing database schema...")
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        with db.connection.cursor() as cursor:
            cursor.execute(schema_sql)
        
        print("✅ Database schema created successfully")
    else:
        print("❌ Schema file not found. Please create customer_support_schema.sql")
        return False
    
    print("🎉 Database setup completed successfully!")
    print("\n📊 Database Statistics:")
    
    # Get some basic stats
    stats_queries = {
        'customers': 'SELECT COUNT(*) FROM customers',
        'tickets': 'SELECT COUNT(*) FROM support_tickets',
        'articles': 'SELECT COUNT(*) FROM knowledge_articles',
        'categories': 'SELECT COUNT(*) FROM categories'
    }
    
    with db.connection.cursor() as cursor:
        for name, query in stats_queries.items():
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"   {name.capitalize()}: {count}")
    
    return True

if __name__ == "__main__":
    asyncio.run(setup_database())