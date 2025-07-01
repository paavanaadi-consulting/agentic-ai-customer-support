"""
Wrapper for the external postgres-mcp package
Integrates with our existing MCP architecture
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from src.mcp.base_mcp_server import BaseMCPServer

try:
    # Import the external postgres-mcp package
    from postgres_mcp import PostgresMCPServer as ExternalPostgresMCPServer
    POSTGRES_MCP_AVAILABLE = True
except ImportError:
    POSTGRES_MCP_AVAILABLE = False
    ExternalPostgresMCPServer = None

class PostgresMCPWrapper(BaseMCPServer):
    """
    Wrapper for the external postgres-mcp package
    Provides a consistent interface with our MCP architecture
    """
    
    def __init__(self, connection_string: str):
        tools = [
            'query',
            'execute',
            'list_tables',
            'describe_table',
            'get_schema',
            'search_schema'
        ]
        
        resources = [
            'postgresql://tables',
            'postgresql://schemas',
            'postgresql://views',
            'postgresql://functions'
        ]
        
        super().__init__(
            server_id="postgres_mcp_external",
            name="PostgreSQL MCP Server (External)",
            capabilities=['tools', 'resources', 'transactions'],
            tools=tools,
            resources=resources
        )
        
        self.connection_string = connection_string
        self.external_server = None
        self.logger = logging.getLogger("PostgresMCPWrapper")
        
        if not POSTGRES_MCP_AVAILABLE:
            self.logger.warning("postgres-mcp package not available. Install with: pip install git+https://github.com/crystaldba/postgres-mcp.git")
    
    async def start(self):
        """Start the PostgreSQL MCP server"""
        if not POSTGRES_MCP_AVAILABLE:
            raise ImportError("postgres-mcp package not available")
        
        try:
            # Initialize the external MCP server
            self.external_server = ExternalPostgresMCPServer(self.connection_string)
            await self.external_server.start()
            
            self.running = True
            self.logger.info("PostgreSQL MCP wrapper started")
            
        except Exception as e:
            self.logger.error(f"Failed to start PostgreSQL MCP server: {e}")
            raise
    
    async def start_as_server(self):
        """Start the wrapper as a standalone server (for Docker compatibility)"""
        await self.initialize()
        self.logger.info("Postgres MCP wrapper started as standalone server")
        
        # Keep the server running
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the PostgreSQL MCP server"""
        if self.external_server:
            await self.external_server.stop()
            self.external_server = None
        
        self.running = False
        self.logger.info("PostgreSQL MCP wrapper stopped")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PostgreSQL operations via external MCP server"""
        if not self.external_server:
            return {
                'success': False,
                'error': 'Server not started'
            }
        
        try:
            # Map our tool names to external server methods
            if tool_name == 'query':
                query = arguments.get('query', '')
                params = arguments.get('params', [])
                result = await self.external_server.query(query, params)
                
                return {
                    'success': True,
                    'result': result
                }
                
            elif tool_name == 'execute':
                query = arguments.get('query', '')
                params = arguments.get('params', [])
                result = await self.external_server.execute(query, params)
                
                return {
                    'success': True,
                    'affected_rows': result
                }
                
            elif tool_name == 'list_tables':
                schema = arguments.get('schema', 'public')
                result = await self.external_server.list_tables(schema)
                
                return {
                    'success': True,
                    'tables': result
                }
                
            elif tool_name == 'describe_table':
                table_name = arguments.get('table_name', '')
                schema = arguments.get('schema', 'public')
                result = await self.external_server.describe_table(schema, table_name)
                
                return {
                    'success': True,
                    'description': result
                }
                
            elif tool_name == 'get_schema':
                schema = arguments.get('schema', 'public')
                result = await self.external_server.get_schema(schema)
                
                return {
                    'success': True,
                    'schema': result
                }
                
            elif tool_name == 'search_schema':
                search_term = arguments.get('search_term', '')
                result = await self.external_server.search_schema(search_term)
                
                return {
                    'success': True,
                    'results': result
                }
                
            # Fallback to our custom methods for customer support specific operations
            elif tool_name == 'get_customer_context':
                return await self._get_customer_context(arguments)
                
            elif tool_name == 'search_knowledge_base':
                return await self._search_knowledge_base(arguments)
                
            elif tool_name == 'save_interaction':
                return await self._save_interaction(arguments)
                
            elif tool_name == 'get_analytics':
                return await self._get_analytics(arguments)
                
            else:
                return {
                    'success': False,
                    'error': f'Unknown tool: {tool_name}'
                }
                
        except Exception as e:
            self.logger.error(f"Tool execution error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_customer_context(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get customer context using external MCP server"""
        customer_id = arguments.get('customer_id', '')
        
        if not customer_id:
            return {'success': False, 'error': 'customer_id required'}
        
        try:
            # Query customer information
            customer_query = """
            SELECT c.*, 
                   COUNT(st.ticket_id) as total_tickets,
                   COUNT(CASE WHEN st.status = 'open' THEN 1 END) as open_tickets,
                   AVG(st.satisfaction_score) as avg_satisfaction
            FROM customers c
            LEFT JOIN support_tickets st ON c.customer_id = st.customer_id
            WHERE c.customer_id = %s
            GROUP BY c.customer_id, c.name, c.email, c.phone, c.created_at, c.updated_at
            """
            
            result = await self.external_server.query(customer_query, [customer_id])
            
            if result and len(result) > 0:
                customer_data = result[0]
                
                # Get recent interactions
                interactions_query = """
                SELECT * FROM query_interactions 
                WHERE customer_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10
                """
                
                interactions = await self.external_server.query(interactions_query, [customer_id])
                
                return {
                    'success': True,
                    'customer': customer_data,
                    'recent_interactions': interactions
                }
            else:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _search_knowledge_base(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base using external MCP server"""
        query = arguments.get('query', '')
        limit = arguments.get('limit', 10)
        
        try:
            search_query = """
            SELECT ka.*, 
                   ts_rank(to_tsvector('english', title || ' ' || content), plainto_tsquery('english', %s)) as relevance
            FROM knowledge_articles ka
            WHERE to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', %s)
            ORDER BY relevance DESC, created_at DESC
            LIMIT %s
            """
            
            result = await self.external_server.query(search_query, [query, query, limit])
            
            return {
                'success': True,
                'articles': result,
                'total_found': len(result)
            }
            
        except Exception as e:
            # Fallback to simple LIKE search if full-text search fails
            try:
                fallback_query = """
                SELECT * FROM knowledge_articles 
                WHERE title ILIKE %s OR content ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
                """
                
                search_term = f"%{query}%"
                result = await self.external_server.query(fallback_query, [search_term, search_term, limit])
                
                return {
                    'success': True,
                    'articles': result,
                    'total_found': len(result),
                    'search_method': 'fallback'
                }
                
            except Exception as fallback_error:
                return {
                    'success': False,
                    'error': str(fallback_error)
                }
    
    async def _save_interaction(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Save customer interaction using external MCP server"""
        interaction_data = arguments.get('interaction_data', {})
        
        required_fields = ['interaction_id', 'customer_id', 'query_text']
        if not all(field in interaction_data for field in required_fields):
            return {
                'success': False,
                'error': f'Missing required fields: {required_fields}'
            }
        
        try:
            insert_query = """
            INSERT INTO query_interactions 
            (interaction_id, query_id, customer_id, query_text, agent_response, 
             customer_satisfaction, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            
            params = [
                interaction_data.get('interaction_id'),
                interaction_data.get('query_id', ''),
                interaction_data.get('customer_id'),
                interaction_data.get('query_text'),
                interaction_data.get('agent_response', ''),
                interaction_data.get('customer_satisfaction')
            ]
            
            result = await self.external_server.execute(insert_query, params)
            
            return {
                'success': True,
                'affected_rows': result,
                'interaction_id': interaction_data.get('interaction_id')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_analytics(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get analytics data using external MCP server"""
        days = arguments.get('days', 7)
        
        try:
            analytics_query = """
            SELECT 
                COUNT(*) as total_interactions,
                COUNT(DISTINCT customer_id) as unique_customers,
                AVG(customer_satisfaction) as avg_satisfaction,
                COUNT(CASE WHEN customer_satisfaction >= 4 THEN 1 END) as positive_feedback,
                COUNT(CASE WHEN customer_satisfaction <= 2 THEN 1 END) as negative_feedback
            FROM query_interactions 
            WHERE created_at >= NOW() - INTERVAL '%s days'
            """
            
            result = await self.external_server.query(analytics_query, [days])
            
            return {
                'success': True,
                'analytics': result[0] if result else {},
                'period_days': days
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Get PostgreSQL resources via external MCP server"""
        if not self.external_server:
            return {
                'success': False,
                'error': 'Server not started'
            }
        
        try:
            # Delegate to external server
            result = await self.external_server.get_resource(resource_uri)
            return result
            
        except Exception as e:
            self.logger.error(f"Resource error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool definitions"""
        definitions = {
            'query': {
                "name": "query",
                "description": "Execute a SELECT query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query"},
                        "params": {"type": "array", "description": "Query parameters"}
                    },
                    "required": ["query"]
                }
            },
            'execute': {
                "name": "execute",
                "description": "Execute INSERT/UPDATE/DELETE query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query"},
                        "params": {"type": "array", "description": "Query parameters"}
                    },
                    "required": ["query"]
                }
            },
            'get_customer_context': {
                "name": "get_customer_context",
                "description": "Get comprehensive customer context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": "Customer ID"}
                    },
                    "required": ["customer_id"]
                }
            },
            'search_knowledge_base': {
                "name": "search_knowledge_base",
                "description": "Search knowledge articles",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Result limit"}
                    },
                    "required": ["query"]
                }
            }
        }
        
        return definitions.get(tool_name, await super()._get_tool_definition(tool_name))
