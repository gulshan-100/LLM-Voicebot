from flask import Flask, request, jsonify, render_template, Response
import json
from llm import generate_llm_response, stream_llm_response
from stt import transcribe_audio
from tts import generate_audio
from dotenv import load_dotenv, find_dotenv
import base64
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
import httpx

app = Flask(__name__)

# Thread pool for concurrent operations (speeds up parallel tasks)
executor = ThreadPoolExecutor(max_workers=4)

language = 'en'


load_dotenv(find_dotenv())

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

            if not transcription.strip():
                return jsonify({'error': 'Transcription is empty'}), 400
            
            llm_response = generate_llm_response(transcription)

            if not llm_response.strip():
                return jsonify({'error': 'LLM response is empty'}), 400

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


@app.route('/process_audio_stream', methods=['POST'])
def process_audio_stream():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    audio_data = file.read()

    def sse_event(event, data):
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    def generate():
        try:
            # Transcribe and immediately stream the transcription so the client can show it
            transcription = transcribe_audio(audio_data)
            yield sse_event('transcription', {'text': transcription})

            # Generate LLM response (stream tokens when available)
            yield sse_event('llm_response_start', {'info': 'Generating response'})
            full_response = ''
            word_buffer = ''
            
            try:
                for token in stream_llm_response(transcription):
                    full_response += token
                    word_buffer += token
                    
                    yield sse_event('llm_token', {'token': token})
                    
                    # Generate audio immediately as tokens arrive (every 1-2 words)
                    if len(word_buffer.strip().split()) >= 1 and (' ' in word_buffer or word_buffer.strip().endswith(('.', '?', '!', ','))):
                        audio_bytes = generate_audio(word_buffer.strip())
                        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                        yield sse_event('audio_chunk', {'data': audio_b64})
                        word_buffer = ''
            except Exception as e:
                yield sse_event('error', {'error': str(e)})
                return

            # Send final full response
            yield sse_event('llm_response', {'text': full_response})

            # Generate audio for any remaining text
            if word_buffer.strip():
                audio_bytes = generate_audio(word_buffer.strip())
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                yield sse_event('audio_chunk', {'data': audio_b64})
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                yield sse_event('audio_chunk', {'data': audio_b64})

            # Final event
            yield sse_event('done', {'status': 'complete'})

        except Exception as e:
            yield sse_event('error', {'error': str(e)})

    return Response(generate(), mimetype='text/event-stream')

@app.route('/llm', methods=['POST'])
def llm():
    data = request.get_json()
    text = data.get('text', '')
    if not text.strip():
        return jsonify({'error': 'No text provided'}), 400
    try:
        response = generate_llm_response(text)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Production-ready settings for lower latency
    app.run(
        debug=False,  # Disable debug mode in production
        threaded=True,  # Handle multiple requests concurrently
        host='0.0.0.0',
        port=5000
    )
