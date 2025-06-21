"""
QueryAgent: Handles query understanding and classification using ChatGPT API.
"""
from .base_agent import BaseAgent
import openai

class QueryAgent(BaseAgent):
    def __init__(self, api_key, config=None):
        # Store the API key for OpenAI and any additional config
        self.api_key = api_key
        self.config = config
        self.chromosome = None  # Used for genetic algorithm optimization

    def process_input(self, input_data):
        """
        Analyze a customer query using the OpenAI ChatGPT API.
        Returns a dictionary with category, urgency, sentiment, and success flag.
        """
        query = input_data.get('query', '')
        # Construct a prompt for the LLM to classify the query
        prompt = (
            "Classify the following customer query. "
            "Return a JSON object with keys: category, urgency, sentiment.\n"
            f"Query: {query}"
        )
        try:
            # Call the OpenAI ChatCompletion API with the prompt
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                api_key=self.api_key,
                messages=[{"role": "user", "content": prompt}]
            )
            # Extract the LLM's response content
            content = response.choices[0].message['content']
            # Try to parse the LLM's response as JSON
            import json
            parsed = json.loads(content)
            return {
                'category': parsed.get('category', 'general'),  # e.g., 'billing', 'technical', etc.
                'urgency': parsed.get('urgency', 'low'),        # e.g., 'high', 'medium', 'low'
                'sentiment': parsed.get('sentiment', 'neutral'),# e.g., 'positive', 'negative', 'neutral'
                'success': True
            }
        except Exception as e:
            # If anything fails, return a default result and include the error
            return {
                'category': 'general',
                'urgency': 'low',
                'sentiment': 'neutral',
                'success': False,
                'error': str(e)
            }

    def set_chromosome(self, chromosome):
        """
        Set the chromosome for this agent (used by the genetic algorithm).
        """
        self.chromosome = chromosome
