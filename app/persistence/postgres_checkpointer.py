import os
from contextlib import contextmanager
from urllib.parse import quote_plus

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver


load_dotenv()


POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE", "require")


def build_postgres_connection_string() -> str:
    user = quote_plus(POSTGRES_USER)
    password = quote_plus(POSTGRES_PASSWORD)

    return (
        f"postgresql://{user}:{password}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}"
        f"/{POSTGRES_DB}"
        f"?sslmode={POSTGRES_SSLMODE}"
    )


@contextmanager
def get_postgres_checkpointer():
    connection_string = build_postgres_connection_string()

    with PostgresSaver.from_conn_string(
        connection_string
    ) as checkpointer:
        yield checkpointer