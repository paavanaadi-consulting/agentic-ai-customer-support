"""
A2A-enabled Knowledge Agent
"""
import time
from typing import Dict, Any, List
from a2a_protocol.base_a2a_agent import A2AAgent
from utils.llm_client import set_openai_api_key, call_chatgpt

class A2AKnowledgeAgent(A2AAgent):
    """Knowledge Agent with A2A protocol capabilities and ChatGPT integration"""
    def __init__(self, agent_id: str = "a2a_knowledge_agent", api_key: str = None, mcp_clients: dict = None):
        super().__init__(agent_id, "knowledge", 8002)
        self.api_key = api_key
        self.mcp_clients = mcp_clients or {}
        self.message_handlers.update({
            'knowledge_search': self._handle_knowledge_search_request,
            'synthesize_info': self._handle_synthesis_request,
            'find_articles': self._handle_article_search_request
        })
        if self.api_key:
            set_openai_api_key(self.api_key)
    def get_capabilities(self) -> List[str]:
        return [
            'knowledge_search',
            'synthesize_info',
            'find_articles',
            'fact_checking',
            'source_validation',
            'content_summarization'
        ]
    def _build_prompt(self, query: str, capability: str) -> str:
        if capability == 'knowledge_search':
            return f"""You are an expert knowledge retrieval agent. Search your knowledge base and provide a concise, factual answer to the following query:

Query: {query}
"""
        elif capability == 'synthesize_info':
            return f"Synthesize information from multiple sources for this query: {query}"
        elif capability == 'find_articles':
            return f"Find relevant articles for this query: {query}"
        elif capability == 'fact_checking':
            return f"Fact-check the following statement or query: {query}"
        elif capability == 'source_validation':
            return f"Validate the sources for this information: {query}"
        elif capability == 'content_summarization':
            return f"Summarize the following content or query: {query}"
        else:
            return query
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
        query = task_data.get('input_data', {}).get('query', '')
        capability = task_data.get('capability', 'knowledge_search')
        if not query:
            return {'success': False, 'error': 'No query provided', 'a2a_processed': True, 'agent_id': self.agent_id}
        try:
            prompt = self._build_prompt(query, capability)
            response = await call_chatgpt(prompt)
            result = {
                'knowledge': response,
                'a2a_processed': True,
                'agent_id': self.agent_id,
                'processing_time': time.time() - start_time,
                'task_type': 'knowledge_search',
                'success': True
            }
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'a2a_processed': True,
                'agent_id': self.agent_id
            }
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
