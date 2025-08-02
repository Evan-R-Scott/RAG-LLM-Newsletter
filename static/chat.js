document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("message-input");
    const chatWindow = document.getElementById("chat-window");
    const sidebarWindow = document.getElementById("similarity_search_json");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const query = input.value.trim();

        if (!query) return;

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
            
            addMessageToChat("user", query);
            addMessageToChat("bot", data.summary);
            addMessageToChat(null, data.related_text);

        } catch (err) {
            console.error("Error:", err);
        }
    });

    function addMessageToChat(sender = null, content) {
        if (sender) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', sender);
            messageDiv.innerHTML = content;
            chatWindow.appendChild(messageDiv);

            if(sender == 'user') {
                messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }
        } else {
            const jsonString = typeof content === "string" ? content : JSON.stringify(content, null, 2);
            sidebarWindow.textContent = jsonString;
        }
    }
});