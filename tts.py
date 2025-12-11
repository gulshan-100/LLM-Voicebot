import openai
import os
from dotenv import load_dotenv, find_dotenv
import httpx

load_dotenv(find_dotenv())

# Persistent HTTP client with connection pooling for lower latency
http_client = httpx.Client(
    timeout=httpx.Timeout(15.0, connect=5.0),
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
    http2=True
)

client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'), http_client=http_client)

def generate_audio(text):
    if not text or not text.strip():
        raise ValueError("No text to speak")
        
    response = client.audio.speech.create(
        model="tts-1-hd",  # HD model is optimized and faster
        voice="nova",  # Nova voice is faster than alloy
        input=text,
        speed=1.15  # Slightly faster speech for reduced latency
    )
    return response.content
