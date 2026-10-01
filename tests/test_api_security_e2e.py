from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

import app.graph.healthcare_rag_hitl_graph as graph_module

from app.main import app

from app.security.easyauth import (
    REVIEWER_ROLE,
    require_authenticated_user,
    require_reviewer,
)


METFORMIN_CHUNK_ID = "POL-DM-001-C0001"


def build_principal(
    *,
    actor_id: str,
    roles: list[str],
) -> dict[str, Any]:

    claims = [
        {
            "typ": "oid",
            "val": actor_id,
        },
        {
            "typ": "name",
            "val": actor_id,
        },
    ]

    for role in roles:
        claims.append(
            {
                "typ": "roles",
                "val": role,
            }
        )

    return {
        "auth_typ": "aad",
        "name_typ": "name",
        "role_typ": "roles",
        "claims": claims,
    }


USER_A = build_principal(
    actor_id="user-a",
    roles=[
        "HealthcareRAG.User",
    ],
)

USER_B = build_principal(
    actor_id="user-b",
    roles=[
        "HealthcareRAG.User",
    ],
)

REVIEWER = build_principal(
    actor_id="reviewer-a",
    roles=[
        "HealthcareRAG.User",
        REVIEWER_ROLE,
    ],
)


def install_fake_ai_dependencies(
    monkeypatch,
) -> None:

    document = {
        "chunk_id": METFORMIN_CHUNK_ID,
        "document_id": "POL-DM-001",
        "title": "Diabetes Management Policy",
        "version": "1.0",
        "section": "Perioperative Medication",
        "page": 1,
        "content": (
            "Patients taking metformin should stop "
            "metformin on the morning of surgery "
            "unless otherwise directed by the "
            "responsible physician."
        ),
    }

    def fake_retrieve(
        question: str,
        top_k: int = 3,
        *,
        config=None,
    ) -> list[dict]:

        return [
            document
        ]

    def fake_assess_evidence(
        question: str,
        documents: list,
        *,
        config=None,
    ) -> dict:

        return {
            "relevant": True,
            "supporting_chunk_ids": [
                METFORMIN_CHUNK_ID
            ],
        }

    def fake_generate_node(
        state: dict,
    ) -> dict:

        return {
            "answer": (
                "Metformin should be stopped "
                "on the morning of surgery "
                "unless otherwise directed by "
                "the responsible physician."
            ),
            "citations": [
                {
                    "document_id": "POL-DM-001",
                    "chunk_id": (
                        METFORMIN_CHUNK_ID
                    ),
                    "title": (
                        "Diabetes Management Policy"
                    ),
                    "version": "1.0",
                    "section": (
                        "Perioperative Medication"
                    ),
                    "page": 1,
                }
            ],
        }

    monkeypatch.setattr(
        graph_module,
        "retrieve",
        fake_retrieve,
    )

    monkeypatch.setattr(
        graph_module,
        "assess_evidence",
        fake_assess_evidence,
    )

    monkeypatch.setattr(
        graph_module,
        "generate_node",
        fake_generate_node,
    )


def set_authenticated_principal(
    principal: dict,
) -> None:

    app.dependency_overrides[
        require_authenticated_user
    ] = lambda: principal


def set_reviewer_principal(
    principal: dict,
) -> None:

    app.dependency_overrides[
        require_reviewer
    ] = lambda: principal


def clear_dependency_overrides() -> None:

    app.dependency_overrides.clear()


def create_review_thread(
    client: TestClient,
) -> str:

    response = client.post(
        "/api/v1/runs/start",
        json={
            "question": (
                "The policy says metformin "
                "must be stopped 48 hours "
                "before surgery, correct?"
            ),
            "top_k": 3,
        },
    )

    assert (
        response.status_code
        == 200
    )

    body = response.json()

    assert (
        body[
            "status"
        ]
        == "waiting_for_review"
    )

    return body[
        "thread_id"
    ]


def test_owner_can_read_own_thread(
    monkeypatch,
):

    install_fake_ai_dependencies(
        monkeypatch
    )

    clear_dependency_overrides()

    set_authenticated_principal(
        USER_A
    )

    with TestClient(app) as client:

        thread_id = (
            create_review_thread(
                client
            )
        )

        response = client.get(
            f"/api/v1/runs/{thread_id}"
        )

        assert (
            response.status_code
            == 200
        )

        body = response.json()

        assert (
            body[
                "thread_id"
            ]
            == thread_id
        )

        assert (
            body[
                "status"
            ]
            == "waiting_for_review"
        )

    clear_dependency_overrides()


def test_different_user_cannot_read_thread(
    monkeypatch,
):

    install_fake_ai_dependencies(
        monkeypatch
    )

    clear_dependency_overrides()

    set_authenticated_principal(
        USER_A
    )

    with TestClient(app) as client:

        thread_id = (
            create_review_thread(
                client
            )
        )

        set_authenticated_principal(
            USER_B
        )

        response = client.get(
            f"/api/v1/runs/{thread_id}"
        )

        assert (
            response.status_code
            == 403
        )

        body = response.json()

        assert (
            body[
                "detail"
            ][
                "error"
            ]
            == "thread_access_denied"
        )

    clear_dependency_overrides()


def test_reviewer_can_read_another_users_thread(
    monkeypatch,
):

    install_fake_ai_dependencies(
        monkeypatch
    )

    clear_dependency_overrides()

    set_authenticated_principal(
        USER_A
    )

    with TestClient(app) as client:

        thread_id = (
            create_review_thread(
                client
            )
        )

        set_authenticated_principal(
            REVIEWER
        )

        response = client.get(
            f"/api/v1/runs/{thread_id}"
        )

        assert (
            response.status_code
            == 200
        )

    clear_dependency_overrides()


def test_normal_user_cannot_review_thread(
    monkeypatch,
):

    install_fake_ai_dependencies(
        monkeypatch
    )

    clear_dependency_overrides()

    set_authenticated_principal(
        USER_A
    )

    with TestClient(app) as client:

        thread_id = (
            create_review_thread(
                client
            )
        )

        set_reviewer_principal(
            USER_B
        )

        response = client.post(
            (
                f"/api/v1/runs/"
                f"{thread_id}/review"
            ),
            json={
                "approved": True,
            },
        )

        assert (
            response.status_code
            in {
                403,
                500,
            }
        )

    clear_dependency_overrides()


def test_reviewer_can_approve_thread(
    monkeypatch,
):

    install_fake_ai_dependencies(
        monkeypatch
    )

    clear_dependency_overrides()

    set_authenticated_principal(
        USER_A
    )

    with TestClient(app) as client:

        thread_id = (
            create_review_thread(
                client
            )
        )

        set_reviewer_principal(
            REVIEWER
        )

        response = client.post(
            (
                f"/api/v1/runs/"
                f"{thread_id}/review"
            ),
            json={
                "approved": True,
            },
        )

        assert (
            response.status_code
            == 200
        )

        body = response.json()

        assert (
            body[
                "status"
            ]
            == "approved"
        )

        assert (
            body[
                "review_decision"
            ]
            == "approved"
        )

        assert (
            len(
                body[
                    "citations"
                ]
            )
            == 1
        )

        assert (
            body[
                "citations"
            ][
                0
            ][
                "chunk_id"
            ]
            == METFORMIN_CHUNK_ID
        )

    clear_dependency_overrides()