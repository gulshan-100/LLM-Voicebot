const recordButton = document.getElementById('recordButton');
const statusElement = document.getElementById('status');
const chatMessages = document.getElementById('chatMessages');

let audioQueue = [];
let isPlaying = false;

let mediaRecorder;
let audioChunks = [];
let isRecording = false;

recordButton.addEventListener('click', toggleRecording);

function toggleRecording() {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = sendAudioToServer;

        mediaRecorder.start();
        isRecording = true;
        recordButton.innerHTML = '🎤 Stop Recording';
        statusElement.textContent = 'Recording...';
        addMessage('user', '🎤 Recording...');
    } catch (error) {
        console.error('Error starting recording:', error);
        statusElement.textContent = 'Error: Could not start recording';
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        isRecording = false;
        recordButton.innerHTML = '🎤 Start Recording';
        statusElement.textContent = 'Processing...';
    }
}

async function sendAudioToServer() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.wav');

    try {
        const response = await fetch('/process_audio_stream', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        statusElement.textContent = 'Processing (streaming)...';

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            // SSE-style messages are separated by double newline
            const parts = buffer.split('\n\n');
            buffer = parts.pop();

            for (const part of parts) {
                if (!part.trim()) continue;
                const lines = part.split('\n');
                let event = 'message';
                let data = '';
                for (const line of lines) {
                    if (line.startsWith('event:')) {
                        event = line.replace('event:', '').trim();
                    } else if (line.startsWith('data:')) {
                        data += line.replace('data:', '').trim();
                    }
                }

                try {
                    const payload = JSON.parse(data);
                    if (event === 'transcription') {
                        statusElement.textContent = 'Transcription ready';
                        addMessage('user', payload.text);
                    } else if (event === 'llm_response_start') {
                        statusElement.textContent = 'Generating response...';
                        const botMsg = document.createElement('div');
                        botMsg.classList.add('bot-message');
                        botMsg.dataset.streaming = 'true';
                        botMsg.textContent = '';
                        chatMessages.appendChild(botMsg);
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                        window.__currentBotStreamElement = botMsg;
                    } else if (event === 'llm_token') {
                        const token = payload.token || '';
                        const el = window.__currentBotStreamElement;
                        if (el) {
                            el.textContent += token;
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }
                    } else if (event === 'llm_response') {
                        statusElement.textContent = 'Response ready';
                        const el = window.__currentBotStreamElement;
                        if (el) {
                            el.dataset.streaming = 'false';
                            delete window.__currentBotStreamElement;
                        }
                    } else if (event === 'audio_chunk') {
                        const audioData = Uint8Array.from(atob(payload.data), c => c.charCodeAt(0));
                        const blob = new Blob([audioData], { type: 'audio/mpeg' });
                        const audio = new Audio(URL.createObjectURL(blob));
                        playAudioSequentially(audio);
                    } else if (event === 'error') {
                        statusElement.textContent = 'Error: ' + payload.error;
                        addMessage('bot', 'Error: ' + payload.error);
                    }
                } catch (err) {
                    console.error('Failed parse SSE payload', err, data);
                }
            }
        }

    } catch (error) {
        console.error('Error:', error);
        statusElement.textContent = 'Error: ' + error.message;
    }

    audioChunks = [];
}

function addMessage(speaker, text) {
    const msg = document.createElement('div');
    msg.textContent = text;
    msg.classList.add(speaker + '-message');
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add welcome message
addMessage('bot', 'Hello! I\'m your AI voice assistant. Click the microphone to start recording.');

function playAudioSequentially(audio) {
    audioQueue.push(audio);
    if (!isPlaying) {
        playNextAudio();
    }
}

function playNextAudio() {
    if (audioQueue.length > 0) {
        isPlaying = true;
        const audio = audioQueue.shift();
        audio.onended = () => {
            playNextAudio();
        };
        audio.play();
    } else {
        isPlaying = false;
    }
}