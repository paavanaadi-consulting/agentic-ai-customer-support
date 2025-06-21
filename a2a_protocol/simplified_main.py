"""
Simplified main application using A2A protocol
"""
import asyncio
import logging
from typing import Dict, Any
from a2a_protocol.a2a_query_agent import A2AQueryAgent
from a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent
from a2a_protocol.a2a_response_agent import A2AResponseAgent
from a2a_protocol.a2a_coordinator import A2ACoordinator
from config.settings import CONFIG

class SimplifiedGeneticAISystem:
    """Simplified AI system using A2A protocol"""
    def __init__(self):
        self.logger = logging.getLogger("SimplifiedGeneticAI")
        self.coordinator = None
        self.agents = {}
        self.initialized = False
    async def initialize(self):
        try:
            self.logger.info("Initializing Simplified Genetic AI System with A2A Protocol...")
            self.coordinator = A2ACoordinator()
            await self.coordinator.start()
            await self._initialize_agents()
            await asyncio.sleep(2.0)
            self.initialized = True
            self.logger.info("Simplified system initialization complete!")
        except Exception as e:
            self.logger.error(f"Failed to initialize simplified system: {e}")
            raise
    async def _initialize_agents(self):
        query_agent = A2AQueryAgent(api_key=CONFIG['ai_models'].claude_api_key)
        await query_agent.start()
        self.agents['query'] = query_agent
        knowledge_agent = A2AKnowledgeAgent(api_key=CONFIG['ai_models'].gemini_api_key)
        await knowledge_agent.start()
        self.agents['knowledge'] = knowledge_agent
        response_agent = A2AResponseAgent(api_key=CONFIG['ai_models'].openai_api_key)
        await response_agent.start()
        self.agents['response'] = response_agent
        self.logger.info("All A2A agents initialized")
    async def process_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        try:
            result = await self.coordinator.process_task({
                'task_type': 'customer_support_workflow',
                'query_data': query_data
            })
            return result
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                'success': False,
                'error': str(e),
                'query_data': query_data
            }
    async def get_system_status(self) -> Dict[str, Any]:
        if not self.coordinator:
            return {'status': 'not_initialized'}
        health_check = await self.coordinator.process_task({
            'task_type': 'agent_health_check'
        })
        return {
            'initialized': self.initialized,
            'coordinator_active': self.coordinator.running,
            'agent_count': len(self.agents),
            'health_check': health_check,
            'a2a_enabled': True
        }
    async def shutdown(self):
        self.logger.info("Shutting down Simplified Genetic AI System...")
        for agent in self.agents.values():
            await agent.stop()
        if self.coordinator:
            await self.coordinator.stop()
        self.logger.info("System shutdown complete")
