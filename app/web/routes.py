from __future__ import annotations

from pathlib import Path

from fastapi import (
    APIRouter,
    Request,
)

from fastapi.responses import (
    HTMLResponse,
)


router = APIRouter(
    tags=[
        "CareGuard UI",
    ],
)


BASE_DIR = Path(
    __file__
).resolve().parent.parent


TEMPLATE_PATH = (
    BASE_DIR
    / "templates"
    / "careguard.html"
)


I18N_STYLESHEET = """
<link
    rel="stylesheet"
    href="/static/careguard_i18n.css?v=1.7"
>
"""


DEMO_STYLESHEET = """
<link
    rel="stylesheet"
    href="/static/careguard_demo.css?v=1.7"
>
"""


I18N_SCRIPT = """
<script src="/static/careguard_i18n.js?v=1.7"></script>
"""


ANSWER_I18N_SCRIPT = """
<script src="/static/careguard_answer_i18n.js?v=1.7"></script>
"""


DEMO_SCRIPT = """
<script src="/static/careguard_demo.js?v=1.7"></script>
"""


@router.get(
    "/app",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def careguard_app(
    request: Request,
) -> HTMLResponse:

    del request

    html = TEMPLATE_PATH.read_text(
        encoding="utf-8"
    )


    # =========================================================
    # V1.6A BILINGUAL STYLES
    # =========================================================

    if (
        "/static/careguard_i18n.css"
        not in html
    ):

        html = html.replace(
            "</head>",
            (
                I18N_STYLESHEET
                + "\n</head>"
            ),
        )


    # =========================================================
    # V1.7 DEMO POLISH STYLES
    # =========================================================

    if (
        "/static/careguard_demo.css"
        not in html
    ):

        html = html.replace(
            "</head>",
            (
                DEMO_STYLESHEET
                + "\n</head>"
            ),
        )


    # =========================================================
    # V1.6A BILINGUAL UI
    # =========================================================

    if (
        "/static/careguard_i18n.js"
        not in html
    ):

        html = html.replace(
            "</body>",
            (
                I18N_SCRIPT
                + "\n</body>"
            ),
        )


    # =========================================================
    # V1.6B ANSWER LOCALIZATION
    # =========================================================

    if (
        "/static/careguard_answer_i18n.js"
        not in html
    ):

        html = html.replace(
            "</body>",
            (
                ANSWER_I18N_SCRIPT
                + "\n</body>"
            ),
        )


    # =========================================================
    # V1.7 HACKATHON PRESENTATION LAYER
    # =========================================================

    if (
        "/static/careguard_demo.js"
        not in html
    ):

        html = html.replace(
            "</body>",
            (
                DEMO_SCRIPT
                + "\n</body>"
            ),
        )


    return HTMLResponse(
        content=html,
        status_code=200,
        headers={
            "Cache-Control":
                "no-store, no-cache, must-revalidate",
            "Pragma":
                "no-cache",
        },
    )