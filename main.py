"""
Main entry point for the Genetic AI Customer Support System
"""
import asyncio
import argparse
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from config.settings import CONFIG
from core.evolution_engine import EvolutionEngine
from agents.query_agent import QueryAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.response_agent import ResponseAgent
from data_sources.rdbms_connector import RDBMSConnector
from data_sources.pdf_processor import PDFProcessor
from data_sources.vector_db_client import VectorDBClient
from data_sources.kafka_consumer import KafkaConsumer
from mcp_servers.server_manager import MCPServerManager
from utils.logger import setup_logger
from api.routes import create_app

class GeneticAISupport:
    """Main orchestrator for the Genetic AI Customer Support System"""
    
    def __init__(self):
        self.logger = setup_logger("GeneticAISupport")
        self.agents = {}
        self.data_sources = {}
        self.evolution_engine = None
        self.mcp_manager = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize all components of the system"""
        try:
            self.logger.info("Initializing Genetic AI Customer Support System...")
            
            # Initialize data sources
            await self._initialize_data_sources()
            
            # Initialize agents
            await self._initialize_agents()
            
            # Initialize evolution engine
            await self._initialize_evolution_engine()
            
            # Initialize MCP server manager
            await self._initialize_mcp_manager()
            
            self.initialized = True
            self.logger.info("System initialization complete!")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system: {str(e)}")
            raise
    
    async def _initialize_data_sources(self):
        """Initialize all data sources"""
        # RDBMS
        self.data_sources['rdbms'] = RDBMSConnector(CONFIG['database'])
        await self.data_sources['rdbms'].connect()
        
        # PDF Processor
        self.data_sources['pdf_processor'] = PDFProcessor()
        
        # Vector Database
        self.data_sources['vector_db'] = VectorDBClient(CONFIG['vector_db'])
        await self.data_sources['vector_db'].connect()
        
        # Kafka Consumer
        self.data_sources['kafka'] = KafkaConsumer(CONFIG['kafka'])
        await self.data_sources['kafka'].start()
        
        self.logger.info("Data sources initialized successfully")
    
    async def _initialize_agents(self):
        """Initialize all AI agents"""
        # Query Agent (Claude)
        self.agents['query'] = QueryAgent(
            api_key=CONFIG['ai_models'].claude_api_key
        )
        
        # Knowledge Agent (Gemini)
        self.agents['knowledge'] = KnowledgeAgent(
            api_key=CONFIG['ai_models'].gemini_api_key
        )
        self.agents['knowledge'].set_knowledge_sources(self.data_sources)
        
        # Response Agent (GPT)
        self.agents['response'] = ResponseAgent(
            api_key=CONFIG['ai_models'].openai_api_key
        )
        
        self.logger.info("AI agents initialized successfully")
    
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
    
    async def process_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a customer query through the agent pipeline"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Step 1: Query Analysis (Claude)
            query_analysis = await self.agents['query'].process_input(query_data)
            
            # Step 2: Knowledge Retrieval (Gemini)
            knowledge_data = {
                'analysis': query_analysis.get('analysis', {}),
                'original_query': query_data.get('query', '')
            }
            knowledge_result = await self.agents['knowledge'].process_input(knowledge_data)
            
            # Step 3: Response Generation (GPT)
            response_data = {
                'query_analysis': query_analysis,
                'knowledge_result': knowledge_result,
                'customer_context': query_data.get('context', {})
            }
            response_result = await self.agents['response'].process_input(response_data)
            
            # Compile final result
            final_result = {
                'query_id': query_data.get('query_id', ''),
                'customer_id': query_data.get('customer_id', ''),
                'query_analysis': query_analysis,
                'knowledge_result': knowledge_result,
                'response_result': response_result,
                'processing_pipeline': ['query_agent', 'knowledge_agent', 'response_agent'],
                'success': all([
                    query_analysis.get('success', False),
                    knowledge_result.get('success', False),
                    response_result.get('success', False)
                ])
            }
            
            # Update evolution engine with results
            await self.evolution_engine.record_interaction(final_result)
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                'error': str(e),
                'success': False,
                'query_data': query_data
            }
    
    async def train_agents(self, generations: int = None):
        """Train agents using genetic evolution"""
        if not self.initialized:
            await self.initialize()
        
        max_generations = generations or CONFIG['genetic'].max_generations
        
        self.logger.info(f"Starting agent training for {max_generations} generations...")
        
        await self.evolution_engine.evolve(max_generations)
        
        self.logger.info("Agent training completed!")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        status = {
            'initialized': self.initialized,
            'agents': {},
            'data_sources': {},
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
                status['data_sources'][source_id] = {
                    'connected': getattr(source, 'connected', False),
                    'status': getattr(source, 'status', 'unknown')
                }
            
            # Evolution status
            if self.evolution_engine:
                status['evolution_status'] = self.evolution_engine.get_status()
        
        return status

async def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server"""
    app = create_app()
    
    # Initialize the AI system
    ai_system = GeneticAISupport()
    await ai_system.initialize()
    
    # Attach to app state
    app.state.ai_system = ai_system
    
    import uvicorn
    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def run_training(generations: int = 50):
    """Run training mode"""
    ai_system = GeneticAISupport()
    await ai_system.train_agents(generations)

async def run_benchmark():
    """Run benchmark tests"""
    from scripts.benchmark import run_benchmark_suite
    await run_benchmark_suite()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Genetic AI Customer Support System")
    parser.add_argument("--mode", choices=["server", "train", "benchmark"], 
                       default="server", help="Run mode")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--generations", type=int, default=50, help="Training generations")
    
    args = parser.parse_args()
    
    if args.mode == "server":
        asyncio.run(run_server(args.host, args.port))
    elif args.mode == "train":
        asyncio.run(run_training(args.generations))
    elif args.mode == "benchmark":
        asyncio.run(run_benchmark())

if __name__ == "__main__":
    main()
