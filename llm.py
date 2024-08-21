from langchain_google_genai import ChatGoogleGenerativeAI
from flask import request
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

model = ChatGoogleGenerativeAI(
    model='gemini-pro',
    temperature=0.6
)

def generate_llm_response(text):
    prompt = f"Respond to this user query in only 30 words: {text}"
    llm_response = model.invoke(prompt)
    return llm_response.content

