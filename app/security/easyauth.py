from __future__ import annotations

import base64
import json
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import Header, HTTPException


load_dotenv()


REVIEWER_ROLE = "HealthcareRAG.Reviewer"

USER_ROLE = "HealthcareRAG.User"


AUTH_MODE = os.getenv(
    "AUTH_MODE",
    "azure",
).strip().lower()


APP_ENV = os.getenv(
    "APP_ENV",
    "production",
).strip().lower()


DEV_REVIEWER = (
    os.getenv(
        "DEV_REVIEWER",
        "false",
    ).strip().lower()
    == "true"
)


ALLOWED_AUTH_MODES = {
    "azure",
    "dev",
}


DEV_ALLOWED_ENVIRONMENTS = {
    "development",
    "test",
}


# =====================================================================
# STARTUP SAFETY
# =====================================================================


if AUTH_MODE not in ALLOWED_AUTH_MODES:

    raise RuntimeError(
        f"Unsupported AUTH_MODE: {AUTH_MODE}"
    )


if (
    AUTH_MODE == "dev"
    and APP_ENV
    not in DEV_ALLOWED_ENVIRONMENTS
):

    raise RuntimeError(
        "AUTH_MODE=dev is only allowed when "
        "APP_ENV=development or APP_ENV=test. "
        "Refusing to start insecure DEV authentication."
    )


# =====================================================================
# DEV PRINCIPAL
# =====================================================================


def build_dev_principal(
) -> dict[str, Any]:

    roles = [
        USER_ROLE,
    ]

    if DEV_REVIEWER:

        roles.append(
            REVIEWER_ROLE
        )

    claims = [
        {
            "typ": "oid",
            "val": "local-developer",
        },
        {
            "typ": "name",
            "val": "local-developer",
        },
        {
            "typ": "preferred_username",
            "val": "local-developer",
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
        "auth_typ": "dev",
        "name_typ": "name",
        "role_typ": "roles",
        "claims": claims,
    }


# =====================================================================
# PRINCIPAL DECODING
# =====================================================================


def decode_client_principal(
    encoded_principal: str,
) -> dict[str, Any]:

    try:

        padded = (
            encoded_principal
            + "="
            * (
                (
                    4
                    - len(
                        encoded_principal
                    )
                    % 4
                )
                % 4
            )
        )

        decoded_bytes = (
            base64.b64decode(
                padded
            )
        )

        decoded_text = (
            decoded_bytes.decode(
                "utf-8"
            )
        )

        principal = json.loads(
            decoded_text
        )

        if not isinstance(
            principal,
            dict,
        ):

            raise ValueError(
                "Principal payload is not an object."
            )

        return principal

    except Exception as exc:

        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid authentication principal."
            ),
        ) from exc


# =====================================================================
# CLAIM HELPERS
# =====================================================================


def get_claim_values(
    principal: dict[str, Any],
    claim_types: set[str],
) -> list[str]:

    values: list[str] = []

    claims = principal.get(
        "claims",
        [],
    )

    if not isinstance(
        claims,
        list,
    ):
        return values

    for claim in claims:

        if not isinstance(
            claim,
            dict,
        ):
            continue

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
            claim_type
            in claim_types
            and claim_value
            is not None
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

    role_claim_types = {
        "roles",
        "role",
        role_claim_type,
        (
            "http://schemas.microsoft.com/"
            "ws/2008/06/identity/claims/role"
        ),
    }

    return set(
        get_claim_values(
            principal,
            role_claim_types,
        )
    )


# =====================================================================
# TRUSTED ACTOR ID
# =====================================================================


def extract_actor_id(
    principal: dict[str, Any],
) -> str:

    stable_id_claims = {
        "oid",
        "objectidentifier",
        "http://schemas.microsoft.com/identity/claims/objectidentifier",
        (
            "http://schemas.xmlsoap.org/"
            "ws/2005/05/identity/claims/"
            "nameidentifier"
        ),
        "sub",
    }

    actor_ids = get_claim_values(
        principal,
        stable_id_claims,
    )

    if actor_ids:

        return actor_ids[
            0
        ]

    fallback_claims = {
        "preferred_username",
        "name",
        (
            "http://schemas.xmlsoap.org/"
            "ws/2005/05/identity/claims/name"
        ),
        (
            "http://schemas.xmlsoap.org/"
            "ws/2005/05/identity/claims/"
            "emailaddress"
        ),
    }

    fallback_values = (
        get_claim_values(
            principal,
            fallback_claims,
        )
    )

    if fallback_values:

        return fallback_values[
            0
        ]

    raise HTTPException(
        status_code=401,
        detail=(
            "Authenticated identity does not "
            "contain a usable actor identifier."
        ),
    )


def extract_actor_name(
    principal: dict[str, Any],
) -> str | None:

    names = get_claim_values(
        principal,
        {
            "preferred_username",
            "name",
            (
                "http://schemas.xmlsoap.org/"
                "ws/2005/05/identity/claims/name"
            ),
            (
                "http://schemas.xmlsoap.org/"
                "ws/2005/05/identity/claims/"
                "emailaddress"
            ),
        },
    )

    if not names:
        return None

    return names[
        0
    ]


# =====================================================================
# AUTHENTICATION DEPENDENCIES
# =====================================================================


def require_authenticated_user(
    x_ms_client_principal: str | None = Header(
        default=None,
        alias=(
            "X-MS-CLIENT-PRINCIPAL"
        ),
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

    principal = (
        decode_client_principal(
            x_ms_client_principal
        )
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

    # Validate that we can derive a stable identity.
    extract_actor_id(
        principal
    )

    return principal


def require_reviewer(
    x_ms_client_principal: str | None = Header(
        default=None,
        alias=(
            "X-MS-CLIENT-PRINCIPAL"
        ),
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

    if (
        REVIEWER_ROLE
        not in roles
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "HealthcareRAG.Reviewer "
                "role required."
            ),
        )

    return principal