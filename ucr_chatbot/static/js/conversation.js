const chatContainer = document.getElementById("chat-container");
const sidebarMessages = document.getElementById("sidebar-messages");
const userMessageTextarea = document.getElementById("userMessage");
const redirectButton = document.getElementById("redirectButton");
const converter = new showdown.Converter({ simpleLineBreaks: true });

let conversationId = document.body.dataset.conversationId
  ? Number(document.body.dataset.conversationId)
  : null;

let courseId = document.body.dataset.courseId
  ? Number(document.body.dataset.courseId)
  : null;

let isNewConversation = courseId !== null;

let isResolved = false;

async function loadAllConversationIds() {
  if (!courseId && !conversationId) return;

  let fetchUrl;
  let fetchBody;

  if (courseId) {
    fetchUrl = `/conversation/new/${courseId}/chat`;
    fetchBody = { type: "ids" };
  } else if (conversationId) {
    fetchUrl = `/conversation/new/0/chat`;
    fetchBody = { type: "ids" };
  }

  const res = await fetch(fetchUrl, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify(fetchBody),
  });

  const conversationIds = await res.json();

  sidebarMessages.innerHTML = "";

  conversationIds.reverse().forEach((id) => {
    addSidebarMessage(`Conversation ${id}`, id);
  });
}

async function loadAllConversationsForUser() {
  if (!conversationId) return;

  const res = await fetch(`/conversation/${conversationId}`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify({ type: "conversation" }),
  });

  const data = await res.json();

  chatContainer.innerHTML = "";

  data.messages.forEach((msg) => {
    appendMessage(msg.sender === "StudentMessage" ? "user" : "bot", msg.body);
  });

  sidebarMessages.innerHTML = "";

  conversationIds.reverse().forEach((id) => {
    addSidebarMessage(`Conversation ${id}`, id);
  });
}

async function loadAllConversationsForUser() {
  if (!conversationId) return;

  const res = await fetch(`/conversation/${conversationId}`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify({ type: "conversation" }),
  });

  const data = await res.json();

  chatContainer.innerHTML = "";

  data.messages.forEach((msg) => {
    appendMessage(msg.sender === "StudentMessage" ? "user" : "bot", msg.body);
  });
}

loadAllConversationIds();

// Set up periodic message checking for real-time updates
let messageCheckInterval;

if (!isNewConversation && conversationId) {
  loadAllConversationsForUser();
  loadAllConversationsForUser();
}

userMessageTextarea.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    handleSend(event);
  }
});

async function handleSend(e) {
  e.preventDefault();
  const textarea = document.getElementById("userMessage");
  const message = textarea.value.trim();
  if (!message) return;

  appendMessage("user", message);
  textarea.value = "";


  if (isNewConversation) {
    const res = await fetch(`/conversation/new/${courseId}/chat`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ type: "create", message }),
    });

    const data = await res.json();
    conversationId = data.conversationId;
    isNewConversation = false;

    window.history.replaceState({}, "", `/conversation/${conversationId}`);
    addSidebarMessage(`Conversation ${conversationId}`, conversationId);

    try {
      const botResponse = await fetchBotReply(message);
      appendMessage("bot", botResponse);
    } catch (error) {
      appendMessage("system", error.message);
      // If conversation is redirected, update the button state
      if (error.message.includes("redirected to a ULA")) {
        redirectButton.textContent = "Mark as Resolved";
        isResolved = true;
      }
    }
  } else {
    await sendMessage(message);
    try {
      const botResponse = await fetchBotReply(message);
      appendMessage("bot", botResponse);
    } catch (error) {
      appendMessage("system", error.message);
      // If conversation is redirected, update the button state
      if (error.message.includes("redirected to a ULA")) {
        redirectButton.textContent = "Mark as Resolved";
        isResolved = true;
      }
    }
  }
}

function appendMessage(sender, text) {
  const messageWrapper = document.createElement("div");
  messageWrapper.classList.add("message-wrapper", sender);

  const pfp = document.createElement("img");
  pfp.classList.add("pfp");

  if (sender === "user") {
    pfp.src = "/static/images/User_PFP.png";
    pfp.alt = "User";
  } else {
    pfp.src = "/static/images/Bot_PFP.png";
    pfp.alt = "Bot";
  }

  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", sender);

  const html = converter.makeHtml(text);
  messageDiv.innerHTML = html;

  messageDiv.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);
  });

  messageWrapper.appendChild(pfp);
  messageWrapper.appendChild(messageDiv);

  chatContainer.appendChild(messageWrapper);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addSidebarMessage(label, convoId) {
  if (document.querySelector(`[data-convo-id="${convoId}"]`)) return;

  const item = document.createElement("div");
  item.classList.add("conversation-item");
  item.textContent = label;
  item.dataset.convoId = convoId;

  item.addEventListener("click", () => {
    window.history.replaceState({}, "", `/conversation/${convoId}`);
    conversationId = convoId;
    chatContainer.innerHTML = "";
    loadAllConversationsForUser();
    loadAllConversationsForUser();
  });

  if (window.location.pathname.endsWith(convoId)) {
    item.classList.add("active");
  }

  sidebarMessages.insertBefore(item, sidebarMessages.firstChild);
}

async function sendMessage(message) {
  await fetch(`/conversation/${conversationId}`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify({ type: "send", message }),
  });
}

async function fetchBotReply(userMessage) {
  const res = await fetch(`/conversation/${conversationId}`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify({ type: "reply", message: userMessage }),
  });

  const data = await res.json();
  
  // Check for error responses
  if (!res.ok) {
    if (data.error === "conversation_redirected") {
      throw new Error("This conversation has been redirected to a ULA. Please wait for assistance.");
    } else if (data.error === "conversation_resolved") {
      throw new Error("This conversation has been resolved.");
    } else {
      throw new Error(data.message || "Failed to get bot reply");
    }
  }
  
  return data.reply;
}

// redirect conversation to assistant or mark as resolved
redirectButton.addEventListener("click", async () => {
  if (!conversationId) {
    alert("No conversation selected.");
    return;
  }

  if (!isResolved) {
    try {
      const res = await fetch(`/conversation/${conversationId}/redirect`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ type: "redirect" }),
      });

      if (!res.ok) throw new Error("Redirect request failed");

      const data = await res.json();
      if (data.status === "redirected") {
        redirectButton.textContent = "Mark as Resolved";
        isResolved = true;
        alert("Conversation has been redirected to an assistant. They will help you shortly!");
      }
    } catch (error) {
      console.error("Redirect error:", error);
      alert("Failed to redirect to assistant. Please try again.");
    }
  } else {
    try {
      const res = await fetch(`/conversation/${conversationId}/resolve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ type: "resolve" }),
      });

      if (!res.ok) throw new Error("Mark as resolved failed");

      const data = await res.json();
      if (data.status === "resolved") {
        redirectButton.textContent = "Resolved";
        redirectButton.disabled = true;
        alert("Conversation marked as resolved!");
      }
    } catch (error) {
      console.error("Resolve error:", error);
      alert("Failed to mark as resolved. Please try again.");
    }
  }
});

// Function to check for new messages from assistants
async function checkForNewMessages() {
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

    if (!res.ok) return;

    const data = await res.json();
    const currentMessageCount = chatContainer.children.length;
    
    // If there are new messages, reload the conversation
    if (data.messages.length > currentMessageCount) {
      loadAllConversationsForUser();
      
      // Show notification for assistant messages
      const newMessages = data.messages.slice(currentMessageCount);
      const assistantMessages = newMessages.filter(msg => msg.sender === "AssistantMessage");
      if (assistantMessages.length > 0) {
        // Show notification
        showNotification("New message from assistant!");
      }
    }
  } catch (error) {
    console.error("Error checking for new messages:", error);
  }
}

// Start periodic message checking for existing conversations
if (!isNewConversation && conversationId) {
  messageCheckInterval = setInterval(checkForNewMessages, 5000); // Check every 5 seconds
}

// Function to show notifications
function showNotification(message) {
  // Create notification element
  const notification = document.createElement("div");
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #28a745;
    color: white;
    padding: 15px 20px;
    border-radius: 5px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    z-index: 1000;
    font-family: 'Fira Sans', sans-serif;
    animation: slideIn 0.3s ease-out;
  `;
  notification.textContent = message;
  
  // Add CSS animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  `;
  document.head.appendChild(style);
  
  document.body.appendChild(notification);
  
  // Remove notification after 3 seconds
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease-in';
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }, 3000);
}

// Clean up interval when page is unloaded
window.addEventListener('beforeunload', function() {
  if (messageCheckInterval) {
    clearInterval(messageCheckInterval);
  }
});
