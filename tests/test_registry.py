from nexus.registry import registry
from nexus.orchestrator import orchestrator
def test_exactly_100_agents(): assert len(registry.agents)==100
def test_cross_domain_route():
    route=orchestrator.route("Research an LLM, implement code, estimate GPU deployment and security risk")
    domains={x.domain for x in route}
    assert {"research","engineering","infrastructure","security"} <= domains
