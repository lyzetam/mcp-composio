# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Build & Run

```bash
# Install dependencies
uv venv && source .venv/bin/activate
uv pip install -e ".[aws]"

# Run MCP server (all tools: management + notion + zoom)
python server.py

# Run CLI
python cli.py notion me
python cli.py notion search "Meeting Notes"
python cli.py zoom list
python cli.py zoom create --topic "Demo" --datetime "2026-02-15T10:00:00"

# Run tests
pytest
```

## Architecture

```
src/composio_mcp/
  client.py          _BaseClient (shared) + ComposioClient (management v3)
  notion.py          NotionClient(_BaseClient) - 28 methods
  zoom.py            ZoomClient(_BaseClient) - 9 methods
  models/
    __init__.py      Management models + re-exports all domain models
    notion.py        Page, Database, Block, Comment, User, SearchResult
    zoom.py          Meeting, Recording, Participant, MeetingSummary

server.py            ONE MCP server: 14 management + 28 notion_* + 10 zoom_*
cli.py               Unified CLI: `notion` and `zoom` subcommands
```

**Key Design:** `_BaseClient` owns httpx setup, Composio v2 action execution, and `_from_env()` credential loading. Domain clients only define methods + response parsing. `ComposioClient` uses the separate v3 management API.

## Credentials

**AWS Secret:** `composio/api-key`
```json
{
  "api_key": "ak_xxx",
  "notion_connected_account_id": "xxx",
  "zoom_connected_account_id": "xxx"
}
```

Each domain client's `from_env()` loads its own connected account ID from the shared secret.

## MCP Tool Naming

All domain tools are prefixed: `notion_create_page`, `zoom_list_meetings`. Management tools have no prefix.

## Tools -> Composio Actions Mapping

### Notion (28 tools)

| MCP Tool | Composio Action | Group |
|----------|----------------|-------|
| `notion_create_page` | `NOTION_CREATE_NOTION_PAGE` | Pages |
| `notion_get_page` | `NOTION_FETCH_BLOCK_METADATA` | Pages |
| `notion_update_page` | `NOTION_UPDATE_PAGE` | Pages |
| `notion_archive_page` | `NOTION_ARCHIVE_NOTION_PAGE` | Pages |
| `notion_duplicate_page` | `NOTION_DUPLICATE_PAGE` | Pages |
| `notion_search_pages` | `NOTION_SEARCH_NOTION_PAGE` | Pages |
| `notion_get_page_property` | `NOTION_GET_PAGE_PROPERTY_ACTION` | Pages |
| `notion_add_content_blocks` | `NOTION_ADD_MULTIPLE_PAGE_CONTENT` | Blocks |
| `notion_append_complex_blocks` | `NOTION_APPEND_BLOCK_CHILDREN` | Blocks |
| `notion_get_block` | `NOTION_FETCH_BLOCK_METADATA` | Blocks |
| `notion_get_block_children` | `NOTION_FETCH_BLOCK_CONTENTS` | Blocks |
| `notion_update_block` | `NOTION_UPDATE_BLOCK` | Blocks |
| `notion_delete_block` | `NOTION_DELETE_BLOCK` | Blocks |
| `notion_create_database` | `NOTION_CREATE_DATABASE` | Databases |
| `notion_get_database` | `NOTION_FETCH_DATABASE` | Databases |
| `notion_query_database` | `NOTION_QUERY_DATABASE` | Databases |
| `notion_create_database_row` | `NOTION_INSERT_ROW_DATABASE` | Databases |
| `notion_get_database_row` | `NOTION_FETCH_ROW` | Databases |
| `notion_update_database_row` | `NOTION_UPDATE_ROW_DATABASE` | Databases |
| `notion_update_database_schema` | `NOTION_UPDATE_SCHEMA_DATABASE` | Databases |
| `notion_get_database_property` | `NOTION_RETRIEVE_DATABASE_PROPERTY` | Databases |
| `notion_create_comment` | `NOTION_CREATE_COMMENT` | Comments |
| `notion_get_comments` | `NOTION_FETCH_COMMENTS` | Comments |
| `notion_get_comment` | `NOTION_RETRIEVE_COMMENT` | Comments |
| `notion_get_current_user` | `NOTION_GET_ABOUT_ME` | Users |
| `notion_get_user` | `NOTION_GET_ABOUT_USER` | Users |
| `notion_list_users` | `NOTION_LIST_USERS` | Users |
| `notion_search_workspace` | `NOTION_FETCH_DATA` | Workspace |

### Zoom (10 tools)

| MCP Tool | Composio Action |
|----------|-----------------|
| `zoom_list_meetings` | `ZOOM_LIST_MEETINGS` |
| `zoom_create_meeting` | `ZOOM_CREATE_A_MEETING` |
| `zoom_get_meeting` | `ZOOM_GET_A_MEETING` |
| `zoom_update_meeting` | `ZOOM_UPDATE_A_MEETING` |
| `zoom_delete_meeting` | `ZOOM_DELETE_A_MEETING` (pending Composio support) |
| `zoom_add_registrant` | `ZOOM_ADD_A_MEETING_REGISTRANT` |
| `zoom_list_recordings` | `ZOOM_LIST_ALL_RECORDINGS` |
| `zoom_get_recording` | `ZOOM_GET_MEETING_RECORDINGS` |
| `zoom_get_participants` | `ZOOM_GET_PAST_MEETING_PARTICIPANTS` |
| `zoom_get_meeting_summary` | `ZOOM_GET_A_MEETING_SUMMARY` |

### Management (14 tools)

| MCP Tool | Purpose |
|----------|---------|
| `list_toolkits` | List available apps |
| `get_toolkit_tools` | List actions for an app |
| `list_auth_configs` | List auth blueprints |
| `get_auth_config` | Get auth config details |
| `create_auth_config` | Create new auth config |
| `delete_auth_config` | Delete auth config |
| `list_connections` | List connected accounts |
| `get_connection` | Get connection details |
| `initiate_connection` | Start OAuth flow |
| `initiate_connection_link` | Create hosted auth link |
| `delete_connection` | Delete connection |
| `refresh_connection` | Refresh OAuth tokens |
| `execute_action` | Execute any Composio action |

## Library Usage (Production)

```python
# Notion
from composio_mcp.notion import NotionClient

async with NotionClient.from_env() as notion:
    pages = await notion.search_pages("Meeting Notes")

# Zoom
from composio_mcp.zoom import ZoomClient
from composio_mcp.models.zoom import MeetingCreate

async with ZoomClient.from_env() as zoom:
    meetings = await zoom.list_meetings()
    meeting = await zoom.create_meeting(MeetingCreate(
        topic="Demo", start_time="2026-02-15T10:00:00"
    ))

# Management
from composio_mcp import ComposioClient

async with ComposioClient.from_env() as mgmt:
    toolkits = await mgmt.list_toolkits("notion")
```
