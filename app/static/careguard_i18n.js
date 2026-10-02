"use strict";


/* ============================================================= */
/* CAREGUARD V1.6A - BILINGUAL UI                                */
/* ============================================================= */


const CAREGUARD_LANGUAGE_KEY =
    "careguard_language";


let careGuardLanguage =
    localStorage.getItem(
        CAREGUARD_LANGUAGE_KEY
    )
    || "en";


let translationScheduled =
    false;


/* ============================================================= */
/* TRANSLATIONS                                                  */
/* ============================================================= */


const translations = {

    en: {

        askCareGuard:
            "Ask CareGuard",

        askSubtitle:
            "Governed AI over approved hospital knowledge.",

        reviews:
            "Reviews",

        auditTrail:
            "Audit Trail",

        analytics:
            "Analytics",

        reviewer:
            "Reviewer",

        healthcareReviewer:
            "Healthcare Reviewer",

        healthcareUser:
            "Healthcare User",

        governedHealthcareAI:
            "GOVERNED HEALTHCARE AI",

        heroTitle:
            "How can CareGuard help?",

        heroDescription:
            "Ask about approved hospital policies, procedures and clinical operations. CareGuard evaluates evidence, provenance and governance risk before responding.",

        approvedKnowledge:
            "Approved knowledge only",

        askButton:
            "Ask CareGuard",

        analyzing:
            "Analyzing",

        demo:
            "Demo:",

        normalPolicy:
            "Normal policy question",

        evidenceConflict:
            "Evidence conflict",

        unsupported:
            "Unsupported",

        criticalRequest:
            "Critical request",

        careguardIntelligence:
            "CAREGUARD INTELLIGENCE",

        governanceAssessment:
            "Governance Assessment",

        riskLevel:
            "Risk Level",

        governance:
            "Governance",

        evidenceStrength:
            "Evidence Strength",

        humanOversight:
            "Human Oversight",

        riskReason:
            "Why CareGuard assigned this risk",

        humanReviewRequired:
            "Human Review Required",

        thread:
            "Thread:",

        reject:
            "Reject",

        approve:
            "Approve",

        response:
            "CAREGUARD RESPONSE",

        groundedAnswer:
            "Grounded Answer",

        evidenceGrounded:
            "Evidence grounded",

        policyProvenance:
            "POLICY PROVENANCE",

        evidenceViewer:
            "Evidence Viewer",

        sources:
            "Sources",

        fullyTraceable:
            "Fully Traceable",

        policies:
            "Policies",

        humanOversightTitle:
            "HUMAN OVERSIGHT",

        commandCenter:
            "Reviewer Command Center",

        commandDescription:
            "Govern high-risk CareGuard requests, inspect policy provenance and record accountable decisions.",

        pending:
            "Pending",

        approved:
            "Approved",

        rejected:
            "Rejected",

        totalReviews:
            "Total Reviews",

        all:
            "All",

        refresh:
            "↻ Refresh",

        noCases:
            "No review cases found",

        noCasesDescription:
            "New escalated cases will appear here.",

        reviewCase:
            "REVIEW CASE",

        caseDetail:
            "Case Detail",

        close:
            "Close",

        status:
            "Status",

        risk:
            "Risk",

        evidence:
            "Evidence",

        requestedBy:
            "Requested By",

        question:
            "Question",

        created:
            "Created",

        policyProvenanceCase:
            "Policy Provenance",

        governanceTitle:
            "GOVERNANCE",

        auditTitle:
            "Audit Trail",

        auditDescription:
            "Transparent tracking of the CareGuard decision lifecycle.",

        authenticated:
            "User authenticated",

        authenticatedDescription:
            "Identity verified using Microsoft Entra ID.",

        questionSubmitted:
            "Question submitted",

        waitingRequest:
            "Waiting for request.",

        riskAssessed:
            "Risk assessed",

        waitingRisk:
            "Waiting for governance assessment.",

        governanceDecision:
            "Governance decision",

        waitingRouting:
            "Waiting for agent routing.",

        humanReview:
            "Human review",

        notRequiredYet:
            "Not required yet.",

        insights:
            "CAREGUARD INSIGHTS",

        analyticsTitle:
            "Analytics",

        analyticsDescription:
            "Hackathon session-level governance metrics.",

        questions:
            "Questions",

        groundedAnswers:
            "Grounded answers",

        humanReviews:
            "Human reviews",

        safeRefusals:
            "Safe refusals",

        highCritical:
            "High / critical risk",

        openCase:
            "Open Case →",

        evidenceLabel:
            "Evidence:",

        policyId:
            "Policy ID",

        chunkId:
            "Chunk ID",

        section:
            "Section",

        version:
            "Version",

        effectiveDate:
            "Effective Date",

        page:
            "Page",

        source:
            "Source:",

        retrievedEvidence:
            "Retrieved Evidence",

        traceable:
            "TRACEABLE",

        partial:
            "PARTIAL",

        limited:
            "LIMITED",

        low:
            "LOW",

        medium:
            "MEDIUM",

        high:
            "HIGH",

        critical:
            "CRITICAL",

        answer:
            "ANSWER",

        refuse:
            "REFUSE",

        humanReviewDecision:
            "HUMAN REVIEW",

        action:
            "ACTION",

        required:
            "REQUIRED",

        notRequired:
            "NOT REQUIRED",

        error:
            "ERROR",

        notProvided:
            "Not provided",

    },


    ar: {

        askCareGuard:
            "اسأل CareGuard",

        askSubtitle:
            "ذكاء اصطناعي محكوم يعتمد على المعرفة المعتمدة في المستشفى.",

        reviews:
            "المراجعات",

        auditTrail:
            "سجل التدقيق",

        analytics:
            "التحليلات",

        reviewer:
            "مراجع",

        healthcareReviewer:
            "مراجع الرعاية الصحية",

        healthcareUser:
            "مستخدم الرعاية الصحية",

        governedHealthcareAI:
            "ذكاء اصطناعي محكوم للرعاية الصحية",

        heroTitle:
            "كيف يمكن لـ CareGuard مساعدتك؟",

        heroDescription:
            "اسأل عن سياسات المستشفى وإجراءاته والعمليات السريرية المعتمدة. يقوم CareGuard بتقييم الأدلة ومصدرها ومخاطر الحوكمة قبل الاستجابة.",

        approvedKnowledge:
            "المعرفة المعتمدة فقط",

        askButton:
            "اسأل CareGuard",

        analyzing:
            "جارٍ التحليل",

        demo:
            "أمثلة:",

        normalPolicy:
            "سؤال عن سياسة",

        evidenceConflict:
            "تعارض مع الدليل",

        unsupported:
            "غير مدعوم",

        criticalRequest:
            "طلب حرج",

        careguardIntelligence:
            "ذكاء CAREGUARD",

        governanceAssessment:
            "تقييم الحوكمة",

        riskLevel:
            "مستوى المخاطر",

        governance:
            "الحوكمة",

        evidenceStrength:
            "قوة الدليل",

        humanOversight:
            "الإشراف البشري",

        riskReason:
            "سبب تصنيف CareGuard لهذه المخاطر",

        humanReviewRequired:
            "مطلوب مراجعة بشرية",

        thread:
            "المعرّف:",

        reject:
            "رفض",

        approve:
            "موافقة",

        response:
            "استجابة CAREGUARD",

        groundedAnswer:
            "إجابة مستندة إلى الأدلة",

        evidenceGrounded:
            "مستند إلى الأدلة",

        policyProvenance:
            "مصدر السياسة",

        evidenceViewer:
            "عارض الأدلة",

        sources:
            "المصادر",

        fullyTraceable:
            "قابل للتتبع بالكامل",

        policies:
            "السياسات",

        humanOversightTitle:
            "الإشراف البشري",

        commandCenter:
            "مركز قيادة المراجعين",

        commandDescription:
            "إدارة طلبات CareGuard عالية المخاطر، وفحص مصادر الأدلة، وتسجيل قرارات المراجعة بشكل قابل للتدقيق.",

        pending:
            "قيد الانتظار",

        approved:
            "تمت الموافقة",

        rejected:
            "مرفوض",

        totalReviews:
            "إجمالي المراجعات",

        all:
            "الكل",

        refresh:
            "↻ تحديث",

        noCases:
            "لا توجد حالات مراجعة",

        noCasesDescription:
            "ستظهر الحالات المحالة الجديدة هنا.",

        reviewCase:
            "حالة مراجعة",

        caseDetail:
            "تفاصيل الحالة",

        close:
            "إغلاق",

        status:
            "الحالة",

        risk:
            "المخاطر",

        evidence:
            "الدليل",

        requestedBy:
            "مقدم الطلب",

        question:
            "السؤال",

        created:
            "تاريخ الإنشاء",

        policyProvenanceCase:
            "مصدر السياسة",

        governanceTitle:
            "الحوكمة",

        auditTitle:
            "سجل التدقيق",

        auditDescription:
            "تتبع شفاف لدورة قرار CareGuard.",

        authenticated:
            "تم التحقق من المستخدم",

        authenticatedDescription:
            "تم التحقق من الهوية باستخدام Microsoft Entra ID.",

        questionSubmitted:
            "تم إرسال السؤال",

        waitingRequest:
            "بانتظار الطلب.",

        riskAssessed:
            "تم تقييم المخاطر",

        waitingRisk:
            "بانتظار تقييم الحوكمة.",

        governanceDecision:
            "قرار الحوكمة",

        waitingRouting:
            "بانتظار توجيه الوكيل.",

        humanReview:
            "المراجعة البشرية",

        notRequiredYet:
            "غير مطلوبة حتى الآن.",

        insights:
            "رؤى CAREGUARD",

        analyticsTitle:
            "التحليلات",

        analyticsDescription:
            "مؤشرات حوكمة جلسة العرض التجريبي.",

        questions:
            "الأسئلة",

        groundedAnswers:
            "الإجابات المستندة إلى الأدلة",

        humanReviews:
            "المراجعات البشرية",

        safeRefusals:
            "الرفض الآمن",

        highCritical:
            "مخاطر عالية / حرجة",

        openCase:
            "فتح الحالة ←",

        evidenceLabel:
            "الدليل:",

        policyId:
            "معرف السياسة",

        chunkId:
            "معرف المقطع",

        section:
            "القسم",

        version:
            "الإصدار",

        effectiveDate:
            "تاريخ السريان",

        page:
            "الصفحة",

        source:
            "المصدر:",

        retrievedEvidence:
            "الدليل المسترجع",

        traceable:
            "قابل للتتبع",

        partial:
            "تتبع جزئي",

        limited:
            "تتبع محدود",

        low:
            "منخفض",

        medium:
            "متوسط",

        high:
            "مرتفع",

        critical:
            "حرج",

        answer:
            "إجابة",

        refuse:
            "رفض آمن",

        humanReviewDecision:
            "مراجعة بشرية",

        action:
            "إجراء",

        required:
            "مطلوب",

        notRequired:
            "غير مطلوب",

        error:
            "خطأ",

        notProvided:
            "غير متوفر",

    },

};


/* ============================================================= */
/* HELPERS                                                       */
/* ============================================================= */


function t(
    key,
) {

    return (
        translations[
            careGuardLanguage
        ]?.[key]
        || translations.en[key]
        || key
    );

}


function setElementText(
    selector,
    value,
) {

    const element =
        document.querySelector(
            selector
        );


    if (
        element
        && element.textContent
            !== value
    ) {

        element.textContent =
            value;

    }

}


function setAllText(
    selector,
    values,
) {

    document
        .querySelectorAll(
            selector
        )
        .forEach(
            (
                element,
                index
            ) => {

                if (
                    values[index]
                    !== undefined
                ) {

                    element.textContent =
                        values[index];

                }

            }
        );

}


/* ============================================================= */
/* SWITCHER                                                      */
/* ============================================================= */


function createLanguageSwitcher() {

    if (
        document.querySelector(
            ".language-switcher"
        )
    ) {

        return;

    }


    const userArea =
        document.querySelector(
            ".user-area"
        );


    if (!userArea) {

        return;

    }


    const wrapper =
        document.createElement(
            "div"
        );


    wrapper.className =
        "language-switcher";


    wrapper.innerHTML = `
        <button
            id="language-en"
            class="language-button"
            type="button"
        >
            English
        </button>

        <button
            id="language-ar"
            class="language-button"
            type="button"
        >
            العربية
        </button>
    `;


    userArea.insertBefore(
        wrapper,
        userArea.firstChild
    );


    document
        .getElementById(
            "language-en"
        )
        .addEventListener(
            "click",
            () => {

                setLanguage(
                    "en"
                );

            }
        );


    document
        .getElementById(
            "language-ar"
        )
        .addEventListener(
            "click",
            () => {

                setLanguage(
                    "ar"
                );

            }
        );

}


/* ============================================================= */
/* STATIC UI                                                     */
/* ============================================================= */


function translateNavigation() {

    document
        .querySelectorAll(
            ".nav-item"
        )
        .forEach(
            item => {

                const section =
                    item.dataset.section;


                const badge =
                    item.querySelector(
                        ".nav-badge"
                    );


                let label =
                    "";


                if (
                    section === "ask"
                ) {

                    label =
                        `✦ ${t("askCareGuard")}`;

                } else if (
                    section === "reviews"
                ) {

                    label =
                        `✓ ${t("reviews")}`;

                } else if (
                    section === "audit"
                ) {

                    label =
                        `◫ ${t("auditTrail")}`;

                } else if (
                    section === "analytics"
                ) {

                    label =
                        `◒ ${t("analytics")}`;

                }


                Array
                    .from(
                        item.childNodes
                    )
                    .filter(
                        node =>
                            node.nodeType
                            === Node.TEXT_NODE
                    )
                    .forEach(
                        node => {

                            node.remove();

                        }
                    );


                item.insertBefore(
                    document.createTextNode(
                        `${label} `
                    ),
                    item.firstChild
                );


                if (
                    badge
                    && badge.parentElement
                        !== item
                ) {

                    item.appendChild(
                        badge
                    );

                }

            }
        );

}


function translatePageHeader() {

    const activeSection =
        document.querySelector(
            ".nav-item.active"
        )?.dataset.section
        || "ask";


    const titles = {

        ask:
            t(
                "askCareGuard"
            ),

        reviews:
            t(
                "commandCenter"
            ),

        audit:
            t(
                "auditTitle"
            ),

        analytics:
            t(
                "analyticsTitle"
            ),

    };


    const subtitles = {

        ask:
            t(
                "askSubtitle"
            ),

        reviews:
            t(
                "commandDescription"
            ),

        audit:
            t(
                "auditDescription"
            ),

        analytics:
            t(
                "analyticsDescription"
            ),

    };


    setElementText(
        "#page-title",
        titles[
            activeSection
        ]
    );


    setElementText(
        "#page-subtitle",
        subtitles[
            activeSection
        ]
    );

}


function translateAskScreen() {

    setElementText(
        "#section-ask .hero .eyebrow",
        t(
            "governedHealthcareAI"
        )
    );


    setElementText(
        "#section-ask .hero h1",
        t(
            "heroTitle"
        )
    );


    setElementText(
        "#section-ask .hero p",
        t(
            "heroDescription"
        )
    );


    setElementText(
        ".knowledge-chip",
        t(
            "approvedKnowledge"
        )
    );


    const askButtonText =
        document.getElementById(
            "ask-button-text"
        );


    if (
        askButtonText
        && !askButtonText.textContent
            .toLowerCase()
            .includes(
                "analy"
            )
    ) {

        askButtonText.textContent =
            t(
                "askButton"
            );

    }


    setAllText(
        ".example-question",
        [
            t(
                "normalPolicy"
            ),
            t(
                "evidenceConflict"
            ),
            t(
                "unsupported"
            ),
            t(
                "criticalRequest"
            ),
        ]
    );


    const demoLabel =
        document.querySelector(
            ".example-row > span"
        );


    if (
        demoLabel
    ) {

        demoLabel.textContent =
            t(
                "demo"
            );

    }


    setElementText(
        ".intelligence-title .eyebrow",
        t(
            "careguardIntelligence"
        )
    );


    setElementText(
        ".intelligence-title h2",
        t(
            "governanceAssessment"
        )
    );


    setAllText(
        ".intelligence-grid .metric-label",
        [
            t(
                "riskLevel"
            ),
            t(
                "governance"
            ),
            t(
                "evidenceStrength"
            ),
            t(
                "humanOversight"
            ),
        ]
    );


    setElementText(
        ".risk-reason-label",
        t(
            "riskReason"
        )
    );


    setElementText(
        ".review-title",
        t(
            "humanReviewRequired"
        )
    );


    setElementText(
        "#reject-button",
        t(
            "reject"
        )
    );


    setElementText(
        "#approve-button",
        t(
            "approve"
        )
    );


    setElementText(
        "#answer-card .eyebrow",
        t(
            "response"
        )
    );


    setElementText(
        "#answer-card h2",
        t(
            "groundedAnswer"
        )
    );


    setElementText(
        ".grounded-chip",
        t(
            "evidenceGrounded"
        )
    );


    setElementText(
        "#provenance-card .eyebrow",
        t(
            "policyProvenance"
        )
    );


    setElementText(
        "#provenance-card h2",
        t(
            "evidenceViewer"
        )
    );


    setAllText(
        ".provenance-summary-label",
        [
            t(
                "sources"
            ),
            t(
                "fullyTraceable"
            ),
            t(
                "policies"
            ),
        ]
    );

}


function translateReviewsScreen() {

    setElementText(
        "#section-reviews .section-header .eyebrow",
        t(
            "humanOversightTitle"
        )
    );


    setElementText(
        "#section-reviews .section-header h1",
        t(
            "commandCenter"
        )
    );


    setElementText(
        "#section-reviews .section-header p",
        t(
            "commandDescription"
        )
    );


    setAllText(
        ".review-stat-label",
        [
            t(
                "pending"
            ),
            t(
                "approved"
            ),
            t(
                "rejected"
            ),
            t(
                "totalReviews"
            ),
        ]
    );


    setAllText(
        ".review-filter",
        [
            t(
                "pending"
            ),
            t(
                "approved"
            ),
            t(
                "rejected"
            ),
            t(
                "all"
            ),
        ]
    );


    setElementText(
        "#refresh-reviews-button",
        t(
            "refresh"
        )
    );


    setElementText(
        "#review-empty h3",
        t(
            "noCases"
        )
    );


    setElementText(
        "#review-empty p",
        t(
            "noCasesDescription"
        )
    );


    setElementText(
        "#review-case-panel .eyebrow",
        t(
            "reviewCase"
        )
    );


    setElementText(
        "#review-case-panel h2",
        t(
            "caseDetail"
        )
    );


    setElementText(
        "#close-review-case",
        t(
            "close"
        )
    );


    setAllText(
        ".case-meta .case-label",
        [
            t(
                "status"
            ),
            t(
                "risk"
            ),
            t(
                "evidence"
            ),
            t(
                "requestedBy"
            ),
        ]
    );


    const caseLabels =
        document.querySelectorAll(
            ".case-section > .case-label"
        );


    const labelValues = [
        t(
            "question"
        ),
        t(
            "riskReason"
        ),
        "Thread ID",
        t(
            "created"
        ),
        t(
            "reviewer"
        ),
        t(
            "policyProvenanceCase"
        ),
    ];


    caseLabels.forEach(
        (
            element,
            index
        ) => {

            if (
                labelValues[index]
                !== undefined
            ) {

                element.textContent =
                    labelValues[index];

            }

        }
    );


    setElementText(
        "#case-reject-button",
        t(
            "reject"
        )
    );


    setElementText(
        "#case-approve-button",
        t(
            "approve"
        )
    );

}


function translateAuditScreen() {

    setElementText(
        "#section-audit .section-header .eyebrow",
        t(
            "governanceTitle"
        )
    );


    setElementText(
        "#section-audit .section-header h1",
        t(
            "auditTitle"
        )
    );


    setElementText(
        "#section-audit .section-header p",
        t(
            "auditDescription"
        )
    );


    const titles =
        document.querySelectorAll(
            "#section-audit .timeline-item strong"
        );


    const titleValues = [
        t(
            "authenticated"
        ),
        t(
            "questionSubmitted"
        ),
        t(
            "riskAssessed"
        ),
        t(
            "governanceDecision"
        ),
        t(
            "humanReview"
        ),
    ];


    titles.forEach(
        (
            element,
            index
        ) => {

            if (
                titleValues[index]
                !== undefined
            ) {

                element.textContent =
                    titleValues[index];

            }

        }
    );

}


function translateAnalyticsScreen() {

    setElementText(
        "#section-analytics .section-header .eyebrow",
        t(
            "insights"
        )
    );


    setElementText(
        "#section-analytics .section-header h1",
        t(
            "analyticsTitle"
        )
    );


    setElementText(
        "#section-analytics .section-header p",
        t(
            "analyticsDescription"
        )
    );


    setAllText(
        "#section-analytics .analytics-label",
        [
            t(
                "questions"
            ),
            t(
                "groundedAnswers"
            ),
            t(
                "humanReviews"
            ),
            t(
                "safeRefusals"
            ),
            t(
                "highCritical"
            ),
        ]
    );

}


/* ============================================================= */
/* DYNAMIC VALUES                                                */
/* ============================================================= */


const tokenKeys = {

    "LOW":
        "low",

    "MEDIUM":
        "medium",

    "HIGH":
        "high",

    "CRITICAL":
        "critical",

    "ANSWER":
        "answer",

    "REFUSE":
        "refuse",

    "HUMAN REVIEW":
        "humanReviewDecision",

    "ACTION":
        "action",

    "REQUIRED":
        "required",

    "NOT REQUIRED":
        "notRequired",

    "ERROR":
        "error",

    "PENDING":
        "pending",

    "APPROVED":
        "approved",

    "REJECTED":
        "rejected",

    "TRACEABLE":
        "traceable",

    "PARTIAL":
        "partial",

    "LIMITED":
        "limited",

};


function translateKnownToken(
    value,
) {

    const source =
        String(
            value
            || ""
        ).trim();


    if (!source) {

        return source;

    }


    const allEnglish =
        Object.keys(
            tokenKeys
        );


    for (
        const english
        of allEnglish
    ) {

        const key =
            tokenKeys[
                english
            ];


        const arabic =
            translations.ar[
                key
            ];


        const englishValue =
            translations.en[
                key
            ];


        if (
            source.toUpperCase()
            === englishValue.toUpperCase()
            || source === arabic
        ) {

            return t(
                key
            );

        }

    }


    return source;

}


function translateDynamicContent() {

    document
        .querySelectorAll(
            [
                ".risk-value",
                ".metric-value",
                ".queue-risk",
                ".queue-status",
                ".traceability-chip",
                ".provenance-chip",
            ].join(",")
        )
        .forEach(
            element => {

                const translated =
                    translateKnownToken(
                        element.textContent
                    );


                if (
                    translated
                    !== element.textContent
                ) {

                    element.textContent =
                        translated;

                }

            }
        );


    document
        .querySelectorAll(
            ".open-case-button"
        )
        .forEach(
            element => {

                element.textContent =
                    t(
                        "openCase"
                    );

            }
        );


    document
        .querySelectorAll(
            ".provenance-field-label"
        )
        .forEach(
            element => {

                const value =
                    element.textContent
                        .trim();


                const labelMap = {

                    "Policy ID":
                        "policyId",

                    "معرف السياسة":
                        "policyId",

                    "Chunk ID":
                        "chunkId",

                    "معرف المقطع":
                        "chunkId",

                    "Section":
                        "section",

                    "القسم":
                        "section",

                    "Version":
                        "version",

                    "الإصدار":
                        "version",

                    "Effective Date":
                        "effectiveDate",

                    "تاريخ السريان":
                        "effectiveDate",

                    "Page":
                        "page",

                    "الصفحة":
                        "page",

                };


                const key =
                    labelMap[
                        value
                    ];


                if (key) {

                    element.textContent =
                        t(
                            key
                        );

                }

            }
        );


    document
        .querySelectorAll(
            ".evidence-excerpt-label"
        )
        .forEach(
            element => {

                element.textContent =
                    t(
                        "retrievedEvidence"
                    );

            }
        );


    document
        .querySelectorAll(
            ".provenance-field-value"
        )
        .forEach(
            element => {

                const value =
                    element.textContent
                        .trim();


                if (
                    value
                    === "Not provided"
                    || value
                    === translations.ar.notProvided
                ) {

                    element.textContent =
                        t(
                            "notProvided"
                        );

                }

            }
        );

}


/* ============================================================= */
/* APPLY LANGUAGE                                                */
/* ============================================================= */


function applyLanguage() {

    const isArabic =
        careGuardLanguage
        === "ar";


    document.documentElement.lang =
        careGuardLanguage;


    document.documentElement.dir =
        isArabic
            ? "rtl"
            : "ltr";


    document.body.classList.toggle(
        "lang-ar",
        isArabic
    );


    document
        .getElementById(
            "language-en"
        )
        ?.classList.toggle(
            "active",
            !isArabic
        );


    document
        .getElementById(
            "language-ar"
        )
        ?.classList.toggle(
            "active",
            isArabic
        );


    translateNavigation();

    translatePageHeader();

    translateAskScreen();

    translateReviewsScreen();

    translateAuditScreen();

    translateAnalyticsScreen();

    translateDynamicContent();

}


function setLanguage(
    language,
) {

    careGuardLanguage =
        (
            language === "ar"
            ? "ar"
            : "en"
        );


    localStorage.setItem(
        CAREGUARD_LANGUAGE_KEY,
        careGuardLanguage
    );


    applyLanguage();

}


/* ============================================================= */
/* OBSERVER FOR DYNAMIC CONTENT                                  */
/* ============================================================= */


function scheduleTranslation() {

    if (
        translationScheduled
    ) {

        return;

    }


    translationScheduled =
        true;


    requestAnimationFrame(
        () => {

            translationScheduled =
                false;


            translatePageHeader();

            translateDynamicContent();

        }
    );

}


function startTranslationObserver() {

    const observer =
        new MutationObserver(
            () => {

                scheduleTranslation();

            }
        );


    observer.observe(
        document.body,
        {

            childList:
                true,

            subtree:
                true,

            characterData:
                true,

        }
    );

}


/* ============================================================= */
/* STARTUP                                                       */
/* ============================================================= */


document.addEventListener(
    "DOMContentLoaded",
    () => {

        createLanguageSwitcher();

        applyLanguage();

        startTranslationObserver();

    }
);