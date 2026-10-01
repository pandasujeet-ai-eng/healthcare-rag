import base64
import json
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import Header, HTTPException


load_dotenv()


REVIEWER_ROLE = "HealthcareRAG.Reviewer"

AUTH_MODE = os.getenv(
    "AUTH_MODE",
    "azure",
).strip().lower()

DEV_REVIEWER = (
    os.getenv(
        "DEV_REVIEWER",
        "false",
    ).strip().lower()
    == "true"
)


def build_dev_principal() -> dict[str, Any]:

    roles = []

    if DEV_REVIEWER:
        roles.append(
            REVIEWER_ROLE
        )

    return {
        "auth_typ": "dev",
        "name_typ": "name",
        "role_typ": "roles",
        "claims": [
            {
                "typ": "name",
                "val": "local-developer",
            },
            *[
                {
                    "typ": "roles",
                    "val": role,
                }
                for role in roles
            ],
        ],
    }


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
            detail=(
                "Invalid authentication principal."
            ),
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
                str(
                    claim_value
                )
            )

    return values


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
        (
            "http://schemas.microsoft.com/"
            "ws/2008/06/identity/claims/role"
        ),
    }

    return set(
        get_claim_values(
            principal,
            role_claims,
        )
    )


def require_authenticated_user(
    x_ms_client_principal: str | None = Header(
        default=None,
        alias="X-MS-CLIENT-PRINCIPAL",
    ),
) -> dict[str, Any]:

    if AUTH_MODE == "dev":

        return build_dev_principal()

    if not x_ms_client_principal:

        raise HTTPException(
            status_code=401,
            detail=(
                "Authentication required."
            ),
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
            detail=(
                "Authentication required."
            ),
        )

    return principal


def require_reviewer(
    x_ms_client_principal: str | None = Header(
        default=None,
        alias="X-MS-CLIENT-PRINCIPAL",
    ),
) -> dict[str, Any]:

    principal = (
        require_authenticated_user(
            x_ms_client_principal
        )
    )

    roles = extract_roles(
        principal
    )

    if REVIEWER_ROLE not in roles:

        raise HTTPException(
            status_code=403,
            detail=(
                "HealthcareRAG.Reviewer "
                "role required."
            ),
        )

    return principal