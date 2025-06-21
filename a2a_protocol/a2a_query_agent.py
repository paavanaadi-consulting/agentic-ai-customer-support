"""
A2A-enabled Query Agent
"""
import time
from typing import Dict, Any, List
from a2a_protocol.base_a2a_agent import A2AAgent
from utils.llm_client import set_openai_api_key, set_gemini_api_key, set_claude_api_key, call_chatgpt, call_gemini, call_claude

class A2AQueryAgent(A2AAgent):
    """Query Agent with A2A protocol capabilities and generalized LLM integration"""
    def __init__(self, agent_id: str = "a2a_query_agent", api_key: str = None, llm_provider: str = "openai", llm_model: str = None, mcp_clients: dict = None):
        super().__init__(agent_id, "query", 8001)
        self.api_key = api_key
        self.llm_provider = llm_provider or "openai"
        self.llm_model = llm_model or self._default_model_for_provider(self.llm_provider)
        self.mcp_clients = mcp_clients or {}
        self.message_handlers.update({
            'analyze_query': self._handle_query_analysis_request,
            'get_analysis_result': self._handle_analysis_result_request
        })
        self._set_llm_api_key()

    def _default_model_for_provider(self, provider):
        if provider == "openai":
            return "gpt-3.5-turbo"
        elif provider == "gemini":
            return "gemini-pro"
        elif provider == "claude":
            return "claude-3-opus-20240229"
        return None

    def _set_llm_api_key(self):
        if self.api_key:
            if self.llm_provider == "openai":
                set_openai_api_key(self.api_key)
            elif self.llm_provider == "gemini":
                set_gemini_api_key(self.api_key)
            elif self.llm_provider == "claude":
                set_claude_api_key(self.api_key)

    def get_capabilities(self) -> List[str]:
        return [
            'analyze_query',
            'classify_intent',
            'extract_entities',
            'detect_sentiment',
            'assess_urgency',
            'language_detection'
        ]
    def _build_prompt(self, query: str, capability: str) -> str:
        if capability == 'analyze_query':
            return f"""You are an AI assistant. Analyze the following customer query and provide a structured analysis including intent, entities, sentiment, urgency, and language:\n\nQuery: {query}\n"""
        elif capability == 'classify_intent':
            return f"Classify the intent of this customer query: {query}"
        elif capability == 'extract_entities':
            return f"Extract all relevant entities from this query: {query}"
        elif capability == 'detect_sentiment':
            return f"Detect the sentiment (positive, negative, neutral) of this query: {query}"
        elif capability == 'assess_urgency':
            return f"Assess the urgency level (low, medium, high) of this query: {query}"
        elif capability == 'language_detection':
            return f"Detect the language of this query: {query}"
        else:
            return query
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get('task_type')
        if task_type == 'analyze_query':
            return await self._process_query_analysis(task_data)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    async def _process_query_analysis(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        query = task_data.get('input_data', {}).get('query', '')
        capability = task_data.get('capability', 'analyze_query')
        llm_provider = task_data.get('llm_provider', self.llm_provider)
        llm_model = task_data.get('llm_model', self.llm_model)
        api_key = task_data.get('api_key', self.api_key)
        if api_key and api_key != self.api_key:
            self.api_key = api_key
            self.llm_provider = llm_provider
            self.llm_model = llm_model
            self._set_llm_api_key()
        if not query:
            return {'success': False, 'error': 'No query provided', 'a2a_processed': True, 'agent_id': self.agent_id}
        try:
            prompt = self._build_prompt(query, capability)
            response = await self._call_llm(prompt, llm_provider, llm_model)
            result = {
                'analysis': response,
                'a2a_processed': True,
                'agent_id': self.agent_id,
                'processing_time': time.time() - start_time,
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
    async def _call_llm(self, prompt: str, provider: str, model: str) -> Any:
        if provider == "openai":
            return await call_chatgpt(prompt, model)
        elif provider == "gemini":
            return await call_gemini(prompt, model)
        elif provider == "claude":
            return await call_claude(prompt, model)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
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
