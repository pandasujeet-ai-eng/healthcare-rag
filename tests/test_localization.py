from __future__ import annotations

import pytest

from fastapi.testclient import (
    TestClient,
)


def test_localization_route_exists(
    monkeypatch,
):

    monkeypatch.setenv(
        "APP_ENV",
        "test",
    )

    monkeypatch.setenv(
        "AUTH_MODE",
        "dev",
    )

    from app.main import app

    client = TestClient(
        app
    )

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
        body["translated_text"]
        == "POL-DM-001"
    )


def test_empty_translation_rejected(
    monkeypatch,
):

    monkeypatch.setenv(
        "APP_ENV",
        "test",
    )

    monkeypatch.setenv(
        "AUTH_MODE",
        "dev",
    )

    from app.main import app

    client = TestClient(
        app
    )

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


def test_invalid_language_rejected(
    monkeypatch,
):

    monkeypatch.setenv(
        "APP_ENV",
        "test",
    )

    monkeypatch.setenv(
        "AUTH_MODE",
        "dev",
    )

    from app.main import app

    client = TestClient(
        app
    )

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