"""
Main entry point for the Genetic AI Customer Support System (LangChain version)
"""
import asyncio
import argparse
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from config.settings import settings
from core.evolution_engine import EvolutionEngine
from data_sources.rdbms_connector import RDBMSConnector
from data_sources.pdf_processor import PDFProcessor
from data_sources.vector_db_client import VectorDBClient
from data_sources.kafka_consumer import KafkaConsumer
from mcp_servers.server_manager import MCPServerManager
from utils.logger import setup_logger
from api.routes import create_app

# LangChain imports
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from langchain.tools import Tool

class GeneticAISupport:
    """Main orchestrator for the Genetic AI Customer Support System (LangChain)"""
    def __init__(self):
        self.logger = setup_logger("GeneticAISupport")
        self.data_sources = {}
        self.evolution_engine = None
        self.mcp_manager = None
        self.agent = None
        self.initialized = False

    async def initialize(self):
        try:
            self.logger.info("Initializing Genetic AI Customer Support System (LangChain)...")
            await self._initialize_data_sources()
            await self._initialize_agent()
            await self._initialize_evolution_engine()
            await self._initialize_mcp_manager()
            self.initialized = True
            self.logger.info("System initialization complete!")
        except Exception as e:
            self.logger.error(f"Failed to initialize system: {str(e)}")
            raise

    async def _initialize_data_sources(self):
        self.data_sources['rdbms'] = RDBMSConnector(settings.dict())
        await self.data_sources['rdbms'].connect()
        self.data_sources['pdf_processor'] = PDFProcessor()
        self.data_sources['vector_db'] = VectorDBClient(settings)
        await self.data_sources['vector_db'].connect()
        self.data_sources['kafka'] = KafkaConsumer(settings.dict())
        await self.data_sources['kafka'].start()
        self.logger.info("Data sources initialized successfully")

    async def _initialize_agent(self):
        # Define LangChain tools (wrapping your data sources or custom logic)
        tools = [
            Tool(
                name="VectorDBSearch",
                func=lambda q: asyncio.run(self.data_sources['vector_db'].search(q)),
                description="Semantic search in the vector database"
            ),
            Tool(
                name="RDBMSQuery",
                func=lambda q: self.data_sources['rdbms'].search_knowledge_base(category=q),
                description="Search knowledge base in RDBMS"
            )
        ]
        # Use OpenAI LLM as an example (replace with your preferred LLM)
        llm = OpenAI(openai_api_key=settings.OPENAI_API_KEY)
        self.agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        self.logger.info("LangChain agent initialized successfully")

    async def _initialize_evolution_engine(self):
        self.evolution_engine = EvolutionEngine(
            agents={'langchain': self.agent},
            config=settings.dict()
        )
        await self.evolution_engine.initialize()
        self.logger.info("Evolution engine initialized successfully")

    async def _initialize_mcp_manager(self):
        self.mcp_manager = MCPServerManager()
        await self.mcp_manager.initialize()
        self.logger.info("MCP server manager initialized successfully")

    async def process_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        try:
            # Use LangChain agent to process the query
            result = self.agent.run(query_data.get('query', ''))
            final_result = {
                'query_id': query_data.get('query_id', ''),
                'customer_id': query_data.get('customer_id', ''),
                'agent_result': result,
                'success': True
            }
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
        if not self.initialized:
            await self.initialize()
        max_generations = generations or settings.MAX_GENERATIONS
        self.logger.info(f"Starting agent training for {max_generations} generations...")
        await self.evolution_engine.evolve(max_generations)
        self.logger.info("Agent training completed!")

    async def get_system_status(self) -> Dict[str, Any]:
        status = {
            'initialized': self.initialized,
            'data_sources': {},
            'evolution_status': {}
        }
        if self.initialized:
            for source_id, source in self.data_sources.items():
                status['data_sources'][source_id] = {
                    'connected': getattr(source, 'connected', False),
                    'status': getattr(source, 'status', 'unknown')
                }
            if self.evolution_engine:
                status['evolution_status'] = self.evolution_engine.get_status()
        return status

async def run_server(host: str = "0.0.0.0", port: int = 8000):
    app = create_app()
    ai_system = GeneticAISupport()
    await ai_system.initialize()
    app.state.ai_system = ai_system
    import uvicorn
    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def run_training(generations: int = 50):
    ai_system = GeneticAISupport()
    await ai_system.train_agents(generations)

def main():
    parser = argparse.ArgumentParser(description="Genetic AI Customer Support System (LangChain)")
    parser.add_argument("--mode", choices=["server", "train"], default="server", help="Run mode")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--generations", type=int, default=50, help="Training generations")
    args = parser.parse_args()
    if args.mode == "server":
        asyncio.run(run_server(args.host, args.port))
    elif args.mode == "train":
        asyncio.run(run_training(args.generations))

if __name__ == "__main__":
    main()
