import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langsmith import traceable

from app.chains.context_builder import build_context


load_dotenv()


AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
CHAT_DEPLOYMENT = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]


EVIDENCE_GATE_PROMPT = """
You are a strict evidence-selection component for a hospital-policy RAG system.

Your job is NOT to answer the user's question.

Your job is to determine:

1. Whether the retrieved approved hospital-policy evidence contains enough
   information to answer or correct the user's question.

2. Which retrieved chunks directly support the answer.

Important rules:

- Use only the supplied retrieved context.
- Do not use general medical knowledge.
- Do not answer the medical question.
- A question is RELEVANT when the retrieved context contains direct evidence
  that can answer the question.
- A question is ALSO RELEVANT when the user makes a false assumption and the
  retrieved policy contains direct evidence that can correct that assumption.

Example:
User:
"The policy says metformin must be stopped 48 hours before surgery, correct?"

Context:
"The patient should stop metformin on the morning of surgery."

This is RELEVANT because the policy directly provides evidence that corrects
the false premise.

Return NOT_RELEVANT when:
- the retrieved documents concern a different topic,
- answering requires outside medical knowledge,
- the evidence is only loosely related,
- the approved documents do not contain sufficient information.

Return ONLY valid JSON using this exact schema:

{
  "decision": "RELEVANT",
  "supporting_chunk_ids": ["CHUNK-ID"]
}

or

{
  "decision": "NOT_RELEVANT",
  "supporting_chunk_ids": []
}

Do not add markdown.
Do not add explanations outside the JSON.
"""


llm = AzureChatOpenAI(
    azure_deployment=CHAT_DEPLOYMENT,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-10-21",
    temperature=0,
)


def extract_chunk_id(document: Any) -> str | None:

    if document is None:
        return None

    if isinstance(document, dict):

        chunk_id = document.get("chunk_id")

        if chunk_id:
            return str(chunk_id)

        metadata = document.get("metadata")

        if isinstance(metadata, dict):

            chunk_id = metadata.get("chunk_id")

            if chunk_id:
                return str(chunk_id)

    metadata = getattr(
        document,
        "metadata",
        None,
    )

    if isinstance(metadata, dict):

        chunk_id = metadata.get("chunk_id")

        if chunk_id:
            return str(chunk_id)

    return None


def clean_json_response(
    raw_response: str,
) -> str:

    text = raw_response.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```\s*",
        "",
        text,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    return text.strip()


@traceable(
    name="rag_evidence_gate",
    run_type="chain",
    metadata={
        "application": "healthcare-rag",
        "component": "evidence-gate",
        "evidence_gate_version": "v2",
    },
)
def assess_evidence(
    question: str,
    documents: list,
) -> dict:

    if not documents:

        return {
            "relevant": False,
            "supporting_chunk_ids": [],
        }

    context = build_context(
        documents
    )

    message = f"""
{EVIDENCE_GATE_PROMPT}

USER QUESTION:
{question}

RETRIEVED APPROVED CONTEXT:
{context}
"""

    response = llm.invoke(
        message
    )

    raw_content = str(
        response.content
    )

    cleaned_content = clean_json_response(
        raw_content
    )

    try:

        parsed = json.loads(
            cleaned_content
        )

    except json.JSONDecodeError:

        print(
            "[EVIDENCE_GATE] "
            f"invalid_json={raw_content}"
        )

        return {
            "relevant": False,
            "supporting_chunk_ids": [],
        }

    decision = str(
        parsed.get(
            "decision",
            "NOT_RELEVANT",
        )
    ).strip().upper()

    requested_ids = parsed.get(
        "supporting_chunk_ids",
        [],
    )

    if not isinstance(
        requested_ids,
        list,
    ):

        requested_ids = []

    available_ids = {
        extract_chunk_id(document)
        for document in documents
    }

    available_ids.discard(
        None
    )

    supporting_ids = [
        str(chunk_id)
        for chunk_id in requested_ids
        if str(chunk_id) in available_ids
    ]

    relevant = (
        decision == "RELEVANT"
        and len(supporting_ids) > 0
    )

    if not relevant:

        supporting_ids = []

    print(
        "[EVIDENCE_GATE] "
        f"decision={decision} "
        f"supporting_chunk_ids={supporting_ids}"
    )

    return {
        "relevant": relevant,
        "supporting_chunk_ids": supporting_ids,
    }