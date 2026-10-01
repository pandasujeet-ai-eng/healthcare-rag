import os
from contextlib import contextmanager

from dotenv import load_dotenv

from app.persistence.sqlite_checkpointer import (
    get_sqlite_checkpointer,
)


load_dotenv()


CHECKPOINT_BACKEND = os.getenv(
    "CHECKPOINT_BACKEND",
    "sqlite",
).strip().lower()


@contextmanager
def get_checkpointer():

    if CHECKPOINT_BACKEND == "sqlite":

        with get_sqlite_checkpointer() as checkpointer:
            yield checkpointer

        return

    if CHECKPOINT_BACKEND == "postgres":

        from app.persistence.postgres_checkpointer import (
            get_postgres_checkpointer,
        )

        with get_postgres_checkpointer() as checkpointer:
            yield checkpointer

        return

    raise RuntimeError(
        f"Unsupported CHECKPOINT_BACKEND: "
        f"{CHECKPOINT_BACKEND}"
    )