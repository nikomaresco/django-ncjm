document.addEventListener("DOMContentLoaded", function() {
    const reactionButtons = document.querySelectorAll(".reaction-button");

    reactionButtons.forEach(button => {
        button.addEventListener("click", function() {
            const emoji = this.getAttribute("data-emoji");
            const reactionLabel = this.getAttribute("aria-label") || "unknown";

            if (window.ncjmAnalytics) {
                window.ncjmAnalytics.track("reaction_attempt", {
                    "joke_format": "classic",
                    "reaction_label": reactionLabel
                });
            }

            fetch(react_url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrf_token,
                },
                body: JSON.stringify({
                    joke_id: joke_id,
                    reaction_emoji: emoji,
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.status == "success") {
                    const countSpan = this.querySelector(".reaction-count");
                    countSpan.textContent = data.new_count;
                    if (window.ncjmAnalytics) {
                        window.ncjmAnalytics.track("reaction_result", {
                            "joke_format": "classic",
                            "reaction_label": reactionLabel,
                            "result": "success"
                        });
                    }
                } else {
                    if (window.ncjmAnalytics) {
                        window.ncjmAnalytics.track("reaction_result", {
                            "joke_format": "classic",
                            "reaction_label": reactionLabel,
                            "result": "rejected"
                        });
                    }
                    alert(data.message);
                }
            })
            .catch(error => {
                if (window.ncjmAnalytics) {
                    window.ncjmAnalytics.track("reaction_result", {
                        "joke_format": "classic",
                        "reaction_label": reactionLabel,
                        "result": "network_error"
                    });
                }
                console.error("Error:", error);
            });
        });
    });
});
