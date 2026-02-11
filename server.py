#!/usr/bin/env python3
"""MCP Server for Composio.

Unified server providing:
- Management tools (auth configs, connections, toolkits, execute)
- Notion tools (28 tools, prefixed notion_*)
- Zoom tools (9 tools, prefixed zoom_*)
"""

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.composio_mcp import ComposioClient
from src.composio_mcp.notion import NotionClient
from src.composio_mcp.zoom import ZoomClient
from src.composio_mcp.models.zoom import MeetingCreate

mcp = FastMCP("composio")

# Lazy-loaded clients
_client: Optional[ComposioClient] = None
_notion: Optional[NotionClient] = None
_zoom: Optional[ZoomClient] = None


def get_client() -> ComposioClient:
    global _client
    if _client is None:
        _client = ComposioClient.from_env()
    return _client


def get_notion() -> NotionClient:
    global _notion
    if _notion is None:
        _notion = NotionClient.from_env()
    return _notion


def get_zoom() -> ZoomClient:
    global _zoom
    if _zoom is None:
        _zoom = ZoomClient.from_env()
    return _zoom


# ==================================================================
# MANAGEMENT TOOLS (11 tools)
# ==================================================================


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


# ==================================================================
# NOTION TOOLS (28 tools)
# ==================================================================


# --- Pages ---

@mcp.tool()
async def notion_create_page(
    parent_id: str,
    title: str,
    parent_type: str = "page_id",
    icon: Optional[str] = None,
    cover: Optional[str] = None,
) -> str:
    """Create a new Notion page.

    Args:
        parent_id: Parent page or database ID
        title: Page title
        parent_type: 'page_id' or 'database_id'
        icon: Optional emoji icon
        cover: Optional cover image URL
    """
    notion = get_notion()
    page = await notion.create_page(parent_id, title, parent_type, icon, cover)
    return json.dumps(page.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_get_page(page_id: str) -> str:
    """Get Notion page metadata.

    Args:
        page_id: The Notion page ID
    """
    notion = get_notion()
    page = await notion.get_page(page_id)
    return json.dumps(page.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_update_page(
    page_id: str,
    title: Optional[str] = None,
    icon: Optional[str] = None,
    cover: Optional[str] = None,
    archived: Optional[bool] = None,
    properties: Optional[str] = None,
) -> str:
    """Update a Notion page's properties.

    Args:
        page_id: The page ID
        title: New title
        icon: New emoji icon
        cover: New cover image URL
        archived: Archive/unarchive the page
        properties: JSON string of properties to update
    """
    notion = get_notion()
    props = json.loads(properties) if properties else None
    page = await notion.update_page(page_id, title, icon, cover, archived, props)
    return json.dumps(page.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_archive_page(page_id: str, archived: bool = True) -> str:
    """Archive or unarchive a Notion page.

    Args:
        page_id: The page ID
        archived: True to archive, False to restore
    """
    notion = get_notion()
    page = await notion.archive_page(page_id, archived)
    return json.dumps(page.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_duplicate_page(page_id: str) -> str:
    """Duplicate a Notion page with all its content.

    Args:
        page_id: The page ID to duplicate
    """
    notion = get_notion()
    page = await notion.duplicate_page(page_id)
    return json.dumps(page.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_search_pages(query: str = "") -> str:
    """Search Notion pages by title. Empty query lists all accessible pages.

    Args:
        query: Search query
    """
    notion = get_notion()
    pages = await notion.search_pages(query)
    return json.dumps([p.model_dump(mode="json") for p in pages], indent=2)


@mcp.tool()
async def notion_get_page_property(page_id: str, property_id: str) -> str:
    """Get a specific Notion page property value.

    Args:
        page_id: The page ID
        property_id: The property ID
    """
    notion = get_notion()
    result = await notion.get_page_property(page_id, property_id)
    return json.dumps(result, indent=2)


# --- Blocks ---

@mcp.tool()
async def notion_add_content_blocks(page_id: str, blocks: str) -> str:
    """Add multiple content blocks to a Notion page (user-friendly format).

    Args:
        page_id: The page ID
        blocks: JSON array of blocks, e.g. [{"type": "paragraph", "text": "Hello"}]
    """
    notion = get_notion()
    result = await notion.add_content_blocks(page_id, json.loads(blocks))
    return json.dumps(result, indent=2)


@mcp.tool()
async def notion_append_complex_blocks(block_id: str, children: str) -> str:
    """Append blocks with full Notion block structure (advanced).

    Args:
        block_id: Parent block or page ID
        children: JSON array of full Notion block objects
    """
    notion = get_notion()
    result = await notion.append_complex_blocks(block_id, json.loads(children))
    return json.dumps(result, indent=2)


@mcp.tool()
async def notion_get_block(block_id: str) -> str:
    """Get Notion block metadata.

    Args:
        block_id: The block ID
    """
    notion = get_notion()
    block = await notion.get_block(block_id)
    return json.dumps(block.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_get_block_children(
    block_id: str,
    start_cursor: Optional[str] = None,
    page_size: int = 100,
) -> str:
    """Get child blocks of a Notion block or page.

    Args:
        block_id: Parent block or page ID
        start_cursor: Pagination cursor
        page_size: Number of results (max 100)
    """
    notion = get_notion()
    blocks = await notion.get_block_children(block_id, start_cursor, page_size)
    return json.dumps([b.model_dump(mode="json") for b in blocks], indent=2)


@mcp.tool()
async def notion_update_block(block_id: str, updates: str) -> str:
    """Update a Notion block's content.

    Args:
        block_id: The block ID
        updates: JSON object of block-type-specific fields to update
    """
    notion = get_notion()
    block = await notion.update_block(block_id, **json.loads(updates))
    return json.dumps(block.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_delete_block(block_id: str) -> str:
    """Delete (archive) a Notion block.

    Args:
        block_id: The block ID
    """
    notion = get_notion()
    result = await notion.delete_block(block_id)
    return json.dumps(result, indent=2)


# --- Databases ---

@mcp.tool()
async def notion_create_database(
    parent_id: str,
    title: str,
    properties: str,
) -> str:
    """Create a new Notion database.

    Args:
        parent_id: Parent page ID
        title: Database title
        properties: JSON object of database property schema
    """
    notion = get_notion()
    db = await notion.create_database(parent_id, title, json.loads(properties))
    return json.dumps(db.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_get_database(database_id: str) -> str:
    """Get Notion database metadata and schema.

    Args:
        database_id: The database ID
    """
    notion = get_notion()
    db = await notion.get_database(database_id)
    return json.dumps(db.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_query_database(
    database_id: str,
    filter: Optional[str] = None,
    sorts: Optional[str] = None,
    page_size: int = 100,
    start_cursor: Optional[str] = None,
) -> str:
    """Query a Notion database for rows.

    Args:
        database_id: The database ID
        filter: JSON Notion filter object
        sorts: JSON array of Notion sort objects
        page_size: Number of results (max 100)
        start_cursor: Pagination cursor
    """
    notion = get_notion()
    f = json.loads(filter) if filter else None
    s = json.loads(sorts) if sorts else None
    rows = await notion.query_database(database_id, f, s, page_size, start_cursor)
    return json.dumps([r.model_dump(mode="json") for r in rows], indent=2)


@mcp.tool()
async def notion_create_database_row(database_id: str, properties: str) -> str:
    """Insert a new row into a Notion database.

    Args:
        database_id: The database ID
        properties: JSON object of row property values
    """
    notion = get_notion()
    row = await notion.create_database_row(database_id, json.loads(properties))
    return json.dumps(row.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_get_database_row(row_id: str) -> str:
    """Get a Notion database row by ID.

    Args:
        row_id: The row (page) ID
    """
    notion = get_notion()
    row = await notion.get_database_row(row_id)
    return json.dumps(row.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_update_database_row(
    row_id: str,
    properties: Optional[str] = None,
    archived: Optional[bool] = None,
) -> str:
    """Update a Notion database row.

    Args:
        row_id: The row (page) ID
        properties: JSON object of properties to update
        archived: Archive/unarchive the row
    """
    notion = get_notion()
    props = json.loads(properties) if properties else None
    row = await notion.update_database_row(row_id, props, archived)
    return json.dumps(row.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_update_database_schema(
    database_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    properties: Optional[str] = None,
) -> str:
    """Update Notion database title, description, or property schema.

    Args:
        database_id: The database ID
        title: New title
        description: New description
        properties: JSON object of properties to add/update
    """
    notion = get_notion()
    props = json.loads(properties) if properties else None
    db = await notion.update_database_schema(database_id, title, description, props)
    return json.dumps(db.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_get_database_property(database_id: str, property_id: str) -> str:
    """Get a specific Notion database property schema.

    Args:
        database_id: The database ID
        property_id: The property ID
    """
    notion = get_notion()
    result = await notion.get_database_property(database_id, property_id)
    return json.dumps(result, indent=2)


# --- Comments ---

@mcp.tool()
async def notion_create_comment(
    parent_id: str,
    rich_text: str,
    discussion_id: Optional[str] = None,
) -> str:
    """Create a comment on a Notion page or reply to a discussion.

    Args:
        parent_id: Page ID for new comment
        rich_text: Comment text
        discussion_id: Discussion ID to reply to an existing thread
    """
    notion = get_notion()
    comment = await notion.create_comment(parent_id, rich_text, discussion_id)
    return json.dumps(comment.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_get_comments(block_id: str) -> str:
    """Get comments on a Notion block or page.

    Args:
        block_id: Block or page ID
    """
    notion = get_notion()
    comments = await notion.get_comments(block_id)
    return json.dumps([c.model_dump(mode="json") for c in comments], indent=2)


@mcp.tool()
async def notion_get_comment(comment_id: str) -> str:
    """Get a specific Notion comment by ID.

    Args:
        comment_id: The comment ID
    """
    notion = get_notion()
    comment = await notion.get_comment(comment_id)
    return json.dumps(comment.model_dump(mode="json"), indent=2)


# --- Users ---

@mcp.tool()
async def notion_get_current_user() -> str:
    """Get the bot user for this Notion integration."""
    notion = get_notion()
    user = await notion.get_current_user()
    return json.dumps(user.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_get_user(user_id: str) -> str:
    """Get a Notion user by ID.

    Args:
        user_id: The user ID
    """
    notion = get_notion()
    user = await notion.get_user(user_id)
    return json.dumps(user.model_dump(mode="json"), indent=2)


@mcp.tool()
async def notion_list_users() -> str:
    """List all users in the Notion workspace."""
    notion = get_notion()
    users = await notion.list_users()
    return json.dumps([u.model_dump(mode="json") for u in users], indent=2)


# --- Workspace ---

@mcp.tool()
async def notion_search_workspace(
    query: str = "",
    filter_type: Optional[str] = None,
    page_size: int = 100,
) -> str:
    """Search the entire Notion workspace for pages and databases.

    Args:
        query: Search query
        filter_type: 'page' or 'database' to filter results (None for all)
        page_size: Number of results (max 100)
    """
    notion = get_notion()
    results = await notion.search_workspace(query, filter_type, page_size)
    return json.dumps([r.model_dump(mode="json") for r in results], indent=2)


# ==================================================================
# ZOOM TOOLS (9 tools)
# ==================================================================


# --- Meetings ---

@mcp.tool()
async def zoom_list_meetings(meeting_type: str = "upcoming") -> str:
    """List Zoom meetings.

    Args:
        meeting_type: Type of meetings - 'upcoming', 'scheduled', 'live', or 'pending'
    """
    zoom = get_zoom()
    meetings = await zoom.list_meetings(meeting_type)
    return json.dumps([m.model_dump(mode="json") for m in meetings], indent=2)


@mcp.tool()
async def zoom_create_meeting(
    topic: str,
    start_time: str,
    duration: int = 45,
    timezone: str = "America/New_York",
    agenda: Optional[str] = None,
    waiting_room: bool = True,
    auto_recording: str = "cloud",
) -> str:
    """Create a new Zoom meeting.

    Args:
        topic: Meeting title
        start_time: Start time in ISO format (e.g., '2026-02-11T10:00:00')
        duration: Duration in minutes (default: 45)
        timezone: IANA timezone (default: America/New_York)
        agenda: Optional meeting description
        waiting_room: Enable waiting room (default: True)
        auto_recording: 'cloud', 'local', or 'none' (default: cloud)
    """
    zoom = get_zoom()
    meeting = await zoom.create_meeting(MeetingCreate(
        topic=topic,
        start_time=start_time,
        duration=duration,
        timezone=timezone,
        agenda=agenda,
        waiting_room=waiting_room,
        auto_recording=auto_recording,
    ))
    return json.dumps(meeting.model_dump(mode="json"), indent=2)


@mcp.tool()
async def zoom_get_meeting(meeting_id: int) -> str:
    """Get details for a specific Zoom meeting.

    Args:
        meeting_id: The Zoom meeting ID
    """
    zoom = get_zoom()
    meeting = await zoom.get_meeting(meeting_id)
    return json.dumps(meeting.model_dump(mode="json"), indent=2)


@mcp.tool()
async def zoom_update_meeting(
    meeting_id: int,
    topic: Optional[str] = None,
    start_time: Optional[str] = None,
    duration: Optional[int] = None,
    agenda: Optional[str] = None,
) -> str:
    """Update an existing Zoom meeting.

    Args:
        meeting_id: The Zoom meeting ID
        topic: New title (optional)
        start_time: New start time in ISO format (optional)
        duration: New duration in minutes (optional)
        agenda: New agenda (optional)
    """
    zoom = get_zoom()
    await zoom.update_meeting(meeting_id, topic, start_time, duration, agenda)
    return json.dumps({"status": "updated", "meeting_id": meeting_id})


@mcp.tool()
async def zoom_delete_meeting(meeting_id: int) -> str:
    """Delete a Zoom meeting.

    Args:
        meeting_id: The Zoom meeting ID to delete
    """
    zoom = get_zoom()
    await zoom.delete_meeting(meeting_id)
    return json.dumps({"status": "deleted", "meeting_id": meeting_id})


@mcp.tool()
async def zoom_add_registrant(
    meeting_id: int,
    email: str,
    first_name: str,
    last_name: str = "",
) -> str:
    """Add a registrant to a Zoom meeting.

    Args:
        meeting_id: The Zoom meeting ID
        email: Registrant's email
        first_name: Registrant's first name
        last_name: Registrant's last name (optional)
    """
    zoom = get_zoom()
    registrant = await zoom.add_registrant(meeting_id, email, first_name, last_name)
    return json.dumps(registrant.model_dump(mode="json"), indent=2)


# --- Recordings ---

@mcp.tool()
async def zoom_list_recordings(from_date: str, to_date: Optional[str] = None) -> str:
    """List Zoom cloud recordings in a date range.

    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD, optional)
    """
    zoom = get_zoom()
    recordings = await zoom.list_recordings(from_date, to_date)
    return json.dumps([r.model_dump(mode="json") for r in recordings], indent=2)


@mcp.tool()
async def zoom_get_recording(meeting_id: int) -> str:
    """Get Zoom recording details for a meeting.

    Args:
        meeting_id: The Zoom meeting ID
    """
    zoom = get_zoom()
    recording = await zoom.get_recording(meeting_id)
    return json.dumps(recording.model_dump(mode="json"), indent=2)


# --- Post-meeting ---

@mcp.tool()
async def zoom_get_participants(meeting_id: int) -> str:
    """Get participants from a past Zoom meeting.

    Args:
        meeting_id: The Zoom meeting ID (must be a past meeting)
    """
    zoom = get_zoom()
    participants = await zoom.get_participants(meeting_id)
    return json.dumps([p.model_dump(mode="json") for p in participants], indent=2)


@mcp.tool()
async def zoom_get_meeting_summary(meeting_id: int) -> str:
    """Get AI-generated Zoom meeting summary.

    Args:
        meeting_id: The Zoom meeting ID
    """
    zoom = get_zoom()
    summary = await zoom.get_meeting_summary(meeting_id)
    return json.dumps(summary.model_dump(mode="json"), indent=2)


if __name__ == "__main__":
    mcp.run()
