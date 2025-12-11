import openai
import os
from dotenv import load_dotenv, find_dotenv
from io import BytesIO
import httpx

load_dotenv(find_dotenv())

# Persistent HTTP client with connection pooling for lower latency
http_client = httpx.Client(
    timeout=httpx.Timeout(15.0, connect=5.0),
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
    http2=True
)

client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'), http_client=http_client)

def transcribe_audio(audio_data):
    audio_file = BytesIO(audio_data)
    audio_file.name = 'audio.wav'  # Whisper needs a name
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text",  # Plain text is faster to parse
        timeout=10  # 10 second timeout
    )
    return transcript.text if hasattr(transcript, 'text') else transcript