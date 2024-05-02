import inspect
import logging
from contextlib import asynccontextmanager
from traceback import format_exc
from typing import Optional, Dict, AsyncGenerator

from aiopg import create_pool
from psycopg2 import OperationalError
from psycopg2.extras import NamedTupleCursor

from config import DATABASE_URL
from data.model import Source, SourceInsert, Destination, Account


@asynccontextmanager
async def db_cursor() -> AsyncGenerator:
    try:
        async with create_pool(DATABASE_URL) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
                    yield cursor
    except OperationalError as err:
        logging.error(
            f"{inspect.currentframe().f_code.co_name} — DB-Operation failed!\npgerror: {err.pgerror} -- pgcode: {err.pgcode}\nextensions.Diagnostics: {err.diag}", )
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")


async def get_source(channel_id: int) -> Optional[Source]:
    async with db_cursor() as c:
        c.execute("select * from sources where channel_id = %s;",
                  [channel_id])
        res: Source = c.fetchone()
        logging.info(res)

        return res


async def get_destination_ids() -> [int]:
    async with db_cursor() as c:
        c.execute("select channel_id from destinations;")
        res: [int] = [item.channel_id for item in c.fetchall()]
        logging.info(f"destination ids: {res}")

        return res


async def set_source(source: SourceInsert):
    async with db_cursor() as c:
        c.execute(
            "INSERT INTO sources(channel_id,channel_name,display_name,bias,invite,username) VALUES (%s, %s,%s,%s,%s,%s)",
            (source.channel_id, source.channel_name, source.display_name, source.bias, source.invite,
             source.username))


async def update_source(source: Source):
    async with db_cursor() as c:
        c.execute(
            "UPDATE sources set channel_name = %s,bias = %s,destination = %s,display_name = %s,"
            "invite = %s, username = %s,api_id = %s,description = %s,"
            "rating = %s, detail_id = %s,is_active = %s where channel_id = %s;",
            (source.channel_name, source.bias, source.destination, source.display_name,
             source.invite,
             source.username, source.api_id, source.description, source.rating, source.detail_id, source.is_active,
             source.channel_id))


async def get_destinations() -> Dict[int, str]:
    async with db_cursor() as c:
        c.execute("select * from destinations;")
        dests: [Destination] = c.fetchall()

        res = dict()
        d: Destination
        for d in dests:
            res[d.channel_id] = d.name

        logging.info(res)

        return res


async def get_accounts() -> Dict[int, str]:
    async with db_cursor() as c:
        c.execute("select * from accounts;")
        accs: [Account] = c.fetchall()

        res = dict()
        a: Account
        for a in accs:
            res[a.api_id] = a.name

        logging.info(res)

        return res


async def set_pattern(channel_id: int, pattern: str):
    async with db_cursor() as c:
        c.execute("INSERT INTO bloats(channel_id,pattern) VALUES (%s, %s)", (channel_id, pattern))


async def get_footer_by_channel_id(channel_id: int) -> str:
    async with db_cursor() as c:
        c.execute("select footer from destinations where channel_id = %s;", [channel_id])
        res = c.fetchone()[0]
        logging.info(f"{channel_id} - footer: {res}")

        return res
