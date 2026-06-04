"""
ME4 Kommunikations-Hub — Status Dashboard
Web UI showing agent status, Plane sync, and hub health.
"""

import json
import time
from pathlib import Path

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ME4 Kommunikations-Hub</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
        .header { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 24px; border-radius: 12px; margin-bottom: 24px; border: 1px solid #30363d; }
        .header h1 { color: #58a6ff; font-size: 28px; margin-bottom: 8px; }
        .header p { color: #8b949e; font-size: 14px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 20px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; }
        .card h2 { color: #58a6ff; font-size: 18px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
        .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #21262d; }
        .stat-row:last-child { border-bottom: none; }
        .stat-label { color: #8b949e; }
        .stat-value { font-weight: 600; }
        .online { color: #3fb950; }
        .offline { color: #f85149; }
        .busy { color: #d29922; }
        .error { color: #f85149; }
        .unknown { color: #8b949e; }
        .agent-card { background: #0d1117; border: 1px solid #21262d; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
        .agent-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .agent-name { font-weight: 600; font-size: 15px; }
        .agent-type { font-size: 11px; padding: 2px 8px; border-radius: 12px; background: #21262d; color: #8b949e; }
        .agent-meta { font-size: 12px; color: #8b949e; display: flex; gap: 12px; }
        .badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .badge-online { background: #1b3a1b; color: #3fb950; }
        .badge-offline { background: #3a1b1b; color: #f85149; }
        .badge-busy { background: #3a2e1b; color: #d29922; }
        .badge-unknown { background: #21262d; color: #8b949e; }
        .refresh { text-align: right; font-size: 12px; color: #484f58; margin-bottom: 8px; }
        .plane-project { background: #0d1117; border: 1px solid #21262d; border-radius: 8px; padding: 10px; margin-bottom: 8px; }
        .summary-box { background: #0d1117; border-radius: 8px; padding: 16px; text-align: center; margin-top: 12px; }
        .summary-box .big { font-size: 32px; font-weight: 700; }
        .progress-bar { height: 8px; background: #21262d; border-radius: 4px; margin-top: 8px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .live { animation: pulse 2s infinite; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛰️ ME4 Kommunikations-Hub</h1>
        <p>Hermes CIO · Clones · PI-Agenten · Status & Sync</p>
        <div class="refresh">aktualisiert: <span id="refreshTime">{{ refresh_time }}</span> | auto-refresh alle 30s</div>
    </div>

    <div class="grid">
        <!-- Agent Status Card -->
        <div class="card">
            <h2>🤖 Agenten Status</h2>
            <div class="stat-row">
                <span class="stat-label">Gesamt registriert</span>
                <span class="stat-value">{{ total_agents }}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Online</span>
                <span class="stat-value online">{{ online_count }}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Offline</span>
                <span class="stat-value offline">{{ offline_count }}</span>
            </div>
            <div style="margin-top: 16px;">
                {{ agent_cards }}
            </div>
        </div>

        <!-- Plane Sync Card -->
        <div class="card">
            <h2>📋 Plane Sync</h2>
            <div class="stat-row">
                <span class="stat-label">Plane URL</span>
                <span class="stat-value">{{ plane_url }}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Verbindung</span>
                <span class="stat-value {{ plane_connected_class }}">{{ plane_connected_text }}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Workspaces</span>
                <span class="stat-value">{{ plane_workspaces }}</span>
            </div>
            {{ plane_projects_html }}
        </div>

        <!-- System Card -->
        <div class="card">
            <h2>⚙️ System</h2>
            <div class="stat-row">
                <span class="stat-label">Hub Version</span>
                <span class="stat-value">1.0.0</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Server Uptime</span>
                <span class="stat-value">{{ uptime }}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">MCP Transport</span>
                <span class="stat-value">stdio</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Dashboard Port</span>
                <span class="stat-value">{{ dashboard_port }}</span>
            </div>
        </div>
    </div>

    <script>
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>"""


def render_dashboard(
    agents_data: dict,
    plane_data: dict,
    uptime_seconds: float,
    dashboard_port: int = 8088,
) -> str:
    """Render the full dashboard HTML."""

    # Agent cards
    agent_cards = ""
    agents = agents_data.get("agents", [])
    if not agents:
        agent_cards = '<p style="color:#8b949e; text-align:center; padding:20px;">Keine Agenten registriert</p>'
    else:
        for a in agents:
            status = a.get("status", "unknown")
            badge_class = f"badge-{status}"
            heartbeat = a.get("seconds_since_heartbeat")
            if heartbeat is not None:
                if heartbeat < 60:
                    ago = f"vor {int(heartbeat)}s"
                elif heartbeat < 3600:
                    ago = f"vor {int(heartbeat/60)}m"
                else:
                    ago = f"vor {int(heartbeat/3600)}h"
            else:
                ago = "nie"

            agent_cards += f"""
            <div class="agent-card">
                <div class="agent-header">
                    <span class="agent-name">{a.get('display_name', a.get('agent_id', '?'))}</span>
                    <span class="badge {badge_class}">{status.upper()}</span>
                </div>
                <div class="agent-meta">
                    <span>{a.get('agent_type', '?')}</span>
                    <span>Heartbeat: {ago}</span>
                </div>
            </div>"""

    # Plane section
    plane_connected = plane_data.get("connected", False)
    plane_connected_class = "online" if plane_connected else "offline"
    plane_connected_text = "✅ Verbunden" if plane_connected else "❌ Nicht verbunden"
    plane_url = plane_data.get("plane_url", "N/A")
    plane_workspaces = plane_data.get("workspaces", "0")

    plane_projects_html = ""
    wl = plane_data.get("workspace_list", [])
    if wl:
        for w in wl:
            plane_projects_html += f"""
            <div class="plane-project" style="margin-top:12px;">
                <strong>{w.get('name')}</strong>
                <span style="color:#8b949e;font-size:12px;margin-left:8px;">({w.get('slug')})</span>
            </div>"""

    # Uptime formatting
    h = int(uptime_seconds // 3600)
    m = int((uptime_seconds % 3600) // 60)
    s = int(uptime_seconds % 60)
    uptime_str = f"{h}h {m}m {s}s"

    html = DASHBOARD_TEMPLATE
    html = html.replace("{{ refresh_time }}", time.strftime("%H:%M:%S"))
    html = html.replace("{{ total_agents }}", str(agents_data.get("total", 0)))
    html = html.replace("{{ online_count }}", str(agents_data.get("online", 0)))
    html = html.replace("{{ offline_count }}", str(agents_data.get("offline", 0)))
    html = html.replace("{{ agent_cards }}", agent_cards)
    html = html.replace("{{ plane_url }}", plane_url)
    html = html.replace("{{ plane_connected_class }}", plane_connected_class)
    html = html.replace("{{ plane_connected_text }}", plane_connected_text)
    html = html.replace("{{ plane_workspaces }}", str(plane_workspaces))
    html = html.replace("{{ plane_projects_html }}", plane_projects_html)
    html = html.replace("{{ uptime }}", uptime_str)
    html = html.replace("{{ dashboard_port }}", str(dashboard_port))

    return html
