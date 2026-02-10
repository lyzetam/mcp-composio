"""Pydantic models for Composio management data."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class Toolkit(BaseModel):
    """A Composio toolkit (app integration)."""
    slug: str
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    auth_schemes: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


class ToolkitTool(BaseModel):
    """A tool/action within a toolkit."""
    action: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None


class AuthConfig(BaseModel):
    """An auth config (blueprint for connecting an app)."""
    id: str
    toolkit_slug: Optional[str] = None
    auth_scheme: Optional[str] = None
    name: Optional[str] = None
    created_at: Optional[str] = None
    expected_input_fields: list[dict[str, Any]] = Field(default_factory=list)


class ConnectedAccount(BaseModel):
    """A connected account."""
    id: str
    status: str
    toolkit_slug: Optional[str] = None
    auth_config_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ConnectionRequest(BaseModel):
    """Result of initiating a connection."""
    id: str
    status: str
    redirect_url: Optional[str] = None
