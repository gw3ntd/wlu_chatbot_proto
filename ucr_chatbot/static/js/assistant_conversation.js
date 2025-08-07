const chatContainer = document.getElementById("chat-container");
const sidebarMessages = document.getElementById("sidebar-messages");
const userMessageTextarea = document.getElementById("userMessage");
const resolveButton = document.getElementById("resolveButton");

let conversationId = document.body.dataset.conversationId
  ? Number(document.body.dataset.conversationId)
  : null;

let courseId = document.body.dataset.courseId
  ? Number(document.body.dataset.courseId)
  : null;

// Load conversation history when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (conversationId) {
        loadConversationHistory();
    }
});

async function loadConversationHistory() {
    if (!conversationId) return;

    try {
        const res = await fetch(`/conversation/${conversationId}`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ type: "conversation" }),
        });

        if (!res.ok) {
            throw new Error('Failed to load conversation');
        }

        const data = await res.json();
        chatContainer.innerHTML = "";

        data.messages.forEach((msg) => {
            const senderType = msg.sender === "StudentMessage" ? "user" : "bot";
            appendMessage(senderType, msg.body);
        });

        // Scroll to bottom to show latest messages
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } catch (error) {
        console.error("Error loading conversation:", error);
        appendMessage("system", "Error loading conversation history.");
    }
}

async function handleAssistantSend(e) {
    e.preventDefault();
    
    const message = userMessageTextarea.value.trim();
    if (!message) return;

    // Clear input
    userMessageTextarea.value = "";

    // Add assistant message to chat
    appendMessage("assistant", message);

    // Send message to backend
    try {
        const res = await fetch(`/assistant/conversation/${conversationId}/send`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ 
                type: "assistant_message", 
                message: message 
            }),
        });

        if (!res.ok) {
            throw new Error('Failed to send message');
        }

        const data = await res.json();
        if (data.status === "sent") {
            // Message sent successfully
            console.log("Assistant message sent successfully");
        }
    } catch (error) {
        console.error("Error sending assistant message:", error);
        appendMessage("system", "Error sending message. Please try again.");
    }
}

function appendMessage(sender, text) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}`;
    
    // Format the message based on sender type
    let displayText = text;
    if (sender === "assistant") {
        displayText = `🤖 Assistant: ${text}`;
    } else if (sender === "user") {
        displayText = `👤 Student: ${text}`;
    } else if (sender === "bot") {
        displayText = `🤖 Bot: ${text}`;
    } else if (sender === "system") {
        displayText = `⚠️ System: ${text}`;
        messageDiv.style.color = "#dc3545";
        messageDiv.style.fontStyle = "italic";
    }
    
    messageDiv.textContent = displayText;
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function resolveConversation() {
    if (!conversationId) {
        alert("No conversation selected.");
        return;
    }

    if (confirm("Are you sure you want to mark this conversation as resolved? This action cannot be undone.")) {
        try {
            const res = await fetch(`/conversation/${conversationId}/resolve`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Accept: "application/json",
                },
                body: JSON.stringify({ type: "resolve" }),
            });

            if (!res.ok) {
                throw new Error("Failed to resolve conversation");
            }

            const data = await res.json();
            if (data.status === "resolved") {
                resolveButton.textContent = "Resolved";
                resolveButton.disabled = true;
                resolveButton.style.backgroundColor = "#6c757d";
                
                // Show success message
                appendMessage("system", "✅ Conversation marked as resolved successfully!");
                
                // Redirect to dashboard after 2 seconds
                setTimeout(() => {
                    window.location.href = "/assistant/dashboard";
                }, 2000);
            }
        } catch (error) {
            console.error("Resolve error:", error);
            appendMessage("system", "❌ Failed to mark conversation as resolved. Please try again.");
        }
    }
}

// Auto-resize textarea
userMessageTextarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Handle Enter key (send on Enter, new line on Shift+Enter)
userMessageTextarea.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('input-form').dispatchEvent(new Event('submit'));
    }
}); 