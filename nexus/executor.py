import asyncio

import httpx

from nexus.config import settings
from nexus.llm import LLMNotConfigured, llm
from nexus.memory import memory
from nexus.model_router import ReasoningEffort, model_router
from nexus.models import Mission, TaskStatus
from nexus.persistence import save_mission


EFFORT_ORDER = [
    ReasoningEffort.low,
    ReasoningEffort.medium,
    ReasoningEffort.high,
    ReasoningEffort.extra_high,
]


def _escalate_effort(current: ReasoningEffort, attempt: int) -> ReasoningEffort:
    index = min(EFFORT_ORDER.index(current) + attempt, len(EFFORT_ORDER) - 1)
    return EFFORT_ORDER[index]


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

    async def execute_adaptive(self, mission: Mission) -> dict:
        """Execute a mission through configured backend models with bounded escalation."""
        if not settings.backend_model_execution_enabled or not llm.configured:
            raise LLMNotConfigured(
                "Adaptive backend execution is not enabled for this deployment."
            )

        strategy = model_router.plan(
            mission.objective,
            mission.route,
            mission.priority,
        )
        decisions = {
            decision["agent_id"]: decision
            for decision in strategy["decisions"]
        }

        mission.status = TaskStatus.running
        await save_mission(mission)

        results = []
        total_input_tokens = 0
        total_output_tokens = 0

        try:
            async with asyncio.timeout(settings.task_timeout_seconds):
                for step in mission.route:
                    decision = decisions[step.agent_id]
                    candidates = [
                        decision["model"],
                        *decision["escalation_models"],
                    ]
                    candidates = candidates[: 1 + settings.max_model_escalations]
                    last_error = None
                    completion = None
                    used_model = None
                    used_effort = None
                    attempts = 0

                    for attempt, candidate in enumerate(candidates):
                        attempts += 1
                        effort = _escalate_effort(
                            ReasoningEffort(decision["reasoning_effort"]),
                            attempt,
                        )
                        try:
                            completion = await llm.complete(
                                model=candidate,
                                reasoning_effort=effort,
                                max_output_tokens=decision["max_output_tokens"],
                                system=(
                                    "You are a NEXUS-100 specialist agent. "
                                    f"Domain: {step.domain}. "
                                    f"Capability: {step.capability}. "
                                    "Return a concise, technically grounded result "
                                    "for this assigned subtask."
                                ),
                                prompt=mission.objective,
                            )
                            used_model = candidate
                            used_effort = effort.value
                            break
                        except (httpx.HTTPError, KeyError, ValueError) as exc:
                            last_error = f"{type(exc).__name__}: {exc}"
                            memory.event(
                                "model_attempt_failed",
                                {
                                    "mission_id": str(mission.id),
                                    "agent_id": step.agent_id,
                                    "model": candidate,
                                    "attempt": attempts,
                                },
                            )

                    if completion is None:
                        mission.status = TaskStatus.failed
                        await save_mission(mission)
                        return {
                            "mission": mission.model_dump(mode="json"),
                            "strategy": strategy,
                            "results": results,
                            "error": "model_execution_failed",
                            "last_error": last_error,
                        }

                    step.status = TaskStatus.completed
                    if completion.input_tokens:
                        total_input_tokens += completion.input_tokens
                    if completion.output_tokens:
                        total_output_tokens += completion.output_tokens

                    result = {
                        "agent_id": step.agent_id,
                        "domain": step.domain,
                        "capability": step.capability,
                        "model": used_model,
                        "reasoning_effort": used_effort,
                        "attempts": attempts,
                        "input_tokens": completion.input_tokens,
                        "output_tokens": completion.output_tokens,
                        "finish_reason": completion.finish_reason,
                        "output": completion.text,
                    }
                    results.append(result)
                    memory.event(
                        "agent_model_completed",
                        {
                            "mission_id": str(mission.id),
                            "agent_id": step.agent_id,
                            "model": used_model,
                            "reasoning_effort": used_effort,
                            "input_tokens": completion.input_tokens,
                            "output_tokens": completion.output_tokens,
                        },
                    )
        except TimeoutError:
            mission.status = TaskStatus.failed
            await save_mission(mission)
            return {
                "mission": mission.model_dump(mode="json"),
                "strategy": strategy,
                "results": results,
                "error": "mission_timeout",
            }

        mission.status = TaskStatus.completed
        await save_mission(mission)
        memory.event(
            "adaptive_mission_completed",
            {
                "mission_id": str(mission.id),
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
            },
        )
        return {
            "mission": mission.model_dump(mode="json"),
            "strategy": strategy,
            "results": results,
            "usage": {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
            },
        }


executor = MissionExecutor()
