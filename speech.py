import assemblyai as aai

aai.settings.api_key = "YOUR_API_KEY"

def speech_to_text(file_path):
    print("🎯 Sending to AssemblyAI...")

    config = aai.TranscriptionConfig(
        speech_model="universal-2"
    )

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(file_path, config=config)

    print("✅ AssemblyAI response received")

    return transcript.text