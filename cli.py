#!/usr/bin/env python3
"""CLI for Composio integrations.

Usage:
    python cli.py notion me
    python cli.py notion search "Notes"
    python cli.py notion page PAGE_ID
    python cli.py notion create-page PARENT_ID "Title"
    python cli.py notion database DATABASE_ID
    python cli.py notion query DATABASE_ID [--filter JSON]

    python cli.py zoom list [--type TYPE]
    python cli.py zoom create --topic "Demo" --datetime "2026-02-15T10:00:00"
    python cli.py zoom get MEETING_ID
    python cli.py zoom update MEETING_ID [--topic TOPIC]
    python cli.py zoom recordings --from DATE [--to DATE]
    python cli.py zoom recording MEETING_ID
    python cli.py zoom participants MEETING_ID
    python cli.py zoom summary MEETING_ID
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime

from src.composio_mcp.notion import NotionClient
from src.composio_mcp.zoom import ZoomClient
from src.composio_mcp.models.zoom import MeetingCreate


# ==================================================================
# NOTION COMMANDS
# ==================================================================


async def notion_me(args):
    async with NotionClient.from_env() as client:
        user = await client.get_current_user()
    print(f"Bot: {user.name or 'Unknown'} ({user.id})")
    if user.type:
        print(f"  Type: {user.type}")


async def notion_users(args):
    async with NotionClient.from_env() as client:
        users = await client.list_users()
    if not users:
        print("No users found.")
        return
    for u in users:
        email = f" ({u.email})" if u.email else ""
        print(f"  {u.name or 'Unknown'}{email} [{u.type or '?'}] - {u.id}")


async def notion_search(args):
    async with NotionClient.from_env() as client:
        results = await client.search_workspace(
            query=args.query,
            filter_type=args.type,
            page_size=args.limit,
        )
    if not results:
        print("No results found.")
        return
    for r in results:
        icon = "p" if r.object_type == "page" else "db"
        print(f"  [{icon}] {r.title or 'Untitled'}")
        print(f"       ID: {r.id}")
        if r.url:
            print(f"       URL: {r.url}")
        print()


async def notion_page(args):
    async with NotionClient.from_env() as client:
        page = await client.get_page(args.page_id)
    print(f"Page: {page.title or 'Untitled'}")
    print(f"  ID: {page.id}")
    if page.url:
        print(f"  URL: {page.url}")
    print(f"  Archived: {page.archived}")
    if page.created_time:
        print(f"  Created: {page.created_time}")
    if page.last_edited_time:
        print(f"  Edited: {page.last_edited_time}")


async def notion_create_page(args):
    async with NotionClient.from_env() as client:
        page = await client.create_page(
            parent_id=args.parent_id,
            title=args.title,
            icon=args.icon,
        )
    print(f"Page created: {page.title}")
    print(f"  ID: {page.id}")
    if page.url:
        print(f"  URL: {page.url}")


async def notion_database(args):
    async with NotionClient.from_env() as client:
        db = await client.get_database(args.database_id)
    print(f"Database: {db.title or 'Untitled'}")
    print(f"  ID: {db.id}")
    if db.url:
        print(f"  URL: {db.url}")
    print(f"  Properties:")
    for name, prop in db.properties.items():
        ptype = prop.get("type", "?") if isinstance(prop, dict) else "?"
        print(f"    - {name} ({ptype})")


async def notion_query(args):
    filter_obj = json.loads(args.filter) if args.filter else None
    async with NotionClient.from_env() as client:
        rows = await client.query_database(
            database_id=args.database_id,
            filter=filter_obj,
            page_size=args.page_size,
        )
    if not rows:
        print("No rows found.")
        return
    print(f"Found {len(rows)} rows:")
    for row in rows:
        title = None
        for prop in row.properties.values():
            if isinstance(prop, dict) and prop.get("type") == "title":
                title_arr = prop.get("title", [])
                if title_arr and isinstance(title_arr, list):
                    title = "".join(t.get("plain_text", "") for t in title_arr)
                break
        print(f"  - {title or 'Untitled'} ({row.id})")


# ==================================================================
# ZOOM COMMANDS
# ==================================================================


def format_meeting(m) -> str:
    dt = m.start_time
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    formatted = dt.strftime("%a, %b %d %Y at %I:%M %p")
    lines = [
        f"  Topic:      {m.topic}",
        f"  Date/Time:  {formatted} {m.timezone}",
        f"  Duration:   {m.duration} min",
        f"  Meeting ID: {m.id}",
    ]
    if m.password:
        lines.append(f"  Password:   {m.password}")
    if m.join_url:
        lines.append(f"  Join URL:   {m.join_url}")
    return "\n".join(lines)


async def zoom_list(args):
    async with ZoomClient.from_env() as client:
        meetings = await client.list_meetings(args.type)
    if not meetings:
        print("No meetings found.")
        return
    for m in meetings:
        print(format_meeting(m))
        print()


async def zoom_create(args):
    async with ZoomClient.from_env() as client:
        meeting = await client.create_meeting(MeetingCreate(
            topic=args.topic,
            start_time=args.datetime,
            duration=args.duration,
            timezone=args.timezone,
            agenda=args.agenda,
        ))
    print("Meeting created:\n")
    print(format_meeting(meeting))


async def zoom_get(args):
    async with ZoomClient.from_env() as client:
        meeting = await client.get_meeting(args.meeting_id)
    print(format_meeting(meeting))


async def zoom_update(args):
    async with ZoomClient.from_env() as client:
        await client.update_meeting(
            args.meeting_id,
            topic=args.topic,
            start_time=args.datetime,
            duration=args.duration,
            agenda=args.agenda,
        )
    print(f"Meeting {args.meeting_id} updated.")


async def zoom_recordings(args):
    async with ZoomClient.from_env() as client:
        recordings = await client.list_recordings(args.from_date, args.to_date)
    if not recordings:
        print("No recordings found.")
        return
    for r in recordings:
        dt = r.start_time
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        print(f"  {r.topic}")
        print(f"    Date: {dt.strftime('%b %d, %Y')}, Duration: {r.duration} min")
        print(f"    Meeting ID: {r.meeting_id}")
        print()


async def zoom_recording(args):
    async with ZoomClient.from_env() as client:
        recording = await client.get_recording(args.meeting_id)
    print(f"Recording: {recording.topic}")
    print(f"  Share URL: {recording.share_url}")
    if recording.password:
        print(f"  Password:  {recording.password}")
    print(f"  Files:")
    for f in recording.files:
        print(f"    - {f.file_type}: {f.file_size // 1024 // 1024}MB")
        if f.download_url:
            print(f"      Download: {f.download_url}")


async def zoom_participants(args):
    async with ZoomClient.from_env() as client:
        participants = await client.get_participants(args.meeting_id)
    if not participants:
        print("No participants found.")
        return
    print("Participants:")
    for p in participants:
        duration = f"{p.duration // 60}m" if p.duration else "?"
        print(f"  - {p.name or 'Unknown'} ({p.email or 'no email'}) - {duration}")


async def zoom_summary(args):
    async with ZoomClient.from_env() as client:
        summary = await client.get_meeting_summary(args.meeting_id)
    if summary.summary:
        print("Summary:")
        print(f"  {summary.summary}")
    if summary.next_steps:
        print("\nNext Steps:")
        for step in summary.next_steps:
            print(f"  - {step}")
    if summary.topics:
        print("\nTopics:")
        for topic in summary.topics:
            print(f"  - {topic}")


# ==================================================================
# MAIN
# ==================================================================


def build_parser():
    parser = argparse.ArgumentParser(description="Composio CLI")
    subparsers = parser.add_subparsers(dest="domain", required=True)

    # --- Notion subcommands ---
    notion_p = subparsers.add_parser("notion", help="Notion operations")
    notion_sub = notion_p.add_subparsers(dest="command", required=True)

    notion_sub.add_parser("me", help="Get current bot user")
    notion_sub.add_parser("users", help="List workspace users")

    search_p = notion_sub.add_parser("search", help="Search workspace")
    search_p.add_argument("query", nargs="?", default="")
    search_p.add_argument("--type", "-t", choices=["page", "database"])
    search_p.add_argument("--limit", "-l", type=int, default=20)

    page_p = notion_sub.add_parser("page", help="Get page details")
    page_p.add_argument("page_id")

    create_p = notion_sub.add_parser("create-page", help="Create a page")
    create_p.add_argument("parent_id")
    create_p.add_argument("title")
    create_p.add_argument("--icon", "-i")

    db_p = notion_sub.add_parser("database", help="Get database details")
    db_p.add_argument("database_id")

    query_p = notion_sub.add_parser("query", help="Query a database")
    query_p.add_argument("database_id")
    query_p.add_argument("--filter", "-f")
    query_p.add_argument("--page-size", "-n", type=int, default=20)

    # --- Zoom subcommands ---
    zoom_p = subparsers.add_parser("zoom", help="Zoom operations")
    zoom_sub = zoom_p.add_subparsers(dest="command", required=True)

    list_p = zoom_sub.add_parser("list", help="List meetings")
    list_p.add_argument("--type", "-t", default="upcoming",
                        choices=["upcoming", "scheduled", "live", "pending"])

    zcreate_p = zoom_sub.add_parser("create", help="Create meeting")
    zcreate_p.add_argument("--topic", "-t", required=True)
    zcreate_p.add_argument("--datetime", "-d", required=True)
    zcreate_p.add_argument("--duration", "-l", type=int, default=45)
    zcreate_p.add_argument("--timezone", "-z", default="America/New_York")
    zcreate_p.add_argument("--agenda", "-a")

    get_p = zoom_sub.add_parser("get", help="Get meeting")
    get_p.add_argument("meeting_id", type=int)

    update_p = zoom_sub.add_parser("update", help="Update meeting")
    update_p.add_argument("meeting_id", type=int)
    update_p.add_argument("--topic", "-t")
    update_p.add_argument("--datetime", "-d")
    update_p.add_argument("--duration", "-l", type=int)
    update_p.add_argument("--agenda", "-a")

    rec_p = zoom_sub.add_parser("recordings", help="List recordings")
    rec_p.add_argument("--from", dest="from_date", required=True)
    rec_p.add_argument("--to", dest="to_date")

    rec_get_p = zoom_sub.add_parser("recording", help="Get recording")
    rec_get_p.add_argument("meeting_id", type=int)

    part_p = zoom_sub.add_parser("participants", help="Get participants")
    part_p.add_argument("meeting_id", type=int)

    sum_p = zoom_sub.add_parser("summary", help="Get meeting summary")
    sum_p.add_argument("meeting_id", type=int)

    return parser


COMMANDS = {
    "notion": {
        "me": notion_me,
        "users": notion_users,
        "search": notion_search,
        "page": notion_page,
        "create-page": notion_create_page,
        "database": notion_database,
        "query": notion_query,
    },
    "zoom": {
        "list": zoom_list,
        "create": zoom_create,
        "get": zoom_get,
        "update": zoom_update,
        "recordings": zoom_recordings,
        "recording": zoom_recording,
        "participants": zoom_participants,
        "summary": zoom_summary,
    },
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        asyncio.run(COMMANDS[args.domain][args.command](args))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
