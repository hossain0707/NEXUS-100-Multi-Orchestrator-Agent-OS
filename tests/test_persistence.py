import pytest

from nexus.orchestrator import orchestrator
from nexus.persistence import init_db, load_mission, save_mission


@pytest.mark.asyncio
async def test_mission_round_trip():
    await init_db()
    mission = orchestrator.plan("Research an LLM")
    await save_mission(mission)
    loaded = await load_mission(str(mission.id))
    assert loaded is not None
    assert loaded.id == mission.id
    assert loaded.objective == mission.objective
