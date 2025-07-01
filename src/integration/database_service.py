"""
Database service layer for the Genetic AI system
"""
import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from src.data_sources.rdbms_connector import EnhancedRDBMSConnector
from config.settings import CONFIG
import logging

class DatabaseService:
    """Centralized database service for the entire system"""
    
    def __init__(self):
        self.db = None
        self.logger = logging.getLogger("DatabaseService")
        self.initialized = False
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            self.db = EnhancedRDBMSConnector(CONFIG['database'])
            await self.db.connect()
            self.initialized = True
            self.logger.info("Database service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize database service: {str(e)}")
            raise
    
    async def process_customer_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a complete customer query workflow with database integration"""
        if not self.initialized:
            await self.initialize()
        
        try:
            customer_id = query_data.get('customer_id')
            query_text = query_data.get('query', '')
            
            # Create or update customer session
            session_id = await self._create_customer_session(customer_id, query_data)
            
            # Check if this should create a ticket
            should_create_ticket = await self._should_create_ticket(query_data)
            
            ticket_id = None
            if should_create_ticket:
                ticket_id = await self._create_support_ticket(query_data, session_id)
            
            # Return enhanced query data
            return {
                **query_data,
                'session_id': session_id,
                'ticket_id': ticket_id,
                'database_context': True
            }
            
        except Exception as e:
            self.logger.error(f"Error processing customer query: {str(e)}")
            return query_data
    
    async def _create_customer_session(self, customer_id: str, query_data: Dict[str, Any]) -> str:
        """Create or update customer session"""
        try:
            session_id = f"SESS_{customer_id}_{int(time.time())}"
            
            # This would be implemented based on your session management needs
            # For now, return the generated session ID
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error creating customer session: {str(e)}")
            return f"SESS_DEFAULT_{int(time.time())}"
    
    async def _should_create_ticket(self, query_data: Dict[str, Any]) -> bool:
        """Determine if query should create a support ticket"""
        # Simple logic - can be enhanced with ML
        query_text = query_data.get('query', '').lower()
        
        ticket_keywords = [
            'help', 'problem', 'issue', 'error', 'bug', 'broken', 
            'not working', 'failed', 'unable', 'cannot', 'billing',
            'refund', 'charge', 'payment'
        ]
        
        return any(keyword in query_text for keyword in ticket_keywords)
    
    async def _create_support_ticket(self, query_data: Dict[str, Any], session_id: str) -> Optional[str]:
        """Create a support ticket from query data"""
        try:
            # Get category prediction from query analysis (if available)
            category_id = await self._get_category_id(query_data.get('predicted_category', 'general'))
            
            ticket_data = {
                'customer_id': query_data['customer_id'],
                'category_id': category_id,
                'subject': query_data.get('subject', query_data['query'][:100]),
                'description': query_data['query'],
                'priority': query_data.get('predicted_priority', 'medium'),
                'source': 'ai',
                'tags': query_data.get('tags', []),
                'session_id': session_id
            }
            
            ticket_id = await self.db.create_ticket(ticket_data)
            
            if ticket_id:
                self.logger.info(f"Created ticket {ticket_id} for customer {query_data['customer_id']}")
            
            return ticket_id
            
        except Exception as e:
            self.logger.error(f"Error creating support ticket: {str(e)}")
            return None
    
    async def _get_category_id(self, category_name: str) -> Optional[int]:
        """Get category ID by name"""
        try:
            query = "SELECT id FROM categories WHERE name ILIKE %s LIMIT 1"
            
            with self.db.connection.cursor() as cursor:
                cursor.execute(query, (f'%{category_name}%',))
                result = cursor.fetchone()
                
                return result['id'] if result else 1  # Default to first category
                
        except Exception as e:
            self.logger.error(f"Error getting category ID: {str(e)}")
            return 1
    
    async def save_agent_interaction_result(self, result: Dict[str, Any]) -> bool:
        """Save the complete agent interaction result"""
        try:
            if not result.get('success'):
                return False
            
            # Update query interaction with response
            if result.get('query_id'):
                interaction_updates = {
                    'response_text': result.get('final_response', ''),
                    'response_type': result.get('response_type', 'ai_generated'),
                    'response_sources': result.get('sources_used', []),
                    'total_processing_time_ms': result.get('total_processing_time', 0),
                    'success_metrics': result.get('success_metrics', {})
                }
                
                await self._update_query_interaction(result['query_id'], interaction_updates)
            
            # Add ticket response if ticket was created
            if result.get('ticket_id'):
                response_data = {
                    'ticket_id': result['ticket_id'],
                    'responder_type': 'ai_agent',
                    'responder_id': 'genetic_ai_system',
                    'responder_name': 'Genetic AI Assistant',
                    'message': result.get('final_response', ''),
                    'is_auto_generated': True,
                    'processing_time_ms': result.get('total_processing_time', 0),
                    'ai_confidence_score': result.get('confidence_score', 0)
                }
                
                await self.db.add_ticket_response(response_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving agent interaction result: {str(e)}")
            return False
    
    async def _update_query_interaction(self, query_id: str, updates: Dict[str, Any]) -> bool:
        """Update query interaction record"""
        try:
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = %s")
                if isinstance(value, (dict, list)):
                    params.append(json.dumps(value))
                else:
                    params.append(value)
            
            params.append(query_id)
            
            query = f"""
            UPDATE query_interactions 
            SET {', '.join(set_clauses)}
            WHERE query_id = %s
            """
            
            with self.db.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error updating query interaction: {str(e)}")
            return False
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics from database"""
        try:
            return await self.db.get_system_analytics(days=1)
        except Exception as e:
            self.logger.error(f"Error getting system health: {str(e)}")
            return {}