const chatContainer = document.getElementById("chat-container");
const sidebarMessages = document.getElementById("sidebar-messages");
const userMessageTextarea = document.getElementById("userMessage");
const redirectButton = document.getElementById("redirectButton");

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

    const botResponse = await fetchBotReply(message);
    appendMessage("bot", botResponse);
  } else {
    await sendMessage(message);
    const botResponse = await fetchBotReply(message);
    appendMessage("bot", botResponse);
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
  messageDiv.textContent = text;

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
        // BACKEND: update this endpoint to handle redirects to assistant
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ type: "redirect" }),
      });

      if (!res.ok) throw new Error("Redirect request failed");

      redirectButton.textContent = "Mark as Resolved";
      isResolved = true;
    } catch (error) {
      console.error("Redirect error:", error);
      alert("Failed to redirect to tutor.");
    }
  } else {
    try {
      const res = await fetch(`/conversation/${conversationId}/resolve`, {
        // BACKEND: update this endpoint to handle resolution of conversation
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ type: "resolve" }),
      });

      if (!res.ok) throw new Error("Mark as resolved failed");

      redirectButton.textContent = "Resolved";
      redirectButton.disabled = true;
    } catch (error) {
      console.error("Resolve error:", error);
      alert("Failed to mark as resolved.");
    }
  }
});
