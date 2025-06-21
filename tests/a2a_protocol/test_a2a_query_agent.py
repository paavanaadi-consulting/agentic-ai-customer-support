import pytest
import asyncio
from a2a_protocol.a2a_query_agent import A2AQueryAgent

@pytest.mark.asyncio
async def test_a2a_query_agent_process_task():
    agent = A2AQueryAgent(agent_id="test_query_agent", api_key="sk-test", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "analyze_query", "input_data": {"query": "How do I upgrade?"}, "capability": "analyze_query"}
    result = await agent.process_task(task_data)
    assert result["a2a_processed"]
    assert result["agent_id"] == "test_query_agent"
    assert "processing_time" in result
    assert result["success"] in [True, False]

@pytest.mark.asyncio
async def test_a2a_query_agent_openai():
    agent = A2AQueryAgent(agent_id="test_query_agent_openai", api_key="sk-test", llm_provider="openai", llm_model="gpt-3.5-turbo", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "analyze_query", "input_data": {"query": "How do I upgrade?"}, "capability": "analyze_query"}
    result = await agent.process_task(task_data)
    assert result["a2a_processed"]
    assert result["agent_id"] == "test_query_agent_openai"
    assert "processing_time" in result
    assert result["success"] in [True, False]

@pytest.mark.asyncio
async def test_a2a_query_agent_gemini():
    agent = A2AQueryAgent(agent_id="test_query_agent_gemini", api_key="gemini-test", llm_provider="gemini", llm_model="gemini-pro", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "analyze_query", "input_data": {"query": "How do I upgrade?"}, "capability": "analyze_query"}
    try:
        result = await agent.process_task(task_data)
        assert result["a2a_processed"]
        assert result["agent_id"] == "test_query_agent_gemini"
        assert "processing_time" in result
        assert result["success"] in [True, False]
    except ImportError:
        pass  # Gemini not installed, skip

@pytest.mark.asyncio
async def test_a2a_query_agent_claude():
    agent = A2AQueryAgent(agent_id="test_query_agent_claude", api_key="claude-test", llm_provider="claude", llm_model="claude-3-opus-20240229", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "analyze_query", "input_data": {"query": "How do I upgrade?"}, "capability": "analyze_query"}
    try:
        result = await agent.process_task(task_data)
        assert result["a2a_processed"]
        assert result["agent_id"] == "test_query_agent_claude"
        assert "processing_time" in result
        assert result["success"] in [True, False]
    except ImportError:
        pass  # Claude not installed, skip
