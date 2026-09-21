from app.chains.rag_chain import answer_question


def test_known_answer():

    result = answer_question(
        "When should metformin be stopped "
        "before surgery?"
    )

    answer = result["answer"].lower()

    assert "morning of surgery" in answer


def test_citation_present():

    result = answer_question(
        "When should metformin be stopped "
        "before surgery?"
    )

    ids = [
        c["document_id"]
        for c in result["citations"]
    ]

    assert "POL-DM-001" in ids