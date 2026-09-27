from collections import deque


class MemoryStore:
    """Development store. Replace with PostgreSQL/vector storage for distributed deployment."""

    def __init__(self):
        self.events = deque(maxlen=5000)
        self.missions = {}
        self.approvals = {}

    def event(self, kind, payload):
        self.events.append({"kind": kind, **payload})


memory = MemoryStore()
