let mediaRecorder;
let audioChunks = [];
let isRecording = false;

const recordButton = document.getElementById('recordButton');
const statusElement = document.getElementById('status');
const chatMessages = document.getElementById('chatMessages');

recordButton.addEventListener('click', toggleRecording);

async function toggleRecording() {
    if (!isRecording) {
        await startRecording();
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
        recordButton.textContent = 'Stop Recording';
        statusElement.textContent = 'Recording...';
        addVoiceMessage('user');
    } catch (error) {
        console.error('Error starting recording:', error);
        statusElement.textContent = 'Error: Could not start recording';
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        isRecording = false;
        recordButton.textContent = 'Start Recording';
        statusElement.textContent = 'Processing...';
    }
}

async function sendAudioToServer() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.wav');

    try {
        const response = await fetch('/process_audio', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        statusElement.textContent = 'Response ready';

        addVoiceMessage('bot');

        const audio = new Audio('/audio/' + data.audio_file);
        audio.play();

        audio.onended = async () => {
            await fetch('/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filename: data.audio_file }),
            });
        };
    } catch (error) {
        console.error('Error:', error);
        statusElement.textContent = 'Error: ' + error.message;
    }

    audioChunks = [];
}

function addVoiceMessage(speaker) {
    const messageContainer = document.createElement('div');
    messageContainer.classList.add('voice-message', speaker + '-voice');

    const voiceIcon = document.createElement('div');
    voiceIcon.classList.add('voice-icon');

    const voiceLine = document.createElement('div');
    voiceLine.classList.add('voice-line');

    messageContainer.appendChild(voiceIcon);
    messageContainer.appendChild(voiceLine);
    chatMessages.appendChild(messageContainer);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}