"""
ME4 Kommunikations-Hub — MCP Server
Starts both the MCP stdio server AND an optional web dashboard.

Usage:
    python server.py                  # MCP stdio server only
    python server.py --dashboard 8088 # MCP + dashboard on port 8088
"""

import sys
import time
import json
import logging
import argparse
import threading
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

import me4_i18n as i18n
from hub_core import get_registry, AgentInfo
from plane_client import get_plane_client
from dashboard import render_dashboard
from i18n_helper import _, set_locale, parse_accept_language

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("me4-hub.server")

# ═══════════════════════════════════════════════
# MCP Server Setup
# ═══════════════════════════════════════════════

server = Server("me4-kommunikations-hub")
start_time = time.time()
DASHBOARD_PORT = None


# ── Tool: hub_status_all ──

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="hub_status_all",
            description=i18n.t("mcp.tools.hubStatusAll.description"),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="hub_sync_plane",
            description=i18n.t("mcp.tools.hubSyncPlane.description"),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_slug": {
                        "type": "string",
                        "description": i18n.t("mcp.tools.hubSyncPlane.params.workspaceSlug"),
                    },
                    "project_id": {
                        "type": "string",
                        "description": i18n.t("mcp.tools.hubSyncPlane.params.projectId"),
                    },
                    "state": {
                        "type": "string",
                        "description": i18n.t("mcp.tools.hubSyncPlane.params.state"),
                    },
                },
            },
        ),
        types.Tool(
            name="hub_register_agent",
            description=i18n.t("mcp.tools.hubRegisterAgent.description"),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": i18n.t("mcp.tools.hubRegisterAgent.params.agentId"),
                    },
                    "agent_type": {
                        "type": "string",
                        "description": i18n.t("mcp.tools.hubRegisterAgent.params.agentType"),
                    },
                    "display_name": {
                        "type": "string",
                        "description": i18n.t("mcp.tools.hubRegisterAgent.params.displayName"),
                    },
                    "endpoint": {
                        "type": "string",
                        "description": i18n.t("mcp.tools.hubRegisterAgent.params.endpoint"),
                    },
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": i18n.t("mcp.tools.hubRegisterAgent.params.capabilities"),
                    },
                },
                "required": ["agent_id", "agent_type", "display_name"],
            },
        ),
        types.Tool(
            name="hub_heartbeat",
            description=i18n.t("mcp.tools.hubHeartbeat.description"),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": i18n.t("mcp.tools.hubHeartbeat.params.agentId"),
                    },
                },
                "required": ["agent_id"],
            },
        ),
        types.Tool(
            name="hub_unregister_agent",
            description=i18n.t("mcp.tools.hubUnregisterAgent.description"),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": i18n.t("mcp.tools.hubUnregisterAgent.params.agentId"),
                    },
                },
                "required": ["agent_id"],
            },
        ),
        types.Tool(
            name="hub_dashboard_url",
            description=i18n.t("mcp.tools.hubDashboardUrl.description"),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
    registry = get_registry()

    if name == "hub_status_all":
        status = registry.get_status_all()
        return [types.TextContent(
            type="text",
            text=json.dumps(status, indent=2, ensure_ascii=False),
        )]

    elif name == "hub_sync_plane":
        plane = get_plane_client()
        result = {}

        # Auto-authenticate
        if not plane.token:
            auth = plane.authenticate()
            result["auth"] = auth
            if not auth.get("authenticated"):
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": i18n.t("errors.planeAuthFailed"), "details": auth}, indent=2, ensure_ascii=False),
                )]

        ws_slug = arguments.get("workspace_slug")
        project_id = arguments.get("project_id")
        state = arguments.get("state")

        # Sync status overview
        sync = plane.sync_status()
        result["sync"] = sync

        # If workspace specified, get projects
        if ws_slug:
            projects = plane.get_projects(ws_slug)
            result["projects"] = projects

            # If project specified, get issues
            if project_id:
                issues = plane.get_issues(ws_slug, project_id, state)
                result["issues"] = issues
                stats = plane.get_stats(ws_slug, project_id)
                result["stats"] = stats

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False),
        )]

    elif name == "hub_register_agent":
        agent = AgentInfo(
            agent_id=arguments["agent_id"],
            agent_type=arguments["agent_type"],
            display_name=arguments["display_name"],
            endpoint=arguments.get("endpoint", ""),
            capabilities=arguments.get("capabilities", []),
            status="online",
            last_heartbeat=time.time(),
        )
        result = registry.register(agent)
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False),
        )]

    elif name == "hub_heartbeat":
        result = registry.heartbeat(arguments["agent_id"])
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False),
        )]

    elif name == "hub_unregister_agent":
        result = registry.unregister(arguments["agent_id"])
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False),
        )]

    elif name == "hub_dashboard_url":
        global DASHBOARD_PORT
        if DASHBOARD_PORT:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "dashboard": f"http://localhost:{DASHBOARD_PORT}",
                    "running": True,
                }, indent=2),
            )]
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "dashboard": None,
                "running": False,
                "hint": i18n.t("errors.dashboardNotRunning"),
            }, indent=2),
        )]

    else:
        raise ValueError(i18n.t("errors.unknownTool", name=name))


# ── Optional Dashboard ──

def _safe_plane_status():
    """Get Plane status without blocking. Returns cached/fallback immediately."""
    plane = get_plane_client()
    return {
        "plane_url": plane.base_url,
        "connected": plane.token is not None,
        "workspaces": 0,
        "note": _("server.plane_sync_note"),
    }


def start_dashboard(port: int):
    """Start a lightweight HTTP dashboard in a background thread."""
    global DASHBOARD_PORT
    DASHBOARD_PORT = port

    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class DashboardHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse query params for ?lang=xx
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                path_only = parsed.path

                # Determine language: ?lang param > Accept-Language header > default de
                lang = "de"
                if "lang" in params:
                    lang = params["lang"][0]
                elif "Accept-Language" in self.headers:
                    accepted = i18n.parse_accept_language(self.headers["Accept-Language"])
                    available = i18n.get_manager().get_available_locales()
                    for loc in accepted:
                        if loc in available:
                            lang = loc
                            break

                if path_only == "/" or path_only == "/index.html":
                    registry = get_registry()
                    agents = registry.get_status_all()
                    plane_status = _safe_plane_status()
                    html = render_dashboard(
                        agents_data=agents,
                        plane_data=plane_status,
                        uptime_seconds=time.time() - start_time,
                        dashboard_port=port,
                        lang=lang,
                    )
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(html.encode("utf-8"))))
                    self.end_headers()
                    self.wfile.write(html.encode("utf-8"))
                elif path_only == "/api/status":
                    registry = get_registry()
                    data = {
                        "agents": registry.get_status_all(),
                        "plane": _safe_plane_status(),
                        "uptime": time.time() - start_time,
                    }
                    body = json.dumps(data, indent=2, ensure_ascii=False)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body.encode("utf-8"))))
                    self.end_headers()
                    self.wfile.write(body.encode("utf-8"))
                else:
                    self.send_response(404)
                    self.end_headers()

        server = HTTPServer(("0.0.0.0", port), DashboardHandler)
        logger.info(_("server.dashboard_started", port=port))
        server.serve_forever()

    except Exception as e:
        logger.error(_("server.dashboard_start_failed", error=str(e)))


# ── Main Entry Points ──

async def run_mcp():
    """Run the MCP server over stdio."""
    logger.info(_("server.mcp_starting"))
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    # Initialize i18n
    locales_dir = Path(__file__).parent / "locales"
    i18n.init(str(locales_dir), default_locale="de")
    logger.info(f"i18n initialized: {i18n.get_manager().get_available_locales()} (default: {i18n.get_locale()})")

    parser = argparse.ArgumentParser(description="ME4 Kommunikations-Hub MCP Server")
    parser.add_argument("--dashboard", type=int, metavar="PORT", help="Dashboard auf angegebenem Port starten")
    parser.add_argument("--dashboard-only", type=int, metavar="PORT", help="NUR Dashboard starten (kein MCP)")
    args = parser.parse_args()

    if args.dashboard_only:
        # Dashboard-only mode
        start_dashboard(args.dashboard_only)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info(_("server.dashboard_stopped"))
        return

    if args.dashboard:
        # Start dashboard in background thread
        dash_thread = threading.Thread(target=start_dashboard, args=(args.dashboard,), daemon=True)
        dash_thread.start()

    # Run MCP server (blocking)
    import asyncio
    asyncio.run(run_mcp())


if __name__ == "__main__":
    main()
