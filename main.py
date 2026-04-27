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
async def whatsapp(request: Request):

    form = await request.form()
    resp = MessagingResponse()
    user = form.get("From")   # 👈 ADD THIS
    print("USER:", user)

    incoming_msg = form.get("Body")
    media_url = form.get("MediaUrl0")

    print("BODY:", incoming_msg)
    print("MEDIA:", media_url)

    # =========================
    # 1. AUDIO FLOW
    # =========================
    if media_url:
        try:
            audio_file = download_audio(media_url)
            text = speech_to_text(audio_file)

            print("📝 Transcription:", text)

            if not text:
                resp.message("❌ Could not understand audio")
                return Response(content=str(resp), media_type="application/xml")

            amount, category = extract_expense(text)

            save_to_sheet(amount, category, user)

            resp.message(f"💰 Expense saved: {amount} - {category}")
            return Response(content=str(resp), media_type="application/xml")

        except Exception as e:
            print("❌ ERROR:", str(e))
            resp.message("❌ Error processing audio")
            return Response(content=str(resp), media_type="application/xml")

    # =========================
    # 2. TEXT FLOW
    # =========================
    if incoming_msg:
        msg = incoming_msg.lower().strip()

        if msg == "summary":
            user = form.get("From")
            summary = get_monthly_summary(user)
            resp.message(summary)
        else:
            resp.message("Send voice note 🎙️ or type 'summary' 📊")

        return Response(content=str(resp), media_type="application/xml")

    # =========================
    # DEFAULT
    # =========================
    resp.message("Send voice note or type 'summary'")
    return Response(content=str(resp), media_type="application/xml")