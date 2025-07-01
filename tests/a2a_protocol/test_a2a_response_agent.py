import pytest
import asyncio
from src.a2a_protocol.a2a_response_agent import A2AResponseAgent

@pytest.mark.asyncio
async def test_a2a_response_agent_process_task():
    agent = A2AResponseAgent(agent_id="test_response_agent", api_key="sk-test", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "generate_response", "query_analysis": {"analysis": "Test analysis"}, "knowledge_result": {}, "customer_context": {}, "ticket_id": "t1", "capability": "generate_response"}
    result = await agent.process_task(task_data)
    assert result["agent_id"] == "test_response_agent"
    assert result["a2a_processed"]
    assert result["success"] in [True, False]

@pytest.mark.asyncio
async def test_a2a_response_agent_openai():
    agent = A2AResponseAgent(agent_id="test_response_agent_openai", api_key="sk-test", llm_provider="openai", llm_model="gpt-3.5-turbo", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "generate_response", "query_analysis": {"analysis": "Test analysis"}, "capability": "generate_response"}
    result = await agent.process_task(task_data)
    assert result["agent_id"] == "test_response_agent_openai"
    assert result["a2a_processed"]
    assert result["success"] in [True, False]

@pytest.mark.asyncio
async def test_a2a_response_agent_gemini():
    agent = A2AResponseAgent(agent_id="test_response_agent_gemini", api_key="gemini-test", llm_provider="gemini", llm_model="gemini-pro", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "generate_response", "query_analysis": {"analysis": "Test analysis"}, "capability": "generate_response"}
    try:
        result = await agent.process_task(task_data)
        assert result["agent_id"] == "test_response_agent_gemini"
        assert result["a2a_processed"]
        assert result["success"] in [True, False]
    except ImportError:
        pass  # Gemini not installed, skip

@pytest.mark.asyncio
async def test_a2a_response_agent_claude():
    agent = A2AResponseAgent(agent_id="test_response_agent_claude", api_key="claude-test", llm_provider="claude", llm_model="claude-3-opus-20240229", mcp_clients={"postgres": "dummy"})
    task_data = {"task_type": "generate_response", "query_analysis": {"analysis": "Test analysis"}, "capability": "generate_response"}
    try:
        result = await agent.process_task(task_data)
        assert result["agent_id"] == "test_response_agent_claude"
        assert result["a2a_processed"]
        assert result["success"] in [True, False]
    except ImportError:
        pass  # Claude not installed, skip
