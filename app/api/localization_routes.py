from __future__ import annotations

import os

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from langchain_openai import (
    AzureChatOpenAI,
)

from pydantic import (
    BaseModel,
    Field,
)

from app.security.easyauth import (
    require_authenticated_user,
)


router = APIRouter(
    prefix="/api/v1/localization",
    tags=[
        "CareGuard Localization",
    ],
)


class TranslateRequest(
    BaseModel,
):

    text: str = Field(
        min_length=1,
        max_length=12000,
    )

    target_language: str = Field(
        pattern="^(en|ar)$",
    )


class TranslateResponse(
    BaseModel,
):

    source_text: str

    translated_text: str

    target_language: str


def _get_model() -> AzureChatOpenAI:

    api_version = (
        os.getenv(
            "AZURE_OPENAI_API_VERSION"
        )
        or "2024-10-21"
    )

    return AzureChatOpenAI(
        azure_endpoint=(
            os.environ[
                "AZURE_OPENAI_ENDPOINT"
            ]
        ),
        api_key=(
            os.environ[
                "AZURE_OPENAI_API_KEY"
            ]
        ),
        azure_deployment=(
            os.environ[
                "AZURE_OPENAI_CHAT_DEPLOYMENT"
            ]
        ),
        api_version=api_version,
        temperature=0,
    )


def _extract_text(
    response,
) -> str:

    content = getattr(
        response,
        "content",
        "",
    )

    if isinstance(
        content,
        str,
    ):

        return content.strip()

    return str(
        content
    ).strip()


@router.post(
    "/translate",
    response_model=TranslateResponse,
)
def translate_grounded_text(
    request: TranslateRequest,
    principal: dict = Depends(
        require_authenticated_user
    ),
) -> TranslateResponse:

    del principal

    if (
        request.target_language
        == "en"
    ):

        return TranslateResponse(
            source_text=request.text,
            translated_text=request.text,
            target_language="en",
        )

    model = _get_model()

    system_message = """
You are the localization component of CareGuard AI.

Translate the supplied healthcare text faithfully into Arabic.

STRICT RULES:

1. Do not add facts.
2. Do not remove facts.
3. Do not provide new medical advice.
4. Do not reinterpret clinical guidance.
5. Preserve all policy identifiers exactly.
6. Preserve all chunk identifiers exactly.
7. Preserve codes, numbers and version identifiers exactly.
8. Preserve medication names accurately.
9. If the source contains a refusal, preserve the refusal.
10. Return only the translated text.

Examples of identifiers that must never be translated:
POL-DM-001
POL-DM-001-C0001
POL-AN-001
POL-IC-001
""".strip()

    try:

        response = model.invoke(
            [
                (
                    "system",
                    system_message,
                ),
                (
                    "human",
                    request.text,
                ),
            ]
        )

        translated_text = (
            _extract_text(
                response
            )
        )

        if not translated_text:

            raise RuntimeError(
                "Translation returned empty text."
            )

        return TranslateResponse(
            source_text=request.text,
            translated_text=translated_text,
            target_language="ar",
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "error":
                    "translation_failed",
                "detail":
                    str(
                        exc
                    ),
            },
        ) from exc