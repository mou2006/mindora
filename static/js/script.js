// =====================================================
// MindSentinel - Global JavaScript
// =====================================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("MindSentinel JavaScript loaded successfully.");


    // =================================================
    // FLASH MESSAGE - CLOSE BUTTON
    // =================================================

    const closeButtons =
        document.querySelectorAll(".flash-close");

    closeButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            const message =
                button.closest(".flash-message");

            if (message) {

                message.style.transition =
                    "opacity 0.4s ease";

                message.style.opacity = "0";

                setTimeout(function () {

                    message.remove();

                }, 400);

            }

        });

    });


    // =================================================
    // AUTO-HIDE FLASH MESSAGES
    // =================================================

    const flashMessages =
        document.querySelectorAll(".flash-message");

    flashMessages.forEach(function (message) {

        setTimeout(function () {

            message.style.transition =
                "opacity 0.4s ease";

            message.style.opacity = "0";


            setTimeout(function () {

                if (message) {
                    message.remove();
                }

            }, 400);

        }, 4000);

    });


    // =================================================
    // FORM SUBMIT PROTECTION
    // Prevent accidental double submission
    // =================================================

    const forms =
        document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.addEventListener(
            "submit",
            function () {

                const submitButton =
                    form.querySelector(
                        'button[type="submit"], input[type="submit"]'
                    );


                if (submitButton) {

                    setTimeout(function () {

                        submitButton.disabled = true;

                        submitButton.style.opacity =
                            "0.7";

                        submitButton.style.cursor =
                            "not-allowed";

                    }, 50);

                }

            }
        );

    });


    // =================================================
    // NAVBAR SUPPORT
    // =================================================

    const navbar =
        document.querySelector(".navbar");

    if (navbar) {

        navbar.classList.add(
            "mindsentinel-navbar-loaded"
        );

    }


    // =================================================
    // SMOOTH SCROLL
    // =================================================

    const internalLinks =
        document.querySelectorAll(
            'a[href^="#"]'
        );

    internalLinks.forEach(function (link) {

        link.addEventListener(
            "click",
            function (event) {

                const targetId =
                    link.getAttribute("href");

                if (
                    targetId &&
                    targetId !== "#"
                ) {

                    const target =
                        document.querySelector(
                            targetId
                        );

                    if (target) {

                        event.preventDefault();

                        target.scrollIntoView({
                            behavior: "smooth"
                        });

                    }

                }

            }
        );

    });


    // =================================================
    // PAGE LOADED
    // =================================================

    console.log(
        "MindSentinel: All JavaScript features initialized."
    );

});
