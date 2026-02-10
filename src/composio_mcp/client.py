"""Composio management client.

Wraps the Composio REST API v3 for managing connections, auth configs,
toolkits, and executing actions.

Usage:
    from composio_mcp import ComposioClient

    client = ComposioClient(api_key="ak_xxx")
    # or
    client = ComposioClient.from_env()

    toolkits = await client.list_toolkits()
    connections = await client.list_connections()
"""

import json
import os
from typing import Any, Optional

import httpx

from .models import (
    AuthConfig,
    ConnectedAccount,
    ConnectionRequest,
    Toolkit,
    ToolkitTool,
)


class ComposioClient:
    """Composio REST API v3 management client."""

    BASE_URL = "https://backend.composio.dev/api/v3"

    def __init__(self, api_key: str, timeout: float = 30.0):
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    @classmethod
    def from_env(cls) -> "ComposioClient":
        """Create client from environment variables or AWS Secrets Manager."""
        api_key = None

        try:
            import boto3
            client = boto3.client("secretsmanager", region_name="us-east-1")
            secret = json.loads(
                client.get_secret_value(SecretId="composio/api-key")["SecretString"]
            )
            api_key = secret.get("api_key")
        except Exception:
            pass

        api_key = api_key or os.environ.get("COMPOSIO_API_KEY")

        if not api_key:
            raise ValueError(
                "Missing COMPOSIO_API_KEY. Set env var or store in "
                "AWS Secrets Manager at composio/api-key"
            )

        return cls(api_key=api_key)

    async def _request(
        self, method: str, path: str, params: Optional[dict] = None, body: Optional[dict] = None
    ) -> Any:
        """Make an API request."""
        url = f"{self.BASE_URL}{path}"
        response = await self._client.request(method, url, params=params, json=body)
        response.raise_for_status()
        if response.status_code == 204:
            return {}
        return response.json()

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    # ============== TOOLKITS ==============

    async def list_toolkits(self, search: Optional[str] = None) -> list[Toolkit]:
        """List available toolkits (apps)."""
        params = {}
        if search:
            params["search"] = search
        data = await self._request("GET", "/toolkits", params=params)
        items = data if isinstance(data, list) else data.get("items", data.get("toolkits", []))
        return [
            Toolkit(
                slug=t.get("slug", t.get("key", "")),
                name=t.get("name", t.get("display_name", "")),
                description=t.get("description"),
                logo=t.get("logo"),
                auth_schemes=t.get("auth_schemes", []),
                categories=t.get("categories", []),
            )
            for t in items
        ]

    async def get_toolkit_tools(self, toolkit_slug: str) -> list[ToolkitTool]:
        """List tools/actions available for a toolkit."""
        # v3 toolkit tools endpoint doesn't exist; use v2 actions with apps filter
        url = "https://backend.composio.dev/api/v2/actions"
        response = await self._client.get(url, params={"apps": toolkit_slug, "limit": 100})
        response.raise_for_status()
        data = response.json()
        items = data if isinstance(data, list) else data.get("items", data.get("tools", []))
        return [
            ToolkitTool(
                action=t.get("name", t.get("action", "")),
                display_name=t.get("display_name", t.get("displayName")),
                description=t.get("description"),
                parameters=t.get("parameters"),
            )
            for t in items
        ]

    # ============== AUTH CONFIGS ==============

    async def list_auth_configs(self, toolkit_slug: Optional[str] = None) -> list[AuthConfig]:
        """List auth configs."""
        params = {}
        if toolkit_slug:
            params["toolkit_slug"] = toolkit_slug
        data = await self._request("GET", "/auth_configs", params=params)
        items = data if isinstance(data, list) else data.get("items", data.get("auth_configs", []))
        return [
            AuthConfig(
                id=c.get("id", ""),
                toolkit_slug=c.get("toolkit_slug", c.get("app_name")),
                auth_scheme=c.get("auth_scheme"),
                name=c.get("name"),
                created_at=c.get("created_at"),
                expected_input_fields=c.get("expected_input_fields", []),
            )
            for c in items
        ]

    async def get_auth_config(self, auth_config_id: str) -> AuthConfig:
        """Get auth config details."""
        c = await self._request("GET", f"/auth_configs/{auth_config_id}")
        return AuthConfig(
            id=c.get("id", auth_config_id),
            toolkit_slug=c.get("toolkit_slug", c.get("app_name")),
            auth_scheme=c.get("auth_scheme"),
            name=c.get("name"),
            created_at=c.get("created_at"),
            expected_input_fields=c.get("expected_input_fields", []),
        )

    async def create_auth_config(
        self,
        toolkit_slug: str,
        auth_scheme: str = "OAUTH2",
        name: Optional[str] = None,
        use_composio_auth: bool = True,
        credentials: Optional[dict] = None,
        scopes: Optional[list[str]] = None,
    ) -> AuthConfig:
        """Create a new auth config for a toolkit.

        Args:
            toolkit_slug: The app slug (e.g., 'instagram', 'github')
            auth_scheme: Auth method - 'OAUTH2', 'API_KEY', 'BEARER_TOKEN', 'BASIC'
            name: Display name for the config
            use_composio_auth: Use Composio's managed credentials (default: True)
            credentials: Custom OAuth credentials (client_id, client_secret) if not using managed auth
            scopes: OAuth scopes to request
        """
        options: dict[str, Any] = {
            "type": "use_composio_managed_auth" if use_composio_auth else "use_custom_auth",
            "auth_scheme": auth_scheme,
        }
        if name:
            options["name"] = name
        if credentials:
            options["credentials"] = credentials
        if scopes:
            options["credentials"] = {**(options.get("credentials") or {}), "scopes": scopes}

        body: dict[str, Any] = {
            "toolkit": {"slug": toolkit_slug},
            "options": options,
        }

        data = await self._request("POST", "/auth_configs", body=body)
        # Response nests config under "auth_config" key
        c = data.get("auth_config", data)
        return AuthConfig(
            id=c.get("id", ""),
            toolkit_slug=data.get("toolkit", {}).get("slug", toolkit_slug) if isinstance(data.get("toolkit"), dict) else c.get("toolkit_slug", toolkit_slug),
            auth_scheme=c.get("auth_scheme", auth_scheme),
            name=c.get("name", name),
            created_at=c.get("created_at"),
            expected_input_fields=c.get("expected_input_fields", []),
        )

    async def delete_auth_config(self, auth_config_id: str) -> dict:
        """Delete an auth config."""
        return await self._request("DELETE", f"/auth_configs/{auth_config_id}")

    # ============== CONNECTED ACCOUNTS ==============

    async def list_connections(
        self,
        toolkit_slug: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[ConnectedAccount]:
        """List connected accounts.

        Args:
            toolkit_slug: Filter by app (e.g., 'instagram')
            status: Filter by status - 'ACTIVE', 'INACTIVE', 'PENDING', 'EXPIRED', 'FAILED'
            user_id: Filter by user ID
        """
        params = {}
        if toolkit_slug:
            params["toolkit_slug"] = toolkit_slug
        if status:
            params["status"] = status
        if user_id:
            params["user_id"] = user_id
        data = await self._request("GET", "/connected_accounts", params=params)
        items = data if isinstance(data, list) else data.get("items", data.get("connected_accounts", []))
        return [
            ConnectedAccount(
                id=a.get("id", ""),
                status=a.get("status", "UNKNOWN"),
                toolkit_slug=(a.get("toolkit", {}).get("slug") if isinstance(a.get("toolkit"), dict) else None) or a.get("toolkit_slug", a.get("app_name")),
                auth_config_id=(a.get("auth_config", {}).get("id") if isinstance(a.get("auth_config"), dict) else None) or a.get("auth_config_id"),
                user_id=a.get("user_id", a.get("entity_id")),
                created_at=a.get("created_at"),
                updated_at=a.get("updated_at"),
                deprecated_uuid=(a.get("deprecated", {}).get("uuid") if isinstance(a.get("deprecated"), dict) else None),
            )
            for a in items
        ]

    async def get_connection(self, connection_id: str) -> ConnectedAccount:
        """Get a connected account by ID."""
        a = await self._request("GET", f"/connected_accounts/{connection_id}")
        return ConnectedAccount(
            id=a.get("id", connection_id),
            status=a.get("status", "UNKNOWN"),
            toolkit_slug=(a.get("toolkit", {}).get("slug") if isinstance(a.get("toolkit"), dict) else None) or a.get("toolkit_slug", a.get("app_name")),
            auth_config_id=(a.get("auth_config", {}).get("id") if isinstance(a.get("auth_config"), dict) else None) or a.get("auth_config_id"),
            user_id=a.get("user_id", a.get("entity_id")),
            created_at=a.get("created_at"),
            updated_at=a.get("updated_at"),
            deprecated_uuid=(a.get("deprecated", {}).get("uuid") if isinstance(a.get("deprecated"), dict) else None),
        )

    async def initiate_connection(
        self,
        auth_config_id: str,
        user_id: str = "default",
        callback_url: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> ConnectionRequest:
        """Initiate a new connection (OAuth flow).

        Returns a redirect URL for OAuth apps that the user must open in a browser.

        Args:
            auth_config_id: The auth config to use
            user_id: User identifier (default: 'default')
            callback_url: Where to redirect after OAuth completes
            config: Additional config (auth_scheme overrides, subdomain, etc.)
        """
        connection: dict[str, Any] = {"user_id": user_id}
        if callback_url:
            connection["callback_url"] = callback_url
        if config:
            connection.update(config)

        body: dict[str, Any] = {
            "auth_config": {"id": auth_config_id},
            "connection": connection,
        }

        data = await self._request("POST", "/connected_accounts", body=body)
        return ConnectionRequest(
            id=data.get("id", data.get("connectedAccountId", "")),
            status=data.get("status", "INITIATED"),
            redirect_url=data.get("redirect_url", data.get("redirectUrl")),
        )

    async def initiate_connection_link(
        self,
        auth_config_id: str,
        user_id: str = "default",
        callback_url: Optional[str] = None,
    ) -> ConnectionRequest:
        """Create a Composio-hosted auth link for the user.

        Args:
            auth_config_id: The auth config to use
            user_id: User identifier
            callback_url: Where to redirect after completion
        """
        connection: dict[str, Any] = {"user_id": user_id}
        if callback_url:
            connection["callback_url"] = callback_url

        body: dict[str, Any] = {
            "auth_config": {"id": auth_config_id},
            "connection": connection,
        }

        data = await self._request("POST", "/connected_accounts/link", body=body)
        return ConnectionRequest(
            id=data.get("id", data.get("link_token", "")),
            status=data.get("status", "INITIATED"),
            redirect_url=data.get("redirect_url", data.get("redirectUrl")),
        )

    async def delete_connection(self, connection_id: str) -> dict:
        """Delete a connected account."""
        return await self._request("DELETE", f"/connected_accounts/{connection_id}")

    async def refresh_connection(self, connection_id: str) -> ConnectedAccount:
        """Refresh authentication for a connected account."""
        a = await self._request("POST", f"/connected_accounts/{connection_id}/refresh")
        return ConnectedAccount(
            id=a.get("id", connection_id),
            status=a.get("status", "UNKNOWN"),
            toolkit_slug=a.get("toolkit_slug", a.get("app_name")),
            auth_config_id=a.get("auth_config_id"),
            user_id=a.get("user_id"),
            created_at=a.get("created_at"),
            updated_at=a.get("updated_at"),
        )

    # ============== ACTIONS ==============

    async def execute_action(
        self,
        action: str,
        connected_account_id: str,
        params: Optional[dict] = None,
    ) -> dict:
        """Execute a Composio action on a connected account.

        Args:
            action: The action name (e.g., 'INSTAGRAM_CREATE_MEDIA_CONTAINER')
            connected_account_id: The connected account ID (v3 ca_* or deprecated UUID)
            params: Action input parameters
        """
        # v2 execute requires deprecated UUIDs, not v3 ca_* IDs
        account_id = connected_account_id
        if connected_account_id.startswith("ca_"):
            conn = await self.get_connection(connected_account_id)
            if conn.deprecated_uuid:
                account_id = conn.deprecated_uuid
            else:
                raise ValueError(
                    f"Cannot resolve v3 ID {connected_account_id} to a UUID for v2 execute. "
                    "Pass the deprecated UUID directly."
                )

        body: dict[str, Any] = {
            "connectedAccountId": account_id,
            "input": params or {},
        }
        # Actions use v2 endpoint
        url = "https://backend.composio.dev/api/v2/actions"
        response = await self._client.post(
            f"{url}/{action}/execute",
            json=body,
        )
        response.raise_for_status()
        return response.json()
