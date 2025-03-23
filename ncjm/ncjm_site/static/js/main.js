document.addEventListener("DOMContentLoaded", function() {

    // handle joke reactions
    const reactionButtons = document.querySelectorAll(".reaction-button");

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
                    const countSpan = this.querySelector(".reaction-count");
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

    // handle form switching
    const showForm = (formType) => {
        document.getElementById("CornyJoke-form").classList.add("hidden");
        document.getElementById("LongJoke-form").classList.add("hidden");

        if (formType === "long") {
            document.getElementById("LongJoke-form").classList.remove("hidden");
        } else {
            document.getElementById("CornyJoke-form").classList.remove("hidden");
        }
    }

    // show the appropriate form based on the initial form type
    // default to corny form if no initial form type is set
    const initialFormType = document.querySelector('input[name="form_type"]').value;
    if (initialFormType === "LongJoke") {
        showForm("LongJoke");
    } else {
        showForm("CornyJoke");
    }

    // add event listeners to the buttons
    document.getElementById("CornyJoke-button").addEventListener("click", function() {
        showForm("CornyJoke");
    });

    document.getElementById("LongJoke-button").addEventListener("click", function() {
        showForm("LongJoke");
    });
});