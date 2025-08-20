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

let isNewConversation = window.location.pathname.includes("/conversation/new");

const conversationStatesUnsafe = {
  "RESOLVED": 1,
  "REDIRECTED": 2,
  "CHATBOT": 3,
}

const conversationStates = new Proxy(conversationStatesUnsafe, {
  get(target, prop, receiver) {
    if (!(prop in target)) {
      throw new Error(`Invalid conversation state: "${prop}". Valid states are: ${Object.keys(target).join(', ')}`);
    }

    return Reflect.get(target, prop, receiver);
  }
});

let conversationState = conversationStates[document.body.dataset.conversationState];

async function loadAllConversationIds() {
  if (!courseId && !conversationId) return;

  let fetchUrl = `/conversation/new/${courseId}/chat`


  const res = await fetch(fetchUrl, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify({ type: "ids" }),
  });

  const conversations = await res.json();

  sidebarMessages.innerHTML = "";

  conversations.reverse().forEach(c => {
    addSidebarMessage(c.title, c.id);
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
    appendMessage(msg.sender === "AssistantMessage" ? "assistant" : (msg.sender === "StudentMessage" ? "user" : "bot"), msg.body);
  });

  const res_2 = await fetch(`/conversation/${conversationId}`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify({ type: "redirect" }),
  });

  const redirect_data = await res_2.json();

  if (redirect_data.redirect === "bot") {
    conversationState = conversationStates.CHATBOT;
    redirectButton.textContent = "Redirect to ULA";
    redirectButton.disabled = false;
    userMessageTextarea.disabled = false;
  }
  else if (redirect_data.redirect === "open") {
    conversationState = conversationStates.REDIRECTED;
    redirectButton.textContent = "Mark as Resolved";
    redirectButton.disabled = false;
    userMessageTextarea.disabled = false;
  }
  else {
    conversationState = conversationStates.RESOLVED;
    redirectButton.textContent = "Resolved";
    redirectButton.disabled = true;
    userMessageTextarea.disabled = true;
  }
}

function createNewConversation() {
  chatContainer.innerHTML = "";
  conversationId = null;
  isNewConversation = true;
  userMessageTextarea.disabled = false;

  document.querySelectorAll(".conversation-item").forEach(el => {
    el.classList.remove("active");
  });
  
  if (courseId) {
    window.history.replaceState({}, "", `/conversation/new/${courseId}/chat`);
  } else {
    alert("Internal error");
  }
  
  redirectButton.textContent = "Redirect to ULA";
  redirectButton.disabled = false;
  conversationState = conversationStates.CHATBOT;
  appendMessage("system", "New conversation started. Type your message below.");
}

loadAllConversationIds();

// Set up periodic message checking for real-time updates
let messageCheckInterval;

if (!isNewConversation && conversationId) {
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
  const message = userMessageTextarea.value.trim();
 if (!message) return;

  appendMessage("user", message);
  userMessageTextarea.value = "";

  if (isNewConversation) {
    await fetch(`/conversation/new/${courseId}/chat`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ type: "create", message }),
    }).then( async response => {

      if (!response.ok) {
        throw Error("Could not connect to the chatbot server to open a new conversation.")
      }

      const data = await response.json();
      conversationId = data.conversationId;
      isNewConversation = false;

      window.history.replaceState({}, "", `/conversation/${conversationId}`);
      addSidebarMessage(data.title, data.conversationId);
    }).catch(error => {
     appendMessage("system", error.message);
     return;
    });
  }
  if (conversationState != conversationStates.CHATBOT) return;
  let thinkingMessageElement = appendMessage('bot', "Thinking...")
  let thinkMessageContentElement = thinkingMessageElement.querySelector(".message")
  let dots = 3;
  const thinkingInterval = setInterval(() => {
    dots = (dots % 3) + 1;
    thinkMessageContentElement.textContent = "Thinking" + ".".repeat(dots);
  }, 400);
  
  fetch(`/conversation/${conversationId}`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify({ type: "reply", message: message }),
  }).then(async response => {

    let data = await response.json()
    if (!response.ok) {
      throw Error("Could not get response from language model.");
    }
    return data;
  }).then(async data => {
    if (data.reply !== "") {
        appendMessage("bot", data.reply);
    }
  }).catch(error => {
     appendMessage("system", error.message);
  }).finally(() => {
      clearInterval(thinkingInterval);
      thinkingMessageElement.remove();
  });
}

function appendMessage(sender, text) {
  const messageWrapper = document.createElement("div");
  messageWrapper.classList.add("message-wrapper");
  if (sender) {
    messageWrapper.classList.add(sender);
  }
  
  if (sender === "user" || sender === "bot" || sender === "assistant") {
    const pfp = document.createElement("img");
    pfp.classList.add("pfp");

    if (sender === "user") {
      pfp.src = "/static/images/PFPs/User_PFP.png";
      pfp.alt = "User";
    } else if (sender === "bot") {
      pfp.src = "/static/images/PFPs/Bot_PFP.png";
      pfp.alt = "Bot";
    } else if (sender === "assistant") {
      pfp.src = "/static/images/PFPs/Assistant_PFP.png";
      pfp.alt = "Assistant";
    }

    messageWrapper.appendChild(pfp);
  }

  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message");
  if (sender) {
    messageDiv.classList.add(sender);
  }

  const html = converter.makeHtml(text);
  messageDiv.innerHTML = html;

  messageDiv.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);
  });

  messageWrapper.appendChild(messageDiv);

  chatContainer.appendChild(messageWrapper);
  chatContainer.scrollTop = chatContainer.scrollHeight;
  return messageWrapper;
}


function addSidebarMessage(label, convoId) {
  if (document.querySelector(`[data-convo-id="${convoId}"]`)) return;

  const item = document.createElement("div");
  item.classList.add("conversation-item");
  item.textContent = label;
  item.dataset.convoId = convoId;

  item.addEventListener("click", () => {
    document.querySelectorAll(".conversation-item").forEach(el => {
      el.classList.remove("active");
    });
    item.classList.add("active");
    window.history.replaceState({}, "", `/conversation/${convoId}`);
    conversationId = convoId;
    chatContainer.innerHTML = "";
    isNewConversation = false
    loadAllConversationsForUser();
  });

  if (window.location.pathname.endsWith(convoId.toString())) {
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

// redirect conversation to assistant or mark as resolved
redirectButton.addEventListener("click", async () => {
  if (!conversationId) {
    appendMessage("system", "There must be at least one message in the conversation before it can be redirected to an Assistant.");
    return;
  }
  switch (conversationState) {
    case conversationStates.CHATBOT:
      fetch(`/conversation/${conversationId}/redirect`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ type: "redirect" }),
      }).then( async response => {
        if (!response.ok) throw new Error("Could not redirect conversation.");
        const data = await response.json();
        if (data.status !== "redirected") throw new Error("Could not redirect conversation.");

        redirectButton.textContent = "Mark as Resolved";
        conversationState = conversationStates.REDIRECTED;
        appendMessage("system", "Your conversation is now visible to assistants and the AI chat bot is disabled for this conversation.");
      }).catch( error => {
        appendMessage("system", error.message)
      });
      break;
    case conversationStates.REDIRECTED:
      fetch(`/conversation/${conversationId}/resolve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ type: "resolve" }),
      }).then( async response => {
        if (!response.ok) throw new Error("Could not resolve conversation.");
        const data = await response.json();
        if (data.status !== "resolved") throw new Error("Could not resolve conversation.");

        redirectButton.textContent = "Resolved";
        conversationState = conversationStates.RESOLVED;
        userMessageTextarea.disabled = true;
        appendMessage("system", "Your conversation is now resolved.");
      }).catch( error => {
        appendMessage("system", error.message)
      });
    case conversationStates.RESOLVED:
      break;
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
messageCheckInterval = setInterval(checkForNewMessages, 5000); // Check every 5 seconds

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