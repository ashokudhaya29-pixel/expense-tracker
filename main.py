from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from fastapi.responses import PlainTextResponse

from utils import download_audio
from speech import speech_to_text
from llm import extract_expense
from sheets import * # 👈 NEW FUNCTION

import os

port = int(os.environ.get("PORT", 10000))

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Server is running ✅"}
@app.post("/whatsapp")
def test():
    return {"message": "Webhook is working ✅"}
async def whatsapp(request: Request):

    form = await request.form()
    resp = MessagingResponse()

    incoming_msg = form.get("Body")
    media_url = form.get("MediaUrl0")

    print("BODY:", incoming_msg)
    print("MEDIA:", media_url)

    # =========================
    # 1. AUDIO EXPENSE FLOW ONLY
    # =========================
    if media_url is not None and media_url != "":
        num_media = int(form.get("NumMedia", 0))

        if num_media > 0:
            media_url = form.get("MediaUrl0")

            print("🎤 Processing audio:", media_url)
        try:
            print("RAW MEDIA VALUE:", repr(media_url))
            print("Processing audio_file = download_audio(media_url)")
            audio_file = download_audio(media_url)
            text = speech_to_text(audio_file)
            print("📝 Transcription:", text)
        except Exception as e:
            print("❌ ERROR in speech:", str(e))
            text = "Could not process audio"
        amount, category = extract_expense(text)
        save_to_sheet(amount, category)

        resp.message(f"💰 Expense saved: {amount} - {category}")
        return Response(content=str(resp), media_type="application/xml")
    
    if text == "Could not process audio":
        return PlainTextResponse("Audio failed")
    # =========================
    # 2. TEXT FLOW ONLY (SUMMARY)
    # =========================
    if incoming_msg:

        msg = incoming_msg.lower().strip()

        if msg == "summary":
            summary = get_monthly_summary()
            resp.message(summary)
        else:
            resp.message("Send voice note to add expense 🎙️ or type 'summary' 📊")

        return Response(content=str(resp), media_type="application/xml")

    # =========================
    # DEFAULT
    # =========================
    resp.message("Send voice note or type 'summary'")
    return Response(content=str(resp), media_type="application/xml")