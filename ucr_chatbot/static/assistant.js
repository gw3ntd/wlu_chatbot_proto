/* BACKEND: Needs Fetch functionality to handle conversation redirects */

/* hardcoded convos for testing. replace with dynamic data. */
const conversations = [
    { id: 101, status: "attention", title: "smth smth comp sci" },
    { id: 102, status: "progress", title: "software and stuff" },
    { id: 103, status: "attention", title: "compooters" },
];

const needsAttentionList = document.getElementById("needs-attention-list");
const inProgressList = document.getElementById("in-progress-list");

conversations.forEach((conv) => {
    const div = document.createElement("div");
    div.className = "conversation-card";
    div.textContent = conv.title;
    div.onclick = () => {
    window.location.href = `/conversation/${conv.id}`;
    };

    if (conv.status === "attention") {
    needsAttentionList.appendChild(div);
    } else {
    inProgressList.appendChild(div);
    }
});