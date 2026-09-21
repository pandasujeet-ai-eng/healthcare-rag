import base64
import json
from typing import Any

from fastapi import Header, HTTPException


REVIEWER_ROLE = "HealthcareRAG.Reviewer"


def decode_client_principal(
    encoded_principal: str,
) -> dict[str, Any]:
    try:
        decoded_bytes = base64.b64decode(
            encoded_principal
        )

        decoded_json = decoded_bytes.decode(
            "utf-8"
        )

        return json.loads(
            decoded_json
        )

    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication principal.",
        ) from exc


def get_claim_values(
    principal: dict[str, Any],
    claim_types: set[str],
) -> list[str]:
    values: list[str] = []

    for claim in principal.get(
        "claims",
        [],
    ):
        claim_type = str(
            claim.get(
                "typ",
                "",
            )
        )

        claim_value = claim.get(
            "val"
        )

        if (
            claim_type in claim_types
            and claim_value is not None
        ):
            values.append(
                str(claim_value)
            )

    return values


def require_authenticated_user(
    x_ms_client_principal: str | None = Header(
        default=None,
        alias="X-MS-CLIENT-PRINCIPAL",
    ),
) -> dict[str, Any]:

    if not x_ms_client_principal:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    principal = decode_client_principal(
        x_ms_client_principal
    )

    auth_type = principal.get(
        "auth_typ"
    )

    if not auth_type:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    return principal


def extract_roles(
    principal: dict[str, Any],
) -> set[str]:

    role_claim_type = str(
        principal.get(
            "role_typ",
            "roles",
        )
    )

    role_claims = {
        "roles",
        role_claim_type,
        "http://schemas.microsoft.com/ws/2008/06/identity/claims/role",
    }

    return set(
        get_claim_values(
            principal,
            role_claims,
        )
    )


def require_reviewer(
    x_ms_client_principal: str | None = Header(
        default=None,
        alias="X-MS-CLIENT-PRINCIPAL",
    ),
) -> dict[str, Any]:

    principal = require_authenticated_user(
        x_ms_client_principal
    )

    roles = extract_roles(
        principal
    )

    if REVIEWER_ROLE not in roles:
        raise HTTPException(
            status_code=403,
            detail=(
                "HealthcareRAG.Reviewer role required."
            ),
        )

    return principal