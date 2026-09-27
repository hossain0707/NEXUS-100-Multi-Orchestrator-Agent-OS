from dataclasses import dataclass

from nexus.models import Risk

SENSITIVE = {"WRITE", "EXECUTE", "DELETE", "FINANCIAL", "EXTERNAL_COMMUNICATION", "DEPLOY"}


@dataclass(frozen=True)
class Decision:
    allowed: bool
    requires_approval: bool
    reason: str


class PolicyEngine:
    def evaluate(self, scopes: set[str], risk: Risk = Risk.low) -> Decision:
        if scopes & SENSITIVE or risk in {Risk.high, Risk.critical}:
            return Decision(False, True, "Human approval required for consequential action.")
        return Decision(True, False, "Within autonomous read/analyze/propose boundary.")


policy = PolicyEngine()
