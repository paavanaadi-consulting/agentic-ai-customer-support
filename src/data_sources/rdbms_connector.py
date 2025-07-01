"""
Enhanced RDBMS connector with full database schema integration
"""
import asyncio
import psycopg2
import psycopg2.extras
from typing import Dict, Any, List, Optional, Tuple
import logging
import json
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

class EnhancedRDBMSConnector:
    """Enhanced PostgreSQL connector with full customer support schema"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.logger = logging.getLogger("EnhancedRDBMSConnector")
        self.connected = False
    
    async def connect(self):
        """Establish database connection"""
        try:
            connection_string = (
                f"host={self.config.host} "
                f"port={self.config.port} "
                f"dbname={self.config.database} "
                f"user={self.config.username} "
                f"password={self.config.password}"
            )
            
            self.connection = psycopg2.connect(
                connection_string,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            self.connection.autocommit = True
            
            self.connected = True
            self.logger.info("Connected to PostgreSQL database")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    # =====================================================
    # CUSTOMER MANAGEMENT
    # =====================================================
    
    async def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get complete customer profile with stats"""
        try:
            query = """
            SELECT 
                c.*,
                cs.total_tickets,
                cs.open_tickets,
                cs.resolved_tickets,
                cs.avg_resolution_hours,
                cs.customer_since,
                cs.last_seen_at as last_activity
            FROM customers c
            LEFT JOIN customer_summary cs ON c.customer_id = cs.customer_id
            WHERE c.customer_id = %s
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (customer_id,))
                result = cursor.fetchone()
                
                if result:
                    return dict(result)
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting customer profile: {str(e)}")
            return {}
    
    async def get_customer_context(self, customer_id: str, include_history: bool = True) -> Dict[str, Any]:
        """Get comprehensive customer context for AI agents"""
        try:
            context = {}
            
            # Basic customer info
            customer = await self.get_customer_profile(customer_id)
            context['customer'] = customer
            
            if not include_history:
                return context
            
            # Recent tickets (last 10)
            recent_tickets = await self.get_customer_tickets(customer_id, limit=10)
            context['recent_tickets'] = recent_tickets
            
            # Recent interactions (last 20)
            recent_interactions = await self.get_customer_interactions(customer_id, limit=20)
            context['recent_interactions'] = recent_interactions
            
            # Customer preferences and patterns
            patterns = await self.analyze_customer_patterns(customer_id)
            context['patterns'] = patterns
            
            # Outstanding issues
            open_tickets = await self.get_customer_tickets(customer_id, status='open')
            context['open_tickets'] = open_tickets
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting customer context: {str(e)}")
            return {}
    
    async def get_customer_tickets(self, customer_id: str, status: str = None, 
                                 limit: int = 50) -> List[Dict[str, Any]]:
        """Get customer tickets with optional status filter"""
        try:
            base_query = """
            SELECT 
                st.*,
                c.name as category_name,
                a.name as agent_name,
                a.email as agent_email
            FROM support_tickets st
            LEFT JOIN categories c ON st.category_id = c.id
            LEFT JOIN agents a ON st.assigned_agent_id = a.id
            WHERE st.customer_id = %s
            """
            
            params = [customer_id]
            
            if status:
                base_query += " AND st.status = %s"
                params.append(status)
            
            base_query += " ORDER BY st.created_at DESC LIMIT %s"
            params.append(limit)
            
            with self.connection.cursor() as cursor:
                cursor.execute(base_query, params)
                results = cursor.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            self.logger.error(f"Error getting customer tickets: {str(e)}")
            return []
    
    async def get_customer_interactions(self, customer_id: str, 
                                      limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent customer interactions"""
        try:
            query = """
            SELECT *
            FROM query_interactions
            WHERE customer_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (customer_id, limit))
                results = cursor.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            self.logger.error(f"Error getting customer interactions: {str(e)}")
            return []
    
    async def analyze_customer_patterns(self, customer_id: str) -> Dict[str, Any]:
        """Analyze customer behavior patterns"""
        try:
            # Common categories
            category_query = """
            SELECT 
                c.name as category,
                COUNT(*) as count,
                AVG(st.satisfaction_score) as avg_satisfaction
            FROM support_tickets st
            JOIN categories c ON st.category_id = c.id
            WHERE st.customer_id = %s
            GROUP BY c.name
            ORDER BY count DESC
            LIMIT 5
            """
            
            # Typical response times
            timing_query = """
            SELECT 
                AVG(EXTRACT(epoch FROM (first_response_at - created_at))/60) as avg_first_response_minutes,
                AVG(EXTRACT(epoch FROM (resolved_at - created_at))/3600) as avg_resolution_hours
            FROM support_tickets
            WHERE customer_id = %s AND resolved_at IS NOT NULL
            """
            
            # Preferred communication times
            time_pattern_query = """
            SELECT 
                EXTRACT(hour FROM created_at) as hour,
                COUNT(*) as interaction_count
            FROM query_interactions
            WHERE customer_id = %s
            GROUP BY EXTRACT(hour FROM created_at)
            ORDER BY interaction_count DESC
            LIMIT 3
            """
            
            patterns = {}
            
            with self.connection.cursor() as cursor:
                # Common categories
                cursor.execute(category_query, (customer_id,))
                patterns['common_categories'] = [dict(row) for row in cursor.fetchall()]
                
                # Timing patterns
                cursor.execute(timing_query, (customer_id,))
                timing = cursor.fetchone()
                patterns['timing'] = dict(timing) if timing else {}
                
                # Time patterns
                cursor.execute(time_pattern_query, (customer_id,))
                patterns['preferred_hours'] = [dict(row) for row in cursor.fetchall()]
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing customer patterns: {str(e)}")
            return {}
    
    # =====================================================
    # TICKET MANAGEMENT
    # =====================================================
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> str:
        """Create a new support ticket"""
        try:
            # Generate ticket ID
            ticket_id = f"TKT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ticket_data['customer_id'][-4:]}"
            
            query = """
            INSERT INTO support_tickets 
            (ticket_id, customer_id, category_id, subject, description, 
             priority, source, tags, estimated_resolution_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING ticket_id
            """
            
            params = (
                ticket_id,
                ticket_data['customer_id'],
                ticket_data.get('category_id'),
                ticket_data['subject'],
                ticket_data['description'],
                ticket_data.get('priority', 'medium'),
                ticket_data.get('source', 'ai'),
                ticket_data.get('tags', []),
                ticket_data.get('estimated_resolution_time')
            )
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                return result['ticket_id'] if result else None
                
        except Exception as e:
            self.logger.error(f"Error creating ticket: {str(e)}")
            return None
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing ticket"""
        try:
            # Build dynamic update query
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                if key in ['status', 'priority', 'assigned_agent_id', 'satisfaction_score', 
                          'satisfaction_comment', 'internal_notes', 'resolved_at', 'closed_at']:
                    set_clauses.append(f"{key} = %s")
                    params.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            params.append(ticket_id)
            
            query = f"""
            UPDATE support_tickets 
            SET {', '.join(set_clauses)}
            WHERE ticket_id = %s
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error updating ticket: {str(e)}")
            return False
    
    async def add_ticket_response(self, response_data: Dict[str, Any]) -> int:
        """Add a response to a ticket"""
        try:
            query = """
            INSERT INTO ticket_responses 
            (ticket_id, responder_type, responder_id, responder_name, 
             message, message_type, is_internal, is_auto_generated, 
             processing_time_ms, ai_confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            params = (
                response_data['ticket_id'],
                response_data['responder_type'],
                response_data.get('responder_id'),
                response_data.get('responder_name'),
                response_data['message'],
                response_data.get('message_type', 'reply'),
                response_data.get('is_internal', False),
                response_data.get('is_auto_generated', True),
                response_data.get('processing_time_ms'),
                response_data.get('ai_confidence_score')
            )
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                # Update first response time if this is the first response
                if response_data['responder_type'] in ['agent', 'ai_agent']:
                    await self._update_first_response_time(response_data['ticket_id'])
                
                return result['id'] if result else None
                
        except Exception as e:
            self.logger.error(f"Error adding ticket response: {str(e)}")
            return None
    
    async def _update_first_response_time(self, ticket_id: str):
        """Update first response time for a ticket"""
        try:
            query = """
            UPDATE support_tickets 
            SET first_response_at = CURRENT_TIMESTAMP
            WHERE ticket_id = %s AND first_response_at IS NULL
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (ticket_id,))
                
        except Exception as e:
            self.logger.error(f"Error updating first response time: {str(e)}")
    
    # =====================================================
    # KNOWLEDGE BASE INTEGRATION
    # =====================================================
    
    async def search_knowledge_base(self, query: str, category: str = None, 
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base using full-text search"""
        try:
            search_query = """
            SELECT 
                ka.*,
                c.name as category_name,
                ts_rank(search_vector, plainto_tsquery('english', %s)) as relevance_score
            FROM knowledge_articles ka
            LEFT JOIN categories c ON ka.category_id = c.id
            WHERE ka.status = 'published'
            AND search_vector @@ plainto_tsquery('english', %s)
            """
            
            params = [query, query]
            
            if category:
                search_query += " AND (c.name ILIKE %s OR ka.keywords && %s)"
                params.extend([f'%{category}%', [category]])
            
            search_query += """
            ORDER BY relevance_score DESC, helpful_votes DESC
            LIMIT %s
            """
            params.append(limit)
            
            with self.connection.cursor() as cursor:
                cursor.execute(search_query, params)
                results = cursor.fetchall()
                
                # Update view counts
                article_ids = [row['article_id'] for row in results]
                if article_ids:
                    await self._update_article_views(article_ids)
                
                return [dict(row) for row in results]
                
        except Exception as e:
            self.logger.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    async def _update_article_views(self, article_ids: List[str]):
        """Update view counts for knowledge articles"""
        try:
            query = """
            UPDATE knowledge_articles 
            SET views_count = views_count + 1
            WHERE article_id = ANY(%s)
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (article_ids,))
                
        except Exception as e:
            self.logger.error(f"Error updating article views: {str(e)}")
    
    async def get_related_articles(self, ticket_data: Dict[str, Any], 
                                 limit: int = 5) -> List[Dict[str, Any]]:
        """Get articles related to a ticket"""
        try:
            # Build search query from ticket subject and description
            search_text = f"{ticket_data.get('subject', '')} {ticket_data.get('description', '')}"
            
            # Use category if available
            category = ticket_data.get('category')
            
            return await self.search_knowledge_base(search_text, category, limit)
            
        except Exception as e:
            self.logger.error(f"Error getting related articles: {str(e)}")
            return []
    
    # =====================================================
    # AI INTERACTION TRACKING
    # =====================================================
    
    async def save_query_interaction(self, interaction_data: Dict[str, Any]) -> str:
        """Save AI query interaction with comprehensive data"""
        try:
            query_id = f"QRY_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            query = """
            INSERT INTO query_interactions 
            (query_id, session_id, customer_id, ticket_id, query_text, query_type,
             detected_language, detected_intent, detected_entities, sentiment, 
             sentiment_score, urgency_level, urgency_score, category_prediction,
             category_confidence, response_text, response_type, response_sources,
             processing_time_ms, total_processing_time_ms, agents_used, 
             success_metrics, customer_satisfaction)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING query_id
            """
            
            params = (
                query_id,
                interaction_data.get('session_id'),
                interaction_data.get('customer_id'),
                interaction_data.get('ticket_id'),
                interaction_data['query_text'],
                interaction_data.get('query_type'),
                interaction_data.get('detected_language', 'en'),
                interaction_data.get('detected_intent'),
                json.dumps(interaction_data.get('detected_entities', {})),
                interaction_data.get('sentiment'),
                interaction_data.get('sentiment_score'),
                interaction_data.get('urgency_level'),
                interaction_data.get('urgency_score'),
                interaction_data.get('category_prediction'),
                interaction_data.get('category_confidence'),
                interaction_data.get('response_text'),
                interaction_data.get('response_type'),
                json.dumps(interaction_data.get('response_sources', [])),
                interaction_data.get('processing_time_ms'),
                interaction_data.get('total_processing_time_ms'),
                interaction_data.get('agents_used', []),
                json.dumps(interaction_data.get('success_metrics', {})),
                interaction_data.get('customer_satisfaction')
            )
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                return result['query_id'] if result else None
                
        except Exception as e:
            self.logger.error(f"Error saving query interaction: {str(e)}")
            return None
    
    async def save_agent_performance(self, performance_data: Dict[str, Any]) -> bool:
        """Save AI agent performance metrics"""
        try:
            query = """
            INSERT INTO agent_performance 
            (agent_id, agent_type, generation, fitness_score, genes, 
             performance_metrics, test_results, training_data_size,
             validation_accuracy, avg_response_time_ms, success_rate,
             customer_satisfaction_avg, queries_processed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                performance_data['agent_id'],
                performance_data['agent_type'],
                performance_data.get('generation', 0),
                performance_data.get('fitness_score'),
                json.dumps(performance_data.get('genes', {})),
                json.dumps(performance_data.get('performance_metrics', {})),
                json.dumps(performance_data.get('test_results', {})),
                performance_data.get('training_data_size'),
                performance_data.get('validation_accuracy'),
                performance_data.get('avg_response_time_ms'),
                performance_data.get('success_rate'),
                performance_data.get('customer_satisfaction_avg'),
                performance_data.get('queries_processed', 0)
            )
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving agent performance: {str(e)}")
            return False
    
    # =====================================================
    # ANALYTICS AND REPORTING
    # =====================================================
    
    async def get_system_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive system analytics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Ticket metrics
            ticket_query = """
            SELECT 
                COUNT(*) as total_tickets,
                COUNT(*) FILTER (WHERE status = 'resolved') as resolved_tickets,
                COUNT(*) FILTER (WHERE priority IN ('urgent', 'high')) as high_priority_tickets,
                AVG(satisfaction_score) as avg_satisfaction,
                AVG(EXTRACT(epoch FROM (resolved_at - created_at))/3600) 
                    FILTER (WHERE resolved_at IS NOT NULL) as avg_resolution_hours,
                AVG(EXTRACT(epoch FROM (first_response_at - created_at))/60) 
                    FILTER (WHERE first_response_at IS NOT NULL) as avg_first_response_minutes
            FROM support_tickets
            WHERE created_at >= %s
            """
            
            # AI performance metrics
            ai_query = """
            SELECT 
                agent_id,
                agent_type,
                AVG(fitness_score) as avg_fitness,
                AVG(success_rate) as avg_success_rate,
                AVG(customer_satisfaction_avg) as avg_customer_satisfaction,
                SUM(queries_processed) as total_queries
            FROM agent_performance
            WHERE created_at >= %s
            GROUP BY agent_id, agent_type
            """
            
            # Category distribution
            category_query = """
            SELECT 
                c.name as category,
                COUNT(st.id) as ticket_count,
                AVG(st.satisfaction_score) as avg_satisfaction
            FROM support_tickets st
            JOIN categories c ON st.category_id = c.id
            WHERE st.created_at >= %s
            GROUP BY c.name
            ORDER BY ticket_count DESC
            """
            
            analytics = {}
            
            with self.connection.cursor() as cursor:
                # Overall metrics
                cursor.execute(ticket_query, (cutoff_date,))
                ticket_metrics = cursor.fetchone()
                analytics['ticket_metrics'] = dict(ticket_metrics) if ticket_metrics else {}
                
                # AI performance
                cursor.execute(ai_query, (cutoff_date,))
                ai_performance = cursor.fetchall()
                analytics['ai_performance'] = [dict(row) for row in ai_performance]
                
                # Category distribution
                cursor.execute(category_query, (cutoff_date,))
                category_dist = cursor.fetchall()
                analytics['category_distribution'] = [dict(row) for row in category_dist]
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error getting system analytics: {str(e)}")
            return {}
    
    async def get_trending_issues(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending issues based on recent ticket patterns"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = """
            SELECT 
                subject,
                COUNT(*) as occurrence_count,
                AVG(satisfaction_score) as avg_satisfaction,
                string_agg(DISTINCT tags::text, ', ') as common_tags,
                MAX(created_at) as latest_occurrence
            FROM support_tickets
            WHERE created_at >= %s
            GROUP BY subject
            HAVING COUNT(*) > 1
            ORDER BY occurrence_count DESC, latest_occurrence DESC
            LIMIT %s
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (cutoff_date, limit))
                results = cursor.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            self.logger.error(f"Error getting trending issues: {str(e)}")
            return []
