"""
Simple MCP Postgres Server
Minimal implementation for database operations via MCP protocol
"""
import asyncio
import os
import logging
import json
from typing import Dict, Any, List, Optional
import asyncpg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any] = {}
    id: Optional[str] = None

class MCPResponse(BaseModel):
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class SimpleMCPPostgresServer:
    """Simple MCP server for PostgreSQL operations"""
    
    def __init__(self):
        self.db_pool = None
        self.capabilities = ['tools', 'resources']
        self.tools = [
            'query_database',
            'get_customers',
            'create_customer',
            'update_customer',
            'get_tickets',
            'create_ticket',
            'update_ticket',
            'get_ticket_details',
            'search_knowledge_base',
            'get_analytics'
        ]
        self.resources = [
            'postgresql://customers',
            'postgresql://tickets',
            'postgresql://knowledge_articles',
            'postgresql://analytics'
        ]
        
    async def initialize_db(self):
        """Initialize database connection pool"""
        try:
            db_host = os.getenv('DB_HOST', 'postgres')
            db_port = int(os.getenv('DB_PORT', '5432'))
            db_name = os.getenv('DB_NAME', 'customer_support')
            db_user = os.getenv('DB_USER', 'admin')
            db_password = os.getenv('DB_PASSWORD', 'password')
            
            dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            self.db_pool = await asyncpg.create_pool(
                dsn,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            
            logger.info("Database connection pool initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    async def execute_query(self, query: str, params: List = None) -> List[Dict]:
        """Execute a database query"""
        if not self.db_pool:
            raise Exception("Database not connected")
            
        async with self.db_pool.acquire() as conn:
            if params:
                rows = await conn.fetch(query, *params)
            else:
                rows = await conn.fetch(query)
            
            return [dict(row) for row in rows]
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool calls"""
        try:
            if tool_name == 'query_database':
                query = arguments.get('query', '')
                params = arguments.get('params', [])
                
                if not query:
                    return {'error': 'Query parameter is required'}
                
                results = await self.execute_query(query, params)
                return {
                    'success': True,
                    'data': results,
                    'count': len(results)
                }
                
            elif tool_name == 'get_customers':
                limit = arguments.get('limit', 50)
                offset = arguments.get('offset', 0)
                
                query = """
                SELECT customer_id, first_name, last_name, email, company, tier, 
                       total_tickets, satisfaction_avg, created_at
                FROM customers 
                ORDER BY created_at DESC 
                LIMIT $1 OFFSET $2
                """
                
                results = await self.execute_query(query, [limit, offset])
                return {
                    'success': True,
                    'customers': results,
                    'count': len(results)
                }
                
            elif tool_name == 'get_tickets':
                status = arguments.get('status')
                customer_id = arguments.get('customer_id')
                limit = arguments.get('limit', 50)
                offset = arguments.get('offset', 0)
                
                query = """
                SELECT st.ticket_id, st.customer_id, st.subject, st.status, 
                       st.priority, st.created_at, c.first_name, c.last_name,
                       a.name as agent_name, cat.name as category_name
                FROM support_tickets st
                LEFT JOIN customers c ON st.customer_id = c.customer_id
                LEFT JOIN agents a ON st.assigned_agent_id = a.id
                LEFT JOIN categories cat ON st.category_id = cat.id
                WHERE 1=1
                """
                
                params = []
                param_count = 0
                
                if status:
                    param_count += 1
                    query += f" AND st.status = ${param_count}"
                    params.append(status)
                
                if customer_id:
                    param_count += 1
                    query += f" AND st.customer_id = ${param_count}"
                    params.append(customer_id)
                
                query += f" ORDER BY st.created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
                params.extend([limit, offset])
                
                results = await self.execute_query(query, params)
                return {
                    'success': True,
                    'tickets': results,
                    'count': len(results)
                }
                
            elif tool_name == 'get_ticket_details':
                ticket_id = arguments.get('ticket_id')
                
                if not ticket_id:
                    return {'error': 'ticket_id parameter is required'}
                
                # Get ticket details
                ticket_query = """
                SELECT st.*, c.first_name, c.last_name, c.email as customer_email,
                       a.name as agent_name, cat.name as category_name
                FROM support_tickets st
                LEFT JOIN customers c ON st.customer_id = c.customer_id
                LEFT JOIN agents a ON st.assigned_agent_id = a.id
                LEFT JOIN categories cat ON st.category_id = cat.id
                WHERE st.ticket_id = $1
                """
                
                # Get ticket responses
                responses_query = """
                SELECT * FROM ticket_responses 
                WHERE ticket_id = $1 
                ORDER BY created_at ASC
                """
                
                ticket_data = await self.execute_query(ticket_query, [ticket_id])
                responses_data = await self.execute_query(responses_query, [ticket_id])
                
                if not ticket_data:
                    return {'error': 'Ticket not found'}
                
                return {
                    'success': True,
                    'ticket': ticket_data[0],
                    'responses': responses_data
                }
                
            elif tool_name == 'search_knowledge_base':
                search_term = arguments.get('search_term', '')
                limit = arguments.get('limit', 10)
                
                query = """
                SELECT article_id, title, summary, content, tags, 
                       views_count, helpful_votes, unhelpful_votes
                FROM knowledge_articles 
                WHERE status = 'published' 
                AND (title ILIKE $1 OR content ILIKE $1 OR $1 = ANY(tags))
                ORDER BY helpful_votes DESC, views_count DESC
                LIMIT $2
                """
                
                search_pattern = f"%{search_term}%"
                results = await self.execute_query(query, [search_pattern, limit])
                
                return {
                    'success': True,
                    'articles': results,
                    'count': len(results)
                }
                
            elif tool_name == 'get_analytics':
                days = arguments.get('days', 30)
                
                query = """
                SELECT 
                    COUNT(*) as total_tickets,
                    COUNT(*) FILTER (WHERE status = 'open') as open_tickets,
                    COUNT(*) FILTER (WHERE status = 'resolved') as resolved_tickets,
                    COUNT(*) FILTER (WHERE priority = 'high') as high_priority,
                    AVG(satisfaction_score) as avg_satisfaction,
                    AVG(EXTRACT(epoch FROM (resolved_at - created_at))/3600) 
                        FILTER (WHERE resolved_at IS NOT NULL) as avg_resolution_hours,
                    (SELECT COUNT(*) FROM customers) as total_customers
                FROM support_tickets
                WHERE created_at >= NOW() - INTERVAL '%s days'
                """ % days
                
                results = await self.execute_query(query)
                
                return {
                    'success': True,
                    'analytics': results[0] if results else {},
                    'period_days': days
                }
                
            elif tool_name == 'create_customer':
                # Extract customer data from arguments
                customer_data = arguments.get('customer_data', {})
                
                if not customer_data:
                    return {'error': 'customer_data parameter is required'}
                
                # Insert customer into database
                query = """
                INSERT INTO customers (customer_id, first_name, last_name, email, phone, company, tier, status, created_at)
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
                    customer_data.get('tier', 'standard'),
                    customer_data.get('status', 'active'),
                    customer_data.get('created_at')
                ]
                
                results = await self.execute_query(query, params)
                
                if results:
                    return {
                        'success': True,
                        'customer': results[0]
                    }
                else:
                    return {'error': 'Failed to create customer'}
                    
            elif tool_name == 'update_customer':
                customer_id = arguments.get('customer_id')
                updates = arguments.get('updates', {})
                
                if not customer_id or not updates:
                    return {'error': 'customer_id and updates parameters are required'}
                
                # Build dynamic update query
                set_clauses = []
                params = []
                param_index = 1
                
                for field, value in updates.items():
                    if field != 'customer_id':  # Don't allow updating the primary key
                        set_clauses.append(f"{field} = ${param_index}")
                        params.append(value)
                        param_index += 1
                
                if not set_clauses:
                    return {'error': 'No valid fields to update'}
                
                query = f"""
                UPDATE customers 
                SET {', '.join(set_clauses)}
                WHERE customer_id = ${param_index}
                RETURNING *
                """
                params.append(customer_id)
                
                results = await self.execute_query(query, params)
                
                if results:
                    return {
                        'success': True,
                        'customer': results[0]
                    }
                else:
                    return {'error': 'Customer not found or update failed'}
                    
            elif tool_name == 'create_ticket':
                # Extract ticket data from arguments
                ticket_data = arguments.get('ticket_data', {})
                
                if not ticket_data:
                    return {'error': 'ticket_data parameter is required'}
                
                # Insert ticket into database
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
                    ticket_data.get('priority', 'medium'),
                    ticket_data.get('status', 'open'),
                    ticket_data.get('created_at')
                ]
                
                results = await self.execute_query(query, params)
                
                if results:
                    return {
                        'success': True,
                        'ticket': results[0]
                    }
                else:
                    return {'error': 'Failed to create ticket'}
                    
            elif tool_name == 'update_ticket':
                ticket_id = arguments.get('ticket_id')
                updates = arguments.get('updates', {})
                
                if not ticket_id or not updates:
                    return {'error': 'ticket_id and updates parameters are required'}
                
                # Build dynamic update query
                set_clauses = []
                params = []
                param_index = 1
                
                for field, value in updates.items():
                    if field != 'ticket_id':  # Don't allow updating the primary key
                        set_clauses.append(f"{field} = ${param_index}")
                        params.append(value)
                        param_index += 1
                
                if not set_clauses:
                    return {'error': 'No valid fields to update'}
                
                query = f"""
                UPDATE support_tickets 
                SET {', '.join(set_clauses)}
                WHERE ticket_id = ${param_index}
                RETURNING *
                """
                params.append(ticket_id)
                
                results = await self.execute_query(query, params)
                
                if results:
                    return {
                        'success': True,
                        'ticket': results[0]
                    }
                else:
                    return {'error': 'Ticket not found or update failed'}
                
            else:
                return {'error': f'Unknown tool: {tool_name}'}
                
        except Exception as e:
            logger.error(f"Error in tool call {tool_name}: {e}")
            return {'error': str(e)}
    
    async def handle_resource_request(self, resource: str) -> Dict[str, Any]:
        """Handle MCP resource requests"""
        try:
            if resource == 'postgresql://customers':
                query = "SELECT COUNT(*) as total FROM customers"
                result = await self.execute_query(query)
                return {
                    'resource': resource,
                    'data': {'total_customers': result[0]['total']}
                }
                
            elif resource == 'postgresql://tickets':
                query = """
                SELECT status, COUNT(*) as count 
                FROM support_tickets 
                GROUP BY status
                """
                results = await self.execute_query(query)
                return {
                    'resource': resource,
                    'data': {'ticket_status_counts': results}
                }
                
            elif resource == 'postgresql://knowledge_articles':
                query = """
                SELECT COUNT(*) as total, 
                       COUNT(*) FILTER (WHERE status = 'published') as published
                FROM knowledge_articles
                """
                result = await self.execute_query(query)
                return {
                    'resource': resource,
                    'data': result[0]
                }
                
            elif resource == 'postgresql://analytics':
                query = """
                SELECT 
                    (SELECT COUNT(*) FROM customers) as total_customers,
                    (SELECT COUNT(*) FROM support_tickets) as total_tickets,
                    (SELECT COUNT(*) FROM knowledge_articles) as total_articles,
                    (SELECT AVG(satisfaction_score) FROM support_tickets WHERE satisfaction_score IS NOT NULL) as avg_satisfaction
                """
                result = await self.execute_query(query)
                return {
                    'resource': resource,
                    'data': result[0]
                }
                
            else:
                return {'error': f'Unknown resource: {resource}'}
                
        except Exception as e:
            logger.error(f"Error in resource request {resource}: {e}")
            return {'error': str(e)}

# Initialize the MCP server
mcp_server = SimpleMCPPostgresServer()

# FastAPI app
app = FastAPI(title="MCP Postgres Server", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Initialize the MCP server on startup"""
    success = await mcp_server.initialize_db()
    if not success:
        logger.error("Failed to initialize database connection")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if mcp_server.db_pool:
            async with mcp_server.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return {
                "status": "healthy",
                "database": "connected",
                "capabilities": mcp_server.capabilities,
                "tools": len(mcp_server.tools),
                "resources": len(mcp_server.resources)
            }
        else:
            return {
                "status": "unhealthy",
                "database": "disconnected"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/mcp/initialize")
async def mcp_initialize():
    """MCP initialize endpoint"""
    return {
        "capabilities": {
            "tools": {},
            "resources": {}
        },
        "serverInfo": {
            "name": "postgres-mcp-server",
            "version": "1.0.0"
        }
    }

@app.get("/mcp/tools/list")
async def list_tools():
    """List available MCP tools"""
    return {
        "tools": [
            {"name": tool, "description": f"Execute {tool} operation"}
            for tool in mcp_server.tools
        ]
    }

@app.get("/mcp/resources/list")
async def list_resources():
    """List available MCP resources"""
    return {
        "resources": [
            {"uri": resource, "description": f"Access {resource} data"}
            for resource in mcp_server.resources
        ]
    }

@app.post("/mcp/tools/call")
async def call_tool(request: MCPRequest):
    """Call an MCP tool"""
    try:
        tool_name = request.params.get('name')
        arguments = request.params.get('arguments', {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name is required")
        
        result = await mcp_server.handle_tool_call(tool_name, arguments)
        
        return MCPResponse(
            result=result,
            id=request.id
        )
        
    except Exception as e:
        return MCPResponse(
            error={"code": -32603, "message": str(e)},
            id=request.id
        )

@app.post("/mcp/resources/read")
async def read_resource(request: MCPRequest):
    """Read an MCP resource"""
    try:
        resource_uri = request.params.get('uri')
        
        if not resource_uri:
            raise HTTPException(status_code=400, detail="Resource URI is required")
        
        result = await mcp_server.handle_resource_request(resource_uri)
        
        return MCPResponse(
            result=result,
            id=request.id
        )
        
    except Exception as e:
        return MCPResponse(
            error={"code": -32603, "message": str(e)},
            id=request.id
        )

if __name__ == "__main__":
    uvicorn.run(
        "mcp_postgres_main:app",
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
