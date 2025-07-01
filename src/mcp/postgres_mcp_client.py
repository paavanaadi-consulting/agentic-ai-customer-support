"""
PostgreSQL MCP Client
Provides optimized PostgreSQL operations via MCP with multiple fallback strategies.
Combines direct connection, HTTP communication, and advanced customer support features.
"""
import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import aiohttp

from .mcp_client_interface import MCPClientInterface

# Try to import external postgres-mcp package
try:
    from postgres_mcp import PostgresMCPServer as ExternalPostgresMCPServer
    POSTGRES_MCP_AVAILABLE = True
except ImportError:
    POSTGRES_MCP_AVAILABLE = False
    # Create a placeholder type for type hints
    class ExternalPostgresMCPServer:
        pass

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Custom exception for MCP client errors."""
    pass


class OptimizedPostgreSQLMCPClient(MCPClientInterface):
    """
    Optimized PostgreSQL MCP Client that provides:
    1. Direct connection to external postgres-mcp server (preferred)
    2. HTTP-based MCP communication (fallback)
    3. Customer support specific operations
    4. Connection pooling and error handling
    """
    
    def __init__(self, 
                 connection_string: Optional[str] = None,
                 mcp_server_url: str = "http://localhost:8001",
                 use_direct_connection: bool = True):
        """
        Initialize the optimized PostgreSQL MCP client.
        
        Args:
            connection_string: PostgreSQL connection string for direct connection
            mcp_server_url: URL of the MCP server for HTTP communication
            use_direct_connection: Whether to prefer direct connection over HTTP
        """
        self.connection_string = connection_string
        self.mcp_server_url = mcp_server_url
        self.use_direct_connection = use_direct_connection and POSTGRES_MCP_AVAILABLE
        
        # Connection objects
        self.external_server: Optional[ExternalPostgresMCPServer] = None
        self.http_session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
        
        # State tracking
        self.connected = False
        self.logger = logging.getLogger("OptimizedPostgreSQLMCPClient")
        
        # Cache for frequently accessed data
        self._cache = {}
        self._cache_ttl = {}
        self.cache_duration = 300  # 5 minutes default cache
        
    async def connect(self) -> bool:
        """
        Connect to PostgreSQL via the best available method.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.connected:
            return True
            
        # Try direct connection first if available and preferred
        if self.use_direct_connection and self.connection_string:
            try:
                await self._connect_direct()
                self.connected = True
                self.logger.info("Connected via direct PostgreSQL MCP server")
                return True
            except Exception as e:
                self.logger.warning(f"Direct connection failed: {e}, falling back to HTTP")
        
        # Fallback to HTTP connection
        try:
            await self._connect_http()
            self.connected = True
            self.logger.info("Connected via HTTP MCP server")
            return True
        except Exception as e:
            self.logger.error(f"All connection methods failed: {e}")
            return False
    
    async def _connect_direct(self):
        """Connect directly to PostgreSQL via external MCP server."""
        if not POSTGRES_MCP_AVAILABLE:
            raise ImportError("postgres-mcp package not available")
        
        self.external_server = ExternalPostgresMCPServer(self.connection_string)
        await self.external_server.start()
    
    async def _connect_http(self):
        """Connect to PostgreSQL via HTTP MCP server."""
        if self.http_session is None or self.http_session.closed:
            async with self._session_lock:
                if self.http_session is None or self.http_session.closed:
                    self.http_session = aiohttp.ClientSession()
        
        # Test connection with a simple health check
        await self._http_call_tool("list_tables", {"schema": "public"})
    
    async def disconnect(self):
        """Disconnect from all connections."""
        self.connected = False
        
        if self.external_server:
            await self.external_server.stop()
            self.external_server = None
        
        if self.http_session and not self.http_session.closed:
            await self.http_session.close()
            self.http_session = None
        
        # Clear cache
        self._cache.clear()
        self._cache_ttl.clear()
        
        self.logger.info("Disconnected from PostgreSQL MCP")
    
    # Cache management
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        return key in self._cache and time.time() < self._cache_ttl.get(key, 0)
    
    def _set_cache(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cache entry with TTL."""
        if ttl is None:
            ttl = self.cache_duration
        self._cache[key] = value
        self._cache_ttl[key] = time.time() + ttl
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """Get cache entry if valid."""
        if self._is_cache_valid(key):
            return self._cache[key]
        return None
    
    # Core MCP operations
    async def _execute_operation(self, operation: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an operation using the best available connection method.
        
        Args:
            operation: The operation to execute
            arguments: Arguments for the operation
            
        Returns:
            Dict containing the operation result
        """
        if not self.connected:
            if not await self.connect():
                raise MCPClientError("Failed to connect to PostgreSQL MCP")
        
        # Try direct connection first
        if self.external_server:
            try:
                return await self._direct_call_tool(operation, arguments)
            except Exception as e:
                self.logger.warning(f"Direct operation failed: {e}, trying HTTP")
        
        # Fallback to HTTP
        return await self._http_call_tool(operation, arguments)
    
    async def _direct_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation via direct connection."""
        if not self.external_server:
            raise MCPClientError("Direct server not available")
        
        try:
            if tool_name == 'query':
                query = arguments.get('query', '')
                params = arguments.get('params', [])
                result = await self.external_server.query(query, params)
                return {'success': True, 'data': result}
                
            elif tool_name == 'execute':
                query = arguments.get('query', '')
                params = arguments.get('params', [])
                result = await self.external_server.execute(query, params)
                return {'success': True, 'affected_rows': result}
                
            elif tool_name == 'list_tables':
                schema = arguments.get('schema', 'public')
                result = await self.external_server.list_tables(schema)
                return {'success': True, 'tables': result}
                
            elif tool_name == 'describe_table':
                table_name = arguments.get('table_name', '')
                schema = arguments.get('schema', 'public')
                result = await self.external_server.describe_table(schema, table_name)
                return {'success': True, 'description': result}
            
            else:
                # Handle custom operations
                return await self._handle_custom_operation(tool_name, arguments)
                
        except Exception as e:
            raise MCPClientError(f"Direct operation failed: {e}")
    
    async def _http_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation via HTTP."""
        if not self.http_session:
            raise MCPClientError("HTTP session not available")
        
        payload = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": f"{tool_name}-{int(time.time())}"
        }
        
        try:
            async with self.http_session.post(
                f"{self.mcp_server_url}/mcp/tools/call",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('error'):
                        raise MCPClientError(f"MCP tool error: {result['error']}")
                    return result.get('result', {})
                else:
                    error_text = await response.text()
                    raise MCPClientError(f"HTTP {response.status}: {error_text}")
        except aiohttp.ClientError as e:
            raise MCPClientError(f"Network error: {e}")
    
    async def _handle_custom_operation(self, operation: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom customer support operations."""
        if operation == 'get_customer_context':
            return await self._get_customer_context(arguments)
        elif operation == 'search_knowledge_base':
            return await self._search_knowledge_base(arguments)
        elif operation == 'save_interaction':
            return await self._save_interaction(arguments)
        elif operation == 'get_analytics':
            return await self._get_analytics(arguments)
        else:
            raise MCPClientError(f"Unknown custom operation: {operation}")
    
    # Customer support specific operations
    async def _get_customer_context(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive customer context."""
        customer_id = arguments.get('customer_id', '')
        
        if not customer_id:
            return {'success': False, 'error': 'customer_id required'}
        
        # Check cache first
        cache_key = f"customer_context:{customer_id}"
        cached_result = self._get_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Query customer information with related data
            query = """
            SELECT c.*, 
                   COUNT(st.ticket_id) as total_tickets,
                   COUNT(CASE WHEN st.status = 'open' THEN 1 END) as open_tickets,
                   AVG(CASE WHEN st.priority = 'high' THEN 3 
                            WHEN st.priority = 'medium' THEN 2 
                            ELSE 1 END) as avg_priority_score,
                   MAX(st.created_at) as last_ticket_date,
                   COUNT(cf.feedback_id) as total_feedback,
                   AVG(cf.rating) as avg_rating
            FROM customers c
            LEFT JOIN support_tickets st ON c.customer_id = st.customer_id
            LEFT JOIN customer_feedback cf ON c.customer_id = cf.customer_id
            WHERE c.customer_id = $1
            GROUP BY c.customer_id, c.first_name, c.last_name, c.email, 
                     c.phone, c.company, c.created_at, c.tier, c.status
            """
            
            result = await self._execute_operation('query', {
                'query': query,
                'params': [customer_id]
            })
            
            if result.get('success') and result.get('data'):
                customer_data = result['data'][0]
                response = {
                    'success': True,
                    'customer': customer_data
                }
                
                # Cache the result
                self._set_cache(cache_key, response, 300)  # 5 minutes cache
                return response
            else:
                return {'success': False, 'error': 'Customer not found'}
                
        except Exception as e:
            self.logger.error(f"Error getting customer context: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _search_knowledge_base(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base with full-text search."""
        search_term = arguments.get('search_term', '')
        limit = arguments.get('limit', 10)
        
        if not search_term:
            return {'success': False, 'error': 'search_term required'}
        
        try:
            # Use PostgreSQL full-text search
            query = """
            SELECT ka.*, 
                   ts_rank(to_tsvector('english', ka.title || ' ' || ka.content), 
                          plainto_tsquery('english', $1)) as relevance_score
            FROM knowledge_articles ka
            WHERE to_tsvector('english', ka.title || ' ' || ka.content) @@ 
                  plainto_tsquery('english', $1)
            ORDER BY relevance_score DESC
            LIMIT $2
            """
            
            result = await self._execute_operation('query', {
                'query': query,
                'params': [search_term, limit]
            })
            
            if result.get('success'):
                return {
                    'success': True,
                    'articles': result.get('data', [])
                }
            else:
                return {'success': False, 'error': 'Search failed'}
                
        except Exception as e:
            self.logger.error(f"Error searching knowledge base: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _save_interaction(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Save customer interaction."""
        interaction_data = arguments.get('interaction_data', {})
        
        if not interaction_data:
            return {'success': False, 'error': 'interaction_data required'}
        
        try:
            query = """
            INSERT INTO customer_interactions 
            (customer_id, interaction_type, content, metadata, created_at)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING interaction_id
            """
            
            params = [
                interaction_data.get('customer_id'),
                interaction_data.get('interaction_type'),
                interaction_data.get('content'),
                json.dumps(interaction_data.get('metadata', {})),
                datetime.utcnow()
            ]
            
            result = await self._execute_operation('query', {
                'query': query,
                'params': params
            })
            
            if result.get('success'):
                return {
                    'success': True,
                    'interaction_id': result.get('data', [{}])[0].get('interaction_id')
                }
            else:
                return {'success': False, 'error': 'Failed to save interaction'}
                
        except Exception as e:
            self.logger.error(f"Error saving interaction: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_analytics(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get analytics data with caching."""
        days = arguments.get('days', 30)
        
        # Check cache first
        cache_key = f"analytics:{days}"
        cached_result = self._get_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Multiple queries for comprehensive analytics
            queries = {
                'ticket_stats': """
                    SELECT 
                        COUNT(*) as total_tickets,
                        COUNT(CASE WHEN status = 'open' THEN 1 END) as open_tickets,
                        COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_tickets,
                        AVG(CASE WHEN priority = 'high' THEN 3 
                                 WHEN priority = 'medium' THEN 2 
                                 ELSE 1 END) as avg_priority
                    FROM support_tickets 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                """ % days,
                
                'customer_stats': """
                    SELECT 
                        COUNT(*) as total_customers,
                        COUNT(CASE WHEN created_at >= NOW() - INTERVAL '%s days' THEN 1 END) as new_customers
                    FROM customers
                """ % days,
                
                'response_times': """
                    SELECT 
                        AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/3600) as avg_response_hours
                    FROM support_tickets 
                    WHERE status = 'closed' 
                    AND created_at >= NOW() - INTERVAL '%s days'
                """ % days
            }
            
            analytics_data = {}
            
            for key, query in queries.items():
                result = await self._execute_operation('query', {'query': query})
                if result.get('success') and result.get('data'):
                    analytics_data[key] = result['data'][0]
            
            response = {
                'success': True,
                'analytics': analytics_data
            }
            
            # Cache for 1 hour
            self._set_cache(cache_key, response, 3600)
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting analytics: {e}")
            return {'success': False, 'error': str(e)}
    
    # High-level API methods for service layer
    async def get_customers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get customers from the database."""
        result = await self._execute_operation("query", {
            "query": "SELECT * FROM customers ORDER BY created_at DESC LIMIT $1",
            "params": [limit]
        })
        if result.get('success'):
            return result.get('data', [])
        else:
            raise MCPClientError(f"Failed to get customers: {result}")
    
    async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific customer by ID."""
        result = await self._execute_operation("query", {
            "query": "SELECT * FROM customers WHERE customer_id = $1",
            "params": [customer_id]
        })
        if result.get('success') and result.get('data'):
            return result['data'][0]
        return None
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer."""
        query = """
        INSERT INTO customers (customer_id, first_name, last_name, email, phone, company, created_at, tier, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
        """
        
        params = [
            customer_data.get('customer_id'),
            customer_data.get('first_name'),
            customer_data.get('last_name'),
            customer_data.get('email'),
            customer_data.get('phone'),
            customer_data.get('company'),
            customer_data.get('created_at'),
            customer_data.get('tier'),
            customer_data.get('status')
        ]
        
        result = await self._execute_operation("query", {"query": query, "params": params})
        if result.get('success') and result.get('data'):
            return result['data'][0]
        else:
            raise MCPClientError(f"Failed to create customer: {result}")
    
    async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer information."""
        # Build dynamic update query
        set_clauses = []
        params = []
        param_count = 1
        
        for key, value in updates.items():
            set_clauses.append(f"{key} = ${param_count}")
            params.append(value)
            param_count += 1
        
        params.append(customer_id)  # for WHERE clause
        
        query = f"""
        UPDATE customers 
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE customer_id = ${param_count}
        RETURNING *
        """
        
        result = await self._execute_operation("query", {"query": query, "params": params})
        if result.get('success') and result.get('data'):
            return result['data'][0]
        else:
            raise MCPClientError(f"Failed to update customer: {result}")
    
    async def get_tickets(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tickets from the database."""
        if status:
            query = "SELECT * FROM support_tickets WHERE status = $1 ORDER BY created_at DESC LIMIT $2"
            params = [status, limit]
        else:
            query = "SELECT * FROM support_tickets ORDER BY created_at DESC LIMIT $1"
            params = [limit]
            
        result = await self._execute_operation("query", {"query": query, "params": params})
        if result.get('success'):
            return result.get('data', [])
        else:
            raise MCPClientError(f"Failed to get tickets: {result}")
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ticket."""
        query = """
        INSERT INTO support_tickets (ticket_id, customer_id, subject, description, priority, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """
        
        params = [
            ticket_data.get('ticket_id'),
            ticket_data.get('customer_id'),
            ticket_data.get('subject'),
            ticket_data.get('description'),
            ticket_data.get('priority'),
            ticket_data.get('status'),
            ticket_data.get('created_at')
        ]
        
        result = await self._execute_operation("query", {"query": query, "params": params})
        if result.get('success') and result.get('data'):
            return result['data'][0]
        else:
            raise MCPClientError(f"Failed to create ticket: {result}")
    
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific ticket by ID."""
        result = await self._execute_operation("query", {
            "query": "SELECT * FROM support_tickets WHERE ticket_id = $1",
            "params": [ticket_id]
        })
        if result.get('success') and result.get('data'):
            return result['data'][0]
        return None
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update ticket information."""
        # Build dynamic update query
        set_clauses = []
        params = []
        param_count = 1
        
        for key, value in updates.items():
            set_clauses.append(f"{key} = ${param_count}")
            params.append(value)
            param_count += 1
        
        params.append(ticket_id)  # for WHERE clause
        
        query = f"""
        UPDATE support_tickets 
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE ticket_id = ${param_count}
        RETURNING *
        """
        
        result = await self._execute_operation("query", {"query": query, "params": params})
        if result.get('success') and result.get('data'):
            return result['data'][0]
        else:
            raise MCPClientError(f"Failed to update ticket: {result}")
    
    async def search_knowledge_base(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge base."""
        result = await self._search_knowledge_base({
            "search_term": search_term,
            "limit": limit
        })
        if result.get('success'):
            return result.get('articles', [])
        else:
            raise MCPClientError(f"Failed to search knowledge base: {result}")
    
    async def get_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics data."""
        result = await self._get_analytics({"days": days})
        if result.get('success'):
            return result.get('analytics', {})
        else:
            raise MCPClientError(f"Failed to get analytics: {result}")


# Global optimized MCP client instance
_optimized_mcp_client: Optional[OptimizedPostgreSQLMCPClient] = None


async def get_optimized_mcp_client(
    connection_string: Optional[str] = None,
    mcp_server_url: str = "http://localhost:8001",
    use_direct_connection: bool = True
) -> OptimizedPostgreSQLMCPClient:
    """Get or create the global optimized MCP client instance."""
    global _optimized_mcp_client
    if _optimized_mcp_client is None:
        _optimized_mcp_client = OptimizedPostgreSQLMCPClient(
            connection_string=connection_string,
            mcp_server_url=mcp_server_url,
            use_direct_connection=use_direct_connection
        )
        await _optimized_mcp_client.connect()
    return _optimized_mcp_client


async def close_optimized_mcp_client():
    """Close the global optimized MCP client instance."""
    global _optimized_mcp_client
    if _optimized_mcp_client:
        await _optimized_mcp_client.disconnect()
        _optimized_mcp_client = None
