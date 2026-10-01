from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException

from app.security.easyauth import (
    REVIEWER_ROLE,
)


DB_PATH = Path(
    "data/security/thread_access.db"
)


def _connect(
) -> sqlite3.Connection:

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
    )

    connection.row_factory = (
        sqlite3.Row
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS thread_ownership
        (
            thread_id TEXT PRIMARY KEY,
            owner_actor_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()

    return connection


def register_thread_owner(
    *,
    thread_id: str,
    actor_id: str,
) -> None:

    created_at = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    with _connect() as connection:

        connection.execute(
            """
            INSERT INTO thread_ownership
            (
                thread_id,
                owner_actor_id,
                created_at
            )
            VALUES
            (
                ?,
                ?,
                ?
            )
            """,
            (
                thread_id,
                actor_id,
                created_at,
            ),
        )

        connection.commit()


def delete_thread_owner(
    *,
    thread_id: str,
) -> None:

    with _connect() as connection:

        connection.execute(
            """
            DELETE FROM thread_ownership
            WHERE thread_id = ?
            """,
            (
                thread_id,
            ),
        )

        connection.commit()


def get_thread_owner(
    *,
    thread_id: str,
) -> str | None:

    with _connect() as connection:

        row = connection.execute(
            """
            SELECT
                owner_actor_id
            FROM thread_ownership
            WHERE thread_id = ?
            """,
            (
                thread_id,
            ),
        ).fetchone()

    if row is None:
        return None

    return str(
        row[
            "owner_actor_id"
        ]
    )


def require_thread_read_access(
    *,
    thread_id: str,
    actor_id: str,
    actor_roles: set[str],
) -> None:

    owner = get_thread_owner(
        thread_id=thread_id
    )

    if owner is None:

        raise HTTPException(
            status_code=404,
            detail={
                "thread_id": (
                    thread_id
                ),
                "error": (
                    "thread_not_found"
                ),
            },
        )

    if (
        actor_id == owner
    ):
        return

    if (
        REVIEWER_ROLE
        in actor_roles
    ):
        return

    raise HTTPException(
        status_code=403,
        detail={
            "thread_id": (
                thread_id
            ),
            "error": (
                "thread_access_denied"
            ),
        },
    )


def require_thread_review_access(
    *,
    thread_id: str,
    actor_roles: set[str],
) -> None:

    owner = get_thread_owner(
        thread_id=thread_id
    )

    if owner is None:

        raise HTTPException(
            status_code=404,
            detail={
                "thread_id": (
                    thread_id
                ),
                "error": (
                    "thread_not_found"
                ),
            },
        )

    if (
        REVIEWER_ROLE
        not in actor_roles
    ):

        raise HTTPException(
            status_code=403,
            detail={
                "thread_id": (
                    thread_id
                ),
                "error": (
                    "reviewer_role_required"
                ),
            },
        )