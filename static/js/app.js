// ==========================================================
// DOCUMIND AI - Complete JavaScript with Document Selection
// ==========================================================

// DOM Elements
const uploadButton = document.getElementById('uploadButton');
const attachButton = document.getElementById('attachButton');
const sendButton = document.getElementById('sendButton');
const fileInput = document.getElementById('fileInput');
const documents = document.getElementById('documents');
const messageInput = document.getElementById('messageInput');
const chatMessages = document.getElementById('chatMessages');
const chatBody = document.getElementById('chatBody');
const welcomeScreen = document.getElementById('welcomeScreen');

let isProcessing = false;
let firstUpload = true;
let uploadedFiles = [];
let selectedDocument = null; // Track selected document

// ==========================================================
// AUTO-SCROLL FUNCTION
// ==========================================================

function scrollToBottom() {
    if (chatMessages) {
        chatMessages.scrollIntoView({ behavior: 'smooth', block: 'end' });
        chatMessages.parentElement?.scrollTo({
            top: chatMessages.parentElement.scrollHeight,
            behavior: 'smooth'
        });
    }
    if (chatBody) {
        chatBody.scrollTop = chatBody.scrollHeight;
    }
}

// ==========================================================
// INITIALIZATION
// ==========================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DocuMind AI loaded');
    loadDocuments();
    checkWelcomeScreen();
    scrollToBottom();
});

function checkWelcomeScreen() {
    const docCards = documents.querySelectorAll('.doc-card:not(.placeholder)');
    if (docCards.length === 0) {
        if (welcomeScreen) welcomeScreen.style.display = 'block';
    } else {
        if (welcomeScreen) welcomeScreen.style.display = 'none';
    }
}

// ==========================================================
// DOCUMENT LOADING WITH SELECTION
// ==========================================================

async function loadDocuments() {
    try {
        console.log('📄 Loading documents...');
        const response = await fetch('/documents');
        const data = await response.json();
        
        if (data.success && data.documents && data.documents.length > 0) {
            firstUpload = false;
            documents.innerHTML = '';
            uploadedFiles = data.documents;
            
            // Add a "All Documents" option first
            const allCard = document.createElement('div');
            allCard.className = 'doc-card';
            allCard.style.border = '2px solid var(--primary)';
            allCard.innerHTML = `
                <i class="bi bi-database"></i>
                <div class="doc-info">
                    <h6>📚 All Documents</h6>
                    <small>${data.documents.length} documents • ${data.total_chunks || 0} chunks</small>
                </div>
            `;
            allCard.onclick = function() {
                selectDocument(null, this);
            };
            documents.appendChild(allCard);
            
            data.documents.forEach(doc => {
                const ext = doc.name.split('.').pop().toLowerCase();
                const iconMap = {
                    'pdf': 'bi-file-earmark-pdf-fill text-danger',
                    'ppt': 'bi-file-earmark-ppt-fill text-warning',
                    'pptx': 'bi-file-earmark-ppt-fill text-warning'
                };
                const icon = iconMap[ext] || 'bi-file-earmark-fill';
                
                const card = document.createElement('div');
                card.className = 'doc-card';
                card.dataset.docName = doc.name;
                card.innerHTML = `
                    <i class="bi ${icon}"></i>
                    <div class="doc-info">
                        <h6>${doc.name}</h6>
                        <small>${doc.total_chunks || 0} Chunks • ${doc.total_pages || 'N/A'} Pages</small>
                    </div>
                    <span class="doc-badge" style="display:none; background: var(--primary); color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px;">Selected</span>
                `;
                card.onclick = function() {
                    selectDocument(doc.name, this);
                };
                documents.appendChild(card);
            });
            
            // Auto-select first document or "All"
            if (data.documents.length === 1) {
                const firstCard = documents.querySelector('.doc-card:not(:first-child)');
                if (firstCard) {
                    selectDocument(data.documents[0].name, firstCard);
                }
            } else {
                selectDocument(null, documents.querySelector('.doc-card:first-child'));
            }
            
            console.log(`✅ Loaded ${data.documents.length} documents, ${data.total_chunks || 0} total chunks`);
            
            if (welcomeScreen) welcomeScreen.style.display = 'none';
        } else {
            documents.innerHTML = `
                <div class="doc-card placeholder">
                    <i class="bi bi-file-earmark"></i>
                    <div class="doc-info">
                        <h6>No Documents</h6>
                        <small>Upload PDF / PPT</small>
                    </div>
                </div>
            `;
            if (welcomeScreen) welcomeScreen.style.display = 'block';
        }
        scrollToBottom();
    } catch (e) {
        console.error('❌ Failed to load documents:', e);
        documents.innerHTML = `
            <div class="doc-card placeholder">
                <i class="bi bi-exclamation-triangle"></i>
                <div class="doc-info">
                    <h6>Error Loading</h6>
                    <small>Refresh the page</small>
                </div>
            </div>
        `;
    }
}

function selectDocument(docName, cardElement) {
    // Clear all selections
    document.querySelectorAll('.doc-card').forEach(c => {
        c.style.border = 'none';
        const badge = c.querySelector('.doc-badge');
        if (badge) badge.style.display = 'none';
    });
    
    // Highlight selected
    if (cardElement) {
        cardElement.style.border = '2px solid var(--primary)';
        const badge = cardElement.querySelector('.doc-badge');
        if (badge) badge.style.display = 'inline';
    }
    
    selectedDocument = docName;
    console.log(`📌 Selected document: ${docName || 'All Documents'}`);
    
    // Add system message
    const info = document.createElement('div');
    info.className = 'bot-message';
    info.style.cssText = 'font-size: 13px; opacity: 0.7; padding: 8px 14px;';
    const docDisplay = docName || 'All Documents';
    info.innerHTML = `🔍 Now searching in: <strong>${docDisplay}</strong>`;
    chatMessages.appendChild(info);
    scrollToBottom();
}

// ==========================================================
// FILE UPLOAD
// ==========================================================

uploadButton?.addEventListener('click', () => fileInput?.click());
attachButton?.addEventListener('click', () => fileInput?.click());

fileInput?.addEventListener('change', async function() {
    const files = this.files;
    if (!files || files.length === 0) return;
    
    for (const file of files) {
        await uploadFile(file);
    }
    
    this.value = '';
});

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        if (welcomeScreen) welcomeScreen.style.display = 'none';
        
        const statusDiv = document.createElement('div');
        statusDiv.className = 'bot-message';
        statusDiv.innerHTML = `⏳ Processing <strong>${file.name}</strong>...`;
        chatMessages.appendChild(statusDiv);
        scrollToBottom();

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        statusDiv.remove();

        if (data.success) {
            if (firstUpload) {
                documents.innerHTML = '';
                firstUpload = false;
            }

            // Reload documents to update the list
            await loadDocuments();

            addMessage(`✅ Document uploaded: **${data.filename}** (${data.chunks} chunks, ${data.pages} pages)`, 'bot');
            
            if (welcomeScreen) welcomeScreen.style.display = 'none';
        } else {
            addMessage(`❌ ${data.message}`, 'bot');
        }
        scrollToBottom();
    } catch (e) {
        console.error('Upload error:', e);
        addMessage(`❌ Failed to upload ${file.name}. Please try again.`, 'bot');
        scrollToBottom();
    }
}

// ==========================================================
// CHAT FUNCTIONS
// ==========================================================

function addMessage(text, sender, metadata = null) {
    const div = document.createElement('div');
    div.className = sender === 'user' ? 'user-message' : 'bot-message';
    
    if (sender === 'bot') {
        div.innerHTML = formatMessage(text, metadata);
    } else {
        div.innerHTML = text;
    }
    
    chatMessages.appendChild(div);
    setTimeout(scrollToBottom, 50);
    return div;
}

function formatMessage(text, metadata) {
    let html = text;
    
    html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang || 'text'}">${escapeHtml(code.trim())}</code></pre>`;
    });
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/^[-*]\s+(.*)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, (match) => `<ul>${match}</ul>`);
    html = html.replace(/^\d+\.\s+(.*)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, (match) => `<ol>${match}</ol>`);
    html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    html = html.replace(/\n/g, '<br>');
    
    if (metadata && metadata.sources && metadata.sources.length > 0) {
        html += '<br><br><details><summary>📚 Sources</summary><ul>';
        metadata.sources.forEach((source, i) => {
            const doc = source.metadata?.document_name || 'Unknown';
            const pageDisplay = source.metadata?.page_display || 'N/A';
            const score = source.score ? ` (${Math.round(source.score * 100)}% match)` : '';
            html += `<li><strong>Source ${i + 1}:</strong> ${doc} (${pageDisplay})${score}</li>`;
        });
        html += '</ul></details>';
    }
    
    if (metadata && metadata.tokens_used > 0) {
        html += `<br><small style="color: #9aa8b5;">⚡ ${metadata.tokens_used} tokens used</small>`;
    }
    
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==========================================================
// SEND MESSAGE
// ==========================================================

async function sendMessage() {
    if (isProcessing) return;
    
    const text = messageInput.value.trim();
    if (text === '') return;

    isProcessing = true;
    
    if (welcomeScreen) welcomeScreen.style.display = 'none';

    addMessage(text, 'user');
    messageInput.value = '';
    messageInput.style.height = '56px';

    const thinking = document.createElement('div');
    thinking.className = 'bot-message';
    thinking.innerHTML = `<div class="thinking-dots"><span></span><span></span><span></span></div>`;
    chatMessages.appendChild(thinking);
    scrollToBottom();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        thinking.remove();

        if (data.success) {
            const metadata = {
                sources: data.sources || [],
                chunks_used: data.chunks_used || 0,
                tokens_used: data.tokens_used || 0
            };
            
            let answerText = data.answer;
            
            if (data.context_used) {
                answerText = '📄 ' + answerText;
            } else {
                answerText = '💡 ' + answerText;
            }
            
            addMessage(answerText, 'bot', metadata);
            
            const infoDiv = document.createElement('div');
            infoDiv.style.cssText = `
                align-self: flex-start;
                font-size: 11px;
                color: #9aa8b5;
                margin-top: -10px;
                margin-bottom: 10px;
                padding: 4px 12px;
                background: rgba(50, 50, 70, 0.5);
                border-radius: 12px;
                animation: fadeIn 0.3s ease;
            `;
            if (data.chunks_used > 0) {
                let docInfo = '';
                if (data.detected_document) {
                    docInfo = ` from <strong>${data.detected_document}</strong>`;
                }
                infoDiv.innerHTML = `📄 Retrieved ${data.chunks_used} chunk${data.chunks_used > 1 ? 's' : ''}${docInfo}`;
            } else {
                infoDiv.innerHTML = `💡 No document context found - using general knowledge`;
            }
            chatMessages.appendChild(infoDiv);
        } else {
            addMessage(`❌ ${data.message}`, 'bot');
        }
        scrollToBottom();
    } catch (error) {
        thinking.remove();
        console.error('Chat error:', error);
        addMessage('❌ Server error. Please try again.', 'bot');
        scrollToBottom();
    }
    
    isProcessing = false;
}

// ==========================================================
// EVENT LISTENERS
// ==========================================================

sendButton?.addEventListener('click', sendMessage);

messageInput?.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

messageInput?.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 160) + 'px';
});

// ==========================================================
// DRAG & DROP
// ==========================================================

document.addEventListener('dragover', (e) => e.preventDefault());
document.addEventListener('drop', (e) => e.preventDefault());

chatBody?.addEventListener('dragover', (e) => {
    e.preventDefault();
    chatBody.style.border = '2px dashed var(--primary)';
});

chatBody?.addEventListener('dragleave', (e) => {
    e.preventDefault();
    chatBody.style.border = 'none';
});

chatBody?.addEventListener('drop', async (e) => {
    e.preventDefault();
    chatBody.style.border = 'none';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        for (const file of files) {
            const ext = file.name.split('.').pop().toLowerCase();
            if (['pdf', 'ppt', 'pptx'].includes(ext)) {
                await uploadFile(file);
            } else {
                addMessage(`❌ Skipped ${file.name} - Only PDF, PPT, and PPTX files are supported.`, 'bot');
            }
        }
        scrollToBottom();
    }
});

// ==========================================================
// UTILITY FUNCTIONS
// ==========================================================

async function clearAllDocuments() {
    if (confirm('⚠️ Are you sure you want to clear ALL uploaded documents?\n\nThis will delete all indexed data and cannot be undone.')) {
        try {
            const response = await fetch('/clear', {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                alert('✅ All documents cleared successfully!');
                location.reload();
            } else {
                alert('❌ Failed to clear: ' + data.message);
            }
        } catch (e) {
            alert('❌ Error clearing documents: ' + e.message);
        }
    }
}

function newChat() {
    chatMessages.innerHTML = '';
    if (welcomeScreen) welcomeScreen.style.display = 'block';
    messageInput.value = '';
    messageInput.style.height = '56px';
    scrollToBottom();
}

function showAbout() {
    alert('🤖 DocuMind AI\n\nIntelligent Document Assistant\n\nUpload PDF and PowerPoint files\nChat with your documents\nGet accurate answers with citations');
}

// ==========================================================
// KEYBOARD SHORTCUTS
// ==========================================================

document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        messageInput.focus();
    }
});

// ==========================================================
// OBSERVER FOR AUTO-SCROLL
// ==========================================================

const observer = new MutationObserver(() => {
    scrollToBottom();
});

if (chatMessages) {
    observer.observe(chatMessages, {
        childList: true,
        subtree: true,
        characterData: true
    });
}

console.log('📚 DocuMind AI ready - supports multiple documents with selection');