import logging
from traceback import format_exc
from typing import Optional, Dict

import psycopg2
from psycopg2.extras import NamedTupleCursor

from config import DATABASE_URL
from data.model import Source, SourceInsert, Account

conn = psycopg2.connect(DATABASE_URL, cursor_factory=NamedTupleCursor)


def execute_db_operation(query: str, params: tuple = (), fetch: str = None):
    try:
        with conn.cursor() as c:
            c.execute(query, params)
            if fetch == "one":
                return c.fetchone()
            elif fetch == "all":
                return c.fetchall()
            conn.commit()
    except Exception as e:
        logging.error(f"DB-Operation failed {repr(e)} - {format_exc()}")


def get_source(channel_id: int) -> Optional[Source]:
    res = execute_db_operation("select * from sources where channel_id = %s;", (channel_id,), "one")
    logging.info(res)
    return res


def get_destination_ids() -> [int]:
    res = execute_db_operation("select channel_id from destinations;", fetch="all")
    ids = [item.channel_id for item in res]
    logging.info(f"destination ids: {ids}")
    return ids


def set_source(source: SourceInsert):
    execute_db_operation(
        "INSERT INTO sources(channel_id,api_id,channel_name,display_name,bias,invite,username) VALUES (%s,%s, %s,%s,%s,%s,%s)",
        (source.channel_id, source.channel_name, source.display_name, source.bias, source.invite, source.username))


def update_source(source: Source):
    execute_db_operation(
        "UPDATE sources set channel_name = %s,bias = %s,destination = %s,display_name = %s,"
        "invite = %s, username = %s,api_id = %s,description = %s,"
        "rating = %s, detail_id = %s,is_active = %s where channel_id = %s;",
        (source.channel_name, source.bias, source.destination, source.display_name, source.invite,
         source.username, source.api_id, source.description, source.rating, source.detail_id, source.is_active,
         source.channel_id))


def get_destinations() -> Dict[int, str]:
    dests = execute_db_operation("select * from destinations;", fetch="all")
    return {d.channel_id: d.name for d in dests}


def get_accounts() -> Dict[int, Account]:
    accs = execute_db_operation("select * from accounts;", fetch="all")
    return {a.api_id: a for a in accs}




def set_pattern(channel_id: int, pattern: str):
    execute_db_operation("INSERT INTO bloats(channel_id,pattern) VALUES (%s, %s)", (channel_id, pattern))


def get_footer_by_channel_id(channel_id: int) -> str:
    res = execute_db_operation("select footer from destinations where channel_id = %s;", (channel_id,), "one")
    logging.info(f"{channel_id} - footer: {res}")
    return res[0] if res else None

def get_free_account_id ()-> Account:
    res = execute_db_operation("SELECT * FROM Account WHERE user_id IN (    SELECT account_id    FROM Source    GROUP BY account_id    HAVING COUNT(*) < 450);", fetch="one")
    logging.info(f"free account id: {res}")
    return res[0]