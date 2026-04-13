import assemblyai as aai

aai.settings.api_key = "YOUR_API_KEY"

def speech_to_text(file_path):
    try:
        transcriber = aai.Transcriber()

        config = aai.TranscriptionConfig(
            speech_models=["universal"]   # ✅ correct (LIST)
        )

        transcript = transcriber.transcribe(file_path, config=config)

        return transcript.text

    except Exception as e:
        print("❌ ERROR in speech:", e)
        return ""