"""
A2A Coordinator for orchestrating agent interactions
"""
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from a2a_protocol.base_a2a_agent import A2AAgent

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
            query_result = await self._delegate_to_query_agent(query_data)
            knowledge_result = await self._delegate_to_knowledge_agent(query_result, query_data)
            response_result = await self._delegate_to_response_agent(query_result, knowledge_result, query_data)
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
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            return {
                'workflow_id': workflow_id,
                'success': False,
                'error': str(e)
            }
    async def _delegate_to_query_agent(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        query_agents = await self._find_agents_by_type('query')
        if not query_agents:
            raise Exception("No Query Agent available")
        best_agent = await self._select_best_agent(query_agents, 'analyze_query')
        result = await self._send_task_and_wait(
            best_agent,
            {
                'task_type': 'analyze_query',
                'input_data': query_data
            }
        )
        return result
    async def _delegate_to_knowledge_agent(self, query_result: Dict[str, Any], original_query: Dict[str, Any]) -> Dict[str, Any]:
        knowledge_agents = await self._find_agents_by_type('knowledge')
        if not knowledge_agents:
            raise Exception("No Knowledge Agent available")
        best_agent = await self._select_best_agent(knowledge_agents, 'knowledge_search')
        result = await self._send_task_and_wait(
            best_agent,
            {
                'task_type': 'knowledge_search',
                'analysis': query_result.get('analysis', {}),
                'original_query': original_query.get('query', '')
            }
        )
        return result
    async def _delegate_to_response_agent(self, query_result: Dict[str, Any], knowledge_result: Dict[str, Any], original_query: Dict[str, Any]) -> Dict[str, Any]:
        response_agents = await self._find_agents_by_type('response')
        if not response_agents:
            raise Exception("No Response Agent available")
        best_agent = await self._select_best_agent(response_agents, 'generate_response')
        result = await self._send_task_and_wait(
            best_agent,
            {
                'task_type': 'generate_response',
                'query_analysis': query_result,
                'knowledge_result': knowledge_result,
                'customer_context': original_query.get('context', {})
            }
        )
        return result
    async def _find_agents_by_type(self, agent_type: str) -> List[str]:
        agents = []
        for agent_id, info in self.discovery_registry.items():
            if info.get('agent_type') == agent_type:
                agents.append(agent_id)
        return agents
    async def _select_best_agent(self, agent_ids: List[str], capability: str) -> str:
        best_agent = None
        best_score = float('inf')
        for agent_id in agent_ids:
            agent_info = self.discovery_registry.get(agent_id, {})
            if capability not in agent_info.get('capabilities', []):
                continue
            load = agent_info.get('load', 1.0)
            available = agent_info.get('available', False)
            if available and load < best_score:
                best_score = load
                best_agent = agent_id
        if best_agent is None:
            raise Exception(f"No suitable agent found for capability: {capability}")
        return best_agent
    async def _send_task_and_wait(self, agent_id: str, task_data: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        future = asyncio.Future()
        self.active_workflows[request_id] = future
        try:
            await self.send_message(
                receiver_id=agent_id,
                message_type="task_delegation",
                payload=task_data,
                request_id=request_id
            )
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            raise Exception(f"Task delegation to {agent_id} timed out")
        finally:
            if request_id in self.active_workflows:
                del self.active_workflows[request_id]
    async def _handle_workflow_start(self, message):
        try:
            result = await self._orchestrate_support_workflow(message.payload)
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="workflow_complete",
                payload=result,
                request_id=message.request_id
            )
        except Exception as e:
            await self.send_error_response(message, str(e))
    async def _handle_workflow_complete(self, message):
        workflow_id = message.payload.get('workflow_id')
        self.logger.info(f"Workflow {workflow_id} completed by {message.sender_id}")
    async def _handle_agent_status_update(self, message):
        agent_id = message.sender_id
        status = message.payload
        if agent_id in self.discovery_registry:
            self.discovery_registry[agent_id].update(status)
    async def _handle_task_result(self, message):
        request_id = message.request_id
        if request_id in self.active_workflows:
            future = self.active_workflows[request_id]
            if message.payload.get('success', False):
                future.set_result(message.payload.get('result', {}))
            else:
                error = message.payload.get('error', 'Unknown error')
                future.set_exception(Exception(error))
    async def _perform_health_check(self) -> Dict[str, Any]:
        health_status = {}
        for agent_id in self.discovery_registry.keys():
            try:
                await self.send_message(
                    receiver_id=agent_id,
                    message_type="capability_query",
                    payload={}
                )
                await asyncio.sleep(0.1)
                health_status[agent_id] = "healthy"
            except Exception as e:
                health_status[agent_id] = f"unhealthy: {str(e)}"
        return {
            'total_agents': len(self.discovery_registry),
            'health_status': health_status,
            'coordinator_status': 'healthy'
        }
