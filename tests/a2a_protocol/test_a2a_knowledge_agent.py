import pytest
import asyncio
from a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent

@pytest.mark.asyncio
async def test_a2a_knowledge_agent_process_task():
    agent = A2AKnowledgeAgent(agent_id="test_knowledge_agent")
    task_data = {"task_type": "knowledge_search", "input_data": {"query": "What is the refund policy?"}}
    result = await agent.process_task(task_data)
    assert "agent_id" in result or "a2a_processed" in result
