"""
RDBMS connector for customer support database
"""
import asyncio
import psycopg2
import psycopg2.extras
from typing import Dict, Any, List, Optional
import logging
from contextlib import asynccontextmanager

class RDBMSConnector:
    """PostgreSQL database connector for customer support data"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.logger = logging.getLogger("RDBMSConnector")
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
            
            # Initialize schema if needed
            await self._initialize_schema()
            
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    async def _initialize_schema(self):
        """Initialize database schema for customer support"""
        schema_sql = """
        -- Customer information table
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            customer_id VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255),
            name VARCHAR(255),
            tier VARCHAR(50) DEFAULT 'standard',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Support tickets table
        CREATE TABLE IF NOT EXISTS support_tickets (
            id SERIAL PRIMARY KEY,
            ticket_id VARCHAR(255) UNIQUE NOT NULL,
            customer_id VARCHAR(255) REFERENCES customers(customer_id),
            subject VARCHAR(500),
            description TEXT,
            category VARCHAR(100),
            status VARCHAR(50) DEFAULT 'open',
            priority VARCHAR(50) DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP NULL
        );
        
        -- Knowledge base articles
        CREATE TABLE IF NOT EXISTS knowledge_articles (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            content TEXT NOT NULL,
            category VARCHAR(100),
            tags TEXT[],
            views_count INTEGER DEFAULT 0,
            helpful_votes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Query interactions for learning
        CREATE TABLE IF NOT EXISTS query_interactions (
            id SERIAL PRIMARY KEY,
            query_id VARCHAR(255) UNIQUE NOT NULL,
            customer_id VARCHAR(255),
            query_text TEXT NOT NULL,
            response_text TEXT,
            category VARCHAR(100),
            sentiment VARCHAR(50),
            satisfaction_score FLOAT,
            processing_time FLOAT,
            agent_used VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Agent performance metrics
        CREATE TABLE IF NOT EXISTS agent_performance (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(100) NOT NULL,
            generation INTEGER,
            fitness_score FLOAT,
            genes JSONB,
            performance_metrics JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_support_tickets_customer_id ON support_tickets(customer_id);
        CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
        CREATE INDEX IF NOT EXISTS idx_support_tickets_category ON support_tickets(category);
        CREATE INDEX IF NOT EXISTS idx_knowledge_articles_category ON knowledge_articles(category);
        CREATE INDEX IF NOT EXISTS idx_query_interactions_customer_id ON query_interactions(customer_id);
        CREATE INDEX IF NOT EXISTS idx_query_interactions_category ON query_interactions(category);
        CREATE INDEX IF NOT EXISTS idx_agent_performance_agent_id ON agent_performance(agent_id);
        """
        
        with self.connection.cursor() as cursor:
            cursor.execute(schema_sql)
        
        self.logger.info("Database schema initialized")
    
    async def search_knowledge_base(self, category: str = None, entities: List[str] = None, 
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base articles"""
        try:
            query = """
            SELECT id, title, content, category, tags, views_count, helpful_votes,
                   CASE 
                       WHEN %s IS NULL THEN 1.0
                       ELSE CASE WHEN category = %s THEN 1.0 ELSE 0.5 END
                   END as relevance
            FROM knowledge_articles
            WHERE (%s IS NULL OR category = %s OR content ILIKE %s)
            """
            
            params = [category, category, category, category, f'%{category}%' if category else None]
            
            if entities:
                entity_conditions = []
                for entity in entities:
                    entity_conditions.append("content ILIKE %s")
                    params.append(f'%{entity}%')
                
                if entity_conditions:
                    query += " AND (" + " OR ".join(entity_conditions) + ")"
            
            query += " ORDER BY relevance DESC, helpful_votes DESC, views_count DESC LIMIT %s"
            params.append(limit)
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            self.logger.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    async def get_customer_context(self, customer_id: str) -> Dict[str, Any]:
        """Get customer context including recent tickets and profile"""
        try:
            # Get customer profile
            customer_query = """
            SELECT * FROM customers WHERE customer_id = %s
            """
            
            # Get recent tickets
            tickets_query = """
            SELECT * FROM support_tickets 
            WHERE customer_id = %s 
            ORDER BY created_at DESC 
            LIMIT 5
            """
            
            # Get recent interactions
            interactions_query = """
            SELECT * FROM query_interactions 
            WHERE customer_id = %s 
            ORDER BY created_at DESC 
            LIMIT 10
            """
            
            context = {}
            
            with self.connection.cursor() as cursor:
                # Customer profile
                cursor.execute(customer_query, (customer_id,))
                customer = cursor.fetchone()
                context['customer'] = dict(customer) if customer else None
                
                # Recent tickets
                cursor.execute(tickets_query, (customer_id,))
                tickets = cursor.fetchall()
                context['recent_tickets'] = [dict(ticket) for ticket in tickets]
                
                # Recent interactions
                cursor.execute(interactions_query, (customer_id,))
                interactions = cursor.fetchall()
                context['recent_interactions'] = [dict(interaction) for interaction in interactions]
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting customer context: {str(e)}")
            return {}
    
    async def save_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """Save query interaction for learning purposes"""
        try:
            query = """
            INSERT INTO query_interactions 
            (query_id, customer_id, query_text, response_text, category, 
             sentiment, satisfaction_score, processing_time, agent_used)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (query_id) DO UPDATE SET
                response_text = EXCLUDED.response_text,
                satisfaction_score = EXCLUDED.satisfaction_score,
                updated_at = CURRENT_TIMESTAMP
            """
            
            params = (
                interaction_data.get('query_id'),
                interaction_data.get('customer_id'),
                interaction_data.get('query_text'),
                interaction_data.get('response_text'),
                interaction_data.get('category'),
                interaction_data.get('sentiment'),
                interaction_data.get('satisfaction_score'),
                interaction_data.get('processing_time'),
                interaction_data.get('agent_used')
            )
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving interaction: {str(e)}")
            return False
    
    async def save_agent_performance(self, agent_id: str, generation: int, 
                                   fitness_score: float, genes: Dict[str, Any],
                                   performance_metrics: Dict[str, Any]) -> bool:
        """Save agent performance data"""
        try:
            query = """
            INSERT INTO agent_performance 
            (agent_id, generation, fitness_score, genes, performance_metrics)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            import json
            params = (
                agent_id,
                generation,
                fitness_score,
                json.dumps(genes),
                json.dumps(performance_metrics)
            )
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving agent performance: {str(e)}")
            return False
    
    async def get_performance_history(self, agent_id: str = None, 
                                    limit: int = 100) -> List[Dict[str, Any]]:
        """Get agent performance history"""
        try:
            if agent_id:
                query = """
                SELECT * FROM agent_performance 
                WHERE agent_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
                """
                params = (agent_id, limit)
            else:
                query = """
                SELECT * FROM agent_performance 
                ORDER BY created_at DESC 
                LIMIT %s
                """
                params = (limit,)
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            self.logger.error(f"Error getting performance history: {str(e)}")
            return []
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connected = False
            self.logger.info("Database connection closed")
