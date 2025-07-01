"""
A2A-enabled Knowledge Agent
"""
import time
from typing import Dict, Any, List
from src.a2a_protocol.base_a2a_agent import A2AAgent
from src.utils.llm_client import set_openai_api_key, call_chatgpt

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
    def _build_prompt(self, query: str, capability: str, context: dict = None, mcp_clients: dict = None) -> str:
        context_str = f"\nContext: {context}" if context else ""
        mcp_str = f"\nMCP: {mcp_clients}" if mcp_clients else ""
        if capability == 'knowledge_search':
            return f"""You are an expert knowledge retrieval agent. Search your knowledge base and provide a concise, factual answer to the following query:{context_str}{mcp_str}\n\nQuery: {query}\n"""
        elif capability == 'synthesize_info':
            return f"Synthesize information from multiple sources for this query: {query}{context_str}{mcp_str}"
        elif capability == 'find_articles':
            return f"Find relevant articles for this query: {query}{context_str}{mcp_str}"
        elif capability == 'fact_checking':
            return f"Fact-check the following statement or query: {query}{context_str}{mcp_str}"
        elif capability == 'source_validation':
            return f"Validate the sources for this information: {query}{context_str}{mcp_str}"
        elif capability == 'content_summarization':
            return f"Summarize the following content or query: {query}{context_str}{mcp_str}"
        else:
            return f"{query}{context_str}{mcp_str}"
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
        context = task_data.get('input_data', {}).get('context', {})
        mcp_clients = task_data.get('mcp_clients', self.mcp_clients)
        capability = task_data.get('capability', 'knowledge_search')
        if not query:
            return {'success': False, 'error': 'No query provided', 'a2a_processed': True, 'agent_id': self.agent_id}
        try:
            prompt = self._build_prompt(query, capability, context, mcp_clients)
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

    # Knowledge sources management
    def set_knowledge_sources(self, knowledge_sources: Dict[str, Any]):
        """Set knowledge sources for the agent"""
        self.knowledge_sources = knowledge_sources
    
    # Genetic Algorithm Support - Knowledge Agent Specific
    def _get_default_gene_template(self) -> Dict[str, Any]:
        """Get gene template for knowledge agent"""
        return {
            'search_depth': 5,
            'relevance_threshold': 0.7,
            'max_sources': 10,
            'include_citations': True,
            'fact_checking_enabled': True,
            'synthesis_level': 'detailed',
            'search_timeout': 10.0,
            'confidence_boost': 1.0,
            'source_diversity': 0.8
        }
    
    def _get_gene_ranges(self) -> Dict[str, Any]:
        """Get valid ranges for knowledge agent genes"""
        return {
            'search_depth': (1, 15),
            'relevance_threshold': (0.1, 1.0),
            'max_sources': (1, 50),
            'include_citations': [True, False],
            'fact_checking_enabled': [True, False],
            'synthesis_level': ['basic', 'detailed', 'comprehensive'],
            'search_timeout': (5.0, 60.0),
            'confidence_boost': (0.5, 2.0),
            'source_diversity': (0.1, 1.0)
        }
    
    def _apply_chromosome_genes(self, genes: Dict[str, Any]):
        """Apply chromosome genes to knowledge agent configuration"""
        super()._apply_chromosome_genes(genes)
        
        # Apply knowledge-specific genes
        if 'search_depth' in genes:
            self.search_depth = genes['search_depth']
        if 'relevance_threshold' in genes:
            self.relevance_threshold = genes['relevance_threshold']
        if 'max_sources' in genes:
            self.max_sources = genes['max_sources']
        if 'include_citations' in genes:
            self.include_citations = genes['include_citations']
        if 'fact_checking_enabled' in genes:
            self.fact_checking_enabled = genes['fact_checking_enabled']
        if 'synthesis_level' in genes:
            self.synthesis_level = genes['synthesis_level']
        if 'search_timeout' in genes:
            self.search_timeout = genes['search_timeout']
        if 'confidence_boost' in genes:
            self.confidence_boost = genes['confidence_boost']
        if 'source_diversity' in genes:
            self.source_diversity = genes['source_diversity']
    
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
                'task_type': 'knowledge_search',
                'input_data': {
                    'query': query,
                    'context': context
                },
                'capability': 'knowledge_search'
            }
            
            # Use synchronous processing for fitness evaluation
            result = self._process_knowledge_sync(query, context)
            result['processing_time'] = time.time() - start_time
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _process_knowledge_sync(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous knowledge processing for fitness evaluation"""
        # Simplified synchronous knowledge retrieval for genetic algorithm evaluation
        
        # Simulate knowledge search based on genes
        search_depth = getattr(self, 'search_depth', 5)
        relevance_threshold = getattr(self, 'relevance_threshold', 0.7)
        max_sources = getattr(self, 'max_sources', 10)
        include_citations = getattr(self, 'include_citations', True)
        
        # Simple knowledge matching
        knowledge_score = self._calculate_knowledge_relevance(query)
        
        knowledge_response = {
            'answer': self._generate_knowledge_answer(query),
            'relevance_score': knowledge_score,
            'sources_used': min(max_sources, search_depth),
            'confidence': knowledge_score * getattr(self, 'confidence_boost', 1.0),
            'citations': self._generate_citations(query) if include_citations else []
        }
        
        return {
            'success': True,
            'knowledge': knowledge_response,
            'content': str(knowledge_response)
        }
    
    def _calculate_knowledge_relevance(self, query: str) -> float:
        """Calculate relevance score for the query"""
        # Simple relevance calculation based on query complexity and gene settings
        query_words = len(query.split())
        base_relevance = min(0.9, 0.3 + (query_words * 0.1))
        
        # Apply threshold
        threshold = getattr(self, 'relevance_threshold', 0.7)
        if base_relevance < threshold:
            return threshold * 0.8  # Reduced score if below threshold
        
        return base_relevance
    
    def _generate_knowledge_answer(self, query: str) -> str:
        """Generate a knowledge answer based on query"""
        # Simplified answer generation
        synthesis_level = getattr(self, 'synthesis_level', 'detailed')
        
        if synthesis_level == 'basic':
            return f"Basic answer for: {query}"
        elif synthesis_level == 'detailed':
            return f"Detailed knowledge response for: {query}. This includes comprehensive information."
        else:  # comprehensive
            return f"Comprehensive analysis for: {query}. This includes detailed information, multiple perspectives, and thorough coverage."
    
    def _generate_citations(self, query: str) -> List[str]:
        """Generate citations for the knowledge"""
        # Simplified citation generation
        max_sources = getattr(self, 'max_sources', 10)
        return [f"Source {i+1}: Knowledge base entry for '{query}'" for i in range(min(3, max_sources))]
