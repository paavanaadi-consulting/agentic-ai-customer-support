#!/usr/bin/env python3
"""
Test PostgreSQL connection and database schema.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import psycopg2
from psycopg2.extras import RealDictCursor
from config.env_settings import CONFIG

def test_postgresql_connection():
    """Test PostgreSQL connection and verify schema."""
    
    connection_params = {
        'host': CONFIG.DB_HOST,
        'port': CONFIG.DB_PORT,
        'user': CONFIG.DB_USER,
        'password': CONFIG.DB_PASSWORD,
        'database': CONFIG.DB_NAME
    }
    
    print("🔗 Testing PostgreSQL Connection...")
    print(f"Host: {connection_params['host']}:{connection_params['port']}")
    print(f"Database: {connection_params['database']}")
    print(f"User: {connection_params['user']}")
    print()
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✅ Successfully connected to PostgreSQL!")
        
        # Test basic queries
        print("\n📊 Database Schema Information:")
        
        # Count tables
        cursor.execute("""
            SELECT COUNT(*) as table_count 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()['table_count']
        print(f"📋 Total tables: {table_count}")
        
        # List all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        print(f"📝 Tables: {', '.join(tables)}")
        
        # Sample data counts
        print("\n📈 Sample Data Summary:")
        
        data_queries = {
            'Customers': 'SELECT COUNT(*) FROM customers',
            'Support Tickets': 'SELECT COUNT(*) FROM support_tickets',
            'Knowledge Articles': 'SELECT COUNT(*) FROM knowledge_articles',
            'Customer Feedback': 'SELECT COUNT(*) FROM customer_feedback',
            'Agents': 'SELECT COUNT(*) FROM agents',
            'Categories': 'SELECT COUNT(*) FROM categories'
        }
        
        for name, query in data_queries.items():
            try:
                cursor.execute(query)
                count = cursor.fetchone()[0]
                print(f"   {name}: {count} records")
            except Exception as e:
                print(f"   {name}: Error - {e}")
        
        # Sample customer data
        print("\n👥 Sample Customer Data:")
        cursor.execute("""
            SELECT customer_id, first_name, last_name, email, company 
            FROM customers 
            LIMIT 3
        """)
        customers = cursor.fetchall()
        for customer in customers:
            print(f"   • {customer['first_name']} {customer['last_name']} ({customer['customer_id']}) - {customer['company']}")
        
        # Sample ticket data
        print("\n🎫 Sample Ticket Data:")
        cursor.execute("""
            SELECT ticket_id, subject, status, priority 
            FROM support_tickets 
            LIMIT 3
        """)
        tickets = cursor.fetchall()
        for ticket in tickets:
            print(f"   • {ticket['ticket_id']}: {ticket['subject']} [{ticket['status']}/{ticket['priority']}]")
        
        print("\n✅ PostgreSQL database is ready and populated with sample data!")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_postgresql_connection()
    sys.exit(0 if success else 1)
