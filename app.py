from flask import Flask, request, jsonify, render_template, send_file
import asyncio
import aiohttp
import assemblyai as aai
import tempfile
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from gtts import gTTS
import uuid
from playsound import playsound
from llm import generate_llm_response
from stt import transcribe_audio
from tts import generate_audio

app = Flask(__name__)

language = 'en'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            file.save(temp_audio.name)
            temp_audio_path = temp_audio.name

        try:
            # Run tasks
            transcription = transcribe_audio(temp_audio_path)
            llm_response = generate_llm_response(transcription)
            audio_file = generate_audio(llm_response)

            return jsonify({
                'transcription': transcription,
                'response': llm_response,
                'audio_file': audio_file
            })
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            os.unlink(temp_audio_path)

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_file(filename, mimetype="audio/mpeg")

@app.route('/cleanup', methods=['POST'])
def cleanup():
    filename = request.json.get('filename')
    if filename and os.path.exists(filename):
        os.remove(filename)
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
