import assemblyai as aai
import os

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

def speech_to_text(file_path):
    print("Using AssemblyAI...")

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(file_path)

    return transcript.text