"""Notion client via Composio API.

Usage:
    from composio_mcp.notion import NotionClient

    async with NotionClient.from_env() as notion:
        pages = await notion.search_pages("Meeting Notes")
        user = await notion.get_current_user()
"""

from typing import Any, Optional

from .client import _BaseClient
from .models.notion import (
    Block,
    Comment,
    Database,
    DatabaseRow,
    Page,
    SearchResult,
    User,
)


class NotionClient(_BaseClient):
    """Notion client using Composio as the OAuth/API layer."""

    @classmethod
    def from_env(cls) -> "NotionClient":
        return cls._from_env("notion_connected_account_id", "NOTION_CONNECTED_ACCOUNT_ID")

    # ============== PAGES ==============

    async def create_page(
        self,
        parent_id: str,
        title: str,
        parent_type: str = "page_id",
        icon: Optional[str] = None,
        cover: Optional[str] = None,
    ) -> Page:
        """Create a new page.

        Args:
            parent_id: Parent page or database ID
            title: Page title
            parent_type: 'page_id' or 'database_id'
            icon: Optional emoji icon
            cover: Optional cover image URL
        """
        params: dict[str, Any] = {
            "parent_type": parent_type,
            "parent_id": parent_id,
            "title": title,
        }
        if icon:
            params["icon"] = icon
        if cover:
            params["cover"] = cover

        data = await self._execute("NOTION_CREATE_NOTION_PAGE", params)
        return self._parse_page(data)

    async def get_page(self, page_id: str) -> Page:
        """Get page metadata."""
        data = await self._execute("NOTION_FETCH_BLOCK_METADATA", {
            "block_id": page_id,
        })
        return self._parse_page(data)

    async def update_page(
        self,
        page_id: str,
        title: Optional[str] = None,
        icon: Optional[str] = None,
        cover: Optional[str] = None,
        archived: Optional[bool] = None,
        properties: Optional[dict] = None,
    ) -> Page:
        """Update page properties."""
        params: dict[str, Any] = {"page_id": page_id}
        if title is not None:
            params["title"] = title
        if icon is not None:
            params["icon"] = icon
        if cover is not None:
            params["cover"] = cover
        if archived is not None:
            params["archived"] = archived
        if properties is not None:
            params["properties"] = properties

        data = await self._execute("NOTION_UPDATE_PAGE", params)
        return self._parse_page(data)

    async def archive_page(self, page_id: str, archived: bool = True) -> Page:
        """Archive or unarchive a page."""
        data = await self._execute("NOTION_ARCHIVE_NOTION_PAGE", {
            "page_id": page_id,
            "archived": archived,
        })
        return self._parse_page(data)

    async def duplicate_page(self, page_id: str) -> Page:
        """Duplicate a page with all its content."""
        data = await self._execute("NOTION_DUPLICATE_PAGE", {
            "page_id": page_id,
        })
        return self._parse_page(data)

    async def search_pages(self, query: str = "") -> list[Page]:
        """Search pages by title. Empty query lists all accessible pages."""
        data = await self._execute("NOTION_SEARCH_NOTION_PAGE", {
            "query": query,
        })
        results = data if isinstance(data, list) else data.get("results", [data])
        return [self._parse_page(r) for r in results if isinstance(r, dict)]

    async def get_page_property(self, page_id: str, property_id: str) -> dict:
        """Get a specific page property."""
        return await self._execute("NOTION_GET_PAGE_PROPERTY_ACTION", {
            "page_id": page_id,
            "property_id": property_id,
        })

    def _parse_page(self, data: dict) -> Page:
        """Parse raw API response into a Page model."""
        title = None
        props = data.get("properties", {})
        for prop in props.values():
            if isinstance(prop, dict) and prop.get("type") == "title":
                title_arr = prop.get("title", [])
                if title_arr and isinstance(title_arr, list):
                    title = "".join(t.get("plain_text", "") for t in title_arr)
                break

        parent = data.get("parent", {})
        parent_type = parent.get("type")
        parent_id = parent.get(parent_type) if parent_type else None

        return Page(
            id=data.get("id", ""),
            url=data.get("url"),
            title=title,
            icon=data.get("icon", {}).get("emoji") if isinstance(data.get("icon"), dict) else None,
            cover=data.get("cover", {}).get("external", {}).get("url") if isinstance(data.get("cover"), dict) else None,
            parent_id=parent_id,
            parent_type=parent_type,
            archived=data.get("archived", False),
            created_time=data.get("created_time"),
            last_edited_time=data.get("last_edited_time"),
            properties=props,
        )

    # ============== BLOCKS ==============

    async def add_content_blocks(self, page_id: str, blocks: list[dict]) -> dict:
        """Add multiple content blocks to a page (user-friendly format).

        Args:
            page_id: The page ID
            blocks: List of block dicts, e.g. [{"type": "paragraph", "text": "Hello"}]
        """
        return await self._execute("NOTION_ADD_MULTIPLE_PAGE_CONTENT", {
            "page_id": page_id,
            "blocks": blocks,
        })

    async def append_complex_blocks(self, block_id: str, children: list[dict]) -> dict:
        """Append complex blocks with full Notion block structure."""
        return await self._execute("NOTION_APPEND_BLOCK_CHILDREN", {
            "block_id": block_id,
            "children": children,
        })

    async def get_block(self, block_id: str) -> Block:
        """Get block metadata."""
        data = await self._execute("NOTION_FETCH_BLOCK_METADATA", {
            "block_id": block_id,
        })
        return self._parse_block(data)

    async def get_block_children(
        self,
        block_id: str,
        start_cursor: Optional[str] = None,
        page_size: int = 100,
    ) -> list[Block]:
        """Get child blocks of a block or page."""
        params: dict[str, Any] = {"block_id": block_id, "page_size": page_size}
        if start_cursor:
            params["start_cursor"] = start_cursor

        data = await self._execute("NOTION_FETCH_BLOCK_CONTENTS", params)
        results = data if isinstance(data, list) else data.get("results", [data])
        return [self._parse_block(b) for b in results if isinstance(b, dict)]

    async def update_block(self, block_id: str, **kwargs) -> Block:
        """Update a block's content."""
        params = {"block_id": block_id, **kwargs}
        data = await self._execute("NOTION_UPDATE_BLOCK", params)
        return self._parse_block(data)

    async def delete_block(self, block_id: str) -> dict:
        """Delete (archive) a block."""
        return await self._execute("NOTION_DELETE_BLOCK", {
            "block_id": block_id,
        })

    def _parse_block(self, data: dict) -> Block:
        """Parse raw API response into a Block model."""
        block_type = data.get("type", "unknown")
        return Block(
            id=data.get("id", ""),
            type=block_type,
            has_children=data.get("has_children", False),
            archived=data.get("archived", False),
            created_time=data.get("created_time"),
            last_edited_time=data.get("last_edited_time"),
            parent_id=data.get("parent", {}).get(data.get("parent", {}).get("type", "")),
            content=data.get(block_type),
        )

    # ============== DATABASES ==============

    async def create_database(
        self,
        parent_id: str,
        title: str,
        properties: dict,
    ) -> Database:
        """Create a new database."""
        data = await self._execute("NOTION_CREATE_DATABASE", {
            "parent_id": parent_id,
            "title": title,
            "properties": properties,
        })
        return self._parse_database(data)

    async def get_database(self, database_id: str) -> Database:
        """Get database metadata."""
        data = await self._execute("NOTION_FETCH_DATABASE", {
            "database_id": database_id,
        })
        return self._parse_database(data)

    async def query_database(
        self,
        database_id: str,
        filter: Optional[dict] = None,
        sorts: Optional[list[dict]] = None,
        page_size: int = 100,
        start_cursor: Optional[str] = None,
    ) -> list[DatabaseRow]:
        """Query a database for rows."""
        params: dict[str, Any] = {
            "database_id": database_id,
            "page_size": page_size,
        }
        if filter:
            params["filter"] = filter
        if sorts:
            params["sorts"] = sorts
        if start_cursor:
            params["start_cursor"] = start_cursor

        data = await self._execute("NOTION_QUERY_DATABASE", params)
        results = data if isinstance(data, list) else data.get("results", [data])
        return [self._parse_database_row(r) for r in results if isinstance(r, dict)]

    async def create_database_row(self, database_id: str, properties: dict) -> DatabaseRow:
        """Insert a new row into a database."""
        data = await self._execute("NOTION_INSERT_ROW_DATABASE", {
            "database_id": database_id,
            "properties": properties,
        })
        return self._parse_database_row(data)

    async def get_database_row(self, row_id: str) -> DatabaseRow:
        """Get a database row by ID."""
        data = await self._execute("NOTION_FETCH_ROW", {
            "row_id": row_id,
        })
        return self._parse_database_row(data)

    async def update_database_row(
        self,
        row_id: str,
        properties: Optional[dict] = None,
        archived: Optional[bool] = None,
    ) -> DatabaseRow:
        """Update a database row."""
        params: dict[str, Any] = {"row_id": row_id}
        if properties is not None:
            params["properties"] = properties
        if archived is not None:
            params["archived"] = archived

        data = await self._execute("NOTION_UPDATE_ROW_DATABASE", params)
        return self._parse_database_row(data)

    async def update_database_schema(
        self,
        database_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        properties: Optional[dict] = None,
    ) -> Database:
        """Update database title, description, or properties."""
        params: dict[str, Any] = {"database_id": database_id}
        if title is not None:
            params["title"] = title
        if description is not None:
            params["description"] = description
        if properties is not None:
            params["properties"] = properties

        data = await self._execute("NOTION_UPDATE_SCHEMA_DATABASE", params)
        return self._parse_database(data)

    async def get_database_property(self, database_id: str, property_id: str) -> dict:
        """Get a specific database property schema."""
        return await self._execute("NOTION_RETRIEVE_DATABASE_PROPERTY", {
            "database_id": database_id,
            "property_id": property_id,
        })

    def _parse_database(self, data: dict) -> Database:
        """Parse raw API response into a Database model."""
        title = None
        title_arr = data.get("title", [])
        if isinstance(title_arr, list) and title_arr:
            title = "".join(t.get("plain_text", "") for t in title_arr)

        desc = None
        desc_arr = data.get("description", [])
        if isinstance(desc_arr, list) and desc_arr:
            desc = "".join(t.get("plain_text", "") for t in desc_arr)

        parent = data.get("parent", {})
        parent_type = parent.get("type")
        parent_id = parent.get(parent_type) if parent_type else None

        return Database(
            id=data.get("id", ""),
            title=title,
            description=desc,
            url=data.get("url"),
            icon=data.get("icon", {}).get("emoji") if isinstance(data.get("icon"), dict) else None,
            parent_id=parent_id,
            archived=data.get("archived", False),
            created_time=data.get("created_time"),
            last_edited_time=data.get("last_edited_time"),
            properties=data.get("properties", {}),
        )

    def _parse_database_row(self, data: dict) -> DatabaseRow:
        """Parse raw API response into a DatabaseRow model."""
        return DatabaseRow(
            id=data.get("id", ""),
            url=data.get("url"),
            properties=data.get("properties", {}),
            created_time=data.get("created_time"),
            last_edited_time=data.get("last_edited_time"),
            archived=data.get("archived", False),
        )

    # ============== COMMENTS ==============

    async def create_comment(
        self,
        parent_id: str,
        rich_text: str,
        discussion_id: Optional[str] = None,
    ) -> Comment:
        """Create a comment on a page or discussion."""
        params: dict[str, Any] = {"rich_text": rich_text}
        if discussion_id:
            params["discussion_id"] = discussion_id
        else:
            params["parent_id"] = parent_id

        data = await self._execute("NOTION_CREATE_COMMENT", params)
        return self._parse_comment(data)

    async def get_comments(self, block_id: str) -> list[Comment]:
        """Get comments on a block or page."""
        data = await self._execute("NOTION_FETCH_COMMENTS", {
            "block_id": block_id,
        })
        results = data if isinstance(data, list) else data.get("results", [data])
        return [self._parse_comment(c) for c in results if isinstance(c, dict)]

    async def get_comment(self, comment_id: str) -> Comment:
        """Get a specific comment by ID."""
        data = await self._execute("NOTION_RETRIEVE_COMMENT", {
            "comment_id": comment_id,
        })
        return self._parse_comment(data)

    def _parse_comment(self, data: dict) -> Comment:
        """Parse raw API response into a Comment model."""
        return Comment(
            id=data.get("id", ""),
            discussion_id=data.get("discussion_id"),
            parent_id=data.get("parent", {}).get("page_id"),
            rich_text=data.get("rich_text"),
            created_time=data.get("created_time"),
            created_by=data.get("created_by"),
        )

    # ============== USERS ==============

    async def get_current_user(self) -> User:
        """Get the bot user for this integration."""
        data = await self._execute("NOTION_GET_ABOUT_ME", {})
        return self._parse_user(data)

    async def get_user(self, user_id: str) -> User:
        """Get a user by ID."""
        data = await self._execute("NOTION_GET_ABOUT_USER", {
            "user_id": user_id,
        })
        return self._parse_user(data)

    async def list_users(self) -> list[User]:
        """List all users in the workspace."""
        data = await self._execute("NOTION_LIST_USERS", {})
        results = data if isinstance(data, list) else data.get("results", [data])
        return [self._parse_user(u) for u in results if isinstance(u, dict)]

    def _parse_user(self, data: dict) -> User:
        """Parse raw API response into a User model."""
        return User(
            id=data.get("id", ""),
            type=data.get("type"),
            name=data.get("name"),
            avatar_url=data.get("avatar_url"),
            email=data.get("person", {}).get("email") if isinstance(data.get("person"), dict) else None,
        )

    # ============== WORKSPACE ==============

    async def search_workspace(
        self,
        query: str = "",
        filter_type: Optional[str] = None,
        page_size: int = 100,
    ) -> list[SearchResult]:
        """Search the entire workspace."""
        params: dict[str, Any] = {"page_size": page_size}
        if query:
            params["query"] = query

        if filter_type == "page":
            params["get_pages"] = True
        elif filter_type == "database":
            params["get_databases"] = True
        else:
            params["get_all"] = True

        data = await self._execute("NOTION_FETCH_DATA", params)
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", data.get("values", []))
        return [self._parse_search_result(r) for r in results if isinstance(r, dict)]

    def _parse_search_result(self, data: dict) -> SearchResult:
        """Parse raw API response into a SearchResult model."""
        obj_type = data.get("object", "page")
        title = None

        if obj_type == "database":
            title_arr = data.get("title", [])
            if isinstance(title_arr, list) and title_arr:
                title = "".join(t.get("plain_text", "") for t in title_arr)
        else:
            for prop in data.get("properties", {}).values():
                if isinstance(prop, dict) and prop.get("type") == "title":
                    title_arr = prop.get("title", [])
                    if isinstance(title_arr, list) and title_arr:
                        title = "".join(t.get("plain_text", "") for t in title_arr)
                    break

        parent = data.get("parent", {})
        parent_type = parent.get("type")
        parent_id = parent.get(parent_type) if parent_type else None

        return SearchResult(
            id=data.get("id", ""),
            object_type=obj_type,
            title=title,
            url=data.get("url"),
            parent_id=parent_id,
            last_edited_time=data.get("last_edited_time"),
        )
