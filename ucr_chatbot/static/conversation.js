const chatContainer = document.getElementById("chat-container");
const sidebarMessages = document.getElementById("sidebar-messages");
const userMessageTextarea = document.getElementById("userMessage");

let conversationId = document.body.dataset.conversationId
  ? Number(document.body.dataset.conversationId)
  : null;

let courseId = document.body.dataset.courseId
  ? Number(document.body.dataset.courseId)
  : null;

let isNewConversation = courseId !== null;

async function loadAllConversationsForUser() {
  sidebarMessages.innerHTML = "";

  const res = await fetch("/api/conversations/get_conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ courseId }), 
  });

  const conversationIds = await res.json();

  sidebarMessages.innerHTML = "";

  conversationIds.reverse().forEach((id) => {
    addSidebarMessage(`Conversation ${id}`, id);
  });
}

//loads a conversation's messages
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

if (!isNewConversation && conversationId) {
  loadAllConversationsForUser();
}

// Send message on Enter key press
userMessageTextarea.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    handleSend(event);
  }
});

// Send message to interface
async function handleSend(e) {
  e.preventDefault();
  const textarea = document.getElementById("userMessage");
  const message = textarea.value.trim();
  if (!message) return;

  appendMessage("user", message);
  textarea.value = "";


  if (isNewConversation) {
    const res = await fetch("/api/create_conversation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ courseId, message }), 
    });

    const data = await res.json();
    conversationId = data.conversationId;
    isNewConversation = false;

    window.history.replaceState({}, "", `/conversation/${conversationId}`);
    addSidebarMessage(`Conversation ${conversationId}`, conversationId);

    const botResponse = await fetchBotReply(conversationId, message);
    appendMessage("bot", botResponse);
  } else {
    await sendMessage(conversationId, message);
    const botResponse = await fetchBotReply(conversationId, message);
    appendMessage("bot", botResponse);
  }
}


// Add user or bot message to interface
function appendMessage(sender, text) {
  const div = document.createElement("div");
  div.classList.add("message", sender);
  div.textContent = text;
  chatContainer.appendChild(div);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Add convo to sidebar
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
  });

  if (window.location.pathname.endsWith(convoId)) {
    item.classList.add("active");
  }

  sidebarMessages.insertBefore(item, sidebarMessages.firstChild);
}

// Load existing conversation and display messages
async function loadConversation(id) {
  const res = await fetch(`/api/conversations/${id}`);
  const data = await res.json();

  chatContainer.innerHTML = "";

  data.messages.forEach((msg) => {
    appendMessage(msg.sender === "StudentMessage" ? "user" : "bot", msg.body);
  });

  const firstUserMessage = data.messages.find((m) => m.sender === "user");
  if (firstUserMessage) {
    addSidebarMessage(firstUserMessage.body, id);
  }
}

// Send message to backend for LM
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

// Get LM response from backend
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
