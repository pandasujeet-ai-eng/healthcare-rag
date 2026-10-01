from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.security.easyauth import (
    REVIEWER_ROLE,
)

from app.security.thread_access import (
    delete_thread_owner,
    register_thread_owner,
    require_thread_read_access,
    require_thread_review_access,
)


def create_thread_id() -> str:

    return (
        "security-test-"
        + str(
            uuid.uuid4()
        )
    )


def test_owner_can_read_thread():

    thread_id = (
        create_thread_id()
    )

    try:

        register_thread_owner(
            thread_id=thread_id,
            actor_id="user-a",
        )

        require_thread_read_access(
            thread_id=thread_id,
            actor_id="user-a",
            actor_roles={
                "HealthcareRAG.User"
            },
        )

    finally:

        delete_thread_owner(
            thread_id=thread_id
        )


def test_other_normal_user_cannot_read_thread():

    thread_id = (
        create_thread_id()
    )

    try:

        register_thread_owner(
            thread_id=thread_id,
            actor_id="user-a",
        )

        with pytest.raises(
            HTTPException
        ) as exc_info:

            require_thread_read_access(
                thread_id=thread_id,
                actor_id="user-b",
                actor_roles={
                    "HealthcareRAG.User"
                },
            )

        assert (
            exc_info.value.status_code
            == 403
        )

    finally:

        delete_thread_owner(
            thread_id=thread_id
        )


def test_reviewer_can_read_thread():

    thread_id = (
        create_thread_id()
    )

    try:

        register_thread_owner(
            thread_id=thread_id,
            actor_id="user-a",
        )

        require_thread_read_access(
            thread_id=thread_id,
            actor_id="reviewer-a",
            actor_roles={
                REVIEWER_ROLE
            },
        )

    finally:

        delete_thread_owner(
            thread_id=thread_id
        )


def test_normal_user_cannot_review():

    thread_id = (
        create_thread_id()
    )

    try:

        register_thread_owner(
            thread_id=thread_id,
            actor_id="user-a",
        )

        with pytest.raises(
            HTTPException
        ) as exc_info:

            require_thread_review_access(
                thread_id=thread_id,
                actor_roles={
                    "HealthcareRAG.User"
                },
            )

        assert (
            exc_info.value.status_code
            == 403
        )

    finally:

        delete_thread_owner(
            thread_id=thread_id
        )


def test_reviewer_can_review():

    thread_id = (
        create_thread_id()
    )

    try:

        register_thread_owner(
            thread_id=thread_id,
            actor_id="user-a",
        )

        require_thread_review_access(
            thread_id=thread_id,
            actor_roles={
                REVIEWER_ROLE
            },
        )

    finally:

        delete_thread_owner(
            thread_id=thread_id
        )