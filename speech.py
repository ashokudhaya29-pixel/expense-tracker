import assemblyai as aai

aai.settings.api_key = "YOUR_API_KEY"

def speech_to_text(file_path):
    config = aai.TranscriptionConfig(
        speech_model="universal-2"   # 🔥 IMPORTANT FIX
    )

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(file_path, config=config)

    return transcript.text