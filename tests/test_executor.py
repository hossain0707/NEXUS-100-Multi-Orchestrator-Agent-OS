import pytest

from nexus.executor import executor
from nexus.orchestrator import orchestrator
from nexus.persistence import init_db


@pytest.mark.asyncio
async def test_executor_without_provider_is_safe():
    await init_db()
    mission = orchestrator.plan("Research an LLM")
    result = await executor.execute(mission)
    assert result.status.value == "completed"
    assert all(step.status.value == "completed" for step in result.route)
