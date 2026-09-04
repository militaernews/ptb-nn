"""Read-only access to mix-sv's own database (a separate Neon Postgres,
distinct from this bot's `sources`/`bloats` tables) so admins can pull in
edits made through the mix-sv web UI. See source/sync_mixsv.py.
"""
import logging
from typing import Dict, List, NamedTuple, Optional

import psycopg2
from psycopg2.extras import NamedTupleCursor

from bot.settings.config import MIX_SV_DATABASE_URL

# Fields an admin can actually change through mix-sv's edit form. Deliberately
# excludes api_id/destination (mix-sv never sets these - only this bot's own
# /edit_source may attach an account or destination) and avatar/detail_id
# (not portable / not editable via mix-sv).
SYNC_FIELDS = [
    "channel_name", "username", "bias", "invite",
    "display_name", "description", "rating", "is_active", "is_spread",
]


class MixSvSource(NamedTuple):
    channel_id: int
    channel_name: str
    username: Optional[str]
    bias: Optional[str]
    invite: Optional[str]
    display_name: Optional[str]
    description: Optional[str]
    rating: Optional[int]
    is_active: Optional[bool]
    is_spread: bool


def is_configured() -> bool:
    return bool(MIX_SV_DATABASE_URL)


def _connect():
    return psycopg2.connect(MIX_SV_DATABASE_URL, cursor_factory=NamedTupleCursor)


def get_mixsv_sources() -> List[MixSvSource]:
    if not is_configured():
        return []
    try:
        with _connect() as conn:
            with conn.cursor() as c:
                c.execute(
                    f"SELECT channel_id, {', '.join(SYNC_FIELDS)} FROM sources;"
                )
                return [MixSvSource(*row) for row in c.fetchall()]
    except Exception as e:
        logging.error(f"Failed to read mix-sv sources: {repr(e)}")
        return []


def get_mixsv_bloats() -> Dict[int, List[str]]:
    if not is_configured():
        return {}
    try:
        with _connect() as conn:
            with conn.cursor() as c:
                c.execute("SELECT channel_id, pattern FROM bloats;")
                result: Dict[int, List[str]] = {}
                for row in c.fetchall():
                    result.setdefault(row.channel_id, []).append(row.pattern)
                return result
    except Exception as e:
        logging.error(f"Failed to read mix-sv bloats: {repr(e)}")
        return {}
