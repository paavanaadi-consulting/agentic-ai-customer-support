"""
A2A-enabled Query Agent
"""
import time
from typing import Dict, Any, List
from src.a2a_protocol.base_a2a_agent import A2AAgent
from src.utils.llm_client import set_openai_api_key, set_gemini_api_key, set_claude_api_key, call_chatgpt, call_gemini, call_claude

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
    def _build_prompt(self, query: str, capability: str, context: dict = None, mcp_clients: dict = None) -> str:
        context_str = f"\nContext: {context}" if context else ""
        mcp_str = f"\nMCP: {mcp_clients}" if mcp_clients else ""
        if capability == 'analyze_query':
            return f"""You are an AI assistant. Analyze the following customer query and provide a structured analysis including intent, entities, sentiment, urgency, and language:{context_str}{mcp_str}\n\nQuery: {query}\n"""
        elif capability == 'classify_intent':
            return f"Classify the intent of this customer query: {query}{context_str}{mcp_str}"
        elif capability == 'extract_entities':
            return f"Extract all relevant entities from this query: {query}{context_str}{mcp_str}"
        elif capability == 'detect_sentiment':
            return f"Detect the sentiment (positive, negative, neutral) of this query: {query}{context_str}{mcp_str}"
        elif capability == 'assess_urgency':
            return f"Assess the urgency level (low, medium, high) of this query: {query}{context_str}{mcp_str}"
        elif capability == 'language_detection':
            return f"Detect the language of this query: {query}{context_str}{mcp_str}"
        else:
            return f"{query}{context_str}{mcp_str}"

    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get('task_type')
        if task_type == 'analyze_query':
            return await self._process_query_analysis(task_data)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    async def _process_query_analysis(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        query = task_data.get('input_data', {}).get('query', '')
        context = task_data.get('input_data', {}).get('context', {})
        mcp_clients = task_data.get('mcp_clients', self.mcp_clients)
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
            prompt = self._build_prompt(query, capability, context, mcp_clients)
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

    # Genetic Algorithm Support - Query Agent Specific
    def _get_default_gene_template(self) -> Dict[str, Any]:
        """Get gene template for query agent"""
        return {
            'confidence_threshold': 0.8,
            'context_window_size': 1000,
            'classification_detail_level': 'medium',
            'include_sentiment': True,
            'extract_entities': True,
            'urgency_detection': True,
            'response_timeout': 5.0,
            'max_analysis_depth': 3,
            'language_detection_enabled': True
        }
    
    def _get_gene_ranges(self) -> Dict[str, Any]:
        """Get valid ranges for query agent genes"""
        return {
            'confidence_threshold': (0.1, 1.0),
            'context_window_size': (100, 5000),
            'classification_detail_level': ['low', 'medium', 'high'],
            'include_sentiment': [True, False],
            'extract_entities': [True, False],
            'urgency_detection': [True, False],
            'response_timeout': (1.0, 30.0),
            'max_analysis_depth': (1, 10),
            'language_detection_enabled': [True, False]
        }
    
    def _apply_chromosome_genes(self, genes: Dict[str, Any]):
        """Apply chromosome genes to query agent configuration"""
        super()._apply_chromosome_genes(genes)
        
        # Apply query-specific genes
        if 'confidence_threshold' in genes:
            self.confidence_threshold = genes['confidence_threshold']
        if 'context_window_size' in genes:
            self.context_window_size = genes['context_window_size']
        if 'classification_detail_level' in genes:
            self.classification_detail_level = genes['classification_detail_level']
        if 'include_sentiment' in genes:
            self.include_sentiment = genes['include_sentiment']
        if 'extract_entities' in genes:
            self.extract_entities = genes['extract_entities']
        if 'urgency_detection' in genes:
            self.urgency_detection = genes['urgency_detection']
        if 'response_timeout' in genes:
            self.response_timeout = genes['response_timeout']
        if 'max_analysis_depth' in genes:
            self.max_analysis_depth = genes['max_analysis_depth']
        if 'language_detection_enabled' in genes:
            self.language_detection_enabled = genes['language_detection_enabled']
    
    def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input for fitness evaluation"""
        import time
        import asyncio
        
        start_time = time.time()
        
        try:
            # Extract query from input
            query = input_data.get('query', '')
            context = input_data.get('context', {})
            
            if not query:
                return {
                    'success': False,
                    'error': 'No query provided',
                    'processing_time': time.time() - start_time
                }
            
            # Create task data structure
            task_data = {
                'task_type': 'analyze_query',
                'input_data': {
                    'query': query,
                    'context': context
                },
                'capability': 'analyze_query',
                'llm_provider': self.llm_provider,
                'llm_model': self.llm_model,
                'api_key': self.api_key
            }
            
            # Run async task in event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an event loop, we need to handle this differently
                    future = asyncio.ensure_future(self._process_query_analysis(task_data))
                    # For fitness evaluation, we'll use a simplified synchronous version
                    result = self._process_query_sync(query, context)
                else:
                    result = loop.run_until_complete(self._process_query_analysis(task_data))
            except RuntimeError:
                # Fallback to synchronous processing for fitness evaluation
                result = self._process_query_sync(query, context)
            
            result['processing_time'] = time.time() - start_time
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _process_query_sync(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous query processing for fitness evaluation"""
        # Simplified synchronous analysis for genetic algorithm evaluation
        analysis = {
            'intent': self._classify_intent_sync(query),
            'entities': self._extract_entities_sync(query) if getattr(self, 'extract_entities', True) else [],
            'sentiment': self._detect_sentiment_sync(query) if getattr(self, 'include_sentiment', True) else 'neutral',
            'urgency': self._assess_urgency_sync(query) if getattr(self, 'urgency_detection', True) else 'low',
            'language': self._detect_language_sync(query) if getattr(self, 'language_detection_enabled', True) else 'en',
            'confidence': getattr(self, 'confidence_threshold', 0.8)
        }
        
        return {
            'success': True,
            'analysis': analysis,
            'content': str(analysis)
        }
    
    def _classify_intent_sync(self, query: str) -> str:
        """Simple synchronous intent classification"""
        query_lower = query.lower()
        if any(word in query_lower for word in ['refund', 'cancel', 'complaint', 'problem', 'issue']):
            return 'complaint'
        elif any(word in query_lower for word in ['billing', 'payment', 'charge', 'invoice']):
            return 'billing'
        elif any(word in query_lower for word in ['login', 'password', 'access', 'account']):
            return 'technical'
        elif any(word in query_lower for word in ['feature', 'request', 'suggestion', 'improve']):
            return 'feature_request'
        else:
            return 'general'
    
    def _extract_entities_sync(self, query: str) -> List[str]:
        """Simple synchronous entity extraction"""
        # Basic entity extraction using keywords
        entities = []
        words = query.split()
        for word in words:
            if word.lower() in ['account', 'password', 'email', 'billing', 'payment']:
                entities.append(word.lower())
        return list(set(entities))
    
    def _detect_sentiment_sync(self, query: str) -> str:
        """Simple synchronous sentiment detection"""
        positive_words = ['thank', 'great', 'excellent', 'good', 'happy', 'satisfied']
        negative_words = ['terrible', 'awful', 'bad', 'angry', 'frustrated', 'disappointed']
        
        query_lower = query.lower()
        pos_count = sum(1 for word in positive_words if word in query_lower)
        neg_count = sum(1 for word in negative_words if word in query_lower)
        
        if neg_count > pos_count:
            return 'negative'
        elif pos_count > neg_count:
            return 'positive'
        else:
            return 'neutral'
    
    def _assess_urgency_sync(self, query: str) -> str:
        """Simple synchronous urgency assessment"""
        urgent_words = ['urgent', 'emergency', 'asap', 'immediately', 'critical', 'broken']
        query_lower = query.lower()
        
        if any(word in query_lower for word in urgent_words):
            return 'high'
        elif any(word in query_lower for word in ['soon', 'quick', 'fast']):
            return 'medium'
        else:
            return 'low'
    
    def _detect_language_sync(self, query: str) -> str:
        """Simple synchronous language detection"""
        # Basic language detection - in practice you'd use a proper library
        return 'en'  # Default to English for simplicity
