"""
A2A-enabled Response Agent
"""
import time
from typing import Dict, Any, List
from a2a_protocol.base_a2a_agent import A2AAgent
from utils.llm_client import set_openai_api_key, set_gemini_api_key, set_claude_api_key, call_chatgpt, call_gemini, call_claude

class A2AResponseAgent(A2AAgent):
    """Response Agent with A2A protocol capabilities and generalized LLM integration"""
    def __init__(self, agent_id: str = "a2a_response_agent", api_key: str = None, llm_provider: str = "openai", llm_model: str = None, mcp_clients: dict = None):
        super().__init__(agent_id, "response", 8003)
        self.api_key = api_key
        self.llm_provider = llm_provider or "openai"
        self.llm_model = llm_model or self._default_model_for_provider(self.llm_provider)
        self.mcp_clients = mcp_clients or {}
        self.message_handlers.update({
            'generate_response': self._handle_response_generation_request,
            'craft_email': self._handle_email_crafting_request,
            'create_ticket_response': self._handle_ticket_response_request
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
            'generate_response',
            'craft_email',
            'create_ticket_response',
            'personalize_content',
            'tone_adjustment',
            'multi_language_response'
        ]
    def _build_prompt(self, query: str, capability: str, context: dict = None, mcp_clients: dict = None) -> str:
        context_str = f"\nContext: {context}" if context else ""
        mcp_str = f"\nMCP: {mcp_clients}" if mcp_clients else ""
        if capability == 'generate_response':
            return f"""You are a customer support agent. Generate a helpful, accurate, and empathetic response to the following query:{context_str}{mcp_str}\n\nQuery: {query}\n"""
        elif capability == 'craft_email':
            return f"Craft a professional customer support email for this query: {query}{context_str}{mcp_str}"
        elif capability == 'create_ticket_response':
            return f"Create a ticket response for this query: {query}{context_str}{mcp_str}"
        elif capability == 'personalize_content':
            return f"Personalize the following content for the customer: {query}{context_str}{mcp_str}"
        elif capability == 'tone_adjustment':
            return f"Adjust the tone of this response as requested: {query}{context_str}{mcp_str}"
        elif capability == 'multi_language_response':
            return f"Translate the following response into the customer's language: {query}{context_str}{mcp_str}"
        else:
            return f"{query}{context_str}{mcp_str}"

    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get('task_type')
        if task_type == 'generate_response':
            return await self._process_response_generation(task_data)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    async def _process_response_generation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        query = task_data.get('query_analysis', {}).get('analysis', '')
        context = task_data.get('context', {})
        mcp_clients = task_data.get('mcp_clients', self.mcp_clients)
        capability = task_data.get('capability', 'generate_response')
        llm_provider = task_data.get('llm_provider', self.llm_provider)
        llm_model = task_data.get('llm_model', self.llm_model)
        api_key = task_data.get('api_key', self.api_key)
        if not query:
            query = task_data.get('query_analysis', {}).get('query', '')
        if api_key and api_key != self.api_key:
            self.api_key = api_key
            self.llm_provider = llm_provider
            self.llm_model = llm_model
            self._set_llm_api_key()
        if not query:
            query = 'Please generate a customer support response.'
        try:
            prompt = self._build_prompt(query, capability, context, mcp_clients)
            response = await self._call_llm(prompt, llm_provider, llm_model)
            result = {
                'response': response,
                'a2a_processed': True,
                'agent_id': self.agent_id,
                'processing_time': time.time() - start_time,
                'task_type': 'generate_response',
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
