"""
Plane API Client — syncs tasks/issues between Plane (localhost:8080) and the Hub.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger("me4-hub.plane")

DEFAULT_PLANE_URL = "http://localhost:8080"
DEFAULT_CREDENTIALS = {
    "email": "hermes@me4.local",
    "password": "Anzemalu#001",
}


class PlaneClient:
    """Minimal Plane.so API client for task syncing."""

    def __init__(self, base_url: str = DEFAULT_PLANE_URL):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.client = httpx.Client(timeout=5.0)  # short timeout for dashboard

    def authenticate(self, email: str = None, password: str = None) -> dict:
        """Authenticate with Plane and get token."""
        email = email or DEFAULT_CREDENTIALS["email"]
        password = password or DEFAULT_CREDENTIALS["password"]

        try:
            resp = self.client.post(
                f"{self.base_url}/api/auth/login/",
                json={"email": email, "password": password},
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                return {"authenticated": True, "user": data.get("user", {}).get("email")}
            return {"authenticated": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"authenticated": False, "error": str(e)}

    def _headers(self) -> dict:
        h = {}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def get_workspaces(self) -> dict:
        """List available Plane workspaces."""
        try:
            resp = self.client.get(
                f"{self.base_url}/api/workspaces/",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return {"workspaces": resp.json()}
            return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def get_projects(self, workspace_slug: str) -> dict:
        """List projects in a workspace."""
        try:
            resp = self.client.get(
                f"{self.base_url}/api/workspaces/{workspace_slug}/projects/",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return {"projects": resp.json()}
            return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def get_issues(self, workspace_slug: str, project_id: str, state: str = None) -> dict:
        """Get issues from a Plane project."""
        try:
            params = {"project": project_id}
            if state:
                params["state"] = state

            resp = self.client.get(
                f"{self.base_url}/api/workspaces/{workspace_slug}/issues/",
                headers=self._headers(),
                params=params,
            )
            if resp.status_code == 200:
                issues = resp.json()
                return {
                    "total": len(issues.get("results", [])),
                    "issues": [
                        {
                            "id": i.get("id"),
                            "name": i.get("name"),
                            "state": i.get("state"),
                            "priority": i.get("priority"),
                            "assignees": i.get("assignees", []),
                            "created_at": i.get("created_at"),
                        }
                        for i in issues.get("results", [])
                    ],
                }
            return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def get_stats(self, workspace_slug: str, project_id: str) -> dict:
        """Get project stats (issue counts by state)."""
        try:
            resp = self.client.get(
                f"{self.base_url}/api/workspaces/{workspace_slug}/projects/{project_id}/",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                project = resp.json()
                return {
                    "project": project.get("name"),
                    "identifier": project.get("identifier"),
                    "total_issues": project.get("total_issues", 0),
                    "total_members": project.get("total_members", 0),
                    "created_at": project.get("created_at"),
                }
            return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def sync_status(self) -> dict:
        """Check Plane connection and return sync status."""
        result = {
            "plane_url": self.base_url,
            "connected": False,
            "workspaces": 0,
            "projects": 0,
            "last_sync": None,
        }

        if not self.token:
            auth = self.authenticate()
            if not auth.get("authenticated"):
                result["error"] = auth.get("error", "Authentication failed")
                return result

        result["connected"] = True

        workspaces = self.get_workspaces()
        if "workspaces" in workspaces:
            ws_list = workspaces["workspaces"] if isinstance(workspaces["workspaces"], list) else workspaces["workspaces"].get("results", [])
            result["workspaces"] = len(ws_list)
            result["workspace_list"] = [
                {"name": w.get("name"), "slug": w.get("slug")}
                for w in ws_list
            ]

        return result


# Singleton
_plane_client: Optional[PlaneClient] = None


def get_plane_client() -> PlaneClient:
    global _plane_client
    if _plane_client is None:
        _plane_client = PlaneClient()
    return _plane_client
