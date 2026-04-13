import whisper
import os

# 👇 SET BOTH ffmpeg + ffprobe explicitly
ffmpeg_path = r"C:\Users\monis\OneDrive\Gen Ai\Monthly Tracker\ffmpeg-8.1-essentials_build\bin"

os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]
os.environ["FFMPEG_BINARY"] = os.path.join(ffmpeg_path, "ffmpeg.exe")

model = whisper.load_model("base")

def speech_to_text(file_path):
    print("Running local Whisper...")

    result = model.transcribe(file_path)

    text = result["text"]

    print("Transcribed text:", text)

    return text