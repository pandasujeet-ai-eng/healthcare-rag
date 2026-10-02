from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.security.easyauth import (
    require_authenticated_user,
)


# =====================================================================
# TEST IDENTITY
# =====================================================================


def _test_authenticated_user() -> dict:

    return {
        "authenticated": True,
        "identity_provider": "test",
        "actor_id": "test-user",
        "user": "test-user",
        "roles": [
            "HealthcareRAG.User",
        ],
        "is_reviewer": False,
    }


# =====================================================================
# HELPERS
# =====================================================================


def _create_client() -> TestClient:

    app.dependency_overrides[
        require_authenticated_user
    ] = _test_authenticated_user

    return TestClient(
        app
    )


def _clear_overrides() -> None:

    app.dependency_overrides.clear()


# =====================================================================
# TESTS
# =====================================================================


def test_localization_route_exists():

    client = _create_client()

    try:

        response = client.post(
            "/api/v1/localization/translate",
            json={
                "text":
                    "POL-DM-001",

                "target_language":
                    "en",
            },
        )

        assert (
            response.status_code
            == 200
        )

        body = response.json()

        assert (
            body["source_text"]
            == "POL-DM-001"
        )

        assert (
            body["translated_text"]
            == "POL-DM-001"
        )

        assert (
            body["target_language"]
            == "en"
        )

    finally:

        _clear_overrides()


def test_empty_translation_rejected():

    client = _create_client()

    try:

        response = client.post(
            "/api/v1/localization/translate",
            json={
                "text":
                    "",

                "target_language":
                    "ar",
            },
        )

        assert (
            response.status_code
            == 422
        )

    finally:

        _clear_overrides()


def test_invalid_language_rejected():

    client = _create_client()

    try:

        response = client.post(
            "/api/v1/localization/translate",
            json={
                "text":
                    "test",

                "target_language":
                    "fr",
            },
        )

        assert (
            response.status_code
            == 422
        )

    finally:

        _clear_overrides()