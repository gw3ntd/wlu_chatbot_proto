const chatContainer = document.getElementById("chat-container");
const sidebarMessages = document.getElementById("sidebar-messages");
const userMessageTextarea = document.getElementById("userMessage");
const showLimitsButton = document.getElementById("showLimitsButton");
const hideLimitsButton = document.getElementById("hideLimitsButton");
const limitInformation = document.getElementById("limitInformation");
const limitList = document.getElementById("limitList");
const redirectButton = document.getElementById("redirectButton");
const converter = new showdown.Converter({ simpleLineBreaks: true });

let conversationId = document.body.dataset.conversationId
  ? Number(document.body.dataset.conversationId)
  : null;

if (document.body.dataset.courseId == undefined) {
  throw Error("Course ID not Provided");
}
const courseId = Number(document.body.dataset.courseId);

const conversationStatesUnsafe = {
  "RESOLVED": 1,
  "REDIRECTED": 2,
  "CHATBOT": 3,
};

const conversationStates = new Proxy(conversationStatesUnsafe, {
  get(target, prop, receiver) {
    if (!(prop in target)) {
      throw new Error(
        `Invalid conversation state: "${prop}". Valid states are: ${
          Object.keys(target).join(", ")
        }`,
      );
    }

    return Reflect.get(target, prop, receiver);
  },
});

let conversationState =
  conversationStates[document.body.dataset.conversationState];

async function loadSidebar() {
  fetch(`/conversations?course_id=${courseId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
  }).then(async (response) => {
    if (!response.ok) {
      throw Error("Could not fetch past conversations.");
    }
    const data = await response.json();
    sidebarMessages.innerHTML = "";

    data.conversations.reverse().forEach((c) => {
      addSidebarMessage(c.title, c.id);
    });
  }).catch((error) => {
    appendMessage("system", error.message);
  });
}

async function loadMessages() {
  if (!conversationId) {
    throw Error("conversationId is not set.");
  }

  fetch(`/messages?conversation_id=${conversationId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
  }).then((response) => {
    if (!response.ok) {
      console.log(response);
      throw Error("Could not fetch messages for the conversation.");
    }
    return response.json();
  }).then((data) => {
    chatContainer.innerHTML = "";
    data.messages.forEach((msg) => {
      appendMessage(
        msg.type === "ASSISTANT_MESSAGE"
          ? "assistant"
          : (msg.type === "STUDENT_MESSAGE" ? "user" : "bot"),
        msg.body,
        msg.message_id,
      );
    });
  }).catch((error) => {
    appendMessage("system", error.message);
  });
}

async function loadConversationState() {
  await fetch(`/conversations/${conversationId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
  }).then((response) => {
    if (!response.ok) {
      throw Error("Could not load redirection data.");
    }
    return response.json();
  }).then((conversation) => {
    switch (conversationStates[conversation.state]) {
      case conversationStates.CHATBOT:
        conversationState = conversationStates.CHATBOT;
        redirectButton.textContent = "Upload Image";
        redirectButton.disabled = false;
        userMessageTextarea.disabled = false;
        break;
      case conversationStates.REDIRECTED:
        conversationState = conversationStates.REDIRECTED;
        redirectButton.textContent = "Upload Image";
        redirectButton.disabled = false;
        userMessageTextarea.disabled = false;
        break;
      case conversationStates.RESOLVED:
        conversationState = conversationStates.RESOLVED;
        redirectButton.textContent = "Upload Image";
        redirectButton.disabled = true;
        userMessageTextarea.disabled = true;
        break;
      default:
        throw Error(`Invalid conversation state: '${conversation.state}'`);
    }
  });
}

function createNewConversation() {
  hideLimits(new Event("dummy"));
  chatContainer.innerHTML = "";
  conversationId = null;
  userMessageTextarea.disabled = false;

  document.querySelectorAll(".conversation-item").forEach((el) => {
    el.classList.remove("active");
  });

  window.history.replaceState(
    {},
    "",
    `/conversations/new?course_id=${courseId}`,
  );

  redirectButton.textContent = "Upload Image";
  redirectButton.disabled = false;
  conversationState = conversationStates.CHATBOT;
  appendMessage("system", "New conversation started. Type your message below.");
}

async function sendMessage(e) {
  e.preventDefault();
  hideLimits(e);
  const message = userMessageTextarea.value.trim();
  if (!message) return;

  appendMessage("user", message);
  userMessageTextarea.value = "";

  if (conversationId === null) {
    let created = await fetch(`/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify({ course_id: courseId, title: "Conversation" }),
    }).then(async (response) => {
      if (!response.ok) {
        throw Error(
          (await response.json()).error ||
            "Could not open new conversation: trouble connecting to server",
        );
      }
      return response.json();
    }).then((data) => {
      conversationId = data.conversation_id;

      window.history.replaceState({}, "", `/conversations/${conversationId}`);
      addSidebarMessage("Conversation", conversationId);
      return true;
    }).catch((error) => {
      appendMessage("system", error.message);
      return false;
    });

    if (!created) {
      return;
    }
  }
  let thinkingInterval;
  let thinkingMessageElement;
  const conversationItemElement = document.querySelector(
    `[data-convo-id="${conversationId}"]`,
  );
  if (conversationState == conversationStates.CHATBOT) {
    thinkingMessageElement = appendMessage("bot-thinking", "Thinking...");
    let thinkMessageContentElement = thinkingMessageElement.querySelector(
      ".message",
    );
    let dots = 3;
    thinkingInterval = setInterval(() => {
      dots = (dots % 3) + 1;
      thinkMessageContentElement.textContent = "Thinking" + ".".repeat(dots);
    }, 400);
    userMessageTextarea.disabled = true;
  }

  await fetch("/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "applicaiton/json",
    },
    body: JSON.stringify({ body: message, conversation_id: conversationId }),
  }).then(async (response) => {
    if (!response.ok) {
      throw Error((await response.json()).error || "Could not send message.");
    }
  }).catch((error) => {
    appendMessage("system", error.message);
  });

  if (conversationState == conversationStates.CHATBOT) {
    await fetch(`/conversations/${conversationId}/ai-responses`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify({ prompt: message }),
    }).then(async (response) => {
      if (!response.ok) {
        throw Error(
          (await response.json()).error || "Could not get AI Tutor response.",
        );
      }

      return response.json();
    }).then(async (data) => {
      appendMessage("bot", data.text, data.message_id);
      conversationItemElement.textContent = data.title;
    }).catch((error) => {
      console.error(error);
      appendMessage("system", "Could not fetch a response from the AI Tutor.");
    }).finally(() => {
      clearInterval(thinkingInterval);
      thinkingMessageElement.remove();
    });
  }
  userMessageTextarea.disabled = false;
  userMessageTextarea.focus();
}
/**
 * @param {string} sender
 * @param {string} text
 * @param {number | null} message_id
 *  */ 
function appendMessage(sender, text, message_id=null) {
  const messageWrapper = document.createElement("div");
  messageWrapper.classList.add("message-wrapper");
  if (sender) {
    messageWrapper.classList.add(sender);
  }

  if (sender === "user" || sender === "bot" || sender === "assistant" || sender === "bot-thinking") {
    const pfp = document.createElement("img");
    pfp.classList.add("pfp");

    if (sender === "user") {
      pfp.src = "/static/images/PFPs/logo_PFP.png";
      pfp.alt = "User";
    } else if (sender === "bot" || sender === "bot-thinking") {
      pfp.src = "/static/images/PFPs/Topper_PFP.webp";
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

  messageDiv.querySelectorAll("pre code").forEach((block) => {
    hljs.highlightElement(block);
  });

  if (sender == "bot") {
    const showSourcesButton = document.createElement("button");
    showSourcesButton.display = "block";
    showSourcesButton.textContent = "Show Sources";
    showSourcesButton.style.float="right";
    showSourcesButton.style.backgroundColor="#0000";
    showSourcesButton.style.fontFamily='"Montserrat", sans-serif'
    showSourcesButton.style.color='white';
    showSourcesButton.style.border='none';
    showSourcesButton.style.cursor='pointer';
    showSourcesButton.style.padding='12px';
    showSourcesButton.style.borderRadius='6px';
    

    const sourcesDiv = document.createElement("div");

    if (message_id === null) {
      console.error("message_id is null");
    } else {

      sourcesDiv.setAttribute("sources-for", message_id)
      showSourcesButton.onclick = function() {showSources(sourcesDiv, showSourcesButton)};
      messageDiv.appendChild(showSourcesButton);
      messageDiv.appendChild(sourcesDiv);
    }
  }

  messageWrapper.appendChild(messageDiv);

  chatContainer.appendChild(messageWrapper);
  chatContainer.scrollTop = chatContainer.scrollHeight;
  return messageWrapper;
}

/**
 * @param {HTMLDivElement} sourcesDiv
 * @param {HTMLButtonElement} showSourcesButton
 */
async function showSources(sourcesDiv, showSourcesButton) {
  showSourcesButton.textContent = "Loading Sources...";

  const messageId = Number(sourcesDiv.getAttribute("sources-for"));


  await fetch(`/messages/${messageId}/sources`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Accept: "applicaiton/json"
    },
  }).then(response => {
    if (!response.ok) {
      throw Error("Could not fetch sources");
    }
    return response.json();
  }).then(data => {
    if (data.sources.length === 0) {
      sourcesDiv.innerHTML = "<h3>No sources were used for this response.</h3>";
    } else {
      sourcesDiv.innerHTML = "";
      data.sources.forEach(source => {
        const sourcesList = document.createElement("ul");
        sourcesList.style.listStyleType = "circle";
        const li = document.createElement("li");
        li.innerHTML = `<h3>Source: ${source.document_name}</h3>${source.text}`;
        sourcesList.appendChild(li);
        sourcesDiv.appendChild(sourcesList);
      });
    }
    
    sourcesDiv.appendChild(showSourcesButton);
  }).catch(error => {
    console.log(error);
    const li = document.createElement("li");
    li.textContent = "Error: Could not load sources.";
  });

  showSourcesButton.textContent = "Hide Sources";

  const oldOnClick = showSourcesButton.onclick;
  showSourcesButton.onclick = function() {
    sourcesDiv.innerHTML = "";
    showSourcesButton.textContent = "Show Sources";
    sourcesDiv.appendChild(showSourcesButton);
    showSourcesButton.onclick = oldOnClick;
  };
}

function addSidebarMessage(label, convoId) {
  if (document.querySelector(`[data-convo-id="${convoId}"]`)) return;

  const item = document.createElement("div");
  item.classList.add("conversation-item");
  item.textContent = label;
  item.dataset.convoId = convoId;

  item.addEventListener("click", () => {
    document.querySelectorAll(".conversation-item").forEach((el) => {
      el.classList.remove("active");
    });
    item.classList.add("active");
    window.history.replaceState({}, "", `/conversations/${convoId}`);
    conversationId = convoId;
    chatContainer.innerHTML = "";
    loadMessages();
    loadConversationState();
    hideLimits(new Event("dummy"));
  });

  if (window.location.pathname.endsWith(convoId.toString())) {
    item.classList.add("active");
  }

  sidebarMessages.insertBefore(item, sidebarMessages.firstChild);
}

loadSidebar();

if (conversationId !== null) {
  loadMessages();
  loadConversationState();
}

userMessageTextarea.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage(event);
  }
});

// redirect conversation to assistant or mark as resolved
redirectButton.addEventListener("click", async () => {
  if (!conversationId) {
    appendMessage(
      "system",
      "There must be at least one message in the conversation before it can be redirected to an Assistant.",
    );
    return;
  }
  switch (conversationState) {
    case conversationStates.CHATBOT:
      fetch(`/conversations/${conversationId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ state: "REDIRECTED" }),
      }).then(async (response) => {
        if (!response.ok) throw Error("Could not redirect conversation.");
        redirectButton.textContent = "Mark as Resolved";
        conversationState = conversationStates.REDIRECTED;
        appendMessage(
          "system",
          "Your conversation is now visible to assistants and the AI chat bot is disabled for this conversation.",
        );
      }).catch((error) => {
        appendMessage("system", error.message);
      });
      break;
    case conversationStates.REDIRECTED:
      fetch(`/conversations/${conversationId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ state: "RESOLVED" }),
      }).then(async (response) => {
        if (!response.ok) throw Error("Could not resolve conversation.");
        redirectButton.textContent = "Resolved";
        conversationState = conversationStates.RESOLVED;
        userMessageTextarea.disabled = true;
        appendMessage("system", "Your conversation is now resolved.");
      }).catch((error) => {
        appendMessage("system", error.message);
      });
    case conversationStates.RESOLVED:
      break;
  }
});

async function checkForNewMessages() {
  if (conversationState != conversationStates.REDIRECTED) return;
  if (!conversationId) return;
  response = await fetch(`/messages?conversation_id=${conversationId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
  });

  if (!response.ok) return;

  await response.json().then((data) => {
    const currentMessageCount = chatContainer.children.length;
    if (data.messages.length > currentMessageCount) {
      loadMessages();
    }
  }).catch((error) => {
    console.error("Error checking for new messages:", error);
  });
}

let messageCheckInterval = setInterval(checkForNewMessages, 5000);

window.addEventListener("beforeunload", function () {
  if (messageCheckInterval) {
    clearInterval(messageCheckInterval);
  }
});

async function showLimits(event) {
  event.preventDefault();
  hideLimitsButton.style.display = "inline";
  limitInformation.style.display = "block";
  showLimitsButton.style.display = "none";

  await fetch(`/limits?course_id=${courseId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
  }).then((response) => {
    if (!response.ok) {
      const errorTextElement = document.createElement("p");
      errorTextElement.textContent = "Could not fetch limit information";
      errorTextElement.style.margin = "0 2%";
      limitInformation.appendChild(errorTextElement);
    }
    return response.json();
  }).then((data) => {
    data.limits.forEach((limit) => {
      const listItem = document.createElement("ul");

      seconds_to_span = new Map([
        [60, "minute"],
        [3600, "hour"],
        [86_400, "day"],
        [604_800, "week"],
      ]);

      listItem.textContent = `${
        limit.maximum_number_of_uses - limit.uses
      } left for this ${
        seconds_to_span.get(limit.time_span_seconds) ||
        limit.time_span_seconds + "-second span"
      }.`;
      limitList.appendChild(listItem);
    });
  }).catch((error) => {
    console.error(error);
  });
}

function hideLimits(event) {
  event.preventDefault();
  hideLimitsButton.style.display = "none";
  showLimitsButton.style.display = "inline";
  limitInformation.style.display = "none";
  limitList.textContent = "";
}
