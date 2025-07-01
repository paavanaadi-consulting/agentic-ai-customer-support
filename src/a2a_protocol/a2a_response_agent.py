"""
A2A-enabled Response Agent
"""
import time
from typing import Dict, Any, List
from src.a2a_protocol.base_a2a_agent import A2AAgent
from src.utils.llm_client import set_openai_api_key, set_gemini_api_key, set_claude_api_key, call_chatgpt, call_gemini, call_claude

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

    # Genetic Algorithm Support - Response Agent Specific
    def _get_default_gene_template(self) -> Dict[str, Any]:
        """Get gene template for response agent"""
        return {
            'tone': 'friendly',
            'length_preference': 'medium',
            'personalization_level': 0.7,
            'empathy_level': 0.8,
            'formality_level': 0.6,
            'include_suggestions': True,
            'response_timeout': 8.0,
            'creativity_level': 0.5,
            'solution_focus': 0.9
        }
    
    def _get_gene_ranges(self) -> Dict[str, Any]:
        """Get valid ranges for response agent genes"""
        return {
            'tone': ['friendly', 'professional', 'empathetic', 'casual', 'formal'],
            'length_preference': ['short', 'medium', 'long'],
            'personalization_level': (0.0, 1.0),
            'empathy_level': (0.0, 1.0),
            'formality_level': (0.0, 1.0),
            'include_suggestions': [True, False],
            'response_timeout': (3.0, 30.0),
            'creativity_level': (0.0, 1.0),
            'solution_focus': (0.0, 1.0)
        }
    
    def _apply_chromosome_genes(self, genes: Dict[str, Any]):
        """Apply chromosome genes to response agent configuration"""
        super()._apply_chromosome_genes(genes)
        
        # Apply response-specific genes
        if 'tone' in genes:
            self.tone = genes['tone']
        if 'length_preference' in genes:
            self.length_preference = genes['length_preference']
        if 'personalization_level' in genes:
            self.personalization_level = genes['personalization_level']
        if 'empathy_level' in genes:
            self.empathy_level = genes['empathy_level']
        if 'formality_level' in genes:
            self.formality_level = genes['formality_level']
        if 'include_suggestions' in genes:
            self.include_suggestions = genes['include_suggestions']
        if 'response_timeout' in genes:
            self.response_timeout = genes['response_timeout']
        if 'creativity_level' in genes:
            self.creativity_level = genes['creativity_level']
        if 'solution_focus' in genes:
            self.solution_focus = genes['solution_focus']
    
    def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input for fitness evaluation"""
        import time
        
        start_time = time.time()
        
        try:
            # Extract data from input
            query_analysis = input_data.get('query_analysis', {})
            context = input_data.get('context', {})
            
            if not query_analysis and 'query' in input_data:
                # If no analysis provided, create basic structure
                query_analysis = {
                    'analysis': input_data['query'],
                    'query': input_data['query']
                }
            
            # Create task data structure
            task_data = {
                'task_type': 'generate_response',
                'query_analysis': query_analysis,
                'context': context,
                'capability': 'generate_response'
            }
            
            # Use synchronous processing for fitness evaluation
            result = self._process_response_sync(query_analysis, context)
            result['processing_time'] = time.time() - start_time
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _process_response_sync(self, query_analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous response processing for fitness evaluation"""
        # Generate response based on genetic parameters
        
        tone = getattr(self, 'tone', 'friendly')
        length_preference = getattr(self, 'length_preference', 'medium')
        personalization_level = getattr(self, 'personalization_level', 0.7)
        empathy_level = getattr(self, 'empathy_level', 0.8)
        formality_level = getattr(self, 'formality_level', 0.6)
        include_suggestions = getattr(self, 'include_suggestions', True)
        solution_focus = getattr(self, 'solution_focus', 0.9)
        
        # Extract query information
        query_text = query_analysis.get('query', query_analysis.get('analysis', ''))
        sentiment = query_analysis.get('sentiment', 'neutral')
        urgency = query_analysis.get('urgency', 'low')
        category = query_analysis.get('category', 'general')
        
        # Generate response based on genes
        response_text = self._generate_response_text(
            query_text, sentiment, urgency, category,
            tone, length_preference, empathy_level, formality_level, solution_focus
        )
        
        # Add suggestions if enabled
        if include_suggestions:
            suggestions = self._generate_suggestions(category, urgency)
            response_text += "\n\n" + suggestions
        
        # Apply personalization
        if personalization_level > 0.5:
            response_text = self._personalize_response(response_text, context, personalization_level)
        
        response_data = {
            'text': response_text,
            'tone_used': tone,
            'length': len(response_text),
            'personalization_applied': personalization_level > 0.5,
            'suggestions_included': include_suggestions,
            'confidence': self._calculate_response_confidence(query_analysis)
        }
        
        return {
            'success': True,
            'response': response_data,
            'content': response_text
        }
    
    def _generate_response_text(self, query: str, sentiment: str, urgency: str, category: str,
                              tone: str, length: str, empathy: float, formality: float, solution_focus: float) -> str:
        """Generate response text based on genetic parameters"""
        
        # Base response templates
        empathy_phrases = {
            'negative': ["I understand your frustration", "I'm sorry to hear about this issue", "I can see why this would be concerning"],
            'neutral': ["Thank you for reaching out", "I'm here to help", "Let me assist you with this"],
            'positive': ["Thank you for your feedback", "I'm glad you contacted us", "It's great to hear from you"]
        }
        
        # Select empathy phrase based on sentiment and empathy level
        if empathy > 0.6 and sentiment in empathy_phrases:
            opening = empathy_phrases[sentiment][0]
        else:
            opening = "Thank you for contacting us"
        
        # Adjust tone
        if tone == 'formal':
            opening = opening.replace("I'm", "I am").replace("you're", "you are")
        elif tone == 'casual':
            opening = opening.lower()
        
        # Generate main content based on category and solution focus
        if solution_focus > 0.7:
            main_content = self._generate_solution_focused_content(category, urgency)
        else:
            main_content = self._generate_general_content(category)
        
        # Adjust length
        if length == 'short':
            response = f"{opening}. {main_content}"
        elif length == 'long':
            response = f"{opening}. {main_content} Please don't hesitate to reach out if you need any additional assistance."
        else:  # medium
            response = f"{opening}. {main_content} Let me know if you need further help."
        
        return response
    
    def _generate_solution_focused_content(self, category: str, urgency: str) -> str:
        """Generate solution-focused content"""
        solutions = {
            'technical': "Let me help you resolve this technical issue. I'll guide you through the troubleshooting steps.",
            'billing': "I'll review your billing information and help resolve any payment-related concerns.",
            'complaint': "I understand your concerns and will work to address them promptly.",
            'feature_request': "Thank you for your suggestion. I'll make sure it's forwarded to our development team.",
            'general': "I'm here to provide you with the information and assistance you need."
        }
        
        base_solution = solutions.get(category, solutions['general'])
        
        if urgency == 'high':
            return f"{base_solution} Given the urgency of your request, I'll prioritize this matter."
        
        return base_solution
    
    def _generate_general_content(self, category: str) -> str:
        """Generate general content"""
        return f"I'll be happy to help you with your {category} inquiry."
    
    def _generate_suggestions(self, category: str, urgency: str) -> str:
        """Generate helpful suggestions"""
        suggestions = {
            'technical': "You might also find our troubleshooting guide helpful in the future.",
            'billing': "Consider setting up auto-pay to avoid future billing concerns.",
            'complaint': "We value your feedback and use it to improve our services.",
            'feature_request': "Keep an eye on our updates page for new feature announcements.",
            'general': "Browse our FAQ section for quick answers to common questions."
        }
        
        base_suggestion = suggestions.get(category, suggestions['general'])
        return f"Suggestion: {base_suggestion}"
    
    def _personalize_response(self, response: str, context: Dict[str, Any], level: float) -> str:
        """Apply personalization to response"""
        if level > 0.8 and 'customer_name' in context:
            return f"Hi {context['customer_name']}, {response}"
        elif level > 0.5 and 'customer_tier' in context and context['customer_tier'] == 'premium':
            return f"{response} As a valued premium customer, you have access to priority support."
        
        return response
    
    def _calculate_response_confidence(self, query_analysis: Dict[str, Any]) -> float:
        """Calculate confidence in the response"""
        # Base confidence
        confidence = 0.8
        
        # Adjust based on query complexity
        if 'intent' in query_analysis:
            confidence += 0.1
        if 'entities' in query_analysis and query_analysis['entities']:
            confidence += 0.05
        
        # Adjust based on genetic parameters
        empathy_level = getattr(self, 'empathy_level', 0.8)
        solution_focus = getattr(self, 'solution_focus', 0.9)
        
        confidence = confidence * (0.5 + 0.5 * empathy_level) * (0.5 + 0.5 * solution_focus)
        
        return min(1.0, confidence)
