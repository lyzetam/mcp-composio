"""Pydantic models for Notion data."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============== PAGES ==============

class PageProperty(BaseModel):
    """A single page property."""
    id: str
    type: str
    value: Any = None


class Page(BaseModel):
    """Notion page."""
    id: str
    url: Optional[str] = None
    title: Optional[str] = None
    icon: Optional[str] = None
    cover: Optional[str] = None
    parent_id: Optional[str] = None
    parent_type: Optional[str] = None
    archived: bool = False
    created_time: Optional[datetime] = None
    last_edited_time: Optional[datetime] = None
    properties: dict[str, Any] = Field(default_factory=dict)


# ============== BLOCKS ==============

class BlockContent(BaseModel):
    """Block content (rich text, children, etc.)."""
    type: str
    data: Any = None


class Block(BaseModel):
    """Notion block."""
    id: str
    type: str
    has_children: bool = False
    archived: bool = False
    created_time: Optional[datetime] = None
    last_edited_time: Optional[datetime] = None
    parent_id: Optional[str] = None
    content: Any = None


# ============== DATABASES ==============

class Database(BaseModel):
    """Notion database."""
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[str] = None
    archived: bool = False
    created_time: Optional[datetime] = None
    last_edited_time: Optional[datetime] = None
    properties: dict[str, Any] = Field(default_factory=dict)


class DatabaseRow(BaseModel):
    """A row (page) in a Notion database."""
    id: str
    url: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)
    created_time: Optional[datetime] = None
    last_edited_time: Optional[datetime] = None
    archived: bool = False


class DatabaseQuery(BaseModel):
    """Input for querying a database."""
    database_id: str
    filter: Optional[dict] = None
    sorts: Optional[list[dict]] = None
    page_size: int = 100
    start_cursor: Optional[str] = None


# ============== COMMENTS ==============

class Comment(BaseModel):
    """Notion comment."""
    id: str
    discussion_id: Optional[str] = None
    parent_id: Optional[str] = None
    rich_text: Any = None
    created_time: Optional[datetime] = None
    created_by: Optional[dict] = None


# ============== USERS ==============

class User(BaseModel):
    """Notion user."""
    id: str
    type: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None


# ============== SEARCH ==============

class SearchResult(BaseModel):
    """Workspace search result."""
    id: str
    object_type: str  # 'page' or 'database'
    title: Optional[str] = None
    url: Optional[str] = None
    parent_id: Optional[str] = None
    last_edited_time: Optional[datetime] = None
