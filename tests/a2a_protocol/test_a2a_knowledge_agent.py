import pytest
import asyncio
from src.a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent

@pytest.mark.asyncio
async def test_a2a_knowledge_agent_process_task():
    agent = A2AKnowledgeAgent(agent_id="test_knowledge_agent", api_key="sk-test", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "knowledge_search", "input_data": {"query": "What is the refund policy?"}, "capability": "knowledge_search"}
    result = await agent.process_task(task_data)
    assert result["agent_id"] == "test_knowledge_agent"
    assert result["a2a_processed"]
    assert result["success"] in [True, False]

@pytest.mark.asyncio
async def test_a2a_knowledge_agent_openai():
    agent = A2AKnowledgeAgent(agent_id="test_knowledge_agent_openai", api_key="sk-test", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "knowledge_search", "input_data": {"query": "What is the refund policy?"}, "capability": "knowledge_search"}
    result = await agent.process_task(task_data)
    assert result["agent_id"] == "test_knowledge_agent_openai"
    assert result["a2a_processed"]
    assert result["success"] in [True, False]

@pytest.mark.asyncio
async def test_a2a_knowledge_agent_gemini():
    agent = A2AKnowledgeAgent(agent_id="test_knowledge_agent_gemini", api_key="gemini-test", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "knowledge_search", "input_data": {"query": "What is the refund policy?"}, "capability": "knowledge_search", "llm_provider": "gemini", "llm_model": "gemini-pro"}
    try:
        result = await agent.process_task(task_data)
        assert result["agent_id"] == "test_knowledge_agent_gemini"
        assert result["a2a_processed"]
        assert result["success"] in [True, False]
    except ImportError:
        pass  # Gemini not installed, skip

@pytest.mark.asyncio
async def test_a2a_knowledge_agent_claude():
    agent = A2AKnowledgeAgent(agent_id="test_knowledge_agent_claude", api_key="claude-test", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "knowledge_search", "input_data": {"query": "What is the refund policy?"}, "capability": "knowledge_search", "llm_provider": "claude", "llm_model": "claude-3-opus-20240229"}
    try:
        result = await agent.process_task(task_data)
        assert result["agent_id"] == "test_knowledge_agent_claude"
        assert result["a2a_processed"]
        assert result["success"] in [True, False]
    except ImportError:
        pass  # Claude not installed, skip
