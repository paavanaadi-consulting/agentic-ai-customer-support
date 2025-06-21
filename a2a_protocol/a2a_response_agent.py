"""
A2A-enabled Response Agent
"""
import time
from typing import Dict, Any, List
from a2a_protocol.base_a2a_agent import A2AAgent
from agents.response_agent import ResponseAgent

class A2AResponseAgent(A2AAgent, ResponseAgent):
    """Response Agent with A2A protocol capabilities"""
    def __init__(self, agent_id: str = "a2a_response_agent", api_key: str = None):
        A2AAgent.__init__(self, agent_id, "response", 8003)
        ResponseAgent.__init__(self, agent_id, api_key)
        self.message_handlers.update({
            'generate_response': self._handle_response_generation_request,
            'craft_email': self._handle_email_crafting_request,
            'create_ticket_response': self._handle_ticket_response_request
        })
    def get_capabilities(self) -> List[str]:
        return [
            'generate_response',
            'craft_email',
            'create_ticket_response',
            'personalize_content',
            'tone_adjustment',
            'multi_language_response'
        ]
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get('task_type')
        if task_type == 'generate_response':
            return await self._process_response_generation(task_data)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    async def _process_response_generation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        input_data = {
            'query_analysis': task_data.get('query_analysis', {}),
            'knowledge_result': task_data.get('knowledge_result', {}),
            'customer_context': task_data.get('customer_context', {}),
            'ticket_id': task_data.get('ticket_id'),
            'session_id': task_data.get('session_id')
        }
        result = await ResponseAgent.process_input(self, input_data)
        result.update({
            'a2a_processed': True,
            'agent_id': self.agent_id,
            'processing_time': time.time() - start_time,
            'task_type': 'generate_response'
        })
        return result
    async def _handle_response_generation_request(self, message):
        try:
            result = await self._process_response_generation(message.payload)
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="response_result",
                payload=result,
                request_id=message.request_id
            )
        except Exception as e:
            await self.send_error_response(message, str(e))
    async def _handle_email_crafting_request(self, message):
        pass
    async def _handle_ticket_response_request(self, message):
        pass
