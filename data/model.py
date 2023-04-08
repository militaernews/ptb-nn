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
    channel_name: str
    bias: Optional[str]
    destination: Optional[str] = None
    display_name: Optional[str] = None
    invite: Optional[str] = None
    username: Optional[str] = None
    api_id: Optional[int] = None
    description: Optional[str] = None
    rating: Optional[int] = None
    detail_id: Optional[int] = None
    is_active: bool = False


@dataclass
class SourceInsert:
    channel_id: int
    channel_name: str
    display_name: Optional[str] = None
    bias: Optional[str] = None
    invite: Optional[str] = None
    username: Optional[str] = None


@dataclass
class Destination:
    channel_id: int
    name: str
    group_id: Optional[int]


@dataclass
class Account:
    api_id: int
    api_hash: str
    name: str
    phone_number: str
    description: str



