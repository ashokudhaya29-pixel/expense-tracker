from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from utils import download_audio
from speech import speech_to_text
from llm import extract_expense
from db import *
import os
import re

port = int(os.environ.get("PORT", 10000))

app = FastAPI()



def detect_category(text, user):
    text = text.lower()

    learned = get_learned_categories(user)
    for keyword, cat in learned.items():
        if keyword in text:
            return cat

    categories = {
        "Food": ["hotel", "food", "restaurant", "biryani", "tea", "coffee", "zomato", "swiggy"],
        "Grocery": ["zepto", "blinkit", "bigbasket", "grocery", "milk", "rice"],
        "Travel": ["uber", "ola", "bus", "petrol", "auto"],
        "Shopping": ["amazon", "flipkart", "myntra"],
        "Medical": ["hospital", "medicine", "tablet"],
        "Bills": ["eb", "electricity", "wifi", "rent", "recharge"]
    }

    for cat, words in categories.items():
        for w in words:
            if w in text:
                return cat

    return "Other"        

@app.get("/")
def home():
    return {"message": "Server is running ✅"}


@app.post("/whatsapp")
async def whatsapp(request: Request):
    form = await request.form()

    user = form.get("From", "")
    auto_archive_if_needed(user)
    body = form.get("Body", "").strip()
    media_url = form.get("MediaUrl0")

    resp = MessagingResponse()

    msg = body.lower().strip()

    print("USER:", user)
    print("BODY:", body)
    print("MEDIA:", media_url)

    # =========================
    # ✅ CONFIRMATION FLOW
    # =========================
    pending = get_pending_expense(user)

    if pending:
        
        if msg == "yes":
            save_to_sheet(pending["amount"], pending["category"], user)

            alert = check_category_budget(user, pending["category"])
            delete_pending_expense(user)
            if alert:
                resp.message(f"✅ Saved\n\n{alert}")
            else:
                resp.message("✅ Expense saved successfully.")
            return Response(str(resp), media_type="application/xml")

        elif msg == "no":
            delete_pending_expense(user)

            resp.message("❌ Expense cancelled.")
            return Response(str(resp), media_type="application/xml")

        elif msg.startswith("correct") or msg.startswith("update"):
            print("CORRECTION BLOCK HIT")
            print("BODY:", body)

            numbers = re.findall(r"\d+", body)

            if not numbers:
                resp.message("⚠️ Amount missing. Use: correct 300 Food")
                return Response(str(resp), media_type="application/xml")

            new_amount = float(numbers[0])

            valid_categories = [
                "food", "grocery", "travel", "shopping",
                "medical", "bills", "emi", "entertainment", "other"
            ]

            new_category = None
            body_lower = body.lower()

            for cat in valid_categories:
                if cat in body_lower:
                    new_category = cat.capitalize()
                    break

            if not new_category:
                resp.message("⚠️ Category missing. Use: correct 300 Food")
                return Response(str(resp), media_type="application/xml")

            try:
                save_to_sheet(new_amount, new_category, user)
                alert = check_category_budget(user, new_category)
                message = (
                    f"✅ Corrected and saved:\n\n"
                    f"Amount: ₹{int(new_amount)}\n"
                    f"Category: {new_category}"
                )

                if alert:
                    message += f"\n\n{alert}"

                   
                delete_pending_expense(user)

                resp.message(message)
                return Response(str(resp), media_type="application/xml")

            except Exception as e:
                print("❌ DB SAVE ERROR:", str(e))
                resp.message(f"❌ Save error: {str(e)}")
                return Response(str(resp), media_type="application/xml")
            
        else:
            resp.message(
                "⚠️ Please reply:\n"
                "yes = save\n"
                "no = cancel\n"
                "update <amount> <Category> = update and save"
            )
            return Response(str(resp), media_type="application/xml")

    # =========================
    # 🧠 LEARNING COMMAND
    # Example: learn zepto Grocery
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
            if amount == 0:
                for word in text.replace(".", "").split():
                    if word.isdigit():
                        amount = float(word)
                        break

            category = detect_category(text, user)

            save_pending_expense(user, amount, category, text)

            resp.message(
                f"📝 Please confirm:\n\n"
                f"Amount: ₹{amount}\n"
                f"Category: {category}\n\n"
                f"Reply:\n"
                f"yes = save\n"
                f"no = cancel\n"
                f"correct 500 Food = update and save"
            )

            return Response(str(resp), media_type="application/xml")

        except Exception as e:
            print("❌ ERROR:", str(e))
            resp.message("❌ Error processing audio")
            return Response(str(resp), media_type="application/xml")

    # =========================
    # 💰 SALARY COMMAND
    # Example: salary 30000
    # =========================
    if msg.startswith("salary"):
        parts = msg.split()

        if len(parts) >= 2 and parts[1].isdigit():
            salary = int(parts[1])
            result = set_salary(user, salary)
            resp.message(result)
        else:
            resp.message("Usage: salary 50000")

        return Response(str(resp), media_type="application/xml")
    if msg.startswith("set budget"):
        parts = msg.split()

        if len(parts) >= 4:
            category = parts[2].capitalize()
            amount = float(parts[3])

            result = set_category_budget(user, category, amount)
            resp.message(result)
        else:
            resp.message("Usage: set budget Food 10000")

        return Response(str(resp), media_type="application/xml")

    # =========================
    # ➕ ADD SALARY COMMAND
    # Example: addsalary 5000
    # =========================
    if msg.startswith("addsalary"):
        parts = msg.split()

        if len(parts) >= 2 and parts[1].isdigit():
            salary = int(parts[1])
            result = add_salary(user, salary)
            resp.message(result)
        else:
            resp.message("Usage: addsalary 5000")

        return Response(str(resp), media_type="application/xml")

    # =========================
    # 💰 BALANCE COMMAND
    # =========================
    if msg == "balance":
        report = get_balance_report(user)
        resp.message(report)
        return Response(str(resp), media_type="application/xml")

    # =========================
    # 📊 SUMMARY COMMAND
    # =========================
    if msg == "summary":
        summary = get_monthly_summary(user)
        resp.message(summary)
        return Response(str(resp), media_type="application/xml")

    # =========================
    # 📅 WEEKLY COMMAND
    # =========================
    if msg == "weekly":
        report = get_weekly_report(user)
        resp.message(report)
        return Response(str(resp), media_type="application/xml")

    # =========================
    # 🗑 DELETE COMMAND
    # Example: delete / delete 2
    # =========================
    if msg.startswith("delete"):
        parts = msg.split()

        if len(parts) == 1:
            entries = get_last_entries(user)

            if not entries:
                resp.message("⚠️ No entries found")
                return Response(str(resp), media_type="application/xml")

            message = "🧾 Last Entries:\n\n"

            for i, (_, row) in enumerate(entries, start=1):
                date = row[0]
                amount = row[2]
                category = row[3]
                message += f"{i}. ₹{amount} - {category} ({date})\n"

            message += "\nReply: delete <number>"

            resp.message(message)
            return Response(str(resp), media_type="application/xml")

        elif len(parts) == 2:
            try:
                serial = int(parts[1])
                result = delete_by_serial(user, serial)
                resp.message(result)
            except Exception as e:
                print("❌ Delete error:", str(e))
                resp.message("⚠️ Invalid format. Use: delete 2")

            return Response(str(resp), media_type="application/xml")

    # =========================
    # ✏️ EDIT COMMAND
    # Example: edit / edit 1 amount 350 / edit 1 category Food
    # =========================
    if msg.startswith("edit"):
        parts = msg.split()

        if len(parts) == 1:
            entries = get_last_entries(user)

            if not entries:
                resp.message("⚠️ No entries found")
                return Response(str(resp), media_type="application/xml")

            message = "✏️ Last Entries:\n\n"

            for i, (_, row) in enumerate(entries, start=1):
                date = row[0]
                amount = row[2]
                category = row[3]
                message += f"{i}. ₹{amount} - {category} ({date})\n"

            message += "\nReply:\nedit 1 amount 350\nedit 1 category Grocery"

            resp.message(message)
            return Response(str(resp), media_type="application/xml")

        elif len(parts) >= 4:
            try:
                serial = int(parts[1])
                field = parts[2]
                new_value = " ".join(parts[3:])

                result = update_entry_by_serial(user, serial, field, new_value)
                resp.message(result)

            except Exception as e:
                print("❌ Edit error:", str(e))
                resp.message("⚠️ Invalid format. Use: edit 1 amount 350")

            return Response(str(resp), media_type="application/xml")

        else:
            resp.message(
                "Usage:\n"
                "edit\n"
                "edit 1 amount 350\n"
                "edit 1 category Grocery"
            )
            return Response(str(resp), media_type="application/xml")
    if msg.startswith("archive"):
        parts = msg.split()

        if len(parts) == 2:
            result = archive_by_month(user, parts[1])
        else:
            result = archive_previous_month(user)

        resp.message(result)
        return Response(str(resp), media_type="application/xml")
        
    if msg == "compare":
        result = compare_months(user)
        resp.message(result)
        return Response(str(resp), media_type="application/xml")
    # =========================
    # DEFAULT MESSAGE
    # =========================
    resp.message(
        "Send voice note 🎙️ or type:\n"
        "summary\n"
        "weekly\n"
        "balance\n"
        "salary 50000\n"
        "addsalary 5000"
    )
    return Response(str(resp), media_type="application/xml")

@app.get("/send-daily-summary")
def send_daily_summary():
    users = supabase.table("expenses").select("user_phone").execute()

    sent_users = set()

    for row in users.data:
        user = row["user_phone"]

        if user in sent_users:
            continue

        summary = get_monthly_summary(user)

        # send via Twilio
        from twilio.rest import Client
        import os

        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )

        client.messages.create(
            body=f"📊 Daily Update:\n\n{summary}",
            from_="whatsapp:+14155238886",
            to=f"whatsapp:+{user}"
        )

        sent_users.add(user)

    return {"status": "sent"}

    