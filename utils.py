import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

def download_audio(url):
    response = requests.get(
        url,
        auth=HTTPBasicAuth(ACCOUNT_SID, AUTH_TOKEN)
    )

    print("Download status:", response.status_code)

    with open("audio.wav", "wb") as f:
        f.write(response.content)

    return "audio.wav"