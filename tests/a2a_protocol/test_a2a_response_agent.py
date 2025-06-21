import pytest
import asyncio
from a2a_protocol.a2a_response_agent import A2AResponseAgent

@pytest.mark.asyncio
async def test_a2a_response_agent_process_task():
    agent = A2AResponseAgent(agent_id="test_response_agent")
    task_data = {"task_type": "generate_response", "query_analysis": {}, "knowledge_result": {}, "customer_context": {}, "ticket_id": "t1"}
    result = await agent.process_task(task_data)
    assert "agent_id" in result or "a2a_processed" in result
