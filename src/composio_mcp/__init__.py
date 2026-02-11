"""Composio client library.

Management:
    from composio_mcp import ComposioClient

Domain clients:
    from composio_mcp.notion import NotionClient
    from composio_mcp.zoom import ZoomClient
"""

from .client import ComposioClient, _BaseClient
from .notion import NotionClient
from .zoom import ZoomClient
from .models import (
    AuthConfig,
    ConnectedAccount,
    ConnectionRequest,
    Toolkit,
    ToolkitTool,
)

__all__ = [
    "ComposioClient",
    "_BaseClient",
    "NotionClient",
    "ZoomClient",
    "AuthConfig",
    "ConnectedAccount",
    "ConnectionRequest",
    "Toolkit",
    "ToolkitTool",
]
