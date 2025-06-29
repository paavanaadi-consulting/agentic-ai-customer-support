"""
A2A Coordinator for orchestrating agent interactions
"""
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from a2a_protocol.base_a2a_agent import A2AAgent
from a2a_protocol.a2a_query_agent import A2AQueryAgent
from a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent
from a2a_protocol.a2a_response_agent import A2AResponseAgent
from config.settings import CONFIG

class A2ACoordinator(A2AAgent):
    """Coordinator agent for managing A2A workflows"""
    def __init__(self, agent_id: str = "a2a_coordinator"):
        super().__init__(agent_id, "coordinator", 8004)
        self.active_workflows = {}
        self.workflow_results = {}
        self.message_handlers.update({
            'start_workflow': self._handle_workflow_start,
            'workflow_complete': self._handle_workflow_complete,
            'agent_status_update': self._handle_agent_status_update
        })
    def get_capabilities(self) -> List[str]:
        return [
            'workflow_orchestration',
            'agent_discovery',
            'load_balancing',
            'task_routing',
            'result_aggregation'
        ]
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get('task_type')
        if task_type == 'customer_support_workflow':
            return await self._orchestrate_support_workflow(task_data)
        elif task_type == 'agent_health_check':
            return await self._perform_health_check()
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    async def _orchestrate_support_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        workflow_id = str(uuid.uuid4())
        query_data = workflow_data.get('query_data', {})
        self.logger.info(f"Starting support workflow {workflow_id}")
        try:
            # Extract LLM config if provided
            llm_provider = query_data.get('llm_provider')
            llm_model = query_data.get('llm_model')
            api_key = query_data.get('api_key')
            # Extract MCP context if present
            mcp_clients = query_data.get('mcp_clients', {})
            context = query_data.get('context', {})
            # Query Agent
            query_agent = A2AQueryAgent(
                api_key=api_key or CONFIG['ai_models']['openai_api_key'],
                llm_provider=llm_provider or 'openai',
                llm_model=llm_model or 'gpt-3.5-turbo',
                mcp_clients=mcp_clients
            )
            query_result = await query_agent.process_task({
                'task_type': 'analyze_query',
                'input_data': {'query': query_data.get('query', ''), 'context': context},
                'capability': 'analyze_query',
                'llm_provider': llm_provider or 'openai',
                'llm_model': llm_model or 'gpt-3.5-turbo',
                'api_key': api_key or CONFIG['ai_models']['openai_api_key'],
                'mcp_clients': mcp_clients,
                'customer_id': query_data.get('customer_id'),
            })

            try:
                # Knowledge Agent
                knowledge_agent = A2AKnowledgeAgent(
                    api_key=api_key or CONFIG['ai_models']['gemini_api_key'],
                    llm_provider=llm_provider or 'gemini',
                    llm_model=llm_model or 'gemini-pro',
                    mcp_clients=mcp_clients
                )
                knowledge_result = await knowledge_agent.process_task({
                    'task_type': 'knowledge_search',
                    'input_data': {'query': query_data.get('query', ''), 'context': context},
                    'capability': 'knowledge_search',
                    'llm_provider': llm_provider or 'gemini',
                    'llm_model': llm_model or 'gemini-pro',
                    'api_key': api_key or CONFIG['ai_models']['gemini_api_key'],
                    'mcp_clients': mcp_clients,
                    'customer_id': query_data.get('customer_id'),
                })

                # Response Agent
                response_agent = A2AResponseAgent(
                    api_key=api_key or CONFIG['ai_models']['claude_api_key'],
                    llm_provider=llm_provider or 'claude',
                    llm_model=llm_model or 'claude-3-opus-20240229',
                    mcp_clients=mcp_clients
                )
                response_result = await response_agent.process_task({
                    'task_type': 'generate_response',
                    'query_analysis': query_result,
                    'knowledge_result': knowledge_result,
                    'capability': 'generate_response',
                    'llm_provider': llm_provider or 'claude',
                    'llm_model': llm_model or 'claude-3-opus-20240229',
                    'api_key': api_key or CONFIG['ai_models']['claude_api_key'],
                    'mcp_clients': mcp_clients,
                    'customer_id': query_data.get('customer_id'),
                    'context': context,
                })

                final_result = {
                    'workflow_id': workflow_id,
                    'success': True,
                    'query_analysis': query_result,
                    'knowledge_result': knowledge_result,
                    'response_result': response_result,
                    'total_agents_used': 3,
                    'coordination_overhead': 'minimal'
                }
                self.logger.info(f"Completed support workflow {workflow_id}")
                return final_result

            except Exception as agent_error:
                self.logger.error(f"Error in agent processing for workflow {workflow_id}: {agent_error}")
                return {
                    'workflow_id': workflow_id,
                    'success': False,
                    'error': f"Agent processing error: {str(agent_error)}"
                }

        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            return {
                'workflow_id': workflow_id,
                'success': False,
                'error': str(e)
            }
    async def _perform_health_check(self):
        return {'status': 'healthy', 'a2a_enabled': True}
    async def _handle_workflow_start(self, message):
        pass
    async def _handle_workflow_complete(self, message):
        pass
    async def _handle_agent_status_update(self, message):
        pass
