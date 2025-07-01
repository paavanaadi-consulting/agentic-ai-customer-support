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
from src.geneticML.engines.evolution_engine import EvolutionEngine
from src.a2a_protocol.a2a_query_agent import A2AQueryAgent
from src.a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent
from src.a2a_protocol.a2a_response_agent import A2AResponseAgent
from src.a2a_protocol.a2a_coordinator import A2ACoordinator
from src.integration.database_service import DatabaseService
from src.data_sources.pdf_processor import PDFProcessor
from src.data_sources.vector_db_client import VectorDBClient
from src.data_sources.kafka_consumer import KafkaConsumer
from src.mcp.mcp_client import MCPClient
# from src.mcp.postgres_mcp_wrapper import PostgresMCPWrapper  # REMOVED - use postgres_mcp_client instead
from src.mcp.postgres_mcp_client import OptimizedPostgreSQLMCPClient
from src.mcp.kafka_mcp_client import OptimizedKafkaMCPClient
from src.mcp.aws_mcp_wrapper import AWSMCPWrapper
from src.utils.logger import setup_logger
from src.api.api_main import app as create_app

class EnhancedGeneticAISupport:
    """Enhanced main orchestrator with full database integration"""
    
    def __init__(self):
        self.logger = setup_logger("EnhancedGeneticAISupport")
        self.agents = {}
        self.data_sources = {}
        self.database_service = None
        self.evolution_engine = None
        self.mcp_services = {}  # Store MCP services for all connectors
        self.mcp_services = {}  # Store MCP services for all connectors
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
            await self._initialize_mcp_services()
            
            # Initialize MCP clients for connectors
            await self._initialize_mcp_services()
            
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
    
    async def _initialize_mcp_services(self):
        """Initialize all MCP connectors and wrap with MCPClient"""
        # Initialize MCP wrappers/servers
        self.mcp_services = {}
        
        # Initialize PostgreSQL MCP wrapper
        postgres_cfg = CONFIG.get('mcp_postgres', {})
        if postgres_cfg:
            # NOTE: PostgresMCPWrapper removed, use OptimizedPostgreSQLMCPClient instead
            # self.mcp_services['postgres'] = OptimizedPostgreSQLMCPClient()
            pass
            
        # Initialize Kafka MCP client
        kafka_cfg = CONFIG.get('mcp_kafka', {})
        if kafka_cfg:
            kafka_servers = kafka_cfg.get('bootstrap_servers', 'localhost:9092')
            mcp_server_url = kafka_cfg.get('mcp_server_url', 'http://localhost:8002')
            topic_prefix = kafka_cfg.get('topic_prefix', 'customer-support')
            group_id = kafka_cfg.get('group_id', 'ai-support-group')
            
            self.mcp_services['kafka'] = OptimizedKafkaMCPClient(
                bootstrap_servers=kafka_servers,
                mcp_server_url=mcp_server_url,
                topic_prefix=topic_prefix,
                group_id=group_id
            )
            
        # Initialize AWS MCP wrapper
        aws_cfg = CONFIG.get('mcp_aws', {})
        if aws_cfg:
            from src.mcp.aws_mcp_wrapper import ExternalMCPConfig
            aws_config = ExternalMCPConfig(
                aws_profile=aws_cfg.get('profile', 'default'),
                aws_region=aws_cfg.get('region', 'us-east-1')
            )
            self.mcp_services['aws'] = AWSMCPWrapper(aws_config)
            
        # Initialize all MCP services
        for name, service in self.mcp_services.items():
            try:
                if hasattr(service, 'connect'):
                    await service.connect()
                elif hasattr(service, 'initialize'):
                    await service.initialize()
                elif hasattr(service, 'start'):
                    await service.start()
                self.logger.info(f"Initialized MCP service: {name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize MCP service {name}: {e}")
                
        self.logger.info(f"Initialized MCP services: {list(self.mcp_services.keys())}")
    
    async def process_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced query processing with full database integration"""
        if not self.initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Pre-process query with database service
            enhanced_query_data = await self.database_service.process_customer_query(query_data)
            
            # Add MCP info to enhanced_query_data
            enhanced_query_data['mcp_services'] = self.mcp_services
            
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
            knowledge_data['mcp_services'] = self.mcp_services
            knowledge_result = await self.agents['knowledge'].process_input(knowledge_data)
            
            # Step 3: Response Generation (GPT with context)
            response_data = {
                'query_analysis': query_analysis,
                'knowledge_result': knowledge_result,
                'customer_context': enhanced_query_data.get('customer_context', {}),
                'ticket_id': enhanced_query_data.get('ticket_id'),
                'session_id': enhanced_query_data.get('session_id')
            }
            response_data['mcp_services'] = self.mcp_services
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
