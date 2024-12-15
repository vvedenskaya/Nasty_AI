// Matrix effect
var canvas = document.getElementById('matrix');
var ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

var matrixChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789@#$%^&*()*&^%";
matrixChars = matrixChars.split("");

var fontSize = 16;
var columns = canvas.width / fontSize;
var drops = [];

for (var x = 0; x < columns; x++) {
    drops[x] = 1;
}

function drawMatrix() {
    ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#0F0";
    ctx.font = fontSize + "px Courier";

    for (var i = 0; i < drops.length; i++) {
        var text = matrixChars[Math.floor(Math.random() * matrixChars.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
            drops[i] = 0;
        }

        drops[i]++;
    }
}

setInterval(drawMatrix, 35);

// Chat logic
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');

function sendMessage() {
    const message = userInput.value.trim();
    if (message) {
        // Add user message
        addMessage('user', message);













        // Simulate root WASP response
        setTimeout(() => {
            addMessage('root', generateWaspResponse(message));
        }, 500);

        userInput.value = '';
    }
}

function addMessage(sender, text) {
    const messageElement = document.createElement('p');
    messageElement.innerHTML = `<strong>${sender === 'user' ? 'user@hostname:~$' : 'root@wasp:~#'}</strong> ${text}`;
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function sendMessage() {
    const userMessage = document.getElementById('user-input').value;

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage}),
    })
    .then(response => response.json())
    .then(data => {
        if (data.response){
            const chatContainer = document.getElementById('chat-container');
            chatContainer.innerHTML += `<p><strong>user@hostname:~$:</strong> ${userMessage}</p>`;
            chatContainer.innerHTML += `<p><strong>root@wasp:</strong> ${data.response}</p>`;



        } if (data.options) {
            // Если есть варианты ответа (Voight-Kampff question)
            chatContainer.innerHTML += `<p><strong>Options:</strong></p>`;
            data.options.forEach((option, index) => {
                chatContainer.innerHTML += `<p>${String.fromCharCode(65 + index)}. ${option}</p>`;
            });
        }
    })
    .catch(error => {
        document.getElementById('response-container').innerText = 'Error: ' + error;
    });

    document.getElementById('user-input').value = '';
}


function generateWaspResponse(message) {
    return "Response to: " + message;
}

// Event listener for user input submission
userInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});
