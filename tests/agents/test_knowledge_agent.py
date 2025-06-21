import pytest
from agents.knowledge_agent import KnowledgeAgent

class DummyKnowledgeSource:
    def __init__(self):
        self.called = False
    async def get_knowledge(self, data):
        self.called = True
        return {"info": "dummy knowledge"}

# DEPRECATED: This test is for the legacy KnowledgeAgent and is no longer maintained.
# Please use tests in tests/a2a_protocol/ for A2A-enabled agents.
@pytest.mark.asyncio
async def test_process_input(monkeypatch):
    agent = KnowledgeAgent(api_key="dummy")
    agent.set_knowledge_sources({"db": DummyKnowledgeSource()})
    async def dummy_parent_process_input(self, input_data):
        return {"success": True, "synthesis": {"confidence": 0.8}, "sources_used": ["db"]}
    monkeypatch.setattr(KnowledgeAgent.__bases__[0], "process_input", dummy_parent_process_input)
    result = await agent.process_input({"analysis": {}, "original_query": "test", "customer_id": "c1", "ticket_id": "t1"})
    assert result["success"]
    assert "synthesis" in result
    assert "sources_used" in result
