import pytest
import asyncio
from src.a2a_protocol.a2a_coordinator import A2ACoordinator

@pytest.mark.asyncio
async def test_a2a_coordinator_init():
    coordinator = A2ACoordinator(agent_id="test_coordinator")
    assert coordinator.agent_id == "test_coordinator"
    assert "workflow_orchestration" in coordinator.get_capabilities()
