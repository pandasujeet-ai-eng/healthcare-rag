"use strict";


let currentThreadId = null;
let currentQuestion = null;
let currentUser = null;
let currentRiskAssessment = null;

let currentReviewFilter = "pending";
let selectedReviewCase = null;


const sessionMetrics = {

    questions: 0,
    answers: 0,
    reviews: 0,
    refusals: 0,
    highRisk: 0,

};


/* ============================================================= */
/* DOM                                                           */
/* ============================================================= */


function byId(id) {

    return document.getElementById(
        id
    );

}


function show(id) {

    byId(id)
        .classList
        .remove(
            "hidden"
        );

}


function hide(id) {

    byId(id)
        .classList
        .add(
            "hidden"
        );

}


function setText(
    id,
    value,
) {

    byId(id).textContent =
        value ?? "—";

}


/* ============================================================= */
/* NAVIGATION                                                    */
/* ============================================================= */


const pageMetadata = {

    ask: {
        title:
            "Ask CareGuard",

        subtitle:
            "Governed AI over approved hospital knowledge.",
    },

    reviews: {
        title:
            "Reviewer Command Center",

        subtitle:
            "Human oversight for governed healthcare AI decisions.",
    },

    audit: {
        title:
            "Audit Trail",

        subtitle:
            "Trace the lifecycle of every governed request.",
    },

    analytics: {
        title:
            "Analytics",

        subtitle:
            "Session-level AI governance insights.",
    },

};


async function activateSection(
    name,
) {

    document
        .querySelectorAll(
            ".section"
        )
        .forEach(
            element => {

                element.classList.remove(
                    "active"
                );

            }
        );


    document
        .querySelectorAll(
            ".nav-item"
        )
        .forEach(
            element => {

                element.classList.remove(
                    "active"
                );

            }
        );


    byId(
        `section-${name}`
    ).classList.add(
        "active"
    );


    document
        .querySelector(
            `[data-section="${name}"]`
        )
        .classList.add(
            "active"
        );


    setText(
        "page-title",
        pageMetadata[name].title,
    );


    setText(
        "page-subtitle",
        pageMetadata[name].subtitle,
    );


    if (
        name === "reviews"
        && currentUser
        && currentUser.is_reviewer
    ) {

        await refreshReviewCommandCenter();

    }

}


/* ============================================================= */
/* USER                                                          */
/* ============================================================= */


async function loadCurrentUser() {

    try {

        const response =
            await fetch(
                "/api/v1/whoami",
                {
                    credentials:
                        "same-origin",
                }
            );


        if (!response.ok) {

            throw new Error(
                "Authentication check failed."
            );

        }


        currentUser =
            await response.json();


        const displayName =

            currentUser.user
            || currentUser.actor_id
            || "Authenticated User";


        setText(
            "user-name",
            displayName,
        );


        setText(
            "avatar-text",
            displayName
                .charAt(0)
                .toUpperCase(),
        );


        if (
            currentUser.is_reviewer
        ) {

            setText(
                "user-role",
                "Healthcare Reviewer",
            );

            show(
                "reviewer-chip"
            );

            await refreshReviewBadge();

        } else {

            setText(
                "user-role",
                "Healthcare User",
            );

        }

    } catch (error) {

        console.error(
            error
        );


        setText(
            "user-name",
            "Authentication required",
        );

    }

}


/* ============================================================= */
/* METRICS                                                       */
/* ============================================================= */


function updateMetrics() {

    setText(
        "metric-questions",
        sessionMetrics.questions,
    );

    setText(
        "metric-answers",
        sessionMetrics.answers,
    );

    setText(
        "metric-reviews",
        sessionMetrics.reviews,
    );

    setText(
        "metric-refusals",
        sessionMetrics.refusals,
    );

    setText(
        "metric-high-risk",
        sessionMetrics.highRisk,
    );

}


/* ============================================================= */
/* ASK                                                           */
/* ============================================================= */


async function askCareGuard() {

    const question =
        byId(
            "question-input"
        )
        .value
        .trim();


    if (!question) {

        return;

    }


    currentQuestion =
        question;


    sessionMetrics.questions += 1;

    updateMetrics();

    resetResult();

    show(
        "result-area"
    );

    setLoading(
        true
    );

    updateAuditQuestion(
        question
    );


    try {

        const response =
            await fetch(
                "/api/v1/runs/start",
                {

                    method:
                        "POST",

                    credentials:
                        "same-origin",

                    headers: {

                        "Content-Type":
                            "application/json",

                    },

                    body:
                        JSON.stringify(
                            {
                                question:
                                    question,

                                top_k:
                                    3,
                            }
                        ),

                }
            );


        const body =
            await response.json();


        if (!response.ok) {

            throw new Error(
                extractErrorMessage(
                    body
                )
            );

        }


        currentThreadId =
            body.thread_id;


        await applyRiskAssessment(
            body
        );


        await renderProvenanceFromCitations(
            body.citations
            || []
        );


        if (
            body.status
            === "waiting_for_review"
        ) {

            await registerReviewCase(
                body
            );

        }


        handleRunResponse(
            body
        );

    } catch (error) {

        await applyErrorRiskAssessment();

        showError(
            error.message
        );

    } finally {

        setLoading(
            false
        );

    }

}


/* ============================================================= */
/* RISK                                                          */
/* ============================================================= */


async function applyRiskAssessment(
    runResult,
) {

    const citations =
        runResult.citations
        || [];


    const response =
        await fetch(
            "/api/v1/governance/risk-assessment",
            {

                method:
                    "POST",

                credentials:
                    "same-origin",

                headers: {

                    "Content-Type":
                        "application/json",

                },

                body:
                    JSON.stringify(
                        {

                            question:
                                currentQuestion,

                            status:
                                runResult.status,

                            answer:
                                runResult.answer,

                            citations_count:
                                citations.length,

                            action_requested:
                                (
                                    runResult.action_result
                                    !== undefined
                                    && runResult.action_result
                                    !== null
                                ),

                            error:
                                false,

                        }
                    ),

            }
        );


    if (!response.ok) {

        return;

    }


    const assessment =
        await response.json();


    currentRiskAssessment =
        assessment;


    renderRiskAssessment(
        assessment
    );

}


async function applyErrorRiskAssessment() {

    try {

        const response =
            await fetch(
                "/api/v1/governance/risk-assessment",
                {

                    method:
                        "POST",

                    credentials:
                        "same-origin",

                    headers: {

                        "Content-Type":
                            "application/json",

                    },

                    body:
                        JSON.stringify(
                            {

                                question:
                                    currentQuestion,

                                citations_count:
                                    0,

                                error:
                                    true,

                            }
                        ),

                }
            );


        if (
            response.ok
        ) {

            renderRiskAssessment(
                await response.json()
            );

        }

    } catch {

        // Safe no-op.

    }

}


function renderRiskAssessment(
    assessment,
) {

    const level =
        assessment.risk_level;


    const riskElement =
        byId(
            "risk-value"
        );


    riskElement.className =
        "risk-value";


    riskElement.classList.add(
        level.toLowerCase()
    );


    setText(
        "risk-value",
        level,
    );


    setText(
        "decision-value",
        assessment
            .governance_decision
            .replaceAll(
                "_",
                " "
            ),
    );


    setText(
        "evidence-value",
        assessment.evidence_strength,
    );


    setText(
        "oversight-value",
        assessment.human_review_required
            ? "REQUIRED"
            : "NOT REQUIRED",
    );


    setText(
        "risk-reason",
        assessment.risk_reason,
    );


    show(
        "risk-reason-card"
    );


    updateAuditRisk(
        `${level}: ${assessment.risk_reason}`
    );


    if (
        level === "HIGH"
        || level === "CRITICAL"
    ) {

        sessionMetrics.highRisk += 1;

        updateMetrics();

    }

}


/* ============================================================= */
/* V1.5 EVIDENCE PROVENANCE                                      */
/* ============================================================= */


async function getEvidenceProvenance(
    citations,
) {

    const response =
        await fetch(
            "/api/v1/governance/evidence-provenance",
            {

                method:
                    "POST",

                credentials:
                    "same-origin",

                headers: {

                    "Content-Type":
                        "application/json",

                },

                body:
                    JSON.stringify(
                        {
                            citations:
                                citations
                                || [],
                        }
                    ),

            }
        );


    if (!response.ok) {

        return null;

    }


    return (
        await response.json()
    );

}


async function renderProvenanceFromCitations(
    citations,
) {

    if (
        !citations
        || citations.length === 0
    ) {

        hide(
            "provenance-card"
        );

        return;

    }


    const provenance =
        await getEvidenceProvenance(
            citations
        );


    if (!provenance) {

        hide(
            "provenance-card"
        );

        return;

    }


    renderMainProvenance(
        provenance
    );

}


function renderMainProvenance(
    provenance,
) {

    setText(
        "provenance-source-count",
        provenance.source_count,
    );


    setText(
        "provenance-traceable-count",
        provenance.traceable_count,
    );


    setText(
        "provenance-policy-count",
        provenance.policy_ids.length,
    );


    let overall =
        "LIMITED";


    if (
        provenance.source_count > 0
        && provenance.traceable_count
            === provenance.source_count
    ) {

        overall =
            "TRACEABLE";

    } else if (
        provenance.traceable_count > 0
        || provenance.partial_count > 0
    ) {

        overall =
            "PARTIAL";

    }


    setText(
        "provenance-overall",
        overall,
    );


    byId(
        "provenance-overall"
    ).className =
        (
            "provenance-chip "
            + overall.toLowerCase()
        );


    renderProvenanceItems(
        "provenance-list",
        provenance.items
    );


    show(
        "provenance-card"
    );

}


function renderProvenanceItems(
    containerId,
    items,
) {

    const container =
        byId(
            containerId
        );


    container.innerHTML =
        "";


    if (
        !items
        || items.length === 0
    ) {

        container.innerHTML =
            (
                "<div class='provenance-empty'>"
                + "No detailed provenance metadata was returned."
                + "</div>"
            );

        return;

    }


    items.forEach(
        (
            item,
            index
        ) => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "provenance-item";


            const title =
                item.title
                || item.policy_id
                || `Evidence Source ${index + 1}`;


            card.innerHTML = `
                <div class="provenance-item-header">

                    <div>

                        <div class="provenance-item-title">
                            ${escapeHtml(title)}
                        </div>

                        <div class="provenance-item-subtitle">
                            Approved knowledge source
                        </div>

                    </div>

                    <span class="traceability-chip ${escapeHtml(
                        item.traceability.toLowerCase()
                    )}">
                        ${escapeHtml(item.traceability)}
                    </span>

                </div>


                <div class="provenance-metadata-grid">

                    ${metadataField(
                        "Policy ID",
                        item.policy_id
                    )}

                    ${metadataField(
                        "Chunk ID",
                        item.chunk_id
                    )}

                    ${metadataField(
                        "Section",
                        item.section
                    )}

                    ${metadataField(
                        "Version",
                        item.version
                    )}

                    ${metadataField(
                        "Effective Date",
                        item.effective_date
                    )}

                    ${metadataField(
                        "Page",
                        item.page
                    )}

                </div>


                ${
                    item.source_name

                    ? `
                    <div class="provenance-source-row">
                        <strong>Source:</strong>
                        ${escapeHtml(item.source_name)}
                    </div>
                    `

                    : ""
                }


                ${
                    item.excerpt

                    ? `
                    <div class="evidence-excerpt">

                        <div class="evidence-excerpt-label">
                            Retrieved Evidence
                        </div>

                        <div class="evidence-excerpt-text">
                            ${escapeHtml(item.excerpt)}
                        </div>

                    </div>
                    `

                    : `
                    <div class="metadata-note">
                        Evidence text was not included in the citation payload.
                    </div>
                    `
                }


                <div class="provenance-support-note">
                    This source was selected by the grounded
                    CareGuard workflow as supporting evidence.
                </div>
            `;


            container.appendChild(
                card
            );

        }
    );

}


function metadataField(
    label,
    value,
) {

    return `
        <div class="provenance-field">

            <div class="provenance-field-label">
                ${escapeHtml(label)}
            </div>

            <div class="provenance-field-value">
                ${escapeHtml(value || "Not provided")}
            </div>

        </div>
    `;

}


/* ============================================================= */
/* REGISTER REVIEW                                               */
/* ============================================================= */


async function registerReviewCase(
    body,
) {

    try {

        const assessment =
            currentRiskAssessment
            || {};


        const response =
            await fetch(
                "/api/v1/reviews/register",
                {

                    method:
                        "POST",

                    credentials:
                        "same-origin",

                    headers: {

                        "Content-Type":
                            "application/json",

                    },

                    body:
                        JSON.stringify(
                            {

                                thread_id:
                                    body.thread_id,

                                question:
                                    currentQuestion,

                                risk_level:
                                    assessment.risk_level
                                    || "HIGH",

                                risk_reason:
                                    assessment.risk_reason
                                    || extractReviewMessage(
                                        body.review_payload
                                    ),

                                evidence_strength:
                                    assessment.evidence_strength
                                    || null,

                            }
                        ),

                }
            );


        if (!response.ok) {

            console.error(
                "Review registration failed.",
                await response.text()
            );

            return;

        }


        await refreshReviewBadge();

    } catch (error) {

        console.error(
            "Could not register review case.",
            error
        );

    }

}


/* ============================================================= */
/* RUN RESPONSE                                                  */
/* ============================================================= */


function handleRunResponse(
    body,
) {

    if (
        body.status
        === "waiting_for_review"
    ) {

        handleReviewRequired(
            body
        );

        return;

    }


    if (
        body.answer
    ) {

        renderAnswer(
            body.answer
        );

    }


    const answer =
        (
            body.answer
            || ""
        ).toLowerCase();


    if (
        answer.includes(
            "cannot find sufficient information"
        )
    ) {

        sessionMetrics.refusals += 1;


        updateAuditDecision(
            "CareGuard safely refused because approved evidence was insufficient."
        );

    } else {

        if (
            body.answer
        ) {

            sessionMetrics.answers += 1;

        }


        updateAuditDecision(
            "CareGuard completed the governed response workflow."
        );

    }


    updateMetrics();

}


/* ============================================================= */
/* REVIEW REQUIRED                                               */
/* ============================================================= */


function handleReviewRequired(
    body,
) {

    setText(
        "review-thread-id",
        body.thread_id,
    );


    const reason =

        currentRiskAssessment
            ?.risk_reason

        || extractReviewMessage(
            body.review_payload
        );


    setText(
        "review-message",
        reason,
    );


    show(
        "review-banner"
    );


    if (
        currentUser
        && currentUser.is_reviewer
    ) {

        show(
            "review-actions"
        );

    }


    sessionMetrics.reviews += 1;

    updateMetrics();


    updateAuditDecision(
        "CareGuard escalated the request for human oversight."
    );


    updateAuditReview(
        "Waiting for an authorized healthcare reviewer."
    );

}


/* ============================================================= */
/* REVIEW DECISION                                               */
/* ============================================================= */


async function submitReview(
    approved,
) {

    if (!currentThreadId) {

        return;

    }


    await executeReviewDecision(
        currentThreadId,
        approved,
        true,
    );

}


async function executeReviewDecision(
    threadId,
    approved,
    renderToAskScreen = false,
) {

    try {

        const graphResponse =
            await fetch(
                `/api/v1/runs/${threadId}/review`,
                {

                    method:
                        "POST",

                    credentials:
                        "same-origin",

                    headers: {

                        "Content-Type":
                            "application/json",

                    },

                    body:
                        JSON.stringify(
                            {
                                approved:
                                    approved,
                            }
                        ),

                }
            );


        const graphBody =
            await graphResponse.json();


        if (!graphResponse.ok) {

            throw new Error(
                extractErrorMessage(
                    graphBody
                )
            );

        }


        const queueResponse =
            await fetch(
                `/api/v1/reviews/${threadId}/complete`,
                {

                    method:
                        "POST",

                    credentials:
                        "same-origin",

                    headers: {

                        "Content-Type":
                            "application/json",

                    },

                    body:
                        JSON.stringify(
                            {
                                approved:
                                    approved,
                            }
                        ),

                }
            );


        if (!queueResponse.ok) {

            console.error(
                "Graph review succeeded but queue update failed.",
                await queueResponse.text()
            );

        }


        if (
            renderToAskScreen
        ) {

            hide(
                "review-banner"
            );


            setText(
                "oversight-value",
                approved
                    ? "APPROVED"
                    : "REJECTED",
            );


            setText(
                "decision-value",
                approved
                    ? "APPROVED"
                    : "REJECTED",
            );


            updateAuditReview(

                approved

                    ? "Authorized reviewer approved the CareGuard response."

                    : "Authorized reviewer rejected the CareGuard response."

            );


            if (
                graphBody.answer
            ) {

                renderAnswer(
                    graphBody.answer
                );

            }


            await renderProvenanceFromCitations(
                graphBody.citations
                || []
            );


            if (
                approved
                && graphBody.answer
            ) {

                sessionMetrics.answers += 1;

                updateMetrics();

            }

        }


        await refreshReviewBadge();


        if (
            byId(
                "section-reviews"
            ).classList.contains(
                "active"
            )
        ) {

            await refreshReviewCommandCenter();

        }


        return graphBody;

    } catch (error) {

        showError(
            error.message
        );

        throw error;

    }

}


/* ============================================================= */
/* REVIEW COMMAND CENTER                                         */
/* ============================================================= */


async function refreshReviewCommandCenter() {

    await Promise.all(
        [
            loadReviewStats(),
            loadReviewList(
                currentReviewFilter
            ),
        ]
    );

}


async function loadReviewStats() {

    const response =
        await fetch(
            "/api/v1/reviews/stats",
            {
                credentials:
                    "same-origin",
            }
        );


    if (!response.ok) {

        return;

    }


    const stats =
        await response.json();


    setText(
        "review-stat-pending",
        stats.pending,
    );


    setText(
        "review-stat-approved",
        stats.approved,
    );


    setText(
        "review-stat-rejected",
        stats.rejected,
    );


    setText(
        "review-stat-total",
        stats.total,
    );


    updateReviewCountBadge(
        stats.pending
    );

}


async function refreshReviewBadge() {

    if (
        !currentUser
        || !currentUser.is_reviewer
    ) {

        return;

    }


    try {

        const response =
            await fetch(
                "/api/v1/reviews/stats",
                {
                    credentials:
                        "same-origin",
                }
            );


        if (!response.ok) {

            return;

        }


        const stats =
            await response.json();


        updateReviewCountBadge(
            stats.pending
        );

    } catch {

        // Safe no-op.

    }

}


function updateReviewCountBadge(
    count,
) {

    setText(
        "review-count",
        count,
    );


    if (
        Number(
            count
        ) > 0
    ) {

        show(
            "review-count"
        );

    } else {

        hide(
            "review-count"
        );

    }

}


async function loadReviewList(
    filter,
) {

    const url =

        filter === "all"

            ? "/api/v1/reviews"

            : (
                "/api/v1/reviews?status="
                + encodeURIComponent(
                    filter
                )
            );


    const response =
        await fetch(
            url,
            {
                credentials:
                    "same-origin",
            }
        );


    if (!response.ok) {

        byId(
            "review-list"
        ).innerHTML =
            (
                "<div class='review-load-error'>"
                + "Unable to load review queue."
                + "</div>"
            );

        return;

    }


    const reviews =
        await response.json();


    renderReviewList(
        reviews
    );

}


function renderReviewList(
    reviews,
) {

    const container =
        byId(
            "review-list"
        );


    container.innerHTML =
        "";


    if (
        !reviews
        || reviews.length === 0
    ) {

        show(
            "review-empty"
        );

        return;

    }


    hide(
        "review-empty"
    );


    reviews.forEach(
        review => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "review-queue-card";


            const risk =
                review.risk_level
                || "UNKNOWN";


            const status =
                review.status
                || "pending";


            card.innerHTML = `
                <div class="review-queue-top">

                    <span class="queue-risk ${risk.toLowerCase()}">
                        ${escapeHtml(risk)}
                    </span>

                    <span class="queue-status ${status.toLowerCase()}">
                        ${escapeHtml(status.toUpperCase())}
                    </span>

                </div>


                <div class="review-queue-question">
                    ${escapeHtml(review.question)}
                </div>


                <div class="review-queue-meta">

                    <span>
                        Evidence:
                        ${escapeHtml(
                            review.evidence_strength
                            || "—"
                        )}
                    </span>

                    <span>
                        ${formatDate(
                            review.created_at
                        )}
                    </span>

                </div>


                <button
                    class="open-case-button"
                    type="button"
                >
                    Open Case →
                </button>
            `;


            card
                .querySelector(
                    ".open-case-button"
                )
                .addEventListener(
                    "click",
                    async () => {

                        await openReviewCase(
                            review
                        );

                    }
                );


            container.appendChild(
                card
            );

        }
    );

}


async function openReviewCase(
    review,
) {

    selectedReviewCase =
        review;


    setText(
        "case-status",
        review.status
        || "—",
    );


    setText(
        "case-risk",
        review.risk_level
        || "—",
    );


    setText(
        "case-evidence",
        review.evidence_strength
        || "—",
    );


    setText(
        "case-requested-by",
        review.requested_by
        || "—",
    );


    setText(
        "case-question",
        review.question
        || "—",
    );


    setText(
        "case-reason",
        review.risk_reason
        || "—",
    );


    setText(
        "case-thread",
        review.thread_id,
    );


    setText(
        "case-created",
        formatDate(
            review.created_at
        ),
    );


    if (
        review.reviewer_id
    ) {

        show(
            "case-reviewer-section"
        );


        setText(
            "case-reviewer",
            review.reviewer_id,
        );

    } else {

        hide(
            "case-reviewer-section"
        );

    }


    if (
        review.status
        === "pending"
    ) {

        show(
            "case-actions"
        );

    } else {

        hide(
            "case-actions"
        );

    }


    await loadCaseProvenance(
        review.thread_id
    );


    show(
        "review-case-panel"
    );


    byId(
        "review-case-panel"
    ).scrollIntoView(
        {
            behavior:
                "smooth",

            block:
                "start",
        }
    );

}


async function loadCaseProvenance(
    threadId,
) {

    try {

        const response =
            await fetch(
                `/api/v1/runs/${threadId}`,
                {
                    credentials:
                        "same-origin",
                }
            );


        if (!response.ok) {

            hide(
                "case-provenance-section"
            );

            return;

        }


        const body =
            await response.json();


        const citations =
            body.citations
            || body.state?.citations
            || body.result?.citations
            || [];


        if (
            citations.length === 0
        ) {

            hide(
                "case-provenance-section"
            );

            return;

        }


        const provenance =
            await getEvidenceProvenance(
                citations
            );


        if (!provenance) {

            hide(
                "case-provenance-section"
            );

            return;

        }


        renderProvenanceItems(
            "case-provenance-list",
            provenance.items
        );


        show(
            "case-provenance-section"
        );

    } catch {

        hide(
            "case-provenance-section"
        );

    }

}


function closeReviewCase() {

    selectedReviewCase =
        null;


    hide(
        "review-case-panel"
    );

}


/* ============================================================= */
/* ANSWER                                                        */
/* ============================================================= */


function renderAnswer(
    answer,
) {

    setText(
        "answer-text",
        answer,
    );


    show(
        "answer-card"
    );

}


/* ============================================================= */
/* AUDIT                                                         */
/* ============================================================= */


function completeTimelineItem(
    id,
) {

    byId(
        id
    )
    .classList
    .add(
        "complete"
    );

}


function updateAuditQuestion(
    value,
) {

    setText(
        "audit-question-text",
        value,
    );


    completeTimelineItem(
        "audit-question"
    );

}


function updateAuditRisk(
    value,
) {

    setText(
        "audit-risk-text",
        value,
    );


    completeTimelineItem(
        "audit-risk"
    );

}


function updateAuditDecision(
    value,
) {

    setText(
        "audit-decision-text",
        value,
    );


    completeTimelineItem(
        "audit-decision"
    );

}


function updateAuditReview(
    value,
) {

    setText(
        "audit-review-text",
        value,
    );


    completeTimelineItem(
        "audit-review"
    );

}


/* ============================================================= */
/* RESET                                                         */
/* ============================================================= */


function resetResult() {

    hide(
        "review-banner"
    );

    hide(
        "review-actions"
    );

    hide(
        "answer-card"
    );

    hide(
        "provenance-card"
    );

    hide(
        "error-card"
    );

    hide(
        "risk-reason-card"
    );


    setText(
        "risk-value",
        "ASSESSING",
    );


    setText(
        "decision-value",
        "PROCESSING",
    );


    setText(
        "evidence-value",
        "CHECKING",
    );


    setText(
        "oversight-value",
        "EVALUATING",
    );


    const riskElement =
        byId(
            "risk-value"
        );


    riskElement.className =
        "risk-value neutral";


    currentThreadId =
        null;


    currentRiskAssessment =
        null;

}


/* ============================================================= */
/* LOADING                                                       */
/* ============================================================= */


function setLoading(
    loading,
) {

    byId(
        "ask-button"
    ).disabled =
        loading;


    if (
        loading
    ) {

        setText(
            "ask-button-text",
            "Analyzing",
        );

        show(
            "ask-spinner"
        );

    } else {

        setText(
            "ask-button-text",
            "Ask CareGuard",
        );

        hide(
            "ask-spinner"
        );

    }

}


/* ============================================================= */
/* HELPERS                                                       */
/* ============================================================= */


function extractReviewMessage(
    payload,
) {

    if (!payload) {

        return (
            "CareGuard determined that this request requires human review."
        );

    }


    if (
        typeof payload
        === "string"
    ) {

        return payload;

    }


    return (
        payload.reason
        || payload.message
        || payload.explanation
        || "CareGuard determined that this request requires human review."
    );

}


function extractErrorMessage(
    body,
) {

    if (!body) {

        return (
            "Unknown CareGuard error."
        );

    }


    if (
        typeof body.detail
        === "string"
    ) {

        return body.detail;

    }


    if (
        body.detail
        && typeof body.detail
            === "object"
    ) {

        return (
            body.detail.detail
            || body.detail.error
            || JSON.stringify(
                body.detail
            )
        );

    }


    return (
        body.message
        || "CareGuard request failed."
    );

}


function showError(
    message,
) {

    setText(
        "error-message",
        message,
    );


    show(
        "error-card"
    );

}


function escapeHtml(
    value,
) {

    return String(
        value
        ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}


function formatDate(
    value,
) {

    if (!value) {

        return "—";

    }


    const date =
        new Date(
            value
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return value;

    }


    return (
        date.toLocaleString()
    );

}


/* ============================================================= */
/* EVENTS                                                        */
/* ============================================================= */


document
    .querySelectorAll(
        ".nav-item"
    )
    .forEach(
        item => {

            item.addEventListener(
                "click",
                async () => {

                    await activateSection(
                        item.dataset.section
                    );

                }
            );

        }
    );


document
    .querySelectorAll(
        ".example-question"
    )
    .forEach(
        item => {

            item.addEventListener(
                "click",
                () => {

                    byId(
                        "question-input"
                    ).value =
                        item.dataset.question;

                }
            );

        }
    );


document
    .querySelectorAll(
        ".review-filter"
    )
    .forEach(
        item => {

            item.addEventListener(
                "click",
                async () => {

                    document
                        .querySelectorAll(
                            ".review-filter"
                        )
                        .forEach(
                            button => {

                                button.classList.remove(
                                    "active"
                                );

                            }
                        );


                    item.classList.add(
                        "active"
                    );


                    currentReviewFilter =
                        item.dataset.reviewFilter;


                    closeReviewCase();


                    await loadReviewList(
                        currentReviewFilter
                    );

                }
            );

        }
    );


byId(
    "ask-button"
)
.addEventListener(
    "click",
    askCareGuard
);


byId(
    "question-input"
)
.addEventListener(
    "keydown",
    event => {

        if (
            event.ctrlKey
            && event.key
                === "Enter"
        ) {

            askCareGuard();

        }

    }
);


byId(
    "approve-button"
)
.addEventListener(
    "click",
    () => {

        submitReview(
            true
        );

    }
);


byId(
    "reject-button"
)
.addEventListener(
    "click",
    () => {

        submitReview(
            false
        );

    }
);


byId(
    "refresh-reviews-button"
)
.addEventListener(
    "click",
    refreshReviewCommandCenter
);


byId(
    "close-review-case"
)
.addEventListener(
    "click",
    closeReviewCase
);


byId(
    "case-approve-button"
)
.addEventListener(
    "click",
    async () => {

        if (!selectedReviewCase) {

            return;

        }


        await executeReviewDecision(
            selectedReviewCase.thread_id,
            true,
            false,
        );


        closeReviewCase();

    }
);


byId(
    "case-reject-button"
)
.addEventListener(
    "click",
    async () => {

        if (!selectedReviewCase) {

            return;

        }


        await executeReviewDecision(
            selectedReviewCase.thread_id,
            false,
            false,
        );


        closeReviewCase();

    }
);


/* ============================================================= */
/* STARTUP                                                       */
/* ============================================================= */


document.addEventListener(
    "DOMContentLoaded",
    async () => {

        updateMetrics();

        await loadCurrentUser();

    }
);