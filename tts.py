from gtts import gTTS
import uuid
from transformers import pipeline
import os 
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


language = 'en'

def generate_audio(text):
    tts = gTTS(text=text, lang=language, slow=False)
    audio_file = f"response_{uuid.uuid4()}.mp3"
    tts.save(audio_file)
    return audio_file
    