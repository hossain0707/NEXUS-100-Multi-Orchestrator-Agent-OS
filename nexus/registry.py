from nexus.models import AgentSpec
DOMAIN_CAPABILITIES={
"research":["literature_search","paper_analysis","llm_research","experiment_design","fact_checking","synthesis","patent_research","benchmarking","citation_review","technical_writing"],
"engineering":["architecture","python","api","debugging","testing","code_review","devops","frontend","backend","automation"],
"business":["market_research","product","strategy","sales","operations","competitive_intelligence","requirements","pricing","partnerships","planning"],
"data":["rag","etl","sql","analytics","knowledge_graph","document_intelligence","vector_search","data_quality","evaluation","reporting"],
"infrastructure":["gpu","cloud","containers","kubernetes","reliability","cost_optimization","serving","monitoring","networking","capacity"],
"security":["threat_analysis","dependency_risk","incident_review","secrets","compliance","audit","iam","privacy","hardening","security_review"],
"productivity":["email","documents","meetings","calendar","summaries","presentations","workflows","notes","scheduling","coordination"],
"finance":["budgeting","expenses","invoices","forecasting","procurement","cost_analysis","unit_economics","reporting","planning","controls"],
"career":["jobs","cv","portfolio","interview","networking","skills","applications","research_profile","learning","positioning"],
"personal":["travel","learning","planning","shopping","household","organization","research","scheduling","comparison","life_admin"]}
class AgentRegistry:
    def __init__(self):
        self.agents={}
        n=1
        for domain,caps in DOMAIN_CAPABILITIES.items():
            for cap in caps:
                aid=f"A{n:03d}"
                self.agents[aid]=AgentSpec(id=aid,name=f"{domain.title()} {cap.replace('_',' ').title()} Agent",domain=domain,capabilities=[cap])
                n+=1
    def by_domain(self,domain): return [a for a in self.agents.values() if a.domain==domain]
    def best(self,domain,capability=None):
        agents=self.by_domain(domain)
        if capability:
            for a in agents:
                if capability in a.capabilities: return a
        return agents[0]
registry=AgentRegistry()
