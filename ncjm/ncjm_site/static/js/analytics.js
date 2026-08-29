(function() {
    "use strict";

    function track(eventName, parameters) {
        if (typeof window.gtag !== "function") {
            return;
        }

        window.gtag("event", eventName, parameters || {});
    }

    window.ncjmAnalytics = Object.freeze({ track: track });

    document.addEventListener("DOMContentLoaded", function() {
        document.querySelectorAll("[data-analytics-event]").forEach(function(element) {
            element.addEventListener("click", function() {
                track(element.dataset.analyticsEvent, {
                    source: element.dataset.analyticsSource || "unknown"
                });
            });
        });
    });
})();
