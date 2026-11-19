import os
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv


def get_database_url() -> str:
    """
    Read the PostgreSQL connection URL from the .env file
    or the environment.
    """

    load_dotenv()

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured. Add it to your .env file.")

    return database_url


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    """
    Create a PostgreSQL connection.

    The context manager automatically closes the connection.
    Successful operations are committed when the context exits.
    """

    with psycopg.connect(get_database_url()) as connection:
        yield connection
