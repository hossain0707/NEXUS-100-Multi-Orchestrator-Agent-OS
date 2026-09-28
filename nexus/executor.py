import asyncio

from nexus.config import settings
from nexus.llm import llm
from nexus.memory import memory
from nexus.models import Mission, TaskStatus
from nexus.persistence import save_mission
from nexus.registry import registry


class MissionExecutor:
    async def execute(self, mission: Mission) -> Mission:
        mission.status = TaskStatus.running
        await save_mission(mission)
        memory.event("mission_started", {"mission_id": str(mission.id)})

        try:
            async with asyncio.timeout(settings.task_timeout_seconds):
                context: list[str] = []
                for step in mission.route:
                    agent = registry.agents[step.agent_id]
                    step.status = TaskStatus.running
                    system = (
                        f"You are {agent.name}. Work only within the capability "
                        f"{step.capability}. Return concise factual output. "
                        "Do not claim external actions that were not actually executed."
                    )
                    result = await llm.complete(
                        system,
                        f"Mission: {mission.objective}\nPrior context: {context[-3:]}",
                    )
                    context.append(result)
                    step.status = TaskStatus.completed
                    memory.event(
                        "agent_completed",
                        {
                            "mission_id": str(mission.id),
                            "agent_id": agent.id,
                            "domain": agent.domain,
                            "result": result,
                        },
                    )
                    await save_mission(mission)
            mission.status = TaskStatus.completed
        except TimeoutError:
            mission.status = TaskStatus.failed
            memory.event("mission_timeout", {"mission_id": str(mission.id)})
        except Exception as exc:
            mission.status = TaskStatus.failed
            memory.event(
                "mission_failed",
                {"mission_id": str(mission.id), "error": type(exc).__name__},
            )
        await save_mission(mission)
        return mission


executor = MissionExecutor()
