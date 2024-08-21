import assemblyai as aai
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def transcribe_audio(file_path):
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(file_path)
    return transcript.text