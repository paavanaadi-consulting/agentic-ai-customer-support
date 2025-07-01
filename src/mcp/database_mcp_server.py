"""
MCP server for database operations
"""
import json
from typing import Dict, Any, List, Optional
from src.mcp.base_mcp_server import BaseMCPServer

class DatabaseMCPServer(BaseMCPServer):
    """MCP server for database operations"""
    
    def __init__(self, db_connector):
        tools = [
            'query_database',
            'get_customer_context',
            'search_knowledge_base',
            'save_interaction',
            'get_analytics'
        ]
        
        resources = [
            'db://customers',
            'db://tickets',
            'db://knowledge_articles',
            'db://interactions',
            'db://analytics'
        ]
        
        super().__init__(
            server_id="mcp_database",
            name="Database MCP Server",
            capabilities=['tools', 'resources', 'transactions'],
            tools=tools,
            resources=resources
        )
        
        self.db_connector = db_connector
    
    async def start(self):
        """Start the database MCP server"""
        self.running = True
        self.logger.info("Database MCP server started")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database operations"""
        if not self.db_connector or not hasattr(self.db_connector, 'connection'):
            return {
                'success': False,
                'error': 'Database connection not available'
            }
            
        try:
            if tool_name == 'query_database':
                query = arguments.get('query')
                params = arguments.get('params', [])
                
                if not query:
                    return {
                        'success': False,
                        'error': 'Query parameter is required'
                    }
                
                with self.db_connector.connection.cursor() as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                return {
                    'success': True,
                    'data': [dict(row) for row in results],
                    'row_count': len(results)
                }
                
            elif tool_name == 'get_customer_context':
                customer_id = arguments.get('customer_id')
                context_query = """
                    SELECT c.*, COUNT(st.ticket_id) as ticket_count,
                           AVG(st.satisfaction_score) as avg_satisfaction
                    FROM customers c
                    LEFT JOIN support_tickets st ON c.customer_id = st.customer_id
                    WHERE c.customer_id = %s
                    GROUP BY c.customer_id
                """
                
                with self.db_connector.connection.cursor() as cursor:
                    cursor.execute(context_query, (customer_id,))
                    result = cursor.fetchone()
                    
                return {
                    'success': True,
                    'customer_context': dict(result) if result else None
                }
                
            elif tool_name == 'search_knowledge_base':
                search_term = arguments.get('search_term')
                limit = arguments.get('limit', 10)
                
                search_query = """
                    SELECT * FROM knowledge_articles 
                    WHERE title ILIKE %s OR content ILIKE %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                
                search_pattern = f"%{search_term}%"
                with self.db_connector.connection.cursor() as cursor:
                    cursor.execute(search_query, (search_pattern, search_pattern, limit))
                    results = cursor.fetchall()
                    
                return {
                    'success': True,
                    'articles': [dict(row) for row in results]
                }
                
            elif tool_name == 'save_interaction':
                interaction_data = arguments.get('interaction_data')
                
                insert_query = """
                    INSERT INTO query_interactions 
                    (query_id, customer_id, query_text, agent_response, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """
                
                with self.db_connector.connection.cursor() as cursor:
                    cursor.execute(insert_query, (
                        interaction_data.get('query_id'),
                        interaction_data.get('customer_id'),
                        interaction_data.get('query_text'),
                        interaction_data.get('agent_response'),
                        interaction_data.get('created_at')
                    ))
                    
                return {
                    'success': True,
                    'message': 'Interaction saved successfully'
                }
                
            elif tool_name == 'get_analytics':
                time_period = arguments.get('time_period', '7 days')
                
                analytics_query = """
                    SELECT 
                        COUNT(*) as total_queries,
                        AVG(customer_satisfaction) as avg_satisfaction,
                        COUNT(DISTINCT customer_id) as unique_customers
                    FROM query_interactions 
                    WHERE created_at >= NOW() - INTERVAL %s
                """
                
                with self.db_connector.connection.cursor() as cursor:
                    cursor.execute(analytics_query, (time_period,))
                    result = cursor.fetchone()
                    
                return {
                    'success': True,
                    'analytics': dict(result) if result else {}
                }
                
            else:
                return {
                    'success': False,
                    'error': f'Unknown tool: {tool_name}'
                }
                
        except Exception as e:
            self.logger.error(f"Database tool error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Get database resource"""
        try:
            if resource_uri == 'db://customers':
                query = "SELECT * FROM customers LIMIT 100"
            elif resource_uri == 'db://tickets':
                query = "SELECT * FROM support_tickets ORDER BY created_at DESC LIMIT 100"
            elif resource_uri == 'db://knowledge_articles':
                query = "SELECT * FROM knowledge_articles ORDER BY created_at DESC LIMIT 100"
            elif resource_uri == 'db://interactions':
                query = "SELECT * FROM query_interactions ORDER BY created_at DESC LIMIT 100"
            elif resource_uri == 'db://analytics':
                query = """
                    SELECT 
                        COUNT(*) as total_interactions,
                        AVG(customer_satisfaction) as avg_satisfaction,
                        COUNT(DISTINCT customer_id) as unique_customers
                    FROM query_interactions
                """
            else:
                return {
                    'success': False,
                    'error': f'Unknown resource: {resource_uri}'
                }
            
            with self.db_connector.connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
            return {
                'success': True,
                'contents': [
                    {
                        'uri': resource_uri,
                        'mimeType': 'application/json',
                        'text': json.dumps([dict(row) for row in results], indent=2)
                    }
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Database resource error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _get_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed tool definitions"""
        definitions = {
            'query_database': {
                "name": "query_database",
                "description": "Execute a SQL query against the database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query to execute"},
                        "params": {"type": "array", "description": "Query parameters"}
                    },
                    "required": ["query"]
                }
            },
            'get_customer_context': {
                "name": "get_customer_context",
                "description": "Get comprehensive customer context and history",
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
                "description": "Search knowledge articles for relevant information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "search_term": {"type": "string", "description": "Search term"},
                        "limit": {"type": "integer", "description": "Maximum results", "default": 10}
                    },
                    "required": ["search_term"]
                }
            }
        }
        
        return definitions.get(tool_name, await super()._get_tool_definition(tool_name))