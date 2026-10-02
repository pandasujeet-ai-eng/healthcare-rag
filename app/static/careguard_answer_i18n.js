"use strict";


/* ============================================================= */
/* CAREGUARD V1.6B - GROUNDED ANSWER LOCALIZATION                */
/* ============================================================= */


const ANSWER_SELECTOR =
    "#answer-text";


let originalEnglishAnswer =
    null;


let translatedArabicAnswer =
    null;


let translationInProgress =
    false;


let internalAnswerUpdate =
    false;


/* ============================================================= */
/* LANGUAGE                                                      */
/* ============================================================= */


function currentLanguage() {

    return (
        localStorage.getItem(
            "careguard_language"
        )
        || "en"
    );

}


/* ============================================================= */
/* TRANSLATION API                                               */
/* ============================================================= */


async function translateToArabic(
    sourceText,
) {

    const response =
        await fetch(
            "/api/v1/localization/translate",
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

                            text:
                                sourceText,

                            target_language:
                                "ar",

                        }
                    ),

            }
        );


    const body =
        await response.json();


    if (!response.ok) {

        throw new Error(
            (
                body.detail
                && body.detail.detail
            )
            || body.detail
            || "Arabic translation failed."
        );

    }


    return (
        body.translated_text
    );

}


/* ============================================================= */
/* ANSWER STATE                                                  */
/* ============================================================= */


function answerElement() {

    return document.querySelector(
        ANSWER_SELECTOR
    );

}


function setAnswerText(
    text,
) {

    const element =
        answerElement();


    if (!element) {

        return;

    }


    internalAnswerUpdate =
        true;


    element.textContent =
        text;


    queueMicrotask(
        () => {

            internalAnswerUpdate =
                false;

        }
    );

}


/* ============================================================= */
/* APPLY LANGUAGE                                                */
/* ============================================================= */


async function applyAnswerLanguage() {

    const element =
        answerElement();


    if (!element) {

        return;

    }


    const visibleText =
        element.textContent
            .trim();


    if (!visibleText) {

        return;

    }


    const language =
        currentLanguage();


    if (
        language === "en"
    ) {

        if (
            originalEnglishAnswer
        ) {

            setAnswerText(
                originalEnglishAnswer
            );

        }

        return;

    }


    if (
        translatedArabicAnswer
    ) {

        setAnswerText(
            translatedArabicAnswer
        );

        return;

    }


    if (
        !originalEnglishAnswer
    ) {

        originalEnglishAnswer =
            visibleText;

    }


    if (
        translationInProgress
    ) {

        return;

    }


    translationInProgress =
        true;


    try {

        const translated =
            await translateToArabic(
                originalEnglishAnswer
            );


        translatedArabicAnswer =
            translated;


        if (
            currentLanguage()
            === "ar"
        ) {

            setAnswerText(
                translatedArabicAnswer
            );

        }

    } catch (error) {

        console.error(
            "CareGuard Arabic answer translation failed.",
            error
        );

    } finally {

        translationInProgress =
            false;

    }

}


/* ============================================================= */
/* WATCH NEW GROUNDED ANSWERS                                    */
/* ============================================================= */


function watchAnswer() {

    const element =
        answerElement();


    if (!element) {

        return;

    }


    const observer =
        new MutationObserver(
            async () => {

                if (
                    internalAnswerUpdate
                ) {

                    return;

                }


                const value =
                    element.textContent
                        .trim();


                if (!value) {

                    return;

                }


                /*
                 * A fresh answer has been produced by CareGuard.
                 */

                originalEnglishAnswer =
                    value;


                translatedArabicAnswer =
                    null;


                await applyAnswerLanguage();

            }
        );


    observer.observe(
        element,
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
/* WATCH LANGUAGE CHANGES                                        */
/* ============================================================= */


function watchLanguageSwitch() {

    const observer =
        new MutationObserver(
            async mutations => {

                for (
                    const mutation
                    of mutations
                ) {

                    if (
                        mutation.type
                        === "attributes"
                        && (
                            mutation.attributeName
                            === "lang"
                            || mutation.attributeName
                            === "dir"
                        )
                    ) {

                        await applyAnswerLanguage();

                        return;

                    }

                }

            }
        );


    observer.observe(
        document.documentElement,
        {
            attributes:
                true,

            attributeFilter: [
                "lang",
                "dir",
            ],
        }
    );

}


/* ============================================================= */
/* STARTUP                                                       */
/* ============================================================= */


document.addEventListener(
    "DOMContentLoaded",
    () => {

        watchAnswer();

        watchLanguageSwitch();

    }
);