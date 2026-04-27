from fastapi import FastAPI,Request
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

    user = form.get("From")
    incoming_msg = form.get("Body") or ""
    media_url = form.get("MediaUrl0")

    print("USER:", user)
    print("BODY:", incoming_msg)
    print("MEDIA:", media_url)

    msg = incoming_msg.lower().strip()

    # =========================
    # 🧠 LEARNING COMMAND
    # =========================
    if msg.startswith("learn"):
        parts = msg.split()

        if len(parts) >= 3:
            keyword = parts[1]
            category = parts[2].capitalize()

            save_learning(user, keyword, category)

            resp.message(f"✅ Learned: {keyword} → {category}")
        else:
            resp.message("Usage: learn <keyword> <category>")

        return Response(str(resp), media_type="application/xml")

    # =========================
    # 🎤 AUDIO FLOW
    # =========================
    if media_url:
        try:
            audio_file = download_audio(media_url)
            text = speech_to_text(audio_file)

            print("📝 Transcription:", text)

            if not text:
                resp.message("❌ Could not understand audio")
                return Response(str(resp), media_type="application/xml")

            amount, category = extract_expense(text, user)

            save_to_sheet(amount, category, user)

            resp.message(f"💰 Expense saved: {amount} - {category}")
            return Response(str(resp), media_type="application/xml")

        except Exception as e:
            print("❌ ERROR:", str(e))
            resp.message("❌ Error processing audio")
            return Response(str(resp), media_type="application/xml")

    # =========================
    # 🗑 DELETE COMMAND
    # =========================
    if msg.startswith("delete"):
        parts = msg.split()

    # 👉 Case 1: Just "delete"
    if len(parts) == 1:
        entries = get_last_entries(user)

        if not entries:
            resp.message("⚠️ No entries found")
            return Response(str(resp), media_type="application/xml")

        reply = "🧾 Last Entries:\n\n"

        for i, (_, row) in enumerate(entries, start=1):
            amount = row[1]
            category = row[2]
            reply += f"{i}. {amount} - {category}\n"

        reply += "\nReply: delete <number>"

        resp.message(reply)
        return Response(str(resp), media_type="application/xml")

    # 👉 Case 2: delete 2
    elif len(parts) == 2:
        try:
            serial = int(parts[1])
            result = delete_by_serial(user, serial)
            resp.message(result)
        except:
            resp.message("⚠️ Invalid format. Use: delete 2")

        return Response(str(resp), media_type="application/xml")

    # =========================
    # 💬 TEXT FLOW
    # =========================
    if incoming_msg:
        if msg == "summary":
            summary = get_monthly_summary(user)
            resp.message(summary)
        else:
            resp.message("Send voice note 🎙️ or type 'summary' 📊")

        return Response(str(resp), media_type="application/xml")

    # =========================
    # DEFAULT
    # =========================
    resp.message("Send voice note or type 'summary'")
    return Response(str(resp), media_type="application/xml")    