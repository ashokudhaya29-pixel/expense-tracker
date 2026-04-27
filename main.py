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