import logging
from traceback import format_exc
from typing import Optional, Dict, List
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import NamedTupleCursor
from psycopg2 import pool

from bot.data.model import Source, SourceInsert, Account
from bot.settings.config import DATABASE_URL

# Use connection pooling instead of a single connection
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 10,
    DATABASE_URL,
    cursor_factory=NamedTupleCursor
)


@contextmanager
def get_db_connection():
    """Context manager for database connections with proper cleanup"""
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
    except psycopg2.OperationalError as e:
        logging.error(f"Database connection error: {repr(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)


def execute_db_operation(query: str, params: tuple = (), fetch: str = None):
    """Execute database operation with automatic retry on connection failure"""
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            with get_db_connection() as conn:
                with conn.cursor() as c:
                    c.execute(query, params)
                    if fetch == "one":
                        result = c.fetchone()
                    elif fetch == "all":
                        result = c.fetchall()
                    else:
                        result = None
                    conn.commit()
                    return result
        except psycopg2.OperationalError as e:
            retry_count += 1
            logging.warning(f"DB operation failed (attempt {retry_count}/{max_retries}): {repr(e)}")
            if retry_count >= max_retries:
                logging.error(f"DB-Operation failed after {max_retries} retries: {repr(e)} - {format_exc()}")
                return None
        except Exception as e:
            logging.error(f"DB-Operation failed {repr(e)} - {format_exc()}")
            return None


def get_source(channel_id: int) -> Optional[Source]:
    res = execute_db_operation("select * from sources where channel_id = %s;", (channel_id,), "one")
    logging.info(res)
    return res


def get_destination_ids() -> List[int]:
    res = execute_db_operation("select channel_id from destinations;", fetch="all")
    if res is None:
        logging.error("Failed to fetch destination IDs")
        return []
    ids = [item.channel_id for item in res]
    logging.info(f"destination ids: {ids}")
    return ids


def set_source(source: SourceInsert):
    execute_db_operation(
        "INSERT INTO sources(channel_id,api_id,channel_name,display_name,bias,invite,username) VALUES (%s,%s, %s,%s,%s,%s,%s)",
        (source.channel_id, source.api_id, source.channel_name, source.display_name, source.bias, source.invite,
         source.username))


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
    if dests is None:
        return {}
    return {d.channel_id: d.name for d in dests}


def get_accounts() -> Dict[int, Account]:
    accs = execute_db_operation("select * from accounts;", fetch="all")
    if accs is None:
        return {}
    return {a.api_id: a for a in accs}


def set_pattern(channel_id: int, pattern: str):
    execute_db_operation("INSERT INTO bloats(channel_id,pattern) VALUES (%s, %s)", (channel_id, pattern))


def get_footer_by_channel_id(channel_id: int) -> str:
    res = execute_db_operation("select footer from destinations where channel_id = %s;", (channel_id,), "one")
    logging.info(f"{channel_id} - footer: {res}")
    return res[0] if res else None


def get_free_account_id() -> Optional[Account]:
    """Get a free account with availability check"""
    res = execute_db_operation(
        "SELECT * FROM accounts WHERE api_id IN ("
        "    SELECT api_id FROM sources GROUP BY api_id HAVING COUNT(*) < 450"
        ") LIMIT 1;",
        fetch="one")

    if res is None:
        logging.warning("No free account available - all accounts may be at capacity")
    else:
        logging.info(f"free account id: {res}")

    return res