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

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from hub_core import get_registry, AgentInfo
from plane_client import get_plane_client
from dashboard import render_dashboard
from i18n import t, set_language, detect_language_from_header, detect_language_from_env, _

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
            name=_("tool.hub_status_all.name"),
            description=_("tool.hub_status_all.desc"),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name=_("tool.hub_sync_plane.name"),
            description=_("tool.hub_sync_plane.desc"),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_slug": {
                        "type": "string",
                        "description": _("tool.param.workspace_slug"),
                    },
                    "project_id": {
                        "type": "string",
                        "description": _("tool.param.project_id"),
                    },
                    "state": {
                        "type": "string",
                        "description": _("tool.param.state"),
                    },
                },
            },
        ),
        types.Tool(
            name=_("tool.hub_register_agent.name"),
            description=_("tool.hub_register_agent.desc"),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": _("tool.param.agent_id"),
                    },
                    "agent_type": {
                        "type": "string",
                        "description": _("tool.param.agent_type"),
                    },
                    "display_name": {
                        "type": "string",
                        "description": _("tool.param.display_name"),
                    },
                    "endpoint": {
                        "type": "string",
                        "description": _("tool.param.endpoint"),
                    },
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": _("tool.param.capabilities"),
                    },
                },
                "required": ["agent_id", "agent_type", "display_name"],
            },
        ),
        types.Tool(
            name=_("tool.hub_heartbeat.name"),
            description=_("tool.hub_heartbeat.desc"),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": _("tool.param.agent_id"),
                    },
                },
                "required": ["agent_id"],
            },
        ),
        types.Tool(
            name=_("tool.hub_unregister_agent.name"),
            description=_("tool.hub_unregister_agent.desc"),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": _("tool.param.agent_id"),
                    },
                },
                "required": ["agent_id"],
            },
        ),
        types.Tool(
            name=_("tool.hub_dashboard_url.name"),
            description=_("tool.hub_dashboard_url.desc"),
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
                    text=json.dumps({"error": "Plane authentication failed", "details": auth}, indent=2, ensure_ascii=False),
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
                "hint": "Start server with --dashboard PORT to enable dashboard",
            }, indent=2),
        )]

    else:
        raise ValueError(_("error.unknown_tool", name=name))


# ── Optional Dashboard ──

def _safe_plane_status():
    """Get Plane status without blocking. Returns cached/fallback immediately."""
    plane = get_plane_client()
    return {
        "plane_url": plane.base_url,
        "connected": plane.token is not None,
        "workspaces": 0,
        "note": _("plane.sync_note"),
    }


def start_dashboard(port: int):
    """Start a lightweight HTTP dashboard in a background thread."""
    global DASHBOARD_PORT
    DASHBOARD_PORT = port

    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class DashboardHandler(BaseHTTPRequestHandler):
            def _detect_lang(self):
                """Detect language from Accept-Language header."""
                header = self.headers.get("Accept-Language", "")
                return detect_language_from_header(header)

            def do_GET(self):
                lang = self._detect_lang()
                if self.path == "/" or self.path == "/index.html":
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
                elif self.path == "/api/status":
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

            def log_message(self, format, *args):
                logger.debug(f"Dashboard: {format % args}")

        server = HTTPServer(("0.0.0.0", port), DashboardHandler)
        logger.info(_("hub.start_dashboard", port=port))
        server.serve_forever()

    except Exception as e:
        logger.error(_("hub.dashboard_error", error=e))


# ── Main Entry Points ──

async def run_mcp():
    """Run the MCP server over stdio."""
    logger.info(_("hub.start_mcp"))
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
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
            logger.info(_("hub.dashboard_stopped"))
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
