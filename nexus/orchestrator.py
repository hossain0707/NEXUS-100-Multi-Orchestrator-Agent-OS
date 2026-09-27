from nexus.memory import memory
from nexus.models import Approval,Mission,RouteStep,TaskStatus,Risk
from nexus.registry import DOMAIN_CAPABILITIES,registry
KEYWORDS={
"research":["research","paper","study","literature","model","llm","benchmark"],
"engineering":["code","build","implement","debug","test","api","software","repository"],
"business":["market","business","product","customer","competitor","sales"],
"data":["data","rag","sql","dataset","analytics","document","vector"],
"infrastructure":["gpu","cloud","deploy","docker","kubernetes","server","latency"],
"security":["security","risk","vulnerability","audit","threat","secret"],
"productivity":["email","document","meeting","calendar","presentation","summary"],
"finance":["budget","cost","invoice","expense","finance","forecast"],
"career":["job","career","resume","cv","interview","portfolio"],
"personal":["travel","learn","shopping","personal","household"]}
class MetaOrchestrator:
    def route(self,objective):
        text=objective.lower(); scored=[]
        for domain,words in KEYWORDS.items():
            score=sum(1 for w in words if w in text)
            if score: scored.append((score,domain))
        domains=[d for _,d in sorted(scored,reverse=True)[:5]] or ["research","productivity"]
        if any(x in text for x in ["deploy","production","code"]) and "security" not in domains: domains.append("security")
        route=[]
        for i,domain in enumerate(domains[:5],1):
            caps=DOMAIN_CAPABILITIES[domain]
            cap=next((c for c in caps if c.replace("_"," ") in text or c in text),caps[0])
            agent=registry.best(domain,cap)
            route.append(RouteStep(order=i,domain=domain,orchestrator=f"{domain.title()} Orchestrator",agent_id=agent.id,capability=cap))
        return route
    def plan(self,objective,priority="normal"):
        mission=Mission(objective=objective,priority=priority,route=self.route(objective))
        memory.missions[str(mission.id)]=mission
        memory.event("mission_planned",{"mission_id":str(mission.id),"route":[s.domain for s in mission.route]})
        return mission
    def start(self,objective,priority="normal",dry_run=True):
        mission=self.plan(objective,priority); mission.status=TaskStatus.planned if dry_run else TaskStatus.queued
        memory.missions[str(mission.id)]=mission; return mission
    def approval(self,action,reason,mission_id=None,risk=Risk.high):
        a=Approval(action=action,reason=reason,mission_id=mission_id,risk=risk)
        memory.approvals[str(a.id)]=a; memory.event("approval_requested",{"approval_id":str(a.id),"action":action}); return a
orchestrator=MetaOrchestrator()
