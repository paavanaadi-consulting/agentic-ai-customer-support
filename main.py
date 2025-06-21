# FILE: main_enhanced.py
"""
Enhanced main application with full database integration
"""

import asyncio
import argparse
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from config.settings import CONFIG
from core.evolution_engine import EvolutionEngine
from a2a_protocol.a2a_query_agent import A2AQueryAgent
from a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent
from a2a_protocol.a2a_response_agent import A2AResponseAgent
from a2a_protocol.a2a_coordinator import A2ACoordinator
from integration.database_service import DatabaseService
from data_sources.pdf_processor import PDFProcessor
from data_sources.vector_db_client import VectorDBClient
from data_sources.kafka_consumer import KafkaConsumer
from mcp_servers.server_manager import MCPServerManager
from mcp_servers.mcp_client import MCPClient
from mcp_servers.postgres_mcp import PostgresMCP
from mcp_servers.kafka_mcp import KafkaMCP
from mcp_servers.aws_mcp import AWSMCP
from utils.logger import setup_logger
from api.routes import create_app

class EnhancedGeneticAISupport:
    """Enhanced main orchestrator with full database integration"""
    
    def __init__(self):
        self.logger = setup_logger("EnhancedGeneticAISupport")
        self.agents = {}
        self.data_sources = {}
        self.database_service = None
        self.evolution_engine = None
        self.mcp_manager = None
        self.mcp_clients = {}  # Store MCP clients for all connectors
        self.initialized = False
    
    async def initialize(self):
        """Initialize all components with database integration"""
        try:
            self.logger.info("Initializing Enhanced Genetic AI Customer Support System...")
            
            # Initialize database service first
            await self._initialize_database_service()
            
            # Initialize data sources
            await self._initialize_data_sources()
            
            # Initialize agents with database integration
            await self._initialize_enhanced_agents()
            
            # Initialize evolution engine
            await self._initialize_evolution_engine()
            
            # Initialize MCP server manager
            await self._initialize_mcp_manager()
            
            # Initialize MCP clients for connectors
            await self._initialize_mcp_clients()
            
            self.initialized = True
            self.logger.info("Enhanced system initialization complete!")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced system: {str(e)}")
            raise
    
    async def _initialize_database_service(self):
        """Initialize database service"""
        self.database_service = DatabaseService()
        await self.database_service.initialize()
        self.logger.info("Database service initialized successfully")
    
    async def _initialize_data_sources(self):
        """Initialize all data sources"""
        # PDF Processor
        self.data_sources['pdf_processor'] = PDFProcessor()
        await self.data_sources['pdf_processor'].initialize()
        
        # Vector Database
        self.data_sources['vector_db'] = VectorDBClient(CONFIG['vector_db'])
        await self.data_sources['vector_db'].connect()
        
        # Kafka Consumer
        self.data_sources['kafka'] = KafkaConsumer(CONFIG['kafka'])
        await self.data_sources['kafka'].start()
        
        # Database is handled by database_service
        self.data_sources['database'] = self.database_service.db
        
        self.logger.info("Data sources initialized successfully")
    
    async def _initialize_enhanced_agents(self):
        """Initialize enhanced agents with database integration"""
        # Enhanced Query Agent (Claude) with database
        self.agents['query'] = A2AQueryAgent(
            api_key=CONFIG['ai_models'].claude_api_key,
            db_connector=self.database_service.db
        )
        
        # Knowledge Agent (Gemini) with database knowledge source
        self.agents['knowledge'] = A2AKnowledgeAgent(
            api_key=CONFIG['ai_models'].gemini_api_key
        )
        
        # Include database in knowledge sources
        knowledge_sources = dict(self.data_sources)
        self.agents['knowledge'].set_knowledge_sources(knowledge_sources)
        
        # Response Agent (GPT)
        self.agents['response'] = A2AResponseAgent(
            api_key=CONFIG['ai_models'].openai_api_key
        )
        
        self.logger.info("Enhanced AI agents initialized successfully")
    
    async def _initialize_evolution_engine(self):
        """Initialize the genetic evolution engine"""
        self.evolution_engine = EvolutionEngine(
            agents=self.agents,
            config=CONFIG['genetic']
        )
        await self.evolution_engine.initialize()
        self.logger.info("Evolution engine initialized successfully")
    
    async def _initialize_mcp_manager(self):
        """Initialize MCP server manager"""
        self.mcp_manager = MCPServerManager()
        await self.mcp_manager.initialize()
        self.logger.info("MCP server manager initialized successfully")
    
    async def _initialize_mcp_clients(self):
        """Initialize all MCP connectors and wrap with MCPClient"""
        self.mcp_clients = {}
        # Example configs; replace with your actual config structure
        postgres_cfg = CONFIG.get('mcp_postgres', {})
        kafka_cfg = CONFIG.get('mcp_kafka', {})
        aws_cfg = CONFIG.get('mcp_aws', {})
        # Initialize each MCP implementation and wrap with MCPClient
        if postgres_cfg:
            self.mcp_clients['postgres'] = MCPClient(PostgresMCP(postgres_cfg))
        if kafka_cfg:
            self.mcp_clients['kafka'] = MCPClient(KafkaMCP(kafka_cfg))
        if aws_cfg:
            self.mcp_clients['aws'] = MCPClient(AWSMCP(aws_cfg))
        # Connect all MCP clients
        for client in self.mcp_clients.values():
            client.connect()
        self.logger.info(f"Initialized MCP clients: {list(self.mcp_clients.keys())}")
    
    async def process_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced query processing with full database integration"""
        if not self.initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Pre-process query with database service
            enhanced_query_data = await self.database_service.process_customer_query(query_data)
            
            # Add MCP info to enhanced_query_data
            enhanced_query_data['mcp_clients'] = self.mcp_clients
            
            # Step 1: Enhanced Query Analysis (Claude with DB context)
            self.logger.info(f"Processing query for customer {enhanced_query_data.get('customer_id')}")
            
            query_analysis = await self.agents['query'].process_input(enhanced_query_data)
            
            # Step 2: Knowledge Retrieval (Gemini with DB knowledge base)
            knowledge_data = {
                'analysis': query_analysis.get('analysis', {}),
                'original_query': enhanced_query_data.get('query', ''),
                'customer_id': enhanced_query_data.get('customer_id'),
                'ticket_id': enhanced_query_data.get('ticket_id')
            }
            knowledge_data['mcp_clients'] = self.mcp_clients
            knowledge_result = await self.agents['knowledge'].process_input(knowledge_data)
            
            # Step 3: Response Generation (GPT with context)
            response_data = {
                'query_analysis': query_analysis,
                'knowledge_result': knowledge_result,
                'customer_context': enhanced_query_data.get('customer_context', {}),
                'ticket_id': enhanced_query_data.get('ticket_id'),
                'session_id': enhanced_query_data.get('session_id')
            }
            response_data['mcp_clients'] = self.mcp_clients
            response_result = await self.agents['response'].process_input(response_data)
            
            # Calculate total processing time
            total_processing_time = int((time.time() - start_time) * 1000)
            
            # Compile enhanced final result
            final_result = {
                'query_id': query_analysis.get('query_id'),
                'customer_id': enhanced_query_data.get('customer_id'),
                'session_id': enhanced_query_data.get('session_id'),
                'ticket_id': enhanced_query_data.get('ticket_id'),
                'query_analysis': query_analysis,
                'knowledge_result': knowledge_result,
                'response_result': response_result,
                'final_response': response_result.get('response', ''),
                'confidence_score': min(
                    query_analysis.get('analysis', {}).get('confidence', 0),
                    knowledge_result.get('synthesis', {}).get('confidence', 0),
                    response_result.get('confidence', 0)
                ),
                'sources_used': knowledge_result.get('sources_used', []),
                'related_articles': query_analysis.get('related_articles', []),
                'processing_pipeline': ['enhanced_query_agent', 'knowledge_agent', 'response_agent'],
                'total_processing_time': total_processing_time,
                'database_integrated': True,
                'success': all([
                    query_analysis.get('success', False),
                    knowledge_result.get('success', False),
                    response_result.get('success', False)
                ])
            }
            
            # Save complete interaction result to database
            await self.database_service.save_agent_interaction_result(final_result)
            
            # Update evolution engine with results
            await self.evolution_engine.record_interaction(final_result)
            
            self.logger.info(f"Query processed successfully in {total_processing_time}ms")
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error processing enhanced query: {str(e)}")
            return {
                'error': str(e),
                'success': False,
                'query_data': query_data,
                'total_processing_time': int((time.time() - start_time) * 1000)
            }
    
    async def get_enhanced_system_status(self) -> Dict[str, Any]:
        """Get enhanced system status with database metrics"""
        status = {
            'initialized': self.initialized,
            'agents': {},
            'data_sources': {},
            'database_health': {},
            'evolution_status': {}
        }
        
        if self.initialized:
            # Agent status
            for agent_id, agent in self.agents.items():
                status['agents'][agent_id] = {
                    'performance_metrics': agent.performance_metrics,
                    'strategy_summary': agent.get_strategy_summary()
                }
            
            # Data source status
            for source_id, source in self.data_sources.items():
                if source_id == 'database':
                    status['data_sources'][source_id] = {
                        'connected': source.connected,
                        'type': 'postgresql'
                    }
                else:
                    status['data_sources'][source_id] = {
                        'connected': getattr(source, 'connected', False),
                        'status': getattr(source, 'status', 'unknown')
                    }
            
            # Database health metrics
            if self.database_service:
                status['database_health'] = await self.database_service.get_system_health()
            
            # Evolution status
            if self.evolution_engine:
                status['evolution_status'] = self.evolution_engine.get_status()
        
        return status
    
    async def get_customer_dashboard(self, customer_id: str) -> Dict[str, Any]:
        """Get customer-specific dashboard data"""
        if not self.database_service:
            return {}
        
        try:
            # Get customer profile and context
            customer_context = await self.database_service.db.get_customer_context(customer_id)
            
            # Get recent analytics
            recent_interactions = await self.database_service.db.get_customer_interactions(customer_id, limit=10)
            
            # Get ticket summary
            tickets = await self.database_service.db.get_customer_tickets(customer_id, limit=20)
            
            return {
                'customer_profile': customer_context.get('customer', {}),
                'recent_interactions': recent_interactions,
                'tickets': tickets,
                'patterns': customer_context.get('patterns', {}),
                'satisfaction_trend': self._calculate_satisfaction_trend(recent_interactions),
                'response_time_avg': self._calculate_avg_response_time(tickets)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting customer dashboard: {str(e)}")
            return {}
    
    def _calculate_satisfaction_trend(self, interactions: List[Dict[str, Any]]) -> List[float]:
        """Calculate satisfaction trend from interactions"""
        return [
            interaction.get('customer_satisfaction', 0) 
            for interaction in interactions[-10:] 
            if interaction.get('customer_satisfaction')
        ]
    
    def _calculate_avg_response_time(self, tickets: List[Dict[str, Any]]) -> float:
        """Calculate average response time from tickets"""
        response_times = []
        for ticket in tickets:
            if ticket.get('first_response_at') and ticket.get('created_at'):
                response_time = (ticket['first_response_at'] - ticket['created_at']).total_seconds() / 60
                response_times.append(response_time)
        
        return sum(response_times) / len(response_times) if response_times else 0
