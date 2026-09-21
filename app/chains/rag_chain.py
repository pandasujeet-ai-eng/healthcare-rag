import os

from dotenv import load_dotenv
from langchain_core.prompts import (
    ChatPromptTemplate
)
from langchain_openai import (
    AzureChatOpenAI
)
from langsmith import traceable

from app.chains.context_builder import (
    build_context
)
from app.observability.tracing import (
    get_tracer
)
from app.prompts.healthcare_prompt import (
    SYSTEM_PROMPT
)
from app.retrieval.azure_retriever import (
    retrieve
)


load_dotenv()


CHAT_DEPLOYMENT = os.environ[
    "AZURE_OPENAI_CHAT_DEPLOYMENT"
]

AZURE_OPENAI_ENDPOINT = os.environ[
    "AZURE_OPENAI_ENDPOINT"
]

AZURE_OPENAI_API_KEY = os.environ[
    "AZURE_OPENAI_API_KEY"
]


REFUSAL_MESSAGE = (
    "I cannot find sufficient information "
    "in the approved knowledge base."
)


llm = AzureChatOpenAI(
    azure_deployment=CHAT_DEPLOYMENT,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-10-21",
    temperature=0,
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            SYSTEM_PROMPT,
        ),
        (
            "human",
            """
Question:

{question}


Approved hospital context:

{context}
""".strip(),
        ),
    ]
)


chain = prompt | llm


azure_tracer = get_tracer()


@traceable(
    name="healthcare_rag",
    run_type="chain",
    metadata={
        "environment": "dev",
        "application": "healthcare-rag",
        "rag_version": "v1",
        "prompt_version":
            "healthcare-prompt-v1",
        "retrieval_mode":
            "hybrid",
        "embedding_model":
            "text-embedding-3-small",
    },
)
def answer_question(
    question: str,
    top_k: int = 3,
) -> dict:
    """
    Execute the complete healthcare RAG flow.

    Flow:
        question
        -> retrieval
        -> context construction
        -> LangChain prompt
        -> Azure OpenAI
        -> answer + citations

    OpenTelemetry captures operational spans.
    LangSmith captures AI-oriented tracing.
    """

    with azure_tracer.start_as_current_span(
        "healthcare_rag_request"
    ) as span:

        span.set_attribute(
            "app.name",
            "healthcare-rag"
        )

        span.set_attribute(
            "app.environment",
            "dev"
        )

        span.set_attribute(
            "rag.version",
            "v1"
        )

        span.set_attribute(
            "rag.prompt_version",
            "healthcare-prompt-v1"
        )

        span.set_attribute(
            "rag.retrieval_mode",
            "hybrid"
        )

        span.set_attribute(
            "rag.top_k",
            top_k
        )

        span.set_attribute(
            "ai.chat_deployment",
            CHAT_DEPLOYMENT
        )

        try:

            documents = retrieve(
                question,
                top_k=top_k,
            )

            span.set_attribute(
                "rag.retrieved_count",
                len(documents)
            )

            if not documents:

                span.set_attribute(
                    "rag.refused",
                    True
                )

                span.set_attribute(
                    "rag.citation_count",
                    0
                )

                return {
                    "answer":
                        REFUSAL_MESSAGE,

                    "citations":
                        [],

                    "retrieved_chunks":
                        [],
                }

            context = build_context(
                documents
            )

            response = chain.invoke(
                {
                    "question":
                        question,

                    "context":
                        context,
                }
            )

            citations = []

            for doc in documents:

                citations.append(
                    {
                        "document_id":
                            doc[
                                "document_id"
                            ],

                        "chunk_id":
                            doc[
                                "chunk_id"
                            ],

                        "title":
                            doc[
                                "title"
                            ],

                        "section":
                            doc[
                                "section"
                            ],

                        "page":
                            doc[
                                "page"
                            ],
                    }
                )

            span.set_attribute(
                "rag.citation_count",
                len(citations)
            )

            span.set_attribute(
                "rag.refused",
                False
            )

            span.set_attribute(
                "rag.answer_length_chars",
                len(
                    response.content
                )
            )

            return {
                "answer":
                    response.content,

                "citations":
                    citations,

                "retrieved_chunks":
                    documents,
            }

        except Exception as exc:

            span.record_exception(
                exc
            )

            span.set_attribute(
                "error.type",
                type(exc).__name__
            )

            span.set_attribute(
                "error.present",
                True
            )

            raise