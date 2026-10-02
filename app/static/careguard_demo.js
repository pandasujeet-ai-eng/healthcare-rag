"use strict";





/* ============================================================= */

/* CAREGUARD V1.7.2 - HACKATHON DEMO POLISH                        */

/* ============================================================= */





let lastObservedState =

    null;





const demoScenarios = [



    {

        type:

            "Grounded Answer",



        name:

            "Approved policy",



        description:

            "Demonstrates evidence-grounded policy answering.",



    },



    {

        type:

            "Human Oversight",



        name:

            "Evidence conflict",



        description:

            "Challenges an incorrect policy assumption and triggers review.",



    },



    {

        type:

            "Safe Refusal",



        name:

            "Unsupported request",



        description:

            "Shows how CareGuard refuses when approved evidence is unavailable.",



    },



    {

        type:

            "Clinical Safety",



        name:

            "Critical request",



        description:

            "Demonstrates clinical risk detection and mandatory oversight.",



    },



];





/* ============================================================= */

/* TRUST STRIP                                                   */

/* ============================================================= */





function createTrustStrip() {



    if (

        document.querySelector(

            ".demo-trust-strip"

        )

    ) {



        return;



    }





    const askSection =

        document.getElementById(

            "section-ask"

        );





    const hero =

        askSection

            ?.querySelector(

                ".hero"

            );





    if (

        !askSection

        || !hero

    ) {



        return;



    }





    const strip =

        document.createElement(

            "div"

        );





    strip.className =

        "demo-trust-strip";





    strip.innerHTML = `

        <div class="demo-trust-left">



            <div class="demo-mode-chip">



                <span class="demo-mode-dot"></span>



                HACKATHON DEMO MODE



            </div>



            <div class="demo-trust-message">

                Governance-first healthcare AI over approved knowledge

            </div>



        </div>





        <div class="demo-capabilities">



            <span class="demo-capability">

                Evidence Grounded

            </span>



            <span class="demo-capability">

                Risk Aware

            </span>



            <span class="demo-capability">

                Human Oversight

            </span>



            <span class="demo-capability">

                Auditable

            </span>



        </div>

    `;





    askSection.insertBefore(

        strip,

        hero

    );



}





/* ============================================================= */

/* SCENARIO CARDS                                                */

/* ============================================================= */





function enhanceScenarioCards() {



    const row =

        document.querySelector(

            ".example-row"

        );





    if (!row) {



        return;



    }





    if (

        !document.querySelector(

            ".demo-scenario-title"

        )

    ) {



        const title =

            document.createElement(

                "div"

            );





        title.className =

            "demo-scenario-title";





        title.innerHTML = `

            <div class="demo-scenario-heading">

                Demo Scenarios

            </div>



            <div class="demo-scenario-helper">

                Select a scenario, then ask CareGuard

            </div>

        `;





        row.parentElement.insertBefore(

            title,

            row

        );



    }





    const buttons =

        row.querySelectorAll(

            ".example-question"

        );





    buttons.forEach(

        (

            button,

            index

        ) => {



            if (

                button.dataset.demoEnhanced

                === "true"

            ) {



                return;



            }





            const scenario =

                demoScenarios[

                    index

                ];





            if (!scenario) {



                return;



            }





            button.dataset.demoEnhanced =

                "true";





            button.innerHTML = `

                <span class="demo-scenario-number">

                    ${index + 1}

                </span>



                <span class="demo-scenario-type">

                    ${escapeDemoHtml(

                        scenario.type

                    )}

                </span>



                <span class="demo-scenario-name">

                    ${escapeDemoHtml(

                        scenario.name

                    )}

                </span>



                <span class="demo-scenario-description">

                    ${escapeDemoHtml(

                        scenario.description

                    )}

                </span>

            `;





            button.addEventListener(

                "click",

                () => {



                    setActiveScenario(

                        button

                    );



                }

            );



        }

    );



}





function setActiveScenario(

    selectedButton,

) {



    document

        .querySelectorAll(

            ".example-question"

        )

        .forEach(

            button => {



                button

                    .classList

                    .remove(

                        "active-demo"

                    );



            }

        );





    selectedButton

        .classList

        .add(

            "active-demo"

        );



}





/* ============================================================= */

/* HEADER                                                        */

/* ============================================================= */





function createHeaderControls() {



    if (

        document.querySelector(

            ".demo-header-controls"

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





    const controls =

        document.createElement(

            "div"

        );





    controls.className =

        "demo-header-controls";





    controls.innerHTML = `

        <button

            id="demo-reset-button"

            class="demo-reset-button"

            type="button"

            title="Reset the presentation UI"

        >

            ↻ Reset Demo

        </button>

    `;





    userArea.insertBefore(

        controls,

        userArea.firstChild

    );





    document

        .getElementById(

            "demo-reset-button"

        )

        .addEventListener(

            "click",

            resetDemo

        );



}





/* ============================================================= */

/* RESET                                                         */

/* ============================================================= */





function resetDemo() {



    const question =

        document.getElementById(

            "question-input"

        );





    if (question) {



        question.value =

            "";



    }





    document

        .querySelectorAll(

            ".example-question"

        )

        .forEach(

            button => {



                button

                    .classList

                    .remove(

                        "active-demo"

                    );



            }

        );





    const hideIds = [



        "result-area",



        "review-banner",



        "review-actions",



        "answer-card",



        "provenance-card",



        "error-card",



        "risk-reason-card",



    ];





    hideIds.forEach(

        id => {



            document

                .getElementById(

                    id

                )

                ?.classList

                .add(

                    "hidden"

                );



        }

    );





    const askNav =

        document.querySelector(

            '[data-section="ask"]'

        );





    if (askNav) {



        askNav.click();



    }





    window.scrollTo(

        {

            top:

                0,



            behavior:

                "smooth",

        }

    );





    showDemoToast(

        "success",

        "Demo reset",

        "CareGuard is ready for the next scenario."

    );



}





/* ============================================================= */

/* RESULT ANIMATION                                              */

/* ============================================================= */





function animateResults() {



    const result =

        document.getElementById(

            "result-area"

        );





    if (!result) {



        return;



    }





    result

        .classList

        .remove(

            "demo-result-enter"

        );





    void result.offsetWidth;





    result

        .classList

        .add(

            "demo-result-enter"

        );



}





/* ============================================================= */

/* TOASTS                                                        */

/* ============================================================= */





function ensureToastRegion() {



    let region =

        document.querySelector(

            ".demo-toast-region"

        );





    if (region) {



        return region;



    }





    region =

        document.createElement(

            "div"

        );





    region.className =

        "demo-toast-region";





    region.setAttribute(

        "aria-live",

        "polite"

    );





    document.body.appendChild(

        region

    );





    return region;



}





function showDemoToast(

    type,

    title,

    message,

) {



    const region =

        ensureToastRegion();





    const toast =

        document.createElement(

            "div"

        );





    toast.className =

        `demo-toast ${type}`;





    const iconMap = {



        success:

            "✓",



        review:

            "!",



        refusal:

            "i",



        critical:

            "!",



    };





    toast.innerHTML = `

        <div class="demo-toast-icon">

            ${iconMap[type] || "i"}

        </div>



        <div>



            <div class="demo-toast-title">

                ${escapeDemoHtml(title)}

            </div>



            <div class="demo-toast-message">

                ${escapeDemoHtml(message)}

            </div>



        </div>

    `;





    region.appendChild(

        toast

    );





    window.setTimeout(

        () => {



            toast.remove();



        },

        4200

    );



}





/* ============================================================= */

/* WATCH GOVERNANCE OUTCOME                                      */

/* ============================================================= */





function observeOutcome() {



    const resultArea =

        document.getElementById(

            "result-area"

        );





    if (!resultArea) {



        return;



    }





    const observer =

        new MutationObserver(

            () => {



                evaluateCurrentOutcome();



            }

        );





    observer.observe(

        resultArea,

        {

            childList:

                true,



            subtree:

                true,



            attributes:

                true,



            characterData:

                true,

        }

    );



}





function evaluateCurrentOutcome() {



    const result =

        document.getElementById(

            "result-area"

        );





    if (

        !result

        || result.classList.contains(

            "hidden"

        )

    ) {



        return;



    }





    const risk =

        document

            .getElementById(

                "risk-value"

            )

            ?.textContent

            ?.trim()

            ?.toUpperCase()

        || "";





    const decision =

        document

            .getElementById(

                "decision-value"

            )

            ?.textContent

            ?.trim()

            ?.toUpperCase()

        || "";





    const answer =

        document

            .getElementById(

                "answer-text"

            )

            ?.textContent

            ?.trim()

        || "";





    const reviewVisible =

        !document

            .getElementById(

                "review-banner"

            )

            ?.classList

            .contains(

                "hidden"

            );





    let state =

        "";





    if (

        risk.includes(

            "CRITICAL"

        )

        && reviewVisible

    ) {



        state =

            "critical-review";



    } else if (

        reviewVisible

    ) {



        state =

            "review";



    } else if (

        answer

            .toLowerCase()

            .includes(

                "cannot find sufficient information"

            )

    ) {



        state =

            "refusal";



    } else if (

        answer

        && decision.includes(

            "ANSWER"

        )

    ) {



        state =

            "answer";



    }





    if (

        !state

        || state

            === lastObservedState

    ) {



        return;



    }





    lastObservedState =

        state;





    animateResults();





    if (

        state

        === "critical-review"

    ) {



        showDemoToast(

            "critical",

            "Critical request intercepted",

            "CareGuard requires authorized human oversight before proceeding."

        );



    } else if (

        state

        === "review"

    ) {



        showDemoToast(

            "review",

            "Human review required",

            "The request has been escalated to the Reviewer Command Center."

        );



    } else if (

        state

        === "refusal"

    ) {



        showDemoToast(

            "refusal",

            "Safe refusal",

            "CareGuard found insufficient approved evidence and refused to speculate."

        );



    } else if (

        state

        === "answer"

    ) {



        showDemoToast(

            "success",

            "Grounded response ready",

            "The answer was generated using approved supporting evidence."

        );



    }



}





/* ============================================================= */

/* VERSION                                                       */

/* ============================================================= */





function updateVersion() {



    const version =

        document.querySelector(

            ".footer-version"

        );





    if (version) {



        version.textContent =

            "Hackathon Product V1.7.2";



    }



}





/* ============================================================= */

/* RTL AWARE SMALL TEXT                                          */

/* ============================================================= */





function updateDemoLanguage() {



    const arabic =

        document.documentElement.lang

        === "ar";





    const chip =

        document.querySelector(

            ".demo-mode-chip"

        );





    const message =

        document.querySelector(

            ".demo-trust-message"

        );





    const heading =

        document.querySelector(

            ".demo-scenario-heading"

        );





    const helper =

        document.querySelector(

            ".demo-scenario-helper"

        );





    const reset =

        document.getElementById(

            "demo-reset-button"

        );





    if (arabic) {



        if (chip) {



            chip.lastChild.textContent =

                " وضع العرض التجريبي";



        }





        if (message) {



            message.textContent =

                "ذكاء اصطناعي محكوم يعتمد على المعرفة المعتمدة";



        }





        if (heading) {



            heading.textContent =

                "سيناريوهات العرض";



        }





        if (helper) {



            helper.textContent =

                "اختر سيناريو ثم اسأل CareGuard";



        }





        if (reset) {



            reset.textContent =

                "↻ إعادة العرض";



        }



    } else {



        if (chip) {



            chip.lastChild.textContent =

                " HACKATHON DEMO MODE";



        }





        if (message) {



            message.textContent =

                "Governance-first healthcare AI over approved knowledge";



        }





        if (heading) {



            heading.textContent =

                "Demo Scenarios";



        }





        if (helper) {



            helper.textContent =

                "Select a scenario, then ask CareGuard";



        }





        if (reset) {



            reset.textContent =

                "↻ Reset Demo";



        }



    }



}





/* ============================================================= */

/* LANGUAGE OBSERVER                                             */

/* ============================================================= */





function observeLanguage() {



    const observer =

        new MutationObserver(

            mutations => {



                mutations.forEach(

                    mutation => {



                        if (

                            mutation.type

                            === "attributes"

                            && mutation.attributeName

                                === "lang"

                        ) {



                            updateDemoLanguage();



                        }



                    }

                );



            }

        );





    observer.observe(

        document.documentElement,

        {

            attributes:

                true,



            attributeFilter: [

                "lang",

            ],

        }

    );



}





/* ============================================================= */

/* HELPERS                                                       */

/* ============================================================= */





function escapeDemoHtml(

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





/* ============================================================= */

/* STARTUP                                                       */

/* ============================================================= */





document.addEventListener(

    "DOMContentLoaded",

    () => {



        createTrustStrip();



        enhanceScenarioCards();



        createHeaderControls();



        ensureToastRegion();



        updateVersion();



        updateDemoLanguage();



        observeOutcome();



        observeLanguage();



    }

);