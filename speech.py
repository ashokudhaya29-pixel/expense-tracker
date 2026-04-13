import os
import assemblyai as aai

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

def speech_to_text(file_path):
    print("🎯 Sending to AssemblyAI...")

    config = aai.TranscriptionConfig(
        speech_model="universal-2"
    )

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(file_path, config=config)

    print("✅ Transcribed:", transcript.text)

    return transcript.text