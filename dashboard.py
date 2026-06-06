"""
ME4 Kommunikations-Hub — Status Dashboard
Web UI showing agent status, Plane sync, and hub health.
All user-facing strings are localized via i18n (DE/EN).
"""

import time
from i18n import t, set_language, _, format_heartbeat_age

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="{html_lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 24px; border-radius: 12px; margin-bottom: 24px; border: 1px solid #30363d; }}
        .header h1 {{ color: #58a6ff; font-size: 28px; margin-bottom: 8px; }}
        .header p {{ color: #8b949e; font-size: 14px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 20px; }}
        .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; }}
        .card h2 {{ color: #58a6ff; font-size: 18px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
        .stat-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #21262d; }}
        .stat-row:last-child {{ border-bottom: none; }}
        .stat-label {{ color: #8b949e; }}
        .stat-value {{ font-weight: 600; }}
        .online {{ color: #3fb950; }}
        .offline {{ color: #f85149; }}
        .busy {{ color: #d29922; }}
        .error {{ color: #f85149; }}
        .unknown {{ color: #8b949e; }}
        .agent-card {{ background: #0d1117; border: 1px solid #21262d; border-radius: 8px; padding: 12px; margin-bottom: 10px; }}
        .agent-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
        .agent-name {{ font-weight: 600; font-size: 15px; }}
        .agent-type {{ font-size: 11px; padding: 2px 8px; border-radius: 12px; background: #21262d; color: #8b949e; }}
        .agent-meta {{ font-size: 12px; color: #8b949e; display: flex; gap: 12px; }}
        .badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
        .badge-online {{ background: #1b3a1b; color: #3fb950; }}
        .badge-offline {{ background: #3a1b1b; color: #f85149; }}
        .badge-busy {{ background: #3a2e1b; color: #d29922; }}
        .badge-unknown {{ background: #21262d; color: #8b949e; }}
        .refresh {{ text-align: right; font-size: 12px; color: #484f58; margin-bottom: 8px; }}
        .plane-project {{ background: #0d1117; border: 1px solid #21262d; border-radius: 8px; padding: 10px; margin-bottom: 8px; }}
        .summary-box {{ background: #0d1117; border-radius: 8px; padding: 16px; text-align: center; margin-top: 12px; }}
        .summary-box .big {{ font-size: 32px; font-weight: 700; }}
        .progress-bar {{ height: 8px; background: #21262d; border-radius: 4px; margin-top: 8px; overflow: hidden; }}
        .progress-fill {{ height: 100%; border-radius: 4px; transition: width 0.5s; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
        .live {{ animation: pulse 2s infinite; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{page_title}</h1>
        <p>{page_subtitle}</p>
        <div class="refresh">{refresh_label}: <span id="refreshTime">{refresh_time}</span> | {auto_refresh}</div>
    </div>

    <div class="grid">
        <!-- Agent Status Card -->
        <div class="card">
            <h2>{agents_title}</h2>
            <div class="stat-row">
                <span class="stat-label">{total_label}</span>
                <span class="stat-value">{total_agents}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">{online_label}</span>
                <span class="stat-value online">{online_count}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">{offline_label}</span>
                <span class="stat-value offline">{offline_count}</span>
            </div>
            <div style="margin-top: 16px;">
                {agent_cards}
            </div>
        </div>

        <!-- Plane Sync Card -->
        <div class="card">
            <h2>{plane_title}</h2>
            <div class="stat-row">
                <span class="stat-label">{plane_url_label}</span>
                <span class="stat-value">{plane_url}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">{connection_label}</span>
                <span class="stat-value {plane_connected_class}">{plane_conn_text}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">{workspaces_label}</span>
                <span class="stat-value">{plane_workspaces}</span>
            </div>
            {plane_projects_html}
        </div>

        <!-- System Card -->
        <div class="card">
            <h2>{system_title}</h2>
            <div class="stat-row">
                <span class="stat-label">{version_label}</span>
                <span class="stat-value">1.0.0</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">{uptime_label}</span>
                <span class="stat-value">{uptime}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">{transport_label}</span>
                <span class="stat-value">stdio</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">{port_label}</span>
                <span class="stat-value">{dashboard_port}</span>
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
    lang: str = "de",
) -> str:
    """Render the full dashboard HTML in the requested language.

    Args:
        agents_data: Output from HubRegistry.get_status_all()
        plane_data: Output from PlaneClient.sync_status()
        uptime_seconds: Server uptime in seconds
        dashboard_port: Port the dashboard is running on
        lang: ISO 639-1 language code ('de' or 'en')
    """
    # Set language for this render
    set_language(lang)

    # ── Compute all translatable UI strings ──
    page_title = _("dashboard.title")
    page_subtitle = _("hub.subtitle")
    refresh_label = _("dashboard.refresh_label")
    auto_refresh = _("dashboard.auto_refresh")
    agents_title = _("agent.title")
    total_label = _("agent.total_registered")
    online_label = _("agent.online")
    offline_label = _("agent.offline")
    no_agents = _("agent.no_agents")
    plane_title = _("plane.title")
    plane_url_label = _("plane.url")
    connection_label = _("plane.connection")
    plane_connected_text = _("plane.connected")
    plane_disconnected_text = _("plane.disconnected")
    workspaces_label = _("plane.workspaces")
    system_title = _("system.title")
    version_label = _("hub.version")
    uptime_label = _("hub.server_uptime")
    transport_label = _("hub.mcp_transport")
    port_label = _("hub.dashboard_port")

    # ── Agent cards ──
    agent_cards = ""
    agents = agents_data.get("agents", [])
    if not agents:
        agent_cards = (
            f'<p style="color:#8b949e; text-align:center; padding:20px;">'
            f'{no_agents}</p>'
        )
    else:
        for a in agents:
            status = a.get("status", "unknown")
            badge_class = f"badge-{status}"
            status_text = _("agent.status." + status)
            ago = format_heartbeat_age(a.get("seconds_since_heartbeat"), lang=lang)

            agent_cards += (
                f'\n            <div class="agent-card">\n'
                f'                <div class="agent-header">\n'
                f'                    <span class="agent-name">'
                f'{a.get("display_name", a.get("agent_id", "?"))}</span>\n'
                f'                    <span class="badge {badge_class}">'
                f'{status_text}</span>\n'
                f'                </div>\n'
                f'                <div class="agent-meta">\n'
                f'                    <span>{a.get("agent_type", "?")}</span>\n'
                f'                    <span>Heartbeat: {ago}</span>\n'
                f'                </div>\n'
                f'            </div>'
            )

    # ── Plane section ──
    plane_connected = plane_data.get("connected", False)
    plane_connected_class = "online" if plane_connected else "offline"
    plane_conn_text = plane_connected_text if plane_connected else plane_disconnected_text
    plane_url = plane_data.get("plane_url", "N/A")
    plane_workspaces = plane_data.get("workspaces", "0")

    # Workspace list
    plane_projects_html = ""
    wl = plane_data.get("workspace_list", [])
    if wl:
        for w in wl:
            plane_projects_html += (
                f'\n            <div class="plane-project" style="margin-top:12px;">\n'
                f'                <strong>{w.get("name")}</strong>\n'
                f'                <span style="color:#8b949e;font-size:12px;'
                f'margin-left:8px;">({w.get("slug")})</span>\n'
                f'            </div>'
            )

    # ── Uptime formatting ──
    h = int(uptime_seconds // 3600)
    m = int((uptime_seconds % 3600) // 60)
    s = int(uptime_seconds % 60)
    uptime_str = f"{h}h {m}m {s}s"

    # ── Assemble HTML ──
    html = DASHBOARD_TEMPLATE.format(
        html_lang=lang,
        page_title=page_title,
        page_subtitle=page_subtitle,
        refresh_label=refresh_label,
        refresh_time=time.strftime("%H:%M:%S"),
        auto_refresh=auto_refresh,
        agents_title=agents_title,
        total_label=total_label,
        total_agents=agents_data.get("total", 0),
        online_label=online_label,
        online_count=agents_data.get("online", 0),
        offline_label=offline_label,
        offline_count=agents_data.get("offline", 0),
        agent_cards=agent_cards,
        plane_title=plane_title,
        plane_url_label=plane_url_label,
        plane_url=plane_url,
        connection_label=connection_label,
        plane_connected_class=plane_connected_class,
        plane_conn_text=plane_conn_text,
        workspaces_label=workspaces_label,
        plane_workspaces=plane_workspaces,
        plane_projects_html=plane_projects_html,
        system_title=system_title,
        version_label=version_label,
        uptime_label=uptime_label,
        uptime=uptime_str,
        transport_label=transport_label,
        port_label=port_label,
        dashboard_port=dashboard_port,
    )

    return html
