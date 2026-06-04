"""
ME4 Kommunikations-Hub — Core Logic
Agent registry, status tracking, heartbeat management.
"""

import time
import json
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("me4-hub")

STATE_FILE = Path(__file__).parent / "hub_state.json"


@dataclass
class AgentInfo:
    agent_id: str
    agent_type: str  # "hermes-cio", "hermes-clone", "pi-agent", "mcp-server"
    display_name: str
    endpoint: str = ""  # URL or IPC path
    status: str = "unknown"  # "online", "offline", "busy", "error"
    last_heartbeat: float = 0.0
    capabilities: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)


class HubRegistry:
    """Central registry for all connected agents."""

    def __init__(self):
        self.agents: dict[str, AgentInfo] = {}
        self._load_state()

    def _load_state(self):
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                for a in data.get("agents", []):
                    agent = AgentInfo(**a)
                    self.agents[agent.agent_id] = agent
            except Exception as e:
                logger.warning(f"Could not load state: {e}")

    def _save_state(self):
        data = {"agents": [asdict(a) for a in self.agents.values()]}
        STATE_FILE.write_text(json.dumps(data, indent=2))

    def register(self, info: AgentInfo) -> dict:
        """Register a new agent or update existing."""
        self.agents[info.agent_id] = info
        self._save_state()
        logger.info(f"Registered agent: {info.agent_id} ({info.agent_type})")
        return {"registered": True, "agent_id": info.agent_id, "total_agents": len(self.agents)}

    def unregister(self, agent_id: str) -> dict:
        """Remove an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self._save_state()
            return {"unregistered": True, "agent_id": agent_id}
        return {"unregistered": False, "error": "Agent not found"}

    def heartbeat(self, agent_id: str) -> dict:
        """Update heartbeat timestamp."""
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = time.time()
            self.agents[agent_id].status = "online"
            self._save_state()
            return {"heartbeat": "ok", "agent_id": agent_id}
        return {"heartbeat": "error", "message": "Unknown agent"}

    def get_status_all(self) -> dict:
        """Get status of all registered agents."""
        now = time.time()
        agents_status = []
        online = 0
        offline = 0

        for agent in self.agents.values():
            # Auto-detect offline if no heartbeat in 5 minutes
            if agent.status == "online" and (now - agent.last_heartbeat) > 300:
                agent.status = "offline"

            if agent.status == "online":
                online += 1
            elif agent.status == "offline":
                offline += 1

            agents_status.append({
                "agent_id": agent.agent_id,
                "agent_type": agent.agent_type,
                "display_name": agent.display_name,
                "status": agent.status,
                "last_heartbeat": agent.last_heartbeat,
                "seconds_since_heartbeat": now - agent.last_heartbeat if agent.last_heartbeat else None,
                "capabilities": agent.capabilities,
                "registered_at": agent.registered_at,
            })

        return {
            "timestamp": now,
            "total": len(self.agents),
            "online": online,
            "offline": offline,
            "agents": agents_status,
        }

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get a single agent's info."""
        return self.agents.get(agent_id)


# Singleton
_registry: Optional[HubRegistry] = None


def get_registry() -> HubRegistry:
    global _registry
    if _registry is None:
        _registry = HubRegistry()
    return _registry
