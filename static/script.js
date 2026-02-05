
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
const suggestionsContainer = document.getElementById('command-suggestions');

const availableCommands = [
    { name: 'check password', desc: 'see if your password was leaked in data breaches', example: 'check password 123456' },
    { name: 'security news', desc: 'fetch latest cybersecurity news', example: 'security news' },
    { name: 'surveillance', desc: 'access random surveillance camera feed', example: 'surveillance' },
    { name: 'search', desc: 'OSINT search (Facebook, LinkedIn, etc.)', example: 'search "John Doe"' }
];

let selectedIndex = -1;

function showSuggestions(filter = '') {
    const filtered = availableCommands.filter(cmd => 
        cmd.name.toLowerCase().includes(filter.toLowerCase())
    );

    if (filtered.length === 0) {
        suggestionsContainer.classList.add('hidden');
        return;
    }

    suggestionsContainer.innerHTML = '';
    filtered.forEach((cmd, index) => {
        const div = document.createElement('div');
        div.className = 'command-item';
        if (index === selectedIndex) div.classList.add('selected');
        
        div.innerHTML = `
            <span class="command-name">/${cmd.name}</span>
            <span class="command-desc">${cmd.desc}</span>
        `;
        
        div.onclick = () => {
            userInput.value = cmd.name + ' ';
            syncMirror(); // Синхронизируем зеркало
            suggestionsContainer.classList.add('hidden');
            userInput.focus();
        };
        
        suggestionsContainer.appendChild(div);
    });

    suggestionsContainer.classList.remove('hidden');
}

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

// Helper function to scroll chat to bottom
function scrollChatToBottom() {
    // Use multiple methods to ensure scrolling works
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
        // Also try scrollIntoView on the last child
        const lastChild = chatContainer.lastElementChild;
        if (lastChild) {
            lastChild.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }, 0);
    
    // Also use requestAnimationFrame for better timing
    requestAnimationFrame(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    });
}

function addMessage(sender, text) {
    const messageElement = document.createElement('p');
    messageElement.innerHTML = `<strong>${sender === 'user' ? 'user@hostname:~$' : 'root@wasp:~#'}</strong> ${text}`;
    chatContainer.appendChild(messageElement);
    scrollChatToBottom();
}

function getUserId() {
    let userId = localStorage.getItem('lisbeth_user_id');
    if (!userId) {
        userId = 'user_' + Date.now();
        localStorage.setItem('lisbeth_user_id', userId);
    }
    return userId;
}

function startNewSession() {
    // Очищаем localStorage для создания нового user_id
    localStorage.removeItem('lisbeth_user_id');
    
    // Очищаем чат контейнер
    const chatContainer = document.getElementById('chat-container');
    chatContainer.innerHTML = '';
    
    // Очищаем зеркало ввода
    const inputMirror = document.getElementById('input-mirror');
    if (inputMirror) inputMirror.textContent = '';
    
    // Создаем новый user_id
    const newUserId = getUserId();
    
    // Показываем сообщение о новой сессии
    const messageElement = document.createElement('p');
    messageElement.innerHTML = `<strong>root@wasp:</strong> [SYSTEM BOOT COMPLETE]...<br>
    <strong>LISBETH:</strong> I'm here. If you're looking for someone, try <strong>/search</strong>. If you're worried about your security, <strong>/check password</strong>. Want to stalk anybody? Try <strong>/surveillance</strong>. Type <strong>/</strong> to see the full list of my tools. Don't waste my time with boring talk.`;
    chatContainer.appendChild(messageElement);
    scrollChatToBottom();
    
    console.log('🔄 New session started with user_id:', newUserId);
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
    const inputMirror = document.getElementById('input-mirror');
    if (inputMirror) inputMirror.textContent = '';
    
    // Reset input type to text after sending
    userInput.type = 'text';
    passwordCommandPrefix = '';
    
    // Показываем вопрос ОДИН РАЗ (with masked password if applicable)
    chatContainer.innerHTML += `<p><strong>user@hostname:~$</strong> ${displayMessage}</p>`;
    scrollChatToBottom();
    
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
    scrollChatToBottom();
    
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
            } else {
                let formattedResult = result.message;
                if (result.status === 'COMPROMISED') {
                    formattedResult += `\n\nOccurrences found: ${result.found}`;
                }
                loadingEl.innerHTML = `<strong>🔐 Tool:</strong><pre>${formattedResult}</pre>`;
            }
            scrollChatToBottom();
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
        })
        .catch(error => {
            console.error('Password check error:', error);
            const loadingEl = document.getElementById(loadingId);
            loadingEl.innerHTML = `<strong>❌ Error:</strong> ${error.message}`;
            scrollChatToBottom();
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
            scrollChatToBottom();
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
            scrollChatToBottom();
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
        })
        .catch(error => {
            document.getElementById(loadingId).innerHTML = `<strong>❌ Error:</strong> ${error.message}`;
            scrollChatToBottom();
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
                const linkHtml = data.link ? `<a href="${data.link}" target="_self" style="color: #00ff00; text-decoration: underline;">${data.link}</a>` : '';
                const messageWithLink = data.message.replace(data.link, linkHtml);
                loadingEl.innerHTML = `<strong>👁️ Tool:</strong> ${messageWithLink}<br><br><div style="background: #1a1a1a; padding: 10px; border-left: 3px solid #ff0000; margin-top: 10px;"><strong style="color: #ffcc00;">⚠️ Tip:</strong> Use browser's <strong>Back</strong> button or press <strong>Alt+←</strong> (Mac: <strong>Cmd+←</strong>) to return to chat.</div>`;
                
                // Open the link directly in the same window after a short delay
                if (data.link) {
                    setTimeout(() => {
                        window.location.href = data.link;
                    }, 2000);
                }
            }
            scrollChatToBottom();
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
    // OSINT SEARCH
    // ============================================================================
    
    if (userMessage.toLowerCase().startsWith('search ')) {
        const target = userMessage.slice(7).trim();
        
        if (!target) {
            document.getElementById(loadingId).innerHTML = `<strong>🔍 Tool:</strong> Usage: search "Name" or search email@example.com`;
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
            return;
        }
        
        console.log('🔍 Performing OSINT search...');      
        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMessage, user_id: getUserId() }),
        })
        .then(response => response.json())
        .then(data => {
            const loadingEl = document.getElementById(loadingId);
            if (data.error) {
                loadingEl.innerHTML = `<strong>🔍 Tool:</strong> ❌ Error: ${data.error}`;
            } else if (data.data && data.tool === 'osint_search') {
                // Robust parsing of the response
                let scorePart = "PUBLICITY SCORE: 0/10";
                let restPart = data.response;

                // Try to find the line containing the score
                const lines = data.response.split('\n');
                const scoreLineIndex = lines.findIndex(l => l.toUpperCase().includes('PUBLICITY SCORE:'));
                
                if (scoreLineIndex !== -1) {
                    scorePart = lines[scoreLineIndex];
                    // Remove the score line and join the rest
                    lines.splice(scoreLineIndex, 1);
                    restPart = lines.join('\n').trim();
                }

                let htmlResponse = `<div style="border-left: 3px solid #00ff00; padding-left: 15px; margin-bottom: 15px;">`;
                htmlResponse += `<strong style="color: #00ff00; font-size: 1.2em;">${scorePart}</strong><br><br>`;
                htmlResponse += `<span style="font-style: italic;">${restPart.replace(/\n/g, '<br>')}</span>`;
                htmlResponse += `</div>`;
                
                // Add links with better formatting
                let linksHtml = `<div style="margin-top: 15px; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px;">`;
                data.data.results.forEach(res => {
                    linksHtml += `<a href="${res.url}" target="_blank" class="osint-link">
                        <span style="color: #00ff00;">🔗 ${res.platform}</span>
                    </a>`;
                });
                linksHtml += `</div>`;
                
                loadingEl.innerHTML = htmlResponse + linksHtml;
            } else {
                loadingEl.innerHTML = `<strong>root@wasp:</strong> ${data.response}`;
            }
            scrollChatToBottom();
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
            
            // If the response contains a surveillance link, open it directly
            if (data.data && data.data.link && data.tool === 'surveillance') {
                setTimeout(() => {
                    window.location.href = data.data.link;
                }, 1500);
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
        
        scrollChatToBottom();
        sendBtn.disabled = false;
        sendBtn.style.opacity = '1';
    })
    .catch(error => {
        document.getElementById(loadingId).innerHTML = `<strong>❌ Error:</strong> ${error.message}`;
        scrollChatToBottom();
        sendBtn.disabled = false;
        sendBtn.style.opacity = '1';
    });
}
function generateWaspResponse(message) {
    return "Response to: " + message;
}


// Функция синхронизации зеркала с инпутом
function syncMirror() {
    const value = userInput.value;
    const lowerValue = value.toLowerCase();
    const inputMirror = document.getElementById('input-mirror');
    
    if (!inputMirror) return;

    // Логика маскировки пароля
    let displayValue = value;
    const passCmd = "check password ";
    
    if (lowerValue.startsWith(passCmd)) {
        const prefix = value.substring(0, passCmd.length);
        const password = value.substring(passCmd.length);
        displayValue = prefix + "*".repeat(password.length);
    }
    
    inputMirror.textContent = displayValue;
    inputMirror.scrollLeft = userInput.scrollLeft;
}

userInput.addEventListener('input', function(event) {
    const value = this.value;
    
    // 1. Показ подсказок команд
    if (value.startsWith('/')) {
        const query = value.slice(1);
        showSuggestions(query);
    } else {
        suggestionsContainer.classList.add('hidden');
    }
    
    // 2. Синхронизируем зеркало
    syncMirror();
});

// Синхронизация прокрутки при ручном скроллинге инпута
userInput.addEventListener('scroll', syncMirror);

// Event listener for user input submission
userInput.addEventListener('keydown', function(event) {
    const items = suggestionsContainer.querySelectorAll('.command-item');
    
    if (!suggestionsContainer.classList.contains('hidden')) {
        if (event.key === 'ArrowDown') {
            event.preventDefault();
            selectedIndex = (selectedIndex + 1) % items.length;
            showSuggestions(userInput.value.slice(1));
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            selectedIndex = (selectedIndex - 1 + items.length) % items.length;
            showSuggestions(userInput.value.slice(1));
        } else if (event.key === 'Enter' && selectedIndex >= 0) {
            event.preventDefault();
            const cmdName = items[selectedIndex].querySelector('.command-name').textContent.slice(1);
            userInput.value = cmdName + ' ';
            syncMirror(); // Синхронизируем зеркало
            suggestionsContainer.classList.add('hidden');
            selectedIndex = -1;
        } else if (event.key === 'Escape') {
            suggestionsContainer.classList.add('hidden');
            selectedIndex = -1;
        } else if (event.key === 'Enter') {
            sendMessage();
        }
    } else if (event.key === 'Enter') {
        sendMessage();
    }
});

// Close suggestions when clicking outside
document.addEventListener('click', function(event) {
    if (!userInput.contains(event.target) && !suggestionsContainer.contains(event.target)) {
        suggestionsContainer.classList.add('hidden');
        selectedIndex = -1;
    }
});

// Initial welcome message
window.addEventListener('DOMContentLoaded', () => {
    if (chatContainer.innerHTML.trim() === '') {
        const messageElement = document.createElement('p');
        messageElement.innerHTML = `<strong>root@wasp:</strong> [SYSTEM BOOT COMPLETE]...<br>
        <strong>LISBETH:</strong> I'm here. If you're looking for someone, try <strong>/search</strong>. If you're worried about your security, <strong>/check password</strong>. Want to stalk anybody? Try <strong>/surveillance</strong>. Type <strong>/</strong> to see the full list of my tools. Don't waste my time with boring talk.`;
        chatContainer.appendChild(messageElement);
        scrollChatToBottom();
    }
});
