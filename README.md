# ME4 Kommunikations-Hub

MCP-Server als zentraler Kommunikations-Hub zwischen Hermes CIO, Clones und PI-Agenten.

## Features

- **hub_status_all()** — Status aller registrierten Agenten (Online/Offline, Heartbeats)
- **hub_sync_plane()** — Synchronisation mit Plane (Projektmanagement)
- **Agent Registry** — Registrierung, Heartbeats, Auto-Offline-Erkennung
- **Status-Dashboard** — Web-UI auf konfigurierbarem Port (optional)

## Installation

```bash
git clone https://github.com/2bai4me/me4-hub-clone.git
cd me4-hub-clone
pip install -e .
```

## Verwendung

### MCP Server (stdio)

```bash
python server.py
```

### MCP Server + Dashboard

```bash
python server.py --dashboard 8088
```

Dashboard dann unter http://localhost:8088

### Nur Dashboard (ohne MCP)

```bash
python server.py --dashboard-only 8088
```

## Hermes Integration

In `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  me4-kommunikations-hub:
    command: "python"
    args: ["-m", "server"]
    timeout: 120
    connect_timeout: 60
```

## MCP Tools

| Tool | Beschreibung |
|------|-------------|
| `hub_status_all` | Status aller registrierten Agenten |
| `hub_sync_plane` | Sync mit Plane (Workspaces, Projekte, Issues) |
| `hub_register_agent` | Neuen Agenten registrieren |
| `hub_heartbeat` | Heartbeat senden (online halten) |
| `hub_unregister_agent` | Agenten entfernen |
| `hub_dashboard_url` | Dashboard-URL abfragen |

## Architektur

```
me4-hub-clone/
├── server.py          # MCP Server + Dashboard
├── hub_core.py        # Agent Registry & Heartbeat-Logik
├── plane_client.py    # Plane API Client
├── dashboard.py       # Web-Dashboard HTML
└── requirements.txt
```
