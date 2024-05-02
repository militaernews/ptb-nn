import inspect
import logging
from traceback import format_exc
from typing import Optional, Dict

import psycopg2
from psycopg2.extras import NamedTupleCursor

from config import DATABASE_URL
from data.model import Source, SourceInsert, Destination, Account

logger = logging.getLogger(__name__)
conn = psycopg2.connect(DATABASE_URL, cursor_factory=NamedTupleCursor)


def get_source(channel_id: int) -> Optional[Source]:
    with conn.cursor() as c:
        c.execute("select * from sources where channel_id = %s;",
                  [channel_id])
        res: Source = c.fetchone()
        logging.info(res)
        return res


def get_destination_ids() -> [int]:
    with conn.cursor() as c:
        c.execute("select channel_id from destinations;")
        res: [int] = [item.channel_id for item in c.fetchall()]
        logging.info(f"destination ids: {res}")
        return res


def set_source(source: SourceInsert):
    try:
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO sources(channel_id,channel_name,display_name,bias,invite,username) VALUES (%s, %s,%s,%s,%s,%s)",
                (source.channel_id, source.channel_name, source.display_name, source.bias, source.invite,
                 source.username))

            conn.commit()

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")

        pass


def update_source(source: Source):
    try:
        with conn.cursor() as c:
            c.execute(
                "UPDATE sources set channel_name = %s,bias = %s,destination = %s,display_name = %s,"
                "invite = %s, username = %s,api_id = %s,description = %s,"
                "rating = %s, detail_id = %s,is_active = %s where channel_id = %s;",
                (source.channel_name, source.bias, source.destination, source.display_name,
                 source.invite,
                 source.username, source.api_id, source.description, source.rating, source.detail_id, source.is_active,
                 source.channel_id))

            conn.commit()

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")

        pass


def get_destinations() -> Dict[int, str]:
    with conn.cursor() as c:
        c.execute("select * from destinations;")
        dests: [Destination] = c.fetchall()

        res = dict()
        d: Destination
        for d in dests:
            res[d.channel_id] = d.name
        logging.info(res)
        return res


def get_accounts() -> Dict[int, str]:
    with conn.cursor() as c:
        c.execute("select * from accounts;")
        accs: [Account] = c.fetchall()

        res = dict()
        a: Account
        for a in accs:
            res[a.api_id] = a.name
        logging.info(res)
        return res


def set_pattern(channel_id: int, pattern: str):
    try:
        with conn.cursor() as c:
            c.execute("INSERT INTO bloats(channel_id,pattern) VALUES (%s, %s)", (channel_id, pattern))
            conn.commit()
    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")
        pass


def get_footer_by_channel_id(channel_id: int) -> str:
    with conn.cursor() as c:
        c.execute("select footer from destinations where channel_id = %s;", [channel_id])
        res = c.fetchone()[0]
        logging.info(f"{channel_id} - footer: {res}")
    return res
