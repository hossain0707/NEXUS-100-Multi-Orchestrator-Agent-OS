from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from nexus.executor import executor
from nexus.memory import memory
from nexus.orchestrator import orchestrator
from nexus.persistence import load_mission, save_mission
from nexus.registry import registry

router = APIRouter(prefix="/api/v1")


class MissionIn(BaseModel):
    objective: str = Field(min_length=3, max_length=4000)
    priority: str = "normal"
    dry_run: bool = True


@router.get("/agents")
async def agents():
    return {
        "count": len(registry.agents),
        "agents": [agent.model_dump() for agent in registry.agents.values()],
    }


@router.post("/missions")
async def create_mission(body: MissionIn):
    mission = orchestrator.start(body.objective, body.priority, body.dry_run)
    await save_mission(mission)
    return mission


@router.post("/missions/{mission_id}/queue")
async def queue_mission(mission_id: str):
    """Queue a planned mission for an MCP client such as ChatGPT."""
    mission = await load_mission(mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    return await executor.queue_for_client(mission)


@router.get("/missions/{mission_id}")
async def get_mission(mission_id: str):
    mission = await load_mission(mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    return mission


@router.get("/events")
async def events(limit: int = 100):
    safe_limit = min(max(limit, 1), 500)
    return {"events": list(memory.events)[-safe_limit:]}
