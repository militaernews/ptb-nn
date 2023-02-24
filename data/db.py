import inspect
import logging
from typing import Optional

import psycopg2
from psycopg2.extras import NamedTupleCursor

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


def set_pattern(channel_id: int, pattern: str):
    try:
        with conn.cursor() as c:
            c.execute("INSERT INTO bloats(channel_id,pattern) VALUES (%s, '%s')", (channel_id, pattern))
            res = c.fetchall()
            conn.commit()

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> get_ptterns: ", res)

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed", e)
        pass
