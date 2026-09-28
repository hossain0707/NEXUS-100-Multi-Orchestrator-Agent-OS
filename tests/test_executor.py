import pytest

from nexus.executor import executor
from nexus.orchestrator import orchestrator
from nexus.persistence import init_db


@pytest.mark.asyncio
async def test_queue_for_chatgpt_does_not_fake_execution():
    await init_db()
    mission = orchestrator.plan("Research an LLM")
    result = await executor.queue_for_client(mission)
    assert result.status.value == "queued"
    assert all(step.status.value == "planned" for step in result.route)
