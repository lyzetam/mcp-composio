# App Integration Guide

## Installation

```bash
# From GitHub (public repo)
uv pip install "mcp-composio[aws] @ git+https://github.com/lyzetam/mcp-composio.git"

# Or add to pyproject.toml dependencies
# "mcp-composio[aws] @ git+https://github.com/lyzetam/mcp-composio.git"
```

The `[aws]` extra includes `boto3` for loading credentials from AWS Secrets Manager.

## Quick Start

```python
from composio_mcp import ComposioClient

async with ComposioClient.from_env() as client:
    result = await client.execute_action(
        "INSTAGRAM_GET_USER_INFO",
        "<your-connection-id>",
        {},
    )
    print(result["data"]["username"])
```

`ComposioClient.from_env()` loads the API key from AWS Secrets Manager (`composio/api-key`), falling back to the `COMPOSIO_API_KEY` environment variable.

## Connected Accounts

Store your connection IDs in environment variables or a config file — never hardcode them in source:

```python
import os

ACCOUNTS = {
    "brand": os.environ["COMPOSIO_IG_BRAND_ID"],      # e.g. ca_xxx
    "personal": os.environ["COMPOSIO_IG_PERSONAL_ID"], # e.g. ca_yyy
}
```

## Instagram Examples

### Post a Photo

Instagram publishing is a 2-step process: create a media container, then publish it.

```python
from composio_mcp import ComposioClient

ACCOUNT = os.environ["COMPOSIO_IG_ACCOUNT_ID"]

async def post_photo(image_url: str, caption: str):
    async with ComposioClient.from_env() as client:
        # Step 1: Create media container
        container = await client.execute_action(
            "INSTAGRAM_CREATE_MEDIA_CONTAINER",
            ACCOUNT,
            {"image_url": image_url, "caption": caption},
        )
        container_id = container["data"]["id"]

        # Step 2: Publish
        post = await client.execute_action(
            "INSTAGRAM_CREATE_POST",
            ACCOUNT,
            {"creation_id": container_id},
        )
        return post["data"]["id"]
```

### Post a Carousel (Multiple Images)

```python
async def post_carousel(image_urls: list[str], caption: str):
    async with ComposioClient.from_env() as client:
        # Step 1: Create carousel container with multiple images
        container = await client.execute_action(
            "INSTAGRAM_CREATE_CAROUSEL_CONTAINER",
            ACCOUNT,
            {"image_urls": image_urls, "caption": caption},
        )
        container_id = container["data"]["id"]

        # Step 2: Publish
        post = await client.execute_action(
            "INSTAGRAM_CREATE_POST",
            ACCOUNT,
            {"creation_id": container_id},
        )
        return post["data"]["id"]
```

### Get Post Analytics

```python
async def get_post_insights(post_id: str):
    async with ComposioClient.from_env() as client:
        return await client.execute_action(
            "INSTAGRAM_GET_POST_INSIGHTS",
            ACCOUNT,
            {"media_id": post_id},
        )
```

### Get Account Analytics

```python
async def get_account_insights():
    async with ComposioClient.from_env() as client:
        return await client.execute_action(
            "INSTAGRAM_GET_USER_INSIGHTS",
            ACCOUNT,
            {},
        )
```

### Get Recent Posts

```python
async def get_recent_posts():
    async with ComposioClient.from_env() as client:
        result = await client.execute_action(
            "INSTAGRAM_GET_USER_MEDIA",
            ACCOUNT,
            {},
        )
        return result["data"]
```

### Reply to Comments

```python
async def reply_to_comment(comment_id: str, message: str):
    async with ComposioClient.from_env() as client:
        return await client.execute_action(
            "INSTAGRAM_REPLY_TO_COMMENT",
            ACCOUNT,
            {"comment_id": comment_id, "message": message},
        )
```

### Send a DM

```python
async def send_dm(recipient_id: str, message: str):
    async with ComposioClient.from_env() as client:
        return await client.execute_action(
            "INSTAGRAM_SEND_TEXT_MESSAGE",
            ACCOUNT,
            {"recipient_id": recipient_id, "message": message},
        )
```

## Multi-Account Pattern

Use environment variables to manage multiple accounts:

```python
import os
from composio_mcp import ComposioClient

INSTAGRAM_ACCOUNTS = {
    "brand": os.environ["COMPOSIO_IG_BRAND_ID"],
    "personal": os.environ["COMPOSIO_IG_PERSONAL_ID"],
}

async def post_to_account(account_name: str, image_url: str, caption: str):
    account_id = INSTAGRAM_ACCOUNTS[account_name]

    async with ComposioClient.from_env() as client:
        container = await client.execute_action(
            "INSTAGRAM_CREATE_MEDIA_CONTAINER",
            account_id,
            {"image_url": image_url, "caption": caption},
        )
        return await client.execute_action(
            "INSTAGRAM_CREATE_POST",
            account_id,
            {"creation_id": container["data"]["id"]},
        )

# Post to personal account
await post_to_account("personal", "https://...", "New post!")

# Post to brand account
await post_to_account("brand", "https://...", "Lab update")
```

## FastAPI Integration

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from composio_mcp import ComposioClient

client: ComposioClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = ComposioClient.from_env()
    yield
    await client.close()

app = FastAPI(lifespan=lifespan)

ACCOUNTS = {
    "brand": os.environ["COMPOSIO_IG_BRAND_ID"],
    "personal": os.environ["COMPOSIO_IG_PERSONAL_ID"],
}

class PostRequest(BaseModel):
    account: str
    image_url: str
    caption: str

@app.post("/instagram/post")
async def create_post(req: PostRequest):
    if req.account not in ACCOUNTS:
        raise HTTPException(400, f"Unknown account: {req.account}")

    container = await client.execute_action(
        "INSTAGRAM_CREATE_MEDIA_CONTAINER",
        ACCOUNTS[req.account],
        {"image_url": req.image_url, "caption": req.caption},
    )
    post = await client.execute_action(
        "INSTAGRAM_CREATE_POST",
        ACCOUNTS[req.account],
        {"creation_id": container["data"]["id"]},
    )
    return {"post_id": post["data"]["id"]}

@app.get("/instagram/{account}/insights")
async def get_insights(account: str):
    if account not in ACCOUNTS:
        raise HTTPException(400, f"Unknown account: {account}")

    return await client.execute_action(
        "INSTAGRAM_GET_USER_INSIGHTS",
        ACCOUNTS[account],
        {},
    )
```

## LangChain/LangGraph Agent Tool

```python
import os
from langchain_core.tools import tool
from composio_mcp import ComposioClient

ACCOUNTS = {
    "brand": os.environ["COMPOSIO_IG_BRAND_ID"],
    "personal": os.environ["COMPOSIO_IG_PERSONAL_ID"],
}

@tool
async def instagram_post(account: str, image_url: str, caption: str) -> str:
    """Post a photo to Instagram. Account must be 'brand' or 'personal'."""
    async with ComposioClient.from_env() as client:
        container = await client.execute_action(
            "INSTAGRAM_CREATE_MEDIA_CONTAINER",
            ACCOUNTS[account],
            {"image_url": image_url, "caption": caption},
        )
        post = await client.execute_action(
            "INSTAGRAM_CREATE_POST",
            ACCOUNTS[account],
            {"creation_id": container["data"]["id"]},
        )
        return f"Posted to {account}: {post['data']['id']}"

@tool
async def instagram_get_comments(account: str, post_id: str) -> dict:
    """Get comments on an Instagram post."""
    async with ComposioClient.from_env() as client:
        return await client.execute_action(
            "INSTAGRAM_GET_POST_COMMENTS",
            ACCOUNTS[account],
            {"media_id": post_id},
        )
```

## Available Instagram Actions

| Action | Description |
|--------|-------------|
| `INSTAGRAM_CREATE_MEDIA_CONTAINER` | Create draft photo/video/reel |
| `INSTAGRAM_CREATE_CAROUSEL_CONTAINER` | Create draft carousel (multi-image) |
| `INSTAGRAM_CREATE_POST` | Publish a draft container |
| `INSTAGRAM_GET_POST_STATUS` | Check draft processing status |
| `INSTAGRAM_GET_POST_INSIGHTS` | Post analytics (impressions, reach) |
| `INSTAGRAM_GET_USER_INSIGHTS` | Account-level analytics |
| `INSTAGRAM_GET_USER_INFO` | Profile details and stats |
| `INSTAGRAM_GET_USER_MEDIA` | List user's posts |
| `INSTAGRAM_GET_POST_COMMENTS` | Get comments on a post |
| `INSTAGRAM_REPLY_TO_COMMENT` | Reply to a comment |
| `INSTAGRAM_LIST_ALL_CONVERSATIONS` | List DM conversations |
| `INSTAGRAM_GET_CONVERSATION` | Get conversation details |
| `INSTAGRAM_LIST_ALL_MESSAGES` | List messages in a conversation |
| `INSTAGRAM_SEND_TEXT_MESSAGE` | Send a DM |
| `INSTAGRAM_SEND_IMAGE` | Send image via DM |
| `INSTAGRAM_MARK_SEEN` | Mark DMs as read |

## Discovering Actions for Other Toolkits

The client can list actions for any Composio-connected app:

```python
async with ComposioClient.from_env() as client:
    tools = await client.get_toolkit_tools("zoom")
    for t in tools:
        print(f"{t.action}: {t.description}")
```
