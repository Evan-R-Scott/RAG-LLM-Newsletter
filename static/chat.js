document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("message-input");
    const chatWindow = document.getElementById("chat-window");
    const sidebarWindow = document.getElementById("similarity_search_json");
    const submitButton = form.querySelector('button[type="submit"]');

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const query = input.value.trim();
        if (!query) return;

        addMessage("user", query);
        input.value = "";
        setLoading(true);

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: query }),
            });
            const data = await response.json();
            
            setLoading(false);
            addMessage("bot", data.summary);
            updateSidebar(data.related_text);
        } catch (err) {
            console.error("Error:", err);
            setLoading(false);
            addMessage("bot", "Sorry, I encountered an error. Please try again.");
        }
    });

    function addMessage(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        
        messageContent.innerHTML = sender === 'bot' ? formatBotMessage(content) : escapeHtml(content);
        
        messageDiv.appendChild(messageContent);
        chatWindow.appendChild(messageDiv);
        messageDiv.scrollIntoView({ behavior: 'smooth', block: sender === 'bot' ? 'start' : 'end' });
    }

// The code below was AI-generated because Markdown was not integrating well with LLM generation

    function formatBotMessage(text) {
        // escape HTML first
        let formatted = escapeHtml(text);
        
        // headers
        formatted = formatted.replace(/^### (.+)$/gm, '<div style="font-size: 17px; font-weight: 600; margin: 8px 0 4px 0;">$1</div>');
        formatted = formatted.replace(/^## (.+)$/gm, '<div style="font-size: 18px; font-weight: 600; margin: 10px 0 5px 0;">$1</div>');
        formatted = formatted.replace(/^# (.+)$/gm, '<div style="font-size: 20px; font-weight: 600; margin: 12px 0 6px 0;">$1</div>');
        
        // bold and italic
        formatted = formatted.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/(?<!\*)\*([^*\s][^*]*?[^*\s])\*(?!\*)/g, '<em>$1</em>');
        
        // bullet points
        formatted = formatted.replace(/^[*•-]\s+(.+)$/gm, '• $1');
        
        // split into paragraphs and format
        return formatted
            .split(/\n\s*\n/)
            .map(section => section.trim())
            .filter(section => section.length > 0)
            .map(section => `<div style="margin-bottom: 6px; line-height: 1.5;">${section.replace(/\n/g, '<br>')}</div>`)
            .join('');
    }

    function escapeHtml(text) {
        return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function setLoading(isLoading) {
        input.disabled = isLoading;
        submitButton.disabled = isLoading;
        submitButton.textContent = isLoading ? 'Thinking...' : 'Send';
        
        if (isLoading) {
            addTypingIndicator();
            sidebarWindow.textContent = "Searching for relevant articles...";
        } else {
            removeTypingIndicator();
        }
    }

    function updateSidebar(content) {
        sidebarWindow.textContent = typeof content === "string" ? content : JSON.stringify(content, null, 2);
    }

    function addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('typing-indicator');
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        chatWindow.appendChild(typingDiv);
        typingDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }
});