from __future__ import annotations

import base64
import json

import pytest
from fastapi import HTTPException

import app.security.easyauth as easyauth

from app.security.easyauth import (
    REVIEWER_ROLE,
    build_dev_principal,
    decode_client_principal,
    extract_actor_id,
    extract_roles,
)


def test_dev_principal_has_stable_actor_id():

    principal = build_dev_principal()

    actor_id = extract_actor_id(
        principal
    )

    assert (
        actor_id
        == "local-developer"
    )


def test_dev_reviewer_role_present_when_enabled(
    monkeypatch,
):

    # Make this test independent of the developer's
    # current PowerShell environment.
    monkeypatch.setattr(
        easyauth,
        "DEV_REVIEWER",
        True,
    )

    principal = build_dev_principal()

    roles = extract_roles(
        principal
    )

    assert (
        REVIEWER_ROLE
        in roles
    )


def test_decode_azure_style_principal():

    principal = {
        "auth_typ": "aad",
        "name_typ": "name",
        "role_typ": "roles",
        "claims": [
            {
                "typ": "oid",
                "val": "user-object-id-123",
            },
            {
                "typ": "name",
                "val": "Test User",
            },
            {
                "typ": "roles",
                "val": REVIEWER_ROLE,
            },
        ],
    }

    encoded = (
        base64.b64encode(
            json.dumps(
                principal
            ).encode(
                "utf-8"
            )
        )
        .decode(
            "utf-8"
        )
    )

    decoded = decode_client_principal(
        encoded
    )

    assert (
        extract_actor_id(
            decoded
        )
        == "user-object-id-123"
    )

    assert (
        REVIEWER_ROLE
        in extract_roles(
            decoded
        )
    )


def test_invalid_principal_rejected():

    with pytest.raises(
        HTTPException
    ):

        decode_client_principal(
            "not-valid-base64-json"
        )