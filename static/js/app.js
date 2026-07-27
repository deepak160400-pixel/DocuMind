const uploadButton = document.getElementById("uploadButton");
const attachButton = document.querySelector(".attach-btn");
const sendButton = document.querySelector(".send-btn");
const fileInput = document.getElementById("fileInput");
const documents = document.getElementById("documents");
const messageInput = document.getElementById("messageInput");
const chatMessages = document.getElementById("chatMessages");

let firstUpload = true;

// --------------------
// Auto Resize
// --------------------

messageInput.addEventListener("input", () => {

    messageInput.style.height = "auto";
    messageInput.style.height = messageInput.scrollHeight + "px";

});

// --------------------
// Upload
// --------------------

uploadButton.onclick = () => fileInput.click();

attachButton.onclick = () => fileInput.click();

fileInput.addEventListener("change", async () => {

    const file = fileInput.files[0];

    if (!file) return;

    const formData = new FormData();

    formData.append("file", file);

    try {

        const response = await fetch("/upload", {

            method: "POST",

            body: formData

        });

        const data = await response.json();

        if (data.success) {

            if (firstUpload) {

                documents.innerHTML = "";

                firstUpload = false;

            }

            documents.innerHTML += `

            <div class="doc-card">

                <i class="bi bi-file-earmark-pdf-fill text-danger"></i>

                <div>

                    <h6>${data.filename}</h6>

                    <small>${data.chunks} Chunks</small>

                </div>

            </div>

            `;

            addMessage("✅ Document uploaded successfully.", "bot");

        } else {

            addMessage(data.message, "bot");

        }

    }

    catch (e) {

        addMessage("Upload failed.", "bot");

    }

    fileInput.value = "";

});

// --------------------
// Chat
// --------------------

function addMessage(text, sender) {

    const div = document.createElement("div");

    div.className = sender === "user"

        ? "user-message"

        : "bot-message";

    div.innerHTML = text;

    chatMessages.appendChild(div);

    chatMessages.scrollTop = chatMessages.scrollHeight;

}

// --------------------

async function sendMessage() {

    const text = messageInput.value.trim();

    if (text === "") return;

    addMessage(text, "user");

    messageInput.value = "";

    messageInput.style.height = "56px";

    const thinking = document.createElement("div");

    thinking.className = "bot-message";

    thinking.innerHTML = "Thinking...";

    chatMessages.appendChild(thinking);

    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify({

                message: text

            })

        });

        const data = await response.json();

        thinking.remove();

        if (data.success) {

            addMessage(data.answer, "bot");

        }

        else {

            addMessage(data.message, "bot");

        }

    }

    catch (error) {

        thinking.remove();

        addMessage("Server Error", "bot");

    }

}

// --------------------

sendButton.addEventListener(

    "click",

    sendMessage

);

// --------------------

messageInput.addEventListener(

    "keydown",

    function (e) {

        if (

            e.key === "Enter"

            &&

            !e.shiftKey

        ) {

            e.preventDefault();

            sendMessage();

        }

    }

);