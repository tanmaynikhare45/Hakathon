    document.getElementById("chatbot-icon").onclick = function () {
    let chatbot = document.getElementById("chatbot-window");
    chatbot.style.display = (chatbot.style.display === "none" || chatbot.style.display === "") ? "flex" : "none";
    };

    async function sendMessage() {
    let inputField = document.getElementById("user-input");
    let message = inputField.value.trim();
    if (!message) return;

    let messagesDiv = document.getElementById("chatbot-messages");
    messagesDiv.innerHTML += `<div><b>You:</b> ${message}</div>`;

    inputField.value = "";

    // Call backend
    let response = await fetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    });
    let data = await response.json();

    messagesDiv.innerHTML += `<div><b>Bot:</b> ${data.reply}</div>`;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
