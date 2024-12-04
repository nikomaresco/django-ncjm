document.addEventListener("DOMContentLoaded", function() {
    const reactionButtons = document.querySelectorAll(".reaction_button");

    reactionButtons.forEach(button => {
        button.addEventListener("click", function() {
            console.log("clicked " + this.getAttribute("data-emoji"));
            const emoji = this.getAttribute("data-emoji");
            console.log(emoji, joke_id);
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
                    const countSpan = this.querySelector(".reaction_count");
                    countSpan.textContent = data.new_count;
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error("Error:", error);
            });
        });
    });
});