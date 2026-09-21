from typing import Any

from fastapi import APIRouter, Depends

from app.security.easyauth import (
    extract_roles,
    get_claim_values,
    require_authenticated_user,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Security"],
)


@router.get(
    "/whoami",
)
def whoami(
    principal: dict[str, Any] = Depends(
        require_authenticated_user
    ),
) -> dict:

    name_claims = {
        "name",
        "preferred_username",
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
    }

    names = get_claim_values(
        principal,
        name_claims,
    )

    roles = sorted(
        extract_roles(
            principal
        )
    )

    return {
        "authenticated": True,
        "identity_provider": principal.get(
            "auth_typ"
        ),
        "user": (
            names[0]
            if names
            else None
        ),
        "roles": roles,
        "is_reviewer": (
            "HealthcareRAG.Reviewer"
            in roles
        ),
    }