from transformers import pipeline
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

transcriber = pipeline(task="automatic-speech-recognition",
                       model="openai/whisper-small")

def transcribe_audio_whisper(file_path):
    result = transcriber(file_path)
    return result.text
