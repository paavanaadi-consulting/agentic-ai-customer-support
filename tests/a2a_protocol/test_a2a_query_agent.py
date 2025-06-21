import pytest
import asyncio
from a2a_protocol.a2a_query_agent import A2AQueryAgent

@pytest.mark.asyncio
async def test_a2a_query_agent_process_task():
    agent = A2AQueryAgent(agent_id="test_query_agent")
    task_data = {"task_type": "analyze_query", "input_data": {"query": "How do I upgrade?"}}
    result = await agent.process_task(task_data)
    assert result["a2a_processed"]
    assert result["agent_id"] == "test_query_agent"
    assert "processing_time" in result
