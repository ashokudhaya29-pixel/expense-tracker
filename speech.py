import assemblyai as aai
import os

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")  

def speech_to_text(file_path):
    transcriber = aai.Transcriber()

    config = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.best
    )

    transcript = transcriber.transcribe(file_path, config=config)

    return transcript.text