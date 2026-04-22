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

    incoming_msg = form.get("Body")
    num_media = int(form.get("NumMedia", 0))

    print("BODY:", repr(incoming_msg))
    print("NUM MEDIA:", num_media)

    # =========================
    # 🎤 AUDIO FLOW (STRICT)
    # =========================
    if num_media > 0:
        try:
            media_url = form.get("MediaUrl0")
            print("🎤 MEDIA URL:", media_url)

            audio_file = download_audio(media_url)
            text = speech_to_text(audio_file)

            print("📝 Transcription:", text)

            amount, category = extract_expense(text)
            save_to_sheet(amount, category)

            resp.message(f"💰 Expense saved: ₹{amount} - {category}")
            return Response(content=str(resp), media_type="application/xml")

        except Exception as e:
            print("❌ AUDIO ERROR:", e)
            resp.message("❌ Failed to process audio")
            return Response(content=str(resp), media_type="application/xml")

    # =========================
    # 📝 TEXT FLOW
    # =========================
    if incoming_msg and incoming_msg.strip():
        msg = incoming_msg.lower().strip()

        print("📝 TEXT MODE:", msg)

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
    return Response(content=str(resp), media_type="application/xml")    # =========================
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