from dataclasses import dataclass
from typing import Optional


@dataclass
class Post:
    source_channel: int
    source_id: int
    post_id: int
    backup_id: int
    reply_id: Optional[int]
    media_id: Optional[str]


@dataclass
class Source:
    channel_id: int
    detail_id: int
    bias: Optional[str]
    description: str
    rating: int
    name: str
    display_name: Optional[str]
    invite: Optional[str]
    username: Optional[str]
