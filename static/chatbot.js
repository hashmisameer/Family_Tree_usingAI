document.addEventListener("DOMContentLoaded", () => {
    const chatbotToggle = document.getElementById("chatbot-toggle");
    const chatbox = document.getElementById("chatbox");
    const chatInputContainer = document.getElementById("chat-input-container");
    const chatInput = document.getElementById("chat-input");
    const sendButton = document.getElementById("send-button");

    // Toggle Chatbot Visibility
    chatbotToggle.addEventListener("click", () => {
        const isChatVisible = chatbox.style.display === "block";
        chatbox.style.display = isChatVisible ? "none" : "block";
        chatInputContainer.style.display = isChatVisible ? "none" : "flex";
    });

    // Send Message
    sendButton.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    function sendMessage() {
        const userMessage = chatInput.value.trim();
        if (!userMessage) return;

        // Append user message
        appendMessage("You", userMessage);
        chatInput.value = "";

        // Send request to backend chatbot
        fetch("/chatbot", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ message: userMessage }),
        })
        .then(response => response.json())
        .then(data => {
            appendMessage("Bot", data.response);
            chatbox.scrollTop = chatbox.scrollHeight;
        })
        .catch(error => {
            appendMessage("Bot", "Sorry, an error occurred. Please try again.");
        });
    }

    function appendMessage(sender, message) {
        const messageElement = document.createElement("div");
        messageElement.className = sender === "You" ? "chat-message user" : "chat-message bot";
        messageElement.textContent = `${sender}: ${message}`;
        chatbox.appendChild(messageElement);
    }
});
