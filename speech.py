import assemblyai as aai
import os

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

def speech_to_text(file_path):
    try:
        print("🎯 Sending to AssemblyAI...")

        transcriber = aai.Transcriber()

        config = aai.TranscriptionConfig(
            speech_models=["universal"]   # ✅ FIXED
        )

        transcript = transcriber.transcribe(file_path, config=config)

        print("📝 Transcribed:", transcript.text)

        return transcript.text or ""

    except Exception as e:
        print("❌ ERROR in speech:", str(e))
        return ""