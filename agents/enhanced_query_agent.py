import time
import json
from typing import Dict, Any
from agents.query_agent import QueryAgent
from data_sources.enhanced_rdbms_connector import EnhancedRDBMSConnector

class EnhancedQueryAgent(QueryAgent):
    """Enhanced Query Agent with database integration"""
    
    def __init__(self, agent_id: str = "enhanced_query_agent", api_key: str = None, db_connector=None):
        super().__init__(agent_id, api_key)
        self.db = db_connector
    
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced processing with database context"""
        start_time = time.time()
        
        try:
            customer_id = input_data.get('customer_id')
            query_text = input_data.get('query', '')
            
            # Get customer context from database
            customer_context = {}
            if customer_id and self.db:
                customer_context = await self.db.get_customer_context(customer_id)
            
            # Enhanced prompt with customer context
            enhanced_input = {
                **input_data,
                'customer_context': customer_context
            }
            
            # Process with parent class
            result = await super().process_input(enhanced_input)
            
            # Save interaction to database
            if self.db and result.get('success'):
                interaction_data = {
                    'customer_id': customer_id,
                    'query_text': query_text,
                    'query_type': result['analysis'].get('category'),
                    'detected_intent': result['analysis'].get('intent'),
                    'detected_entities': result['analysis'].get('entities', []),
                    'sentiment': result['analysis'].get('sentiment'),
                    'sentiment_score': result['analysis'].get('sentiment_score'),
                    'urgency_level': result['analysis'].get('urgency'),
                    'urgency_score': result['analysis'].get('urgency_score'),
                    'category_prediction': result['analysis'].get('category'),
                    'category_confidence': result['analysis'].get('confidence'),
                    'processing_time_ms': int((time.time() - start_time) * 1000),
                    'agents_used': [self.agent_id],
                    'success_metrics': {
                        'analysis_confidence': result['analysis'].get('confidence', 0),
                        'processing_success': True
                    }
                }
                
                query_id = await self.db.save_query_interaction(interaction_data)
                result['query_id'] = query_id
            
            # Suggest related knowledge articles
            if self.db and result.get('success'):
                related_articles = await self.db.get_related_articles({
                    'subject': query_text,
                    'category': result['analysis'].get('category')
                })
                result['related_articles'] = related_articles
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in enhanced processing: {str(e)}")
            return await super().process_input(input_data)
    
    def _build_analysis_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Enhanced prompt building with customer context"""
        base_prompt = super()._build_analysis_prompt(query, context)
        
        customer_context = context.get('customer_context', {})
        
        if customer_context:
            context_info = f"""
            
            Customer Context:
            - Customer Tier: {customer_context.get('customer', {}).get('tier', 'unknown')}
            - Total Previous Tickets: {customer_context.get('customer', {}).get('total_tickets', 0)}
            - Average Satisfaction: {customer_context.get('customer', {}).get('satisfaction_avg', 0)}
            - Recent Categories: {[cat['category'] for cat in customer_context.get('patterns', {}).get('common_categories', [])[:3]]}
            - Open Tickets: {len(customer_context.get('open_tickets', []))}
            
            Consider this context when analyzing the query for more personalized insights.
            """
            
            base_prompt += context_info
        
        return base_prompt
