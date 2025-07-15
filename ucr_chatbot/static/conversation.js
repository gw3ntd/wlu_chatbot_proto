const chatContainer = document.getElementById("chat-container");
const sidebarMessages = document.getElementById("sidebar-messages");
const userMessageTextarea = document.getElementById("userMessage");

let conversationId = null;
let isNewConversation = false;

// Detect if this is a new conversation or not (for the sidebar)
const path = window.location.pathname;
if (path.startsWith("/new_conversation/")) {
  isNewConversation = true;
} else if (path.startsWith("/conversation/")) {
  conversationId = path.split("/").pop();
}

if (!isNewConversation && conversationId) {
  loadConversation(conversationId);
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
<<<<<<< HEAD

  

=======
>>>>>>> 6090418 (Sidebar edit)
  e.preventDefault();
  const textarea = document.getElementById("userMessage");
  const message = textarea.value.trim();
  if (!message) return;

  appendMessage("user", message);
<<<<<<< HEAD
  addSidebarMessage(message); // this just adds every message to the sidebar - needs to summarize conversations like chatgpt
  textarea.value = "";

  // FIX
  // Creates a new conversation
  if (isNewConversation) {
    const courseId = Number(path.split("/")[2]);
=======
  textarea.value = "";

  if (isNewConversation) {
    // Create new conversation
    const courseId = path.split("/").pop();
>>>>>>> 6090418 (Sidebar edit)
    const res = await fetch("/api/create_conversation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ courseId, message }),
    });

    const data = await res.json();
    conversationId = data.conversationId;
    isNewConversation = false;
    window.history.replaceState({}, "", `/conversation/${conversationId}`);

<<<<<<< HEAD
    const botResponse = await fetchBotReply(conversationId, message);
    appendMessage("bot", botResponse);
  } else {
=======
    // Add this conversation to the sidebar
    addSidebarMessage(message, conversationId);

    // Get bot response and show to interface
    const botResponse = await fetchBotReply(conversationId, message);
    appendMessage("bot", botResponse);
  } else {
    // Use existing conversation
>>>>>>> 6090418 (Sidebar edit)
    await sendMessage(conversationId, message);
    const botResponse = await fetchBotReply(conversationId, message);
    appendMessage("bot", botResponse);
  }
}

<<<<<<< HEAD
=======
// Add user or bot message to interface
>>>>>>> 6090418 (Sidebar edit)
function appendMessage(sender, text) {
  const div = document.createElement("div");
  div.classList.add("message", sender);
  div.textContent = text;
  chatContainer.appendChild(div);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

<<<<<<< HEAD
// FIX
// Adds new conversation to sidebar
function addSidebarMessage(text, convoId) {
=======
// Add convo to sidebar
function addSidebarMessage(text, convoId) {
  if (document.querySelector(`[data-convo-id="${convoId}"]`)) return;

>>>>>>> 6090418 (Sidebar edit)
  const item = document.createElement("div");
  item.classList.add("conversation-item");
  item.textContent = text.length > 40 ? text.slice(0, 40) + "..." : text;
  item.dataset.convoId = convoId;

  item.addEventListener("click", () => {
<<<<<<< HEAD
    window.location.href = `/conversation/${item.dataset.convoId}`;
=======
    window.location.href = `/conversation/${convoId}`;
>>>>>>> 6090418 (Sidebar edit)
  });

  if (window.location.pathname.endsWith(convoId)) {
    item.classList.add("active");
  }

  sidebarMessages.appendChild(item);
}

<<<<<<< HEAD
// FIX
// On click, leads to new conversation page for that conversation
=======
// Load existing conversation and display messages
>>>>>>> 6090418 (Sidebar edit)
async function loadConversation(id) {
  const res = await fetch(`/api/conversations/${id}`);
  const data = await res.json();

  data.messages.forEach((msg) => {
    appendMessage(msg.sender, msg.text);
<<<<<<< HEAD
    if (msg.sender === "user") {
      addSidebarMessage(msg.text);aaaaa
    }
  });
}

// FIX
// Sends a message to LM
=======
  });

  const firstUserMessage = data.messages.find((m) => m.sender === "user");
  if (firstUserMessage) {
    addSidebarMessage(firstUserMessage.text, id);
  }
}

// Send message to backend for LM
>>>>>>> 6090418 (Sidebar edit)
async function sendMessage(id, message) {
  await fetch(`/api/conversations/${id}/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
}

<<<<<<< HEAD
// FIX
// Gets message from LM
=======
// Get LM response from backend
>>>>>>> 6090418 (Sidebar edit)
async function fetchBotReply(id, userMessage) {
  const res = await fetch(`/api/conversations/${id}/reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ userMessage }),
  });

  const data = await res.json();
  return data.reply;
}
