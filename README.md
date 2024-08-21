# LLM-Voicebot

It is a Voicebot that processes audio by transcribing them, generating responses using a language model, and converting those responses into audio files. It leverages various python libraries and services to accomplish these tasks.

## Functionality

- **Audio Transcription**: Powered by Assembly AI API.
- **Language Model**: Utilizes Gemini API for generating responses.
- **Text-to-Speech**: Converts text responses to audio using the gTTS library.


## Demo Video
[Watch the demo video here](https://github.com/user-attachments/assets/69db1566-1575-4edf-a485-98cf2ababe1f)


## SET UP 

1. **Clone the repository**
  ```
  git clonehttps://github.com/gulshan-100/LLM-Voicebot.git
  cd LLM-Voicebot
  ```
2. **Create a Virtual Environment (Optional but recommended)**
3. **Install Dependencies**
   ```
   pip install -r requirementx.txt
   ```
4. **Add .env file:** Create a .env file in the root directory and add your API keys for Assembly AI, Google Gemini, and Hugging Face:
  ```
  aai.settings.api_key = ""
  GOOGLE_API_KEY = ""
  HUGGING_FACE_API = ""
  ```
4. **Run the voicebot**
   ```
   python app.py
   ```
   By default, the application will be accessible at http://127.0.0.1:5000/

## Future Improvements
We need to focus on enhancing the turnaround time for our voicebot. Currently, the process of transcribing audio, generating responses, and producing output files can be slow. By optimizing these workflows, implementing asynchronous processing, and exploring more efficient technologies, we aim to significantly reduce the time required to handle each request. This will improve user experience and make our service more responsive and efficient.





   
