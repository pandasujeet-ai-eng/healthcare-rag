from __future__ import annotations

import os
import sqlite3

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(
    "data/reviews/careguard_review_queue.db"
)


def _utc_now() -> str:

    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


class ReviewQueueStore:

    def __init__(
        self,
        db_path: str | Path,
    ) -> None:

        self.db_path = Path(
            db_path
        )

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()


    def _connect(
        self,
    ) -> sqlite3.Connection:

        connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection


    def _initialize(
        self,
    ) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS review_queue (
                    thread_id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    risk_level TEXT,
                    risk_reason TEXT,
                    evidence_strength TEXT,
                    requested_by TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    decision TEXT,
                    reviewer_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    reviewed_at TEXT
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_review_queue_status
                ON review_queue(status)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_review_queue_created_at
                ON review_queue(created_at)
                """
            )

            connection.commit()


    @staticmethod
    def _row_to_dict(
        row: sqlite3.Row | None,
    ) -> dict[str, Any] | None:

        if row is None:

            return None

        return dict(
            row
        )


    def register_review(
        self,
        *,
        thread_id: str,
        question: str,
        risk_level: str | None,
        risk_reason: str | None,
        evidence_strength: str | None,
        requested_by: str | None,
    ) -> dict[str, Any]:

        now = _utc_now()

        with self._connect() as connection:

            existing = connection.execute(
                """
                SELECT *
                FROM review_queue
                WHERE thread_id = ?
                """,
                (
                    thread_id,
                ),
            ).fetchone()

            if existing is None:

                connection.execute(
                    """
                    INSERT INTO review_queue (
                        thread_id,
                        question,
                        risk_level,
                        risk_reason,
                        evidence_strength,
                        requested_by,
                        status,
                        decision,
                        reviewer_id,
                        created_at,
                        updated_at,
                        reviewed_at
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?,
                        'pending',
                        NULL,
                        NULL,
                        ?,
                        ?,
                        NULL
                    )
                    """,
                    (
                        thread_id,
                        question,
                        risk_level,
                        risk_reason,
                        evidence_strength,
                        requested_by,
                        now,
                        now,
                    ),
                )

            else:

                connection.execute(
                    """
                    UPDATE review_queue
                    SET
                        question = ?,
                        risk_level = ?,
                        risk_reason = ?,
                        evidence_strength = ?,
                        requested_by = ?,
                        updated_at = ?
                    WHERE thread_id = ?
                    """,
                    (
                        question,
                        risk_level,
                        risk_reason,
                        evidence_strength,
                        requested_by,
                        now,
                        thread_id,
                    ),
                )

            connection.commit()

            row = connection.execute(
                """
                SELECT *
                FROM review_queue
                WHERE thread_id = ?
                """,
                (
                    thread_id,
                ),
            ).fetchone()

        result = self._row_to_dict(
            row
        )

        if result is None:

            raise RuntimeError(
                "Review could not be registered."
            )

        return result


    def get_review(
        self,
        thread_id: str,
    ) -> dict[str, Any] | None:

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT *
                FROM review_queue
                WHERE thread_id = ?
                """,
                (
                    thread_id,
                ),
            ).fetchone()

        return self._row_to_dict(
            row
        )


    def list_reviews(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:

        safe_limit = max(
            1,
            min(
                limit,
                500,
            ),
        )

        with self._connect() as connection:

            if status:

                rows = connection.execute(
                    """
                    SELECT *
                    FROM review_queue
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (
                        status,
                        safe_limit,
                    ),
                ).fetchall()

            else:

                rows = connection.execute(
                    """
                    SELECT *
                    FROM review_queue
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (
                        safe_limit,
                    ),
                ).fetchall()

        return [
            dict(
                row
            )
            for row in rows
        ]


    def complete_review(
        self,
        *,
        thread_id: str,
        approved: bool,
        reviewer_id: str,
    ) -> dict[str, Any]:

        now = _utc_now()

        decision = (
            "approved"
            if approved
            else "rejected"
        )

        with self._connect() as connection:

            existing = connection.execute(
                """
                SELECT *
                FROM review_queue
                WHERE thread_id = ?
                """,
                (
                    thread_id,
                ),
            ).fetchone()

            if existing is None:

                raise KeyError(
                    thread_id
                )

            connection.execute(
                """
                UPDATE review_queue
                SET
                    status = ?,
                    decision = ?,
                    reviewer_id = ?,
                    reviewed_at = ?,
                    updated_at = ?
                WHERE thread_id = ?
                """,
                (
                    decision,
                    decision,
                    reviewer_id,
                    now,
                    now,
                    thread_id,
                ),
            )

            connection.commit()

            row = connection.execute(
                """
                SELECT *
                FROM review_queue
                WHERE thread_id = ?
                """,
                (
                    thread_id,
                ),
            ).fetchone()

        result = self._row_to_dict(
            row
        )

        if result is None:

            raise RuntimeError(
                "Review decision could not be saved."
            )

        return result


    def stats(
        self,
    ) -> dict[str, int]:

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT
                    status,
                    COUNT(*) AS total
                FROM review_queue
                GROUP BY status
                """
            ).fetchall()

        counts = {
            "pending": 0,
            "approved": 0,
            "rejected": 0,
        }

        for row in rows:

            status = row[
                "status"
            ]

            counts[
                status
            ] = row[
                "total"
            ]

        counts[
            "total"
        ] = sum(
            value
            for key, value
            in counts.items()
            if key != "total"
        )

        return counts


def get_review_queue_store() -> ReviewQueueStore:

    configured_path = os.getenv(
        "CAREGUARD_REVIEW_DB"
    )

    db_path = (
        Path(
            configured_path
        )
        if configured_path
        else DEFAULT_DB_PATH
    )

    return ReviewQueueStore(
        db_path
    )