from nexus.memory import memory
from nexus.models import Approval, Mission, Risk, RouteStep, TaskStatus
from nexus.registry import DOMAIN_CAPABILITIES, registry

KEYWORDS = {
    "research": ["research", "paper", "study", "literature", "model", "llm", "benchmark"],
    "engineering": ["code", "build", "implement", "debug", "test", "api", "software", "repository"],
    "business": ["market", "business", "product", "customer", "competitor", "sales"],
    "data": ["data", "rag", "sql", "dataset", "analytics", "document", "vector"],
    "infrastructure": ["gpu", "cloud", "deploy", "docker", "kubernetes", "server", "latency"],
    "security": ["security", "risk", "vulnerability", "audit", "threat", "secret"],
    "productivity": ["email", "document", "meeting", "calendar", "presentation", "summary"],
    "finance": ["budget", "cost", "invoice", "expense", "finance", "forecast"],
    "career": ["job", "career", "resume", "cv", "interview", "portfolio"],
    "personal": ["travel", "learn", "shopping", "personal", "household"],
}


class MetaOrchestrator:
    def route(self, objective):
        text = objective.lower()
        scored = []
        for domain, words in KEYWORDS.items():
            score = sum(1 for word in words if word in text)
            if score:
                scored.append((score, domain))

        domains = [domain for _, domain in sorted(scored, reverse=True)[:5]]
        if not domains:
            domains = ["research", "productivity"]

        if any(word in text for word in ["deploy", "production", "code"]):
            if "security" not in domains:
                domains.append("security")

        route = []
        for order, domain in enumerate(domains[:5], 1):
            capabilities = DOMAIN_CAPABILITIES[domain]
            capability = next(
                (item for item in capabilities if item.replace("_", " ") in text or item in text),
                capabilities[0],
            )
            agent = registry.best(domain, capability)
            route.append(
                RouteStep(
                    order=order,
                    domain=domain,
                    orchestrator=f"{domain.title()} Orchestrator",
                    agent_id=agent.id,
                    capability=capability,
                )
            )
        return route

    def plan(self, objective, priority="normal"):
        mission = Mission(objective=objective, priority=priority, route=self.route(objective))
        memory.missions[str(mission.id)] = mission
        memory.event(
            "mission_planned",
            {"mission_id": str(mission.id), "route": [step.domain for step in mission.route]},
        )
        return mission

    def start(self, objective, priority="normal", dry_run=True):
        mission = self.plan(objective, priority)
        mission.status = TaskStatus.planned if dry_run else TaskStatus.queued
        memory.missions[str(mission.id)] = mission
        return mission

    def approval(self, action, reason, mission_id=None, risk=Risk.high):
        approval = Approval(action=action, reason=reason, mission_id=mission_id, risk=risk)
        memory.approvals[str(approval.id)] = approval
        memory.event("approval_requested", {"approval_id": str(approval.id), "action": action})
        return approval


orchestrator = MetaOrchestrator()
