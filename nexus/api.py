from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from nexus.memory import memory
from nexus.orchestrator import orchestrator
from nexus.registry import registry
router=APIRouter(prefix="/api/v1")
class MissionIn(BaseModel):
    objective:str=Field(min_length=3,max_length=4000)
    priority:str="normal"
    dry_run:bool=True
@router.get("/agents")
async def agents(): return {"count":len(registry.agents),"agents":[a.model_dump() for a in registry.agents.values()]}
@router.post("/missions")
async def create_mission(body:MissionIn): return orchestrator.start(body.objective,body.priority,body.dry_run)
@router.get("/missions/{mission_id}")
async def get_mission(mission_id:str):
    mission=memory.missions.get(mission_id)
    if not mission: raise HTTPException(404,"Mission not found")
    return mission
@router.get("/events")
async def events(limit:int=100): return {"events":list(memory.events)[-min(max(limit,1),500):]}
