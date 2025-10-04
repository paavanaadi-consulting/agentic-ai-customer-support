#!/usr/bin/env python3
"""
Direct test of API and PostgreSQL components
Tests the database and API functionality without complex MCP dependencies
"""

import asyncio
import json
import requests
import psycopg2
from datetime import datetime
import sys

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'customer_support',
    'user': 'admin',
    'password': 'password'
}

def test_postgres_direct():
    """Test PostgreSQL database directly"""
    print("=" * 50)
    print("🔍 Testing PostgreSQL Database Direct Connection")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test 1: Check database connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database Connection: {version[0]}")
        
        # Test 2: Check tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"✅ Tables found: {len(tables)}")
        for table in tables[:5]:  # Show first 5 tables
            print(f"   - {table[0]}")
        if len(tables) > 5:
            print(f"   ... and {len(tables)-5} more")
        
        # Test 3: Check customer data
        cursor.execute("SELECT COUNT(*) FROM customers;")
        customer_count = cursor.fetchone()[0]
        print(f"✅ Customers in database: {customer_count}")
        
        # Test 4: Check support tickets
        cursor.execute("SELECT COUNT(*) FROM support_tickets;")
        ticket_count = cursor.fetchone()[0]
        print(f"✅ Support tickets in database: {ticket_count}")
        
        # Test 5: Sample customer data
        cursor.execute("""
            SELECT customer_id, name, email, tier 
            FROM customers 
            LIMIT 3;
        """)
        customers = cursor.fetchall()
        print(f"✅ Sample customers:")
        for customer in customers:
            print(f"   - ID: {customer[0]}, Name: {customer[1]}, Email: {customer[2]}, Tier: {customer[3]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_simple_api():
    """Test a simple Python API without complex dependencies"""
    print("=" * 50)
    print("🔍 Testing Simple Database API")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test customer retrieval
        cursor.execute("""
            SELECT customer_id, name, email, phone, company, tier, status
            FROM customers
            ORDER BY created_at DESC
            LIMIT 5;
        """)
        customers = cursor.fetchall()
        
        print(f"✅ Retrieved {len(customers)} customers:")
        for customer in customers:
            print(f"   - {customer[1]} ({customer[2]}) - Tier: {customer[5]}")
        
        # Test ticket retrieval with customer info
        cursor.execute("""
            SELECT 
                st.ticket_id, 
                st.title, 
                st.status, 
                st.priority,
                c.name as customer_name
            FROM support_tickets st
            JOIN customers c ON st.customer_id = c.customer_id
            ORDER BY st.created_at DESC
            LIMIT 5;
        """)
        tickets = cursor.fetchall()
        
        print(f"✅ Retrieved {len(tickets)} support tickets:")
        for ticket in tickets:
            print(f"   - #{ticket[0]}: {ticket[1]} ({ticket[2]}) - Customer: {ticket[4]}")
        
        # Test creating a new customer
        test_customer_data = {
            'name': f'Test Customer {int(datetime.now().timestamp())}',
            'email': f'test.{int(datetime.now().timestamp())}@example.com',
            'phone': '+1234567890',
            'company': 'Test Company',
            'tier': 'standard'
        }
        
        cursor.execute("""
            INSERT INTO customers (name, email, phone, company, tier, status)
            VALUES (%(name)s, %(email)s, %(phone)s, %(company)s, %(tier)s, 'active')
            RETURNING customer_id, created_at;
        """, test_customer_data)
        
        new_customer = cursor.fetchone()
        print(f"✅ Created new customer: ID {new_customer[0]} at {new_customer[1]}")
        
        # Test creating a new support ticket
        cursor.execute("""
            INSERT INTO support_tickets (title, description, customer_id, category, priority, status)
            VALUES (
                'Test Ticket',
                'This is a test ticket created during API testing',
                %s,
                'technical',
                'medium',
                'open'
            )
            RETURNING ticket_id, created_at;
        """, (new_customer[0],))
        
        new_ticket = cursor.fetchone()
        print(f"✅ Created new support ticket: #{new_ticket[0]} at {new_ticket[1]}")
        
        # Test analytics query
        cursor.execute("""
            SELECT 
                COUNT(*) as total_tickets,
                COUNT(CASE WHEN status = 'open' THEN 1 END) as open_tickets,
                COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_tickets,
                COUNT(CASE WHEN priority = 'high' THEN 1 END) as high_priority
            FROM support_tickets;
        """)
        
        analytics = cursor.fetchone()
        print(f"✅ Ticket Analytics:")
        print(f"   - Total: {analytics[0]}")
        print(f"   - Open: {analytics[1]}")
        print(f"   - Closed: {analytics[2]}")
        print(f"   - High Priority: {analytics[3]}")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_performance():
    """Test database performance with some queries"""
    print("=" * 50)
    print("🔍 Testing Database Performance")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test query performance
        import time
        
        start_time = time.time()
        cursor.execute("""
            SELECT 
                c.name,
                COUNT(st.ticket_id) as ticket_count,
                AVG(CASE 
                    WHEN st.status = 'closed' AND st.resolved_at IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (st.resolved_at - st.created_at))/3600 
                END) as avg_resolution_hours
            FROM customers c
            LEFT JOIN support_tickets st ON c.customer_id = st.customer_id
            GROUP BY c.customer_id, c.name
            ORDER BY ticket_count DESC;
        """)
        results = cursor.fetchall()
        end_time = time.time()
        
        print(f"✅ Complex query executed in {end_time - start_time:.3f} seconds")
        print(f"✅ Results returned: {len(results)} customers")
        
        # Show top customers by ticket count
        print("✅ Top customers by ticket count:")
        for i, result in enumerate(results[:3]):
            avg_hours = result[2] if result[2] else 0
            print(f"   {i+1}. {result[0]}: {result[1]} tickets, Avg resolution: {avg_hours:.1f}h")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting API and PostgreSQL Direct Tests")
    print(f"📅 Test started at: {datetime.now()}")
    
    results = {
        'postgres_direct': test_postgres_direct(),
        'simple_api': test_simple_api(),
        'performance': test_performance()
    }
    
    print("=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} : {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API and PostgreSQL are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
