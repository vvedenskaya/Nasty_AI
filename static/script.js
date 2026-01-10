
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

// function sendMessage() {
//     const message = userInput.value.trim();
//     if (message) {
//         // Add user message
//         addMessage('user', message);

//         // Simulate root WASP response
//         setTimeout(() => {
//             addMessage('root', generateWaspResponse(message));
//         }, 500);

//         userInput.value = '';
//     }
// }

function addMessage(sender, text) {
    const messageElement = document.createElement('p');
    messageElement.innerHTML = `<strong>${sender === 'user' ? 'user@hostname:~$' : 'root@wasp:~#'}</strong> ${text}`;
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function getUserId() {
    let userId = localStorage.getItem('lisbeth_user_id');
    if (!userId) {
        userId = 'user_' + Date.now();
        localStorage.setItem('lisbeth_user_id', userId);
    }
    return userId;
}

async function checkEmail(email) {
    try {
        const response = await fetch('/check-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        return response.json();
    } catch (error) {
        return { error: error.message };
    }
}


function formatEmailResult(result) {
    if (result.error) {
        return `❌ Error: ${result.error}`;
    }
    
    if (result.status === 'COMPROMISED') {
        const breachesList = result.breaches.map(b => `  • ${b}`).join('\n');
        return `${result.message}\n\nBreaches found: ${result.count}\n\nBreach names:\n${breachesList}`;
    }
    
    return result.message;
}

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const userMessage = userInput.value.trim();
    
    if (!userMessage) return;
    
    const chatContainer = document.getElementById('chat-container');
    const sendBtn = document.querySelector('input[type="submit"]');
    
    // Mask password in display if it's a password check command
    let displayMessage = userMessage;
    let actualPassword = '';
    
    if (userMessage.toLowerCase().startsWith('check password')) {
        const password = userMessage.replace(/^check password/i, '').trim();
        if (password) {
            actualPassword = password;
            // Mask the password with asterisks for display
            const maskedPassword = '*'.repeat(password.length);
            displayMessage = 'check password ' + maskedPassword;
        }
    }
    
    // ОЧИЩАЕМ INPUT ПЕРВЫМ ДЕЛОМ
    userInput.value = '';
    // Reset input type to text after sending
    userInput.type = 'text';
    passwordCommandPrefix = '';
    
    // Показываем вопрос ОДИН РАЗ (with masked password if applicable)
    chatContainer.innerHTML += `<p><strong>user@hostname:~$</strong> ${displayMessage}</p>`;
    
    // Блокируем кнопку
    sendBtn.disabled = true;
    sendBtn.style.opacity = '0.5';
    
    // Уникальный ID для loading элемента
    const loadingId = 'loading_' + Date.now();
    
    // Loading с ОТДЕЛЬНЫМ спаном для класса
    const loadingElement = document.createElement('p');
    loadingElement.id = loadingId;
    loadingElement.innerHTML = `<span class="loading">🐇</span> Loading...`;
    chatContainer.appendChild(loadingElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // ============================================================================
    // CHECK PASSWORD
    // ============================================================================
    
    if (userMessage.toLowerCase().startsWith('check password')) {
        // Get the actual password (it might be masked in the input, so use the original)
        const password = userMessage.replace(/^check password/i, '').trim();
        
        if (!password) {
            document.getElementById(loadingId).innerHTML = `<strong>🔐 Tool:</strong> Usage: check password yourpassword`;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
            return;
        }
        
        console.log('🔐 Checking password strength...');      
        fetch('/check-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: password }),
        })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(result => {
            console.log('Password check result:', result);
            const loadingEl = document.getElementById(loadingId);
            if (result.error) {
                loadingEl.innerHTML = `<strong>🔐 Tool:</strong> ❌ Error: ${result.error}`;
            } else if (result.feedback && Array.isArray(result.feedback)) {
                const feedbackList = result.feedback.map(f => `  • ${f}`).join('\n');
                const formattedResult = `${result.message}\n\nScore: ${result.score}/100\nStrength: ${result.strength}\n\nFeedback:\n${feedbackList}`;
                loadingEl.innerHTML = `<strong>🔐 Tool:</strong><pre>${formattedResult}</pre>`;
            } else {
                loadingEl.innerHTML = `<strong>🔐 Tool:</strong> ${result.message || JSON.stringify(result)}`;
            }
            chatContainer.scrollTop = chatContainer.scrollHeight;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
        })
        .catch(error => {
            console.error('Password check error:', error);
            const loadingEl = document.getElementById(loadingId);
            loadingEl.innerHTML = `<strong>❌ Error:</strong> ${error.message}`;
            chatContainer.scrollTop = chatContainer.scrollHeight;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
        });
        
        return; 
    }
    
    // ============================================================================
    // CHECK EMAIL
    // ============================================================================
    
    if (userMessage.toLowerCase().startsWith('check email')) {
        const email = userMessage.replace(/^check email/i, '').trim();
        
        if (!email) {
            document.getElementById(loadingId).innerHTML = `<strong>📧 Tool:</strong> Usage: check email your_email@example.com`;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
            return;
        }
        
        console.log('📧 Checking if email was pwned...');      
        fetch('/check-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email }),
        })
        .then(response => response.json())
        .then(result => {
            const loadingEl = document.getElementById(loadingId);
            if (result.error) {
                loadingEl.innerHTML = `<strong>📧 Tool:</strong> ❌ Error: ${result.error}`;
            } else {
                let formattedResult = result.message;
                if (result.status === 'COMPROMISED' && result.count > 0) {
                    const breachesList = result.breaches.map(b => `  • ${b}`).join('\n');
                    formattedResult += `\n\nBreaches found: ${result.count}\n\nBreach names:\n${breachesList}`;
                }
                loadingEl.innerHTML = `<strong>📧 Tool:</strong></p><pre>${formattedResult}</pre>`;
            }
            chatContainer.scrollTop = chatContainer.scrollHeight;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
        })
        .catch(error => {
            document.getElementById(loadingId).innerHTML = `<strong>❌ Error:</strong> ${error.message}`;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
        });
        
        return; 
    }
    
    // ============================================================================
    // SECURITY NEWS
    // ============================================================================
    
    if (userMessage.toLowerCase().startsWith('security news') || 
        userMessage.toLowerCase().startsWith('hacker news')) {
        
        console.log('📰 Fetching security news...');
        
        fetch('/security-news', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            const loadingEl = document.getElementById(loadingId);
            if (data.error) {
                loadingEl.innerHTML = `<strong>❌ Error:</strong> ${data.error}`;
            } else {
                let newsDisplay = `<strong>📰 ${data.message}</strong></p><pre>`;
                data.news.forEach((item, idx) => {
                    newsDisplay += `${idx + 1}. ${item.title}\n`;
                    newsDisplay += `   Source: ${item.source}\n`;
                    newsDisplay += `   Date: ${item.published}\n`;
                    newsDisplay += `   Link: ${item.link}\n\n`;
                });
                newsDisplay += `</pre>`;
                loadingEl.innerHTML = newsDisplay;
            }
            chatContainer.scrollTop = chatContainer.scrollHeight;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
        })
        .catch(error => {
            document.getElementById(loadingId).innerHTML = `<strong>❌ Error:</strong> ${error.message}`;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
        });
        
        return;
    }
    
    // ============================================================================
    // SURVEILLANCE
    // ============================================================================
    
    if (userMessage.toLowerCase().includes('surveillance') || 
        userMessage.toLowerCase().includes('survelliance')) {
        
        console.log('👁️ Fetching surveillance feed...');
        
        fetch('/surveillance', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            const loadingEl = document.getElementById(loadingId);
            if (data.error) {
                loadingEl.innerHTML = `<strong>❌ Error:</strong> ${data.error}`;
            } else {
                // Make the link clickable in the chat
                const linkHtml = data.link ? `<a href="${data.link}" target="_blank" style="color: #00ff00; text-decoration: underline;">${data.link}</a>` : '';
                const messageWithLink = data.message.replace(data.link, linkHtml);
                loadingEl.innerHTML = `<strong>👁️ Tool:</strong> ${messageWithLink}`;
                
                // Try to open the link in a new window/tab
                if (data.link) {
                    const win = window.open(data.link, '_blank');
                    if (!win || win.closed || typeof win.closed == 'undefined') {
                        // Popup was blocked - inform user
                        loadingEl.innerHTML += `<br><span style="color: #ffcc00;">⚠️ Pop-up blocked! Click the link above to open manually.</span>`;
                    }
                }
            }
            chatContainer.scrollTop = chatContainer.scrollHeight;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
        })
        .catch(error => {
            document.getElementById(loadingId).innerHTML = `<strong>❌ Error:</strong> ${error.message}`;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
        });
        
        return;
    }
    
    // ============================================================================
    // NORMAL CHAT
    // ============================================================================
    
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, user_id: getUserId() }),
    })
    .then(response => response.json())
    .then(data => {
        const loadingEl = document.getElementById(loadingId);
        
        if (data.response) {
            loadingEl.innerHTML = `<strong>root@wasp:</strong> ${data.response}`;
            
            // If the response contains a surveillance link, open it
            if (data.data && data.data.link && data.tool === 'surveillance') {
                const win = window.open(data.data.link, '_blank');
                if (!win || win.closed || typeof win.closed == 'undefined') {
                    console.warn('Popup blocked by browser');
                }
            }
        }
        
        if (data.error) {
            loadingEl.innerHTML = `<strong>❌ Error:</strong> ${data.error}`;
        }
        
        if (data.options) {
            let optionsHtml = `<p><strong>Options:</strong></p>`;
            data.options.forEach((option, index) => {
                optionsHtml += `<p>${String.fromCharCode(65 + index)}. ${option}</p>`;
            });
            loadingEl.insertAdjacentHTML('afterend', optionsHtml);
        }
        
        chatContainer.scrollTop = chatContainer.scrollHeight;
        sendBtn.disabled = false;
        sendBtn.style.opacity = '1';
    })
    .catch(error => {
        document.getElementById(loadingId).innerHTML = `<strong>❌ Error:</strong> ${error.message}`;
        sendBtn.disabled = false;
        sendBtn.style.opacity = '1';
    });
}
function generateWaspResponse(message) {
    return "Response to: " + message;
}


// Event listener to mask password input when typing "check password"
userInput.addEventListener('input', function(event) {
    const value = this.value;
    const lowerValue = value.toLowerCase();
    
    // Check if user is typing "check password" followed by space and password
    const passwordMatch = value.match(/^(check password)\s+(.+)$/i);
    
    if (passwordMatch) {
        // User has typed "check password " followed by password
        // Change input type to password to mask it
        if (this.type !== 'password') {
            this.type = 'password';
        }
    } else if (lowerValue.startsWith('check password')) {
        // User is typing "check password" but no password yet
        // Keep as text so they can see the command
        if (this.type === 'password') {
            this.type = 'text';
        }
    } else {
        // Not a password command, ensure it's text type
        if (this.type === 'password') {
            this.type = 'text';
        }
    }
});

// Event listener for user input submission
userInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});
