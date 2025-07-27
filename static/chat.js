const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const chatWindow = document.getElementById("chat-window");

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    // Show user message
    input.value = "";

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ message: query }),
        });

        const data = await response.json();

    } catch (err) {
        console.error("Error:", err);
    }
});