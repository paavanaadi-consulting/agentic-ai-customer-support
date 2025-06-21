import pytest
import asyncio
from agents.enhanced_query_agent import EnhancedQueryAgent

class DummyDB:
    async def get_customer_context(self, customer_id):
        return {
            'customer': {'tier': 'gold', 'total_tickets': 5, 'satisfaction_avg': 4.5},
            'patterns': {'common_categories': [{'category': 'billing'}, {'category': 'support'}]},
            'open_tickets': [1, 2]
        }
    async def save_query_interaction(self, interaction_data):
        return 'test-query-id'
    async def get_related_articles(self, query):
        return ['article1', 'article2']

# DEPRECATED: This test is for the legacy EnhancedQueryAgent and is no longer maintained.
# Please use tests in tests/a2a_protocol/ for A2A-enabled agents.
@pytest.mark.asyncio
async def test_process_input_enhanced(monkeypatch):
    agent = EnhancedQueryAgent(api_key='dummy', db_connector=DummyDB())
    input_data = {'customer_id': 'cust1', 'query': 'How do I upgrade my plan?'}
    # Patch parent process_input to return a dummy result
    async def dummy_parent_process_input(self, enhanced_input):
        return {
            'success': True,
            'analysis': {
                'category': 'upgrade',
                'intent': 'upgrade_plan',
                'entities': ['plan'],
                'sentiment': 'neutral',
                'sentiment_score': 0.5,
                'urgency': 'low',
                'urgency_score': 0.2,
                'confidence': 0.9
            }
        }
    monkeypatch.setattr(EnhancedQueryAgent.__bases__[0], 'process_input', dummy_parent_process_input)
    result = await agent.process_input(input_data)
    assert result['success']
    assert result['query_id'] == 'test-query-id'
    assert 'related_articles' in result

def test_build_analysis_prompt():
    agent = EnhancedQueryAgent(api_key='dummy', db_connector=None)
    context = {
        'customer_context': {
            'customer': {'tier': 'gold', 'total_tickets': 5, 'satisfaction_avg': 4.5},
            'patterns': {'common_categories': [{'category': 'billing'}, {'category': 'support'}]},
            'open_tickets': [1, 2]
        }
    }
    prompt = agent._build_analysis_prompt('Test query', context)
    assert 'Customer Context' in prompt
    assert 'gold' in prompt
    assert 'billing' in prompt
