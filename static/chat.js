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
            // get related articles
            const articleResponse = await fetch("/related_articles", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: query }),
            });
            const article_data = await articleResponse.json();
            updateSidebar(article_data.related_text);

            // start streaming chat response
            const chatResponse = await fetch("/chat", {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: query,
                    articles_list: article_data.articles_list
                }),
            });

            if (!chatResponse.ok) {
                throw new Error(`HTTP ${chatResponse.status}: ${chatResponse.statusText}`);
            }

            // add empty bot message to fill with streamed content
            addMessage("bot", "");
            const lastBotMessage = chatWindow.querySelector(".message.bot:last-child .message-content");
            let accumulatedText = "";

            // read the plain text stream directly from llm
            const reader = chatResponse.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                accumulatedText += chunk;
                
                // apply markdown formatting
                lastBotMessage.innerHTML = formatBotMessage(accumulatedText);
                lastBotMessage.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }
            
            setLoading(false);

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
        
        if (sender === 'bot' && content) {
            messageContent.innerHTML = formatBotMessage(content);
        } else {
            messageContent.textContent = content || "";
        }
        
        messageDiv.appendChild(messageContent);
        chatWindow.appendChild(messageDiv);
        messageDiv.scrollIntoView({ behavior: 'smooth', block: sender === 'bot' ? 'start' : 'end' });
    }

// AI for this Markdown formatting below

    function formatBotMessage(text) {
        // escape HTML first
        let formatted = escapeHtml(text);
        
        // headers
        formatted = formatted.replace(/^#### (.+)$/gm, '<div style="font-size: 16px; font-weight: 600; margin: 6px 0 3px 0;">$1</div>');
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
    }

    function updateSidebar(content) {
        sidebarWindow.textContent = typeof content === "string" ? content : JSON.stringify(content, null, 2);
    }
});