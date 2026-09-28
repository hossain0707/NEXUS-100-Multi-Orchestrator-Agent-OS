from nexus.memory import memory
from nexus.models import Mission, TaskStatus
from nexus.persistence import save_mission


class MissionExecutor:
    async def queue_for_client(self, mission: Mission) -> Mission:
        """Queue a mission for an MCP client such as ChatGPT to reason over."""
        mission.status = TaskStatus.queued
        await save_mission(mission)
        memory.event(
            "mission_queued_for_client",
            {"mission_id": str(mission.id), "mode": "chatgpt_mcp"},
        )
        return mission


executor = MissionExecutor()
