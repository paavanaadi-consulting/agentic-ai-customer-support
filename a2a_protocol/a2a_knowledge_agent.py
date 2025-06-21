"""
A2A-enabled Knowledge Agent
"""
import time
from typing import Dict, Any, List
from a2a_protocol.base_a2a_agent import A2AAgent
from agents.knowledge_agent import KnowledgeAgent

class A2AKnowledgeAgent(A2AAgent, KnowledgeAgent):
    """Knowledge Agent with A2A protocol capabilities"""
    def __init__(self, agent_id: str = "a2a_knowledge_agent", api_key: str = None):
        A2AAgent.__init__(self, agent_id, "knowledge", 8002)
        KnowledgeAgent.__init__(self, agent_id, api_key)
        self.message_handlers.update({
            'knowledge_search': self._handle_knowledge_search_request,
            'synthesize_info': self._handle_synthesis_request,
            'find_articles': self._handle_article_search_request
        })
    def get_capabilities(self) -> List[str]:
        return [
            'knowledge_search',
            'synthesize_info',
            'find_articles',
            'fact_checking',
            'source_validation',
            'content_summarization'
        ]
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get('task_type')
        if task_type == 'knowledge_search':
            return await self._process_knowledge_search(task_data)
        elif task_type == 'synthesize_info':
            return await self._process_synthesis(task_data)
        elif task_type == 'find_articles':
            return await self._process_article_search(task_data)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    async def _process_knowledge_search(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        input_data = {
            'analysis': task_data.get('analysis', {}),
            'original_query': task_data.get('original_query', ''),
            'customer_id': task_data.get('customer_id', '')
        }
        result = await KnowledgeAgent.process_input(self, input_data)
        result.update({
            'a2a_processed': True,
            'agent_id': self.agent_id,
            'processing_time': time.time() - start_time,
            'task_type': 'knowledge_search'
        })
        return result
    async def _process_synthesis(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        return {'synthesis': 'not_implemented'}
    async def _process_article_search(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        return {'articles': []}
    async def _handle_knowledge_search_request(self, message):
        try:
            result = await self._process_knowledge_search(message.payload)
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="knowledge_result",
                payload=result,
                request_id=message.request_id
            )
        except Exception as e:
            await self.send_error_response(message, str(e))
    async def _handle_synthesis_request(self, message):
        pass
    async def _handle_article_search_request(self, message):
        pass
