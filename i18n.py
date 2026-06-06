"""
ME4 Hub — i18n Internationalization Module
Provides translation functions for multi-language support (DE, EN).

Usage:
    from i18n import t, set_language, get_language, _

    set_language("en")
    print(t("hub.title"))              # "ME4 Communication Hub"
    print(t("agent.status.online"))    # "Online"

    # Parameterized strings
    print(t("agent.registered", agent_id="clone-1", total=3))
    # → "Agent registered: clone-1 (total: 3)"

    # Accept-Language header parsing for web requests
    lang = detect_language_from_header("de,en-US;q=0.7,en;q=0.3")

Design choices:
    - No external dependencies (pure Python stdlib)
    - Flat key → value mapping per language
    - dot-separated keys for namespacing (hub.*, agent.*, plane.*, dashboard.*)
    - German (de) is the default/fallback language
"""

import os
import re
from typing import Optional

# ═══════════════════════════════════════════════════════
# Translation dictionaries
# ═══════════════════════════════════════════════════════

_TRANSLATIONS = {}

# ── German (default) ──

_TRANSLATIONS["de"] = {
    # ── Hub general ──
    "hub.title": "ME4 Kommunikations-Hub",
    "hub.subtitle": "Hermes CIO · Clones · PI-Agenten · Status & Sync",
    "hub.version": "Hub Version",
    "hub.server_uptime": "Server Uptime",
    "hub.mcp_transport": "MCP Transport",
    "hub.dashboard_port": "Dashboard Port",
    "hub.start_mcp": "ME4 Kommunikations-Hub MCP Server startet (stdio)",
    "hub.start_dashboard": "📊 Dashboard gestartet auf http://localhost:{port}",
    "hub.dashboard_error": "Dashboard konnte nicht gestartet werden: {error}",
    "hub.dashboard_stopped": "Dashboard gestoppt.",
    "hub.no_dashboard": "Dashboard nicht gestartet. Server mit --dashboard PORT starten, um das Dashboard zu aktivieren.",

    # ── Agent registry ──
    "agent.title": "Agenten Status",
    "agent.total_registered": "Gesamt registriert",
    "agent.online": "Online",
    "agent.offline": "Offline",
    "agent.no_agents": "Keine Agenten registriert",
    "agent.registered": "Registered agent: {agent_id} ({agent_type})",
    "agent.registered_ok": "Registration erfolgreich: {agent_id} ({total_agents} Agent(en))",
    "agent.registered_fail": "Registration fehlgeschlagen",
    "agent.unregistered": "Agent {agent_id} entfernt",
    "agent.not_found": "Agent nicht gefunden: {agent_id}",
    "agent.heartbeat_ok": "Heartbeat empfangen von {agent_id}",
    "agent.heartbeat_error": "Heartbeat fehlgeschlagen: Agent {agent_id} nicht registriert",
    "agent.heartbeat_ago_seconds": "vor {seconds}s",
    "agent.heartbeat_ago_minutes": "vor {minutes}m",
    "agent.heartbeat_ago_hours": "vor {hours}h",
    "agent.heartbeat_never": "nie",
    "agent.state_loaded": "Agent-Registry aus {file} geladen",
    "agent.state_load_error": "Konnte Registry-Status nicht laden: {error}",

    # Agent types
    "agent.type.hermes-cio": "Hermes CIO",
    "agent.type.hermes-clone": "Hermes Clone",
    "agent.type.pi-agent": "PI-Agent",
    "agent.type.mcp-server": "MCP Server",
    "agent.type.unknown": "Unbekannt",

    # Agent status
    "agent.status.online": "Online",
    "agent.status.offline": "Offline",
    "agent.status.busy": "Busy",
    "agent.status.error": "Fehler",
    "agent.status.unknown": "Unbekannt",

    # ── Plane ──
    "plane.title": "Plane Sync",
    "plane.url": "Plane URL",
    "plane.connection": "Verbindung",
    "plane.connected": "✅ Verbunden",
    "plane.disconnected": "❌ Nicht verbunden",
    "plane.workspaces": "Workspaces",
    "plane.auth_success": "Plane Authentifizierung erfolgreich: {user}",
    "plane.auth_failed": "Plane Authentifizierung fehlgeschlagen",
    "plane.sync_note": "Plane sync verfügbar via MCP-Tool hub_sync_plane()",
    "plane.sync_error": "Plane Sync-Fehler",
    "plane.sync_status": "Sync Status: {connected}, {workspaces} Workspace(s)",

    # ── Dashboard ──
    "dashboard.title": "🛰️ ME4 Kommunikations-Hub",
    "dashboard.refresh_label": "Aktualisiert",
    "dashboard.refresh_time": "aktualisiert: {time}",
    "dashboard.auto_refresh": "auto-refresh alle 30s",
    "dashboard.system_title": "⚙️ System",
    "dashboard.refreshing": "Aktualisiere...",

    # ── Tools / MCP ──
    "tool.hub_status_all.name": "hub_status_all",
    "tool.hub_status_all.desc": "Zeigt den Status aller registrierten Agenten (Hermes CIO, Clones, PI-Agenten) im Kommunikations-Hub an. Gibt Online/Offline-Status, Heartbeat-Zeiten und Agent-Typen zurück.",
    "tool.hub_sync_plane.name": "hub_sync_plane",
    "tool.hub_sync_plane.desc": "Synchronisiert mit Plane (Projektmanagement auf localhost:8080). Authentifiziert sich automatisch und gibt Workspaces, Projekte und Issues zurück. Optional: workspace_slug und project_id für gezielte Abfragen.",
    "tool.hub_register_agent.name": "hub_register_agent",
    "tool.hub_register_agent.desc": "Registriert einen neuen Agenten (Hermes Clone, PI-Agent, etc.) im Kommunikations-Hub. Notwendig bevor Heartbeats gesendet werden können.",
    "tool.hub_heartbeat.name": "hub_heartbeat",
    "tool.hub_heartbeat.desc": "Sendet einen Heartbeat für einen registrierten Agenten. Hält den Status auf 'online'. Sollte alle 60-120 Sekunden aufgerufen werden.",
    "tool.hub_unregister_agent.name": "hub_unregister_agent",
    "tool.hub_unregister_agent.desc": "Entfernt einen Agenten aus der Registry.",
    "tool.hub_dashboard_url.name": "hub_dashboard_url",
    "tool.hub_dashboard_url.desc": "Gibt die URL des Status-Dashboards zurück, falls es läuft.",

    # Tool parameter descriptions
    "tool.param.agent_id": "Eindeutige ID des Agenten (z.B. 'hermes-clone-1', 'pi-agent-researcher').",
    "tool.param.agent_type": "Typ: 'hermes-cio', 'hermes-clone', 'pi-agent', 'mcp-server'.",
    "tool.param.display_name": "Anzeigename fürs Dashboard.",
    "tool.param.endpoint": "Erreichbarkeits-URL oder IPC-Pfad (optional).",
    "tool.param.capabilities": "Fähigkeiten des Agenten (optional).",
    "tool.param.workspace_slug": "Plane Workspace-Slug (z.B. 'me4'). Leer lassen für alle.",
    "tool.param.project_id": "Plane Project-ID für Issue-Abfrage. Leer lassen für Übersicht.",
    "tool.param.state": "Issue-Status filter (z.B. 'backlog', 'unstarted', 'started', 'completed', 'cancelled').",

    # ── Error / Unknown tool ──
    "error.unknown_tool": "Unbekanntes Tool: {name}",
    "error.unknown": "Unbekannter Fehler",

    # ── System ──
    "system.title": "⚙️ System",
}


# ── English ──

_TRANSLATIONS["en"] = {
    # ── Hub general ──
    "hub.title": "ME4 Communication Hub",
    "hub.subtitle": "Hermes CIO · Clones · PI Agents · Status & Sync",
    "hub.version": "Hub Version",
    "hub.server_uptime": "Server Uptime",
    "hub.mcp_transport": "MCP Transport",
    "hub.dashboard_port": "Dashboard Port",
    "hub.start_mcp": "ME4 Communication Hub MCP Server starting (stdio)",
    "hub.start_dashboard": "📊 Dashboard started at http://localhost:{port}",
    "hub.dashboard_error": "Dashboard could not be started: {error}",
    "hub.dashboard_stopped": "Dashboard stopped.",
    "hub.no_dashboard": "Dashboard not started. Start server with --dashboard PORT to enable the dashboard.",

    # ── Agent registry ──
    "agent.title": "Agent Status",
    "agent.total_registered": "Total Registered",
    "agent.online": "Online",
    "agent.offline": "Offline",
    "agent.no_agents": "No agents registered",
    "agent.registered": "Registered agent: {agent_id} ({agent_type})",
    "agent.registered_ok": "Registration successful: {agent_id} ({total_agents} agent(s))",
    "agent.registered_fail": "Registration failed",
    "agent.unregistered": "Agent {agent_id} removed",
    "agent.not_found": "Agent not found: {agent_id}",
    "agent.heartbeat_ok": "Heartbeat received from {agent_id}",
    "agent.heartbeat_error": "Heartbeat failed: Agent {agent_id} not registered",
    "agent.heartbeat_ago_seconds": "{seconds}s ago",
    "agent.heartbeat_ago_minutes": "{minutes}m ago",
    "agent.heartbeat_ago_hours": "{hours}h ago",
    "agent.heartbeat_never": "never",
    "agent.state_loaded": "Agent registry loaded from {file}",
    "agent.state_load_error": "Could not load registry state: {error}",

    # Agent types
    "agent.type.hermes-cio": "Hermes CIO",
    "agent.type.hermes-clone": "Hermes Clone",
    "agent.type.pi-agent": "PI Agent",
    "agent.type.mcp-server": "MCP Server",
    "agent.type.unknown": "Unknown",

    # Agent status
    "agent.status.online": "Online",
    "agent.status.offline": "Offline",
    "agent.status.busy": "Busy",
    "agent.status.error": "Error",
    "agent.status.unknown": "Unknown",

    # ── Plane ──
    "plane.title": "Plane Sync",
    "plane.url": "Plane URL",
    "plane.connection": "Connection",
    "plane.connected": "✅ Connected",
    "plane.disconnected": "❌ Disconnected",
    "plane.workspaces": "Workspaces",
    "plane.auth_success": "Plane authentication successful: {user}",
    "plane.auth_failed": "Plane authentication failed",
    "plane.sync_note": "Plane sync available via MCP tool hub_sync_plane()",
    "plane.sync_error": "Plane sync error",
    "plane.sync_status": "Sync Status: {connected}, {workspaces} Workspace(s)",

    # ── Dashboard ──
    "dashboard.title": "🛰️ ME4 Communication Hub",
    "dashboard.refresh_label": "Updated",
    "dashboard.refresh_time": "updated: {time}",
    "dashboard.auto_refresh": "auto-refresh every 30s",
    "dashboard.system_title": "⚙️ System",
    "dashboard.refreshing": "Refreshing...",

    # ── Tools / MCP ──
    "tool.hub_status_all.name": "hub_status_all",
    "tool.hub_status_all.desc": "Shows the status of all registered agents (Hermes CIO, Clones, PI Agents) in the Communication Hub. Returns online/offline status, heartbeat times, and agent types.",
    "tool.hub_sync_plane.name": "hub_sync_plane",
    "tool.hub_sync_plane.desc": "Syncs with Plane (project management at localhost:8080). Auto-authenticates and returns workspaces, projects, and issues. Optional: workspace_slug and project_id for targeted queries.",
    "tool.hub_register_agent.name": "hub_register_agent",
    "tool.hub_register_agent.desc": "Registers a new agent (Hermes Clone, PI Agent, etc.) in the Communication Hub. Required before heartbeats can be sent.",
    "tool.hub_heartbeat.name": "hub_heartbeat",
    "tool.hub_heartbeat.desc": "Sends a heartbeat for a registered agent. Keeps status as 'online'. Should be called every 60-120 seconds.",
    "tool.hub_unregister_agent.name": "hub_unregister_agent",
    "tool.hub_unregister_agent.desc": "Removes an agent from the registry.",
    "tool.hub_dashboard_url.name": "hub_dashboard_url",
    "tool.hub_dashboard_url.desc": "Returns the URL of the status dashboard, if it is running.",

    # Tool parameter descriptions
    "tool.param.agent_id": "Unique ID of the agent (e.g. 'hermes-clone-1', 'pi-agent-researcher').",
    "tool.param.agent_type": "Type: 'hermes-cio', 'hermes-clone', 'pi-agent', 'mcp-server'.",
    "tool.param.display_name": "Display name for the dashboard.",
    "tool.param.endpoint": "Reachability URL or IPC path (optional).",
    "tool.param.capabilities": "Agent capabilities (optional).",
    "tool.param.workspace_slug": "Plane workspace slug (e.g. 'me4'). Leave empty for all.",
    "tool.param.project_id": "Plane project ID for issue queries. Leave empty for overview.",
    "tool.param.state": "Issue state filter (e.g. 'backlog', 'unstarted', 'started', 'completed', 'cancelled').",

    # ── Error / Unknown tool ──
    "error.unknown_tool": "Unknown tool: {name}",
    "error.unknown": "Unknown error",

    # ── System ──
    "system.title": "⚙️ System",
}


# ═══════════════════════════════════════════════════════
# Supported languages and fallback order
# ═══════════════════════════════════════════════════════

SUPPORTED_LANGUAGES = frozenset({"de", "en"})
DEFAULT_LANGUAGE = "de"


# ═══════════════════════════════════════════════════════
# Current language (configurable at runtime)
# ═══════════════════════════════════════════════════════

_current_language: str = DEFAULT_LANGUAGE


def set_language(lang: str) -> None:
    """Set the active language for all subsequent translations.

    Args:
        lang: ISO 639-1 language code ('de' or 'en'). Falls back to 'de' if unsupported.
    """
    global _current_language
    lang = lang.lower().strip()
    if lang in SUPPORTED_LANGUAGES:
        _current_language = lang
    else:
        # Try to match primary language tag (e.g. 'en-US' → 'en')
        primary = lang.split("-")[0]
        _current_language = primary if primary in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def get_language() -> str:
    """Return the currently active language code."""
    return _current_language


def detect_language_from_header(accept_language: Optional[str]) -> str:
    """Parse an HTTP Accept-Language header and return the best match.

    Falls back to DEFAULT_LANGUAGE if no match found.

    Args:
        accept_language: Value of the Accept-Language HTTP header
                         (e.g. 'de,en-US;q=0.7,en;q=0.3')

    Returns:
        ISO 639-1 language code ('de' or 'en')
    """
    if not accept_language:
        return DEFAULT_LANGUAGE

    # Parse quality-weighted language tags
    # Format: "de,en-US;q=0.7,en;q=0.3"
    pattern = re.compile(r"([a-zA-Z]{1,8})(?:-[a-zA-Z]{1,8})?(?:\s*;\s*q=([0-9.]+))?")
    matches = pattern.findall(accept_language)

    if not matches:
        return DEFAULT_LANGUAGE

    # Sort by quality (higher first) or position (earlier = higher by default)
    scored = []
    for i, (lang, q) in enumerate(matches):
        quality = float(q) if q else 1.0
        scored.append((quality, -i, lang.lower()))

    scored.sort(reverse=True)

    for _, _, lang_primary in scored:
        if lang_primary in SUPPORTED_LANGUAGES:
            return lang_primary

    return DEFAULT_LANGUAGE


def detect_language_from_env() -> str:
    """Detect language from environment variable ME4_LANG or LANG.

    Returns:
        ISO 639-1 language code
    """
    for var in ("ME4_LANG", "LANG", "LANGUAGE"):
        val = os.environ.get(var)
        if val:
            primary = val.lower().strip().split(".")[0].split("_")[0].split("-")[0]
            if primary in SUPPORTED_LANGUAGES:
                return primary
    return DEFAULT_LANGUAGE


# ═══════════════════════════════════════════════════════
# Translation function
# ═══════════════════════════════════════════════════════


def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """Translate a key to the current or specified language.

    Args:
        key: Dot-separated translation key (e.g. 'hub.title', 'agent.status.online')
        lang: Override language ('de' or 'en'). Uses current language if None.
        **kwargs: Values to interpolate into the translated string.
                  Placeholders are {name} in translation strings.

    Returns:
        Translated string with kwargs interpolated.
        Falls back to the key itself if no translation exists.

    Examples:
        >>> set_language("de")
        >>> t("hub.title")
        'ME4 Kommunikations-Hub'
        >>> t("agent.registered", agent_id="clone-1", agent_type="hermes-clone")
        'Registered agent: clone-1 (hermes-clone)'
        >>> t("agent.heartbeat_ago_seconds", seconds=30)
        'vor 30s'
    """
    lang = lang or _current_language

    # Get dictionary for the language, fallback to default
    lang_dict = _TRANSLATIONS.get(lang, _TRANSLATIONS[DEFAULT_LANGUAGE])

    # Look up key in requested language, then fallback to default
    text = lang_dict.get(key)
    if text is None:
        text = _TRANSLATIONS[DEFAULT_LANGUAGE].get(key)

    # Return key itself if still not found
    if text is None:
        return key

    # Interpolate kwargs if any
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            # Missing a format key — return as-is with a marker
            text = f"{text} [?missing-args]"

    return text


def _(key: str, **kwargs) -> str:
    """Convenience alias for t() using current language.

    Usage:
        from i18n import _

        print(_("hub.title"))  # Uses currently set language
    """
    return t(key, **kwargs)


# ═══════════════════════════════════════════════════════
# Heartbeat age formatter (convenience)
# ═══════════════════════════════════════════════════════


def format_heartbeat_age(seconds_since: Optional[float], lang: Optional[str] = None) -> str:
    """Format a heartbeat age into a human-readable localized string.

    Args:
        seconds_since: Seconds since last heartbeat, or None.
        lang: Language override.

    Returns:
        Localized string like 'vor 30s', '5m ago', 'never'.
    """
    if seconds_since is None:
        return t("agent.heartbeat_never", lang=lang)

    if seconds_since < 60:
        return t("agent.heartbeat_ago_seconds", lang=lang, seconds=int(seconds_since))
    elif seconds_since < 3600:
        return t("agent.heartbeat_ago_minutes", lang=lang, minutes=int(seconds_since / 60))
    else:
        return t("agent.heartbeat_ago_hours", lang=lang, hours=int(seconds_since / 3600))


# ═══════════════════════════════════════════════════════
# Auto-detect on import
# ═══════════════════════════════════════════════════════

_lang_from_env = detect_language_from_env()
if _lang_from_env != DEFAULT_LANGUAGE:
    set_language(_lang_from_env)
