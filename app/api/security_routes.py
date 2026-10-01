from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
)

from app.security.easyauth import (
    REVIEWER_ROLE,
    extract_actor_id,
    extract_actor_name,
    extract_roles,
    require_authenticated_user,
)


router = APIRouter(
    prefix="/api/v1",
    tags=[
        "Security"
    ],
)


@router.get(
    "/whoami"
)
def whoami(
    principal: dict[str, Any] = Depends(
        require_authenticated_user
    ),
) -> dict:

    actor_id = (
        extract_actor_id(
            principal
        )
    )

    actor_name = (
        extract_actor_name(
            principal
        )
    )

    roles = sorted(
        extract_roles(
            principal
        )
    )

    return {
        "authenticated": True,
        "identity_provider": (
            principal.get(
                "auth_typ"
            )
        ),
        "actor_id": actor_id,
        "user": actor_name,
        "roles": roles,
        "is_reviewer": (
            REVIEWER_ROLE
            in roles
        ),
    }