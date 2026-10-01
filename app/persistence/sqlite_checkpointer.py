import sqlite3
from contextlib import contextmanager
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


DB_PATH = Path(
    "data/checkpoints/langgraph_checkpoints.db"
)


@contextmanager
def get_sqlite_checkpointer():

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
    )

    try:
        checkpointer = SqliteSaver(
            connection
        )

        yield checkpointer

    finally:
        connection.close()