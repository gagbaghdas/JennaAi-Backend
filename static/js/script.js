const textEditor = document.getElementById('editor-container');
const responseText = document.getElementById('response-text');
let askJennaBtn = null;

textEditor.addEventListener('mouseup', (event) => {
    const selectedText = window.getSelection().toString();
    if (selectedText) {
        if (!askJennaBtn) {
            askJennaBtn = document.createElement('button');
            askJennaBtn.innerText = 'Ask Jenna';
            askJennaBtn.addEventListener('click', sendTextToBackend);
            document.body.appendChild(askJennaBtn);
        }
        askJennaBtn.style.position = 'absolute';
        askJennaBtn.style.left = `${event.clientX + window.scrollX}px`;
        askJennaBtn.style.top = `${event.clientY + window.scrollY - askJennaBtn.offsetHeight}px`;
    } else {
        removeAskJennaButton();
    }
});

document.addEventListener('mousedown', (event) => {
    if (askJennaBtn && event.target !== askJennaBtn && event.target !== textEditor) {
        removeAskJennaButton();
    }
});

function sendTextToBackend() {
    const loadingIndicator = document.getElementById('loading-indicator');
    const editorContainer = document.getElementById('editor-container');
    const responsePanel = document.getElementById('response-panel');

    loadingIndicator.style.display = 'block';
    editorContainer.style.pointerEvents = 'none';
    responsePanel.style.pointerEvents = 'none';

    const selectedText = window.getSelection().toString();
    if (selectedText) {
        fetch('/ask-jenna-promts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: selectedText }),
        })
        .then(response => response.json())
        .then(data => {
            const promptsSection = document.getElementById('prompts-section');
            promptsSection.innerHTML = '';  // Clear any existing buttons
            data.generated_response.forEach((prompt, index) => {
                const button = document.createElement('button');
                button.innerText = prompt;
                button.className = 'prompt-button';
                button.addEventListener('click', () => sendPromptToBackend(prompt));
                promptsSection.appendChild(button);
            });
            
            loadingIndicator.style.display = 'none';
            editorContainer.style.pointerEvents = '';
            responsePanel.style.pointerEvents = '';
        })
        .catch(error => {
            console.error('Error:', error);
            loadingIndicator.style.display = 'none';
            editorContainer.style.pointerEvents = '';
            responsePanel.style.pointerEvents = '';
        });
    }
    removeAskJennaButton();
}

function sendPromptToBackend(prompt) {
    const loadingIndicator = document.getElementById('loading-indicator');
    const editorContainer = document.getElementById('editor-container');
    const responsePanel = document.getElementById('response-panel');
    const promptsSection = document.getElementById('prompts-section');
    const chatConversation = document.getElementById('chat-conversation');

    loadingIndicator.style.display = 'block';
    editorContainer.style.pointerEvents = 'none';
    responsePanel.style.pointerEvents = 'none';

    fetch('/ask-jenna-ideas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: prompt }),
    })
    .then(response => response.json())
    .then(data => {
        const strategy = data.strategy;
        if (!strategy || Object.keys(strategy).length === 0) {
            console.log('No insight generated');
            return;
        }
        chatConversation.innerHTML = '';
        updateChatConversation(prompt, strategy);

        loadingIndicator.style.display = 'none';
        editorContainer.style.pointerEvents = '';
        responsePanel.style.pointerEvents = '';
    })
    .catch(error => {
        console.error('Error:', error);
        loadingIndicator.style.display = 'none';
        editorContainer.style.pointerEvents = '';
        responsePanel.style.pointerEvents = '';
    });
}

function updateChatConversation(userMessage, jennaMessage) {
    const chatConversation = document.getElementById('chat-conversation');
    
    if(userMessage) {
        // Add user's message
        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'chat-message user-message';
        const userIconDiv = document.createElement('div');
        userIconDiv.className = 'icon';
        userMessageDiv.appendChild(userIconDiv);
        const userTextDiv = document.createElement('div');
        userTextDiv.className = 'message-text';
        userTextDiv.innerText = userMessage;
        userMessageDiv.appendChild(userTextDiv);
        chatConversation.appendChild(userMessageDiv);
    }
    if(jennaMessage){
        const { description, use_case } = jennaMessage;
        // Add Jenna's response
        const jennaMessageDiv = document.createElement('div');
        jennaMessageDiv.className = 'chat-message jenna-message';
        const jennaIconDiv = document.createElement('div');
        jennaIconDiv.className = 'icon';
        jennaMessageDiv.appendChild(jennaIconDiv);
        const jennaTextDiv = document.createElement('div');
        jennaTextDiv.className = 'message-text';
        if (typeof jennaMessage === 'string') {
            jennaTextDiv.innerHTML = jennaMessage;
        } else {
            jennaTextDiv.innerHTML = `
            <div class="insight">
                <div class="insight-section">
                    <div class="insight-heading">Insight Description:</div>
                    <div class="insight-content">${description}</div>
                </div>
                <div class="insight-section">
                    <div class="insight-heading">Use cases:</div>
                    <div class="insight-content">${use_case}</div>
                </div>
            </div>`;
        }

        jennaMessageDiv.appendChild(jennaTextDiv);
        chatConversation.appendChild(jennaMessageDiv);
    }

    // Scroll to the bottom of the chat conversation
    chatConversation.scrollTop = chatConversation.scrollHeight;
}

function sendConversationToBackend() {
    const loadingIndicator = document.getElementById('loading-indicator');
    const chatConversation = document.getElementById('chat-conversation');
    const conversationText = chatConversation.innerText;

    const chatTextElement = document.getElementById('chat-text');
    const chatText = chatTextElement.value.trim();
    loadingIndicator.style.display = 'block';
    
    fetch('/process-conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: chatText }),
    })
    .then(response => response.json())
    .then(data => {
        chatTextElement.value = '';
        const responseMessage = data.response_message;
        responseDict = JSON.parse(responseMessage);
        userMessage = responseDict.question;
        jennaMessage = responseDict.text;
        updateChatConversation(userMessage, jennaMessage);
        
        loadingIndicator.style.display = 'none';
    })
    .catch(error => {
        console.error('Error:', error);
        loadingIndicator.style.display = 'none';
    });
}

function updateInsights() {
    const textEditor = document.getElementById('editor-container');
    const insightsPanel = document.getElementById('insights-panel');
    
    // Get the text from the editor and trim any leading/trailing whitespace
    const editorText = textEditor.innerText.trim();
    
    // Check if the trimmed text is empty
    if (editorText.length === 0) {
        console.log('No text in editor, not sending request.');
        return;
    }

    // Extract data from insightsPanel, assuming it's formatted as in your example
    const insightSections = insightsPanel.getElementsByClassName('insight-section');
    const insightData = {};
    if (insightSections.length > 0) {
        Array.prototype.forEach.call(insightSections, section => {
            const heading = section.getElementsByClassName('insight-heading')[0].innerText;
            const content = section.getElementsByClassName('insight-content')[0].innerText;
            switch (heading) {
                case 'Insight Description:':
                    insightData.description = content;
                    break;
                case 'Use cases:':
                    insightData.use_cases = content;
                    break;
                case 'Source:':
                    insightData.source = content;
                    break;
                default:
                    console.error('Unknown heading:', heading);
            }
        });
    }

    fetch('/get-insights', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            text: editorText,
            insightData: insightData
        }),
    })
    .then(response => response.json())
    .then(data => {
        const insight = data.generated_insight;
        if (!insight || Object.keys(insight).length === 0) {
            console.log('No insight generated');
            return;
        }
        const { description, use_case, source } = insight;
        insightsPanel.innerHTML = `
            <div class="insight">
                <div class="insight-section">
                    <div class="insight-heading">Insight Description:</div>
                    <div class="insight-content">${description}</div>
                </div>
                <div class="insight-section">
                    <div class="insight-heading">Use cases:</div>
                    <div class="insight-content">${use_case}</div>
                </div>
                <div class="insight-section">
                    <div class="insight-heading">Source:</div>
                    <div class="insight-content"><a href="${source}" class="insight-link" target="_blank">${source}</a></div>
                </div>
            </div>`;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function removeAskJennaButton() {
    if (askJennaBtn) {
        document.body.removeChild(askJennaBtn);
        askJennaBtn = null;
    }
}

document.getElementById('send-button').addEventListener('click', sendConversationToBackend);

let intervalId = null;

document.getElementById('updateSwitch').addEventListener('change', function() {
    if (this.checked) {
        updateInsights();
        intervalId = setInterval(updateInsights, 180000);
    } else {
        clearInterval(intervalId);
    }
});
