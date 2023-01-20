import logging
from typing import Optional

import psycopg2
from psycopg2.extras import NamedTupleCursor
from telegram import Message
from telegram.ext import CallbackContext

from config import DATABASE_URL
from data.model import Source

logger = logging.getLogger(__name__)
conn = psycopg2.connect(DATABASE_URL, cursor_factory=NamedTupleCursor)


def get_source(channel_id: int) -> Optional[Source]:
    with conn.cursor() as c:
        c.execute("select * from sources where channel_id = %s;",
                  [channel_id])
        res = c.fetchone()
        print(res)

        return res
