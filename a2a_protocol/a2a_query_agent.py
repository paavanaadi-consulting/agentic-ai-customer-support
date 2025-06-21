"""
A2A-enabled Query Agent
"""
import time
from typing import Dict, Any, List
from a2a_protocol.base_a2a_agent import A2AAgent
from agents.query_agent import QueryAgent

class A2AQueryAgent(A2AAgent, QueryAgent):
    """Query Agent with A2A protocol capabilities"""
    def __init__(self, agent_id: str = "a2a_query_agent", api_key: str = None):
        A2AAgent.__init__(self, agent_id, "query", 8001)
        QueryAgent.__init__(self, agent_id, api_key)
        self.message_handlers.update({
            'analyze_query': self._handle_query_analysis_request,
            'get_analysis_result': self._handle_analysis_result_request
        })
    def get_capabilities(self) -> List[str]:
        return [
            'analyze_query',
            'classify_intent',
            'extract_entities',
            'detect_sentiment',
            'assess_urgency',
            'language_detection'
        ]
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get('task_type')
        if task_type == 'analyze_query':
            return await self._process_query_analysis(task_data)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    async def _process_query_analysis(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        result = await QueryAgent.process_input(self, task_data.get('input_data', {}))
        result.update({
            'a2a_processed': True,
            'agent_id': self.agent_id,
            'processing_time': time.time() - start_time
        })
        return result
    async def _handle_query_analysis_request(self, message):
        try:
            result = await self._process_query_analysis(message.payload)
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="analysis_result",
                payload=result,
                request_id=message.request_id
            )
        except Exception as e:
            await self.send_error_response(message, str(e))
    async def _handle_analysis_result_request(self, message):
        pass
