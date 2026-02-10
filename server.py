#!/usr/bin/env python3
"""MCP Server for Composio management.

Provides tools to manage Composio connections, auth configs, toolkits,
and execute actions across any connected app.
"""

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.composio_mcp import ComposioClient

mcp = FastMCP("composio")

_client: Optional[ComposioClient] = None


def get_client() -> ComposioClient:
    global _client
    if _client is None:
        _client = ComposioClient.from_env()
    return _client


# ============== TOOLKITS ==============


@mcp.tool()
async def list_toolkits(search: Optional[str] = None) -> str:
    """List available Composio toolkits (apps like Instagram, GitHub, Slack, etc.).

    Args:
        search: Optional search query to filter toolkits
    """
    client = get_client()
    toolkits = await client.list_toolkits(search)
    return json.dumps([t.model_dump(mode="json") for t in toolkits], indent=2)


@mcp.tool()
async def get_toolkit_tools(toolkit_slug: str) -> str:
    """List all tools/actions available for a specific toolkit.

    Args:
        toolkit_slug: The toolkit slug (e.g., 'instagram', 'github', 'slack')
    """
    client = get_client()
    tools = await client.get_toolkit_tools(toolkit_slug)
    return json.dumps([t.model_dump(mode="json") for t in tools], indent=2)


# ============== AUTH CONFIGS ==============


@mcp.tool()
async def list_auth_configs(toolkit_slug: Optional[str] = None) -> str:
    """List auth configs (authentication blueprints for connecting apps).

    Args:
        toolkit_slug: Filter by app slug (e.g., 'instagram')
    """
    client = get_client()
    configs = await client.list_auth_configs(toolkit_slug)
    return json.dumps([c.model_dump(mode="json") for c in configs], indent=2)


@mcp.tool()
async def get_auth_config(auth_config_id: str) -> str:
    """Get details for a specific auth config including required fields.

    Args:
        auth_config_id: The auth config ID
    """
    client = get_client()
    config = await client.get_auth_config(auth_config_id)
    return json.dumps(config.model_dump(mode="json"), indent=2)


@mcp.tool()
async def create_auth_config(
    toolkit_slug: str,
    auth_scheme: str = "OAUTH2",
    name: Optional[str] = None,
    use_composio_auth: bool = True,
    scopes: Optional[str] = None,
) -> str:
    """Create a new auth config for connecting an app.

    Args:
        toolkit_slug: The app to configure (e.g., 'instagram', 'github', 'slack')
        auth_scheme: Auth method - 'OAUTH2', 'API_KEY', 'BEARER_TOKEN', 'BASIC'
        name: Display name for this config
        use_composio_auth: Use Composio's managed OAuth credentials (recommended)
        scopes: Comma-separated OAuth scopes (e.g., 'read,write,publish')
    """
    client = get_client()
    scope_list = [s.strip() for s in scopes.split(",")] if scopes else None
    config = await client.create_auth_config(
        toolkit_slug=toolkit_slug,
        auth_scheme=auth_scheme,
        name=name,
        use_composio_auth=use_composio_auth,
        scopes=scope_list,
    )
    return json.dumps(config.model_dump(mode="json"), indent=2)


@mcp.tool()
async def delete_auth_config(auth_config_id: str) -> str:
    """Delete an auth config.

    Args:
        auth_config_id: The auth config ID to delete
    """
    client = get_client()
    result = await client.delete_auth_config(auth_config_id)
    return json.dumps({"status": "deleted", "id": auth_config_id, **result})


# ============== CONNECTED ACCOUNTS ==============


@mcp.tool()
async def list_connections(
    toolkit_slug: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """List connected accounts.

    Args:
        toolkit_slug: Filter by app (e.g., 'instagram', 'zoom')
        status: Filter by status - 'ACTIVE', 'INACTIVE', 'PENDING', 'EXPIRED', 'FAILED'
        user_id: Filter by user ID
    """
    client = get_client()
    connections = await client.list_connections(toolkit_slug, status, user_id)
    return json.dumps([c.model_dump(mode="json") for c in connections], indent=2)


@mcp.tool()
async def get_connection(connection_id: str) -> str:
    """Get details for a specific connected account.

    Args:
        connection_id: The connected account ID
    """
    client = get_client()
    connection = await client.get_connection(connection_id)
    return json.dumps(connection.model_dump(mode="json"), indent=2)


@mcp.tool()
async def initiate_connection(
    auth_config_id: str,
    user_id: str = "default",
    callback_url: Optional[str] = None,
) -> str:
    """Initiate a new app connection (starts OAuth flow).

    Returns a redirect URL that must be opened in a browser to complete authentication.
    After the user completes auth, use get_connection to check status.

    Args:
        auth_config_id: The auth config ID to use (from list_auth_configs)
        user_id: User identifier (default: 'default')
        callback_url: URL to redirect to after OAuth completes
    """
    client = get_client()
    request = await client.initiate_connection(
        auth_config_id=auth_config_id,
        user_id=user_id,
        callback_url=callback_url,
    )
    return json.dumps(request.model_dump(mode="json"), indent=2)


@mcp.tool()
async def initiate_connection_link(
    auth_config_id: str,
    user_id: str = "default",
    callback_url: Optional[str] = None,
) -> str:
    """Create a Composio-hosted auth link for connecting an app.

    Similar to initiate_connection but uses Composio's hosted auth page.

    Args:
        auth_config_id: The auth config ID to use
        user_id: User identifier
        callback_url: URL to redirect to after completion
    """
    client = get_client()
    request = await client.initiate_connection_link(
        auth_config_id=auth_config_id,
        user_id=user_id,
        callback_url=callback_url,
    )
    return json.dumps(request.model_dump(mode="json"), indent=2)


@mcp.tool()
async def delete_connection(connection_id: str) -> str:
    """Delete a connected account.

    Args:
        connection_id: The connected account ID to delete
    """
    client = get_client()
    result = await client.delete_connection(connection_id)
    return json.dumps({"status": "deleted", "id": connection_id, **result})


@mcp.tool()
async def refresh_connection(connection_id: str) -> str:
    """Refresh authentication for a connected account (e.g., expired OAuth tokens).

    Args:
        connection_id: The connected account ID to refresh
    """
    client = get_client()
    connection = await client.refresh_connection(connection_id)
    return json.dumps(connection.model_dump(mode="json"), indent=2)


# ============== ACTIONS ==============


@mcp.tool()
async def execute_action(
    action: str,
    connected_account_id: str,
    params: Optional[str] = None,
) -> str:
    """Execute a Composio action on a connected account.

    Args:
        action: The action name (e.g., 'INSTAGRAM_CREATE_MEDIA_CONTAINER')
        connected_account_id: The connected account ID to use
        params: JSON string of action input parameters
    """
    client = get_client()
    parsed_params = json.loads(params) if params else {}
    result = await client.execute_action(action, connected_account_id, parsed_params)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run()
