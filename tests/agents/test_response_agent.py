import pytest
from agents.response_agent import ResponseAgent

# DEPRECATED: This test is for the legacy ResponseAgent and is no longer maintained.
# Please use tests in tests/a2a_protocol/ for A2A-enabled agents.

@pytest.mark.asyncio
async def test_process_input(monkeypatch):
    agent = ResponseAgent(api_key="dummy")
    async def dummy_parent_process_input(self, input_data):
        return {"success": True, "response": "Test response", "confidence": 0.95}
    monkeypatch.setattr(ResponseAgent.__bases__[0], "process_input", dummy_parent_process_input)
    result = await agent.process_input({"query_analysis": {}, "knowledge_result": {}, "customer_context": {}, "ticket_id": "t1", "session_id": "s1"})
    assert result["success"]
    assert result["response"] == "Test response"
    assert result["confidence"] == 0.95
