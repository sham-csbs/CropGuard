```javascript
// ===============================
// CROP GUARD - FRONTEND SCRIPT
// ===============================

// Change this later to YOUR hosted backend URL.
// Do NOT put the Lyzr API key here.
const BACKEND_URL = "YOUR_BACKEND_URL";


// ===============================
// AI CHAT
// ===============================

async function sendMessage() {

    const input = document.getElementById("userMessage");
    const chatBox = document.getElementById("chatBox");
    const sendButton = document.getElementById("sendButton");

    if (!input || !chatBox) {
        console.error("Chat elements not found in index.html");
        return;
    }

    const message = input.value.trim();

    if (message === "") {
        return;
    }

    // Display user's message
    addMessage(message, "user-message");

    input.value = "";

    if (sendButton) {
        sendButton.disabled = true;
        sendButton.innerText = "Thinking...";
    }

    // Temporary loading message
    const loadingMessage = addMessage(
        "🌱 Crop Guard is thinking...",
        "bot-message"
    );

    try {

        const response = await fetch(`${BACKEND_URL}/chat`, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })
        });

        if (!response.ok) {
            throw new Error("Backend request failed");
        }

        const data = await response.json();

        // Remove loading message
        if (loadingMessage) {
            loadingMessage.remove();
        }

        const aiResponse =
            data.response ||
            data.message ||
            data.answer ||
            "Sorry, I couldn't generate a response.";

        addMessage(aiResponse, "bot-message");

    } catch (error) {

        console.error("Error:", error);

        if (loadingMessage) {
            loadingMessage.remove();
        }

        addMessage(
            "⚠️ Unable to connect to Crop Guard AI. Please try again.",
            "bot-message"
        );

    } finally {

        if (sendButton) {
            sendButton.disabled = false;
            sendButton.innerText = "Send";
        }
    }
}


// ===============================
// ADD MESSAGE TO CHAT
// ===============================

function addMessage(text, className) {

    const chatBox = document.getElementById("chatBox");

    if (!chatBox) {
        return null;
    }

    const messageDiv = document.createElement("div");

    messageDiv.classList.add("message", className);

    messageDiv.innerText = text;

    chatBox.appendChild(messageDiv);

    // Automatically scroll to latest message
    chatBox.scrollTop = chatBox.scrollHeight;

    return messageDiv;
}


// ===============================
// ENTER KEY SUPPORT
// ===============================

function handleEnter(event) {

    if (event.key === "Enter") {
        sendMessage();
    }
}


// ===============================
// DASHBOARD DATA
// ===============================

// These functions can later be connected
// to your actual sensor/backend data.

function updateSoilMoisture(value) {

    const element = document.getElementById("soilMoisture");

    if (element) {
        element.innerText = value + "%";
    }
}


function updateTemperature(value) {

    const element = document.getElementById("temperature");

    if (element) {
        element.innerText = value + "°C";
    }
}


function updateHumidity(value) {

    const element = document.getElementById("humidity");

    if (element) {
        element.innerText = value + "%";
    }
}


// ===============================
// INITIAL MESSAGE
// ===============================

document.addEventListener("DOMContentLoaded", function () {

    console.log("🌾 Crop Guard frontend loaded successfully.");

});
```
