import assemblyai as aai

# ✅ PASTE HERE (temporary test)
aai.settings.api_key = "8b03ef5fe2314819b4562443793d9d62"

def speech_to_text(file_path):
    transcriber = aai.Transcriber()

    config = aai.TranscriptionConfig(
        speech_models=["universal"]
    )

    transcript = transcriber.transcribe(file_path, config=config)

    return transcript.text