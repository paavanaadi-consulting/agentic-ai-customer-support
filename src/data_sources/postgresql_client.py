"""
PostgreSQL database client for customer support system.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None

from config.env_settings import CONFIG

logger = logging.getLogger(__name__)


class PostgreSQLClient:
    """PostgreSQL database client with connection pooling."""
    
    def __init__(self):
        self.pool = None  # Will be asyncpg.Pool if asyncpg is available
        if not ASYNCPG_AVAILABLE:
            logger.warning("asyncpg not available - PostgreSQLClient will not function properly")
            
        self.connection_params = {
            'host': CONFIG.DB_HOST,
            'port': CONFIG.DB_PORT,
            'user': CONFIG.DB_USER,
            'password': CONFIG.DB_PASSWORD,
            'database': CONFIG.DB_NAME,
            'min_size': 5,
            'max_size': 20,
            'command_timeout': 30
        }
    
    async def connect(self) -> None:
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(**self.connection_params)
            logger.info("PostgreSQL connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    async def health_check(self) -> bool:
        """Check database health."""
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries."""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_command(self, command: str, *args) -> str:
        """Execute an INSERT/UPDATE/DELETE command and return status."""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(command, *args)
                return result
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute a query and return the first result as a dictionary."""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Fetch one failed: {e}")
            raise
    
    # Customer operations
    async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID."""
        query = """
            SELECT customer_id, email, first_name, last_name, phone, company, 
                   tier, language, timezone, is_active, total_tickets, 
                   satisfaction_avg, created_at, updated_at, last_seen_at
            FROM customers 
            WHERE customer_id = $1
        """
        return await self.fetch_one(query, customer_id)
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> str:
        """Create a new customer and return customer_id."""
        command = """
            INSERT INTO customers (customer_id, email, first_name, last_name, phone, company, tier)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING customer_id
        """
        async with self.pool.acquire() as conn:
            customer_id = await conn.fetchval(
                command,
                customer_data['customer_id'],
                customer_data['email'],
                customer_data.get('first_name'),
                customer_data.get('last_name'),
                customer_data.get('phone'),
                customer_data.get('company'),
                customer_data.get('tier', 'standard')
            )
            return customer_id
    
    async def list_customers(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """List customers with pagination."""
        query = """
            SELECT customer_id, email, first_name, last_name, phone, company, 
                   tier, total_tickets, satisfaction_avg, created_at
            FROM customers 
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        return await self.execute_query(query, limit, offset)
    
    # Ticket operations
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID."""
        query = """
            SELECT t.ticket_id, t.customer_id, t.subject, t.description, t.status, 
                   t.priority, t.source, t.tags, t.created_at, t.updated_at,
                   c.first_name, c.last_name, c.email,
                   cat.name as category_name
            FROM support_tickets t
            LEFT JOIN customers c ON t.customer_id = c.customer_id
            LEFT JOIN categories cat ON t.category_id = cat.id
            WHERE t.ticket_id = $1
        """
        return await self.fetch_one(query, ticket_id)
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> str:
        """Create a new ticket and return ticket_id."""
        command = """
            INSERT INTO support_tickets (ticket_id, customer_id, category_id, subject, 
                                        description, priority, source, tags)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING ticket_id
        """
        async with self.pool.acquire() as conn:
            ticket_id = await conn.fetchval(
                command,
                ticket_data['ticket_id'],
                ticket_data['customer_id'],
                ticket_data.get('category_id'),
                ticket_data['subject'],
                ticket_data['description'],
                ticket_data.get('priority', 'medium'),
                ticket_data.get('source', 'web'),
                ticket_data.get('tags', [])
            )
            return ticket_id
    
    async def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Update ticket status."""
        command = """
            UPDATE support_tickets 
            SET status = $2, updated_at = CURRENT_TIMESTAMP
            WHERE ticket_id = $1
        """
        result = await self.execute_command(command, ticket_id, status)
        return "UPDATE 1" in result
    
    async def list_tickets(self, customer_id: Optional[str] = None, 
                          status: Optional[str] = None, 
                          priority: Optional[str] = None,
                          limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """List tickets with optional filters."""
        conditions = []
        params = []
        param_count = 0
        
        if customer_id:
            param_count += 1
            conditions.append(f"t.customer_id = ${param_count}")
            params.append(customer_id)
        
        if status:
            param_count += 1
            conditions.append(f"t.status = ${param_count}")
            params.append(status)
        
        if priority:
            param_count += 1
            conditions.append(f"t.priority = ${param_count}")
            params.append(priority)
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
            SELECT t.ticket_id, t.customer_id, t.subject, t.status, t.priority, 
                   t.created_at, c.first_name, c.last_name
            FROM support_tickets t
            LEFT JOIN customers c ON t.customer_id = c.customer_id
            WHERE {where_clause}
            ORDER BY t.created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([limit, offset])
        
        return await self.execute_query(query, *params)
    
    # Analytics operations
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get system analytics summary."""
        queries = {
            'total_customers': "SELECT COUNT(*) FROM customers WHERE is_active = TRUE",
            'total_tickets': "SELECT COUNT(*) FROM support_tickets",
            'open_tickets': "SELECT COUNT(*) FROM support_tickets WHERE status = 'open'",
            'avg_satisfaction': "SELECT AVG(satisfaction_avg) FROM customers WHERE satisfaction_avg > 0"
        }
        
        result = {}
        for key, query in queries.items():
            rows = await self.execute_query(query)
            result[key] = rows[0].get('count', 0) if rows else 0
        
        return result


# Global database client instance
db_client = PostgreSQLClient()


async def get_db_client() -> PostgreSQLClient:
    """Get database client instance."""
    if not db_client.pool:
        await db_client.connect()
    return db_client
