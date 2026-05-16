from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from utils import download_audio
from speech import speech_to_text
from llm import extract_expense
from db import *
from advisor import ask_finance_advisor
import os
import re

app = FastAPI()


def twiml(resp):
    return Response(str(resp), media_type="application/xml")


def detect_category(text, user):
    text = text.lower()

    learned = get_learned_categories(user)
    for keyword, cat in learned.items():
        if keyword.lower() in text:
            return cat

    categories = {
        "Food": ["hotel", "food", "restaurant", "biryani", "tea", "coffee", "zomato", "swiggy"],
        "Grocery": ["zepto", "blinkit", "bigbasket", "grocery", "milk", "rice"],
        "Travel": ["uber", "ola", "bus", "petrol", "auto"],
        "Shopping": ["amazon", "flipkart", "myntra"],
        "Medical": ["hospital", "medicine", "tablet"],
        "Bills": ["eb", "electricity", "wifi", "rent", "recharge"],
    }

    for cat, words in categories.items():
        for word in words:
            if word in text:
                return cat

    return "Other"


def parse_correction(body, user):
    numbers = re.findall(r"\d+", body)

    if not numbers:
        return None, None, "⚠️ Amount missing. Use: correct 300 Food"

    amount = float(numbers[0])

    clean_text = body.lower()
    clean_text = clean_text.replace("correct", "")
    clean_text = clean_text.replace("update", "")
    clean_text = re.sub(r"\d+", "", clean_text)
    clean_text = clean_text.replace("=", "")
    clean_text = clean_text.replace("and save", "")
    clean_text = clean_text.strip()

    if not clean_text:
        return None, None, "⚠️ Category missing. Use: correct 300 Food"

    learned = get_learned_categories(user)
    category = None

    for keyword, cat in learned.items():
        if keyword.lower() in clean_text:
            category = cat
            break

    if not category:
        category = clean_text

    category = category.strip().replace(" ", "_")
    category = "_".join(part.capitalize() for part in category.split("_") if part)

    return amount, category, None


@app.get("/")
def home():
    return {"message": "Server is running ✅"}


@app.get("/ping")
def ping():
    return {"status": "alive"}


@app.post("/whatsapp")
async def whatsapp(request: Request):
    form = await request.form()

    user = form.get("From", "")
    body = form.get("Body", "").strip()
    media_url = form.get("MediaUrl0")
    

    resp = MessagingResponse()
    msg = body.lower().strip()
    print("📩 MESSAGE RECEIVED:", msg)

    print("USER:", user)
    print("BODY:", body)
    print("MEDIA:", media_url)

    auto_archive_if_needed(user)

    pending = get_pending_expense(user)

    # =========================
    # CONFIRMATION FLOW
    # =========================
    if pending:
        if msg == "yes":
            save_to_sheet(pending["amount"], pending["category"], user, pending.get("raw_text"))

            alert = check_category_budget(user, pending["category"])
            anomaly = detect_spending_anomaly(user)
            delete_pending_expense(user)

            message = "✅ Expense saved successfully."

            if alert:
                message += f"\n\n{alert}"

            if anomaly:
                message += f"\n\n{anomaly}"

            resp.message(message)
            return twiml(resp)

        if msg == "no":
            delete_pending_expense(user)
            resp.message("❌ Expense cancelled.")
            return twiml(resp)

        if msg.startswith("correct") or msg.startswith("update"):
            try:
                amount, category, error = parse_correction(body, user)

                if error:
                    resp.message(error)
                    return twiml(resp)

                save_to_sheet(amount, category, user, pending.get("raw_text"))

                alert = check_category_budget(user, category)
                anomaly = detect_spending_anomaly(user)
                delete_pending_expense(user)

                message = (
                    f"✅ Corrected and saved:\n\n"
                    f"Amount: ₹{int(amount)}\n"
                    f"Category: {category}"
                )

                if alert:
                    message += f"\n\n{alert}"

                if anomaly:
                    message += f"\n\n{anomaly}"

                resp.message(message)
                return twiml(resp)

            except Exception as e:
                print("❌ CORRECTION ERROR:", str(e))
                resp.message(f"❌ Correction error: {str(e)}")
                return twiml(resp)

        resp.message(
            "⚠️ Please reply:\n"
            "yes = save\n"
            "no = cancel\n"
            "correct 300 Food = update and save"
        )
        return twiml(resp)

    # =========================
    # AI ADVISOR / RAG
    # =========================
    if msg.startswith("ask"):
        question = body[3:].strip()

        if not question:
            resp.message("Usage: ask where am I overspending?")
            return twiml(resp)

        answer = ask_finance_advisor(user, question)
        resp.message(answer)
        return twiml(resp)

    # =========================
    # LEARNING
    # =========================
    if msg.startswith("learn"):
        parts = msg.split()

        if len(parts) >= 3:
            keyword = parts[1]
            category = "_".join(parts[2:]).title().replace(" ", "_")

            save_learning(user, keyword, category)
            resp.message(f"✅ Learned: {keyword} → {category}")
        else:
            resp.message("Usage: learn <keyword> <category>")

        return twiml(resp)

    # =========================
    # AUDIO FLOW
    # =========================
    if media_url:
        try:
            audio_file = download_audio(media_url)
            text = speech_to_text(audio_file)

            print("📝 Transcription:", text)

            if not text:
                resp.message("❌ Could not understand audio. Please try again.")
                return twiml(resp)

            # =========================
            # SAFE EXTRACTION
            # =========================
            try:
                amount, category = extract_expense(text, user)
            except Exception as e:
                print("❌ EXTRACT ERROR:", str(e))
                amount, category = extract_expense(text, user)

            # fallback if amount is 0
            if not amount or amount == 0:
                fallback_amount, fallback_category = extract_expense(text, user)
                amount = fallback_amount

                if not category or category == "Other":
                    category = fallback_category

            # always detect category again from keywords/learning
            detected_category = detect_category(text, user)
            if detected_category and detected_category != "Other":
                category = detected_category

            if not category:
                category = "Other"

            print("✅ FINAL AMOUNT:", amount)
            print("✅ FINAL CATEGORY:", category)

            # =========================
            # SAVE PENDING SAFELY
            # =========================
            try:
                save_pending_expense(user, amount, category, text)
            except Exception as e:
                print("❌ PENDING SAVE ERROR:", str(e))
                resp.message(f"❌ Could not save pending expense: {str(e)}")
                return twiml(resp)

            resp.message(
                f"📝 Please confirm:\n\n"
                f"Amount: ₹{amount}\n"
                f"Category: {category}\n\n"
                f"Reply:\n"
                f"yes = save\n"
                f"no = cancel\n"
                f"correct 500 Food = update and save"
            )
            return twiml(resp)

        except Exception as e:
            print("❌ AUDIO FLOW ERROR:", str(e))
            resp.message(f"❌ Error processing audio: {str(e)}")
            return twiml(resp)

    if msg.startswith("debt add"):
        parts = body.split()

        if len(parts) >= 4:
            debt_name = parts[2]
            amount = float(parts[3])
            result = add_debt(user, debt_name, amount)
            resp.message(result)
        else:
            resp.message("Usage: debt add Muthoot 50000")

        return twiml(resp)


    if msg.startswith("emi"):
        parts = body.split()

        if len(parts) >= 3:
            debt_name = parts[1]
            amount = float(parts[2])
            result = pay_debt(user, debt_name, amount)
            resp.message(result)
        else:
            resp.message("Usage: emi muthoot 3000")

        return twiml(resp)


    if msg == "debt":
        result = get_debt_summary(user)
        resp.message(result)
        return twiml(resp)    

    # =========================
    # COMMANDS
    # =========================
    if msg.startswith("salary"):
        parts = msg.split()

        if len(parts) >= 2 and parts[1].isdigit():
            result = set_salary(user, int(parts[1]))
            resp.message(result)
        else:
            resp.message("Usage: salary 50000")

        return twiml(resp)

    if msg.startswith("set budget"):
        parts = msg.split()

        if len(parts) >= 4:
            category = "_".join(parts[2:-1]).title().replace(" ", "_")
            amount = float(parts[-1])
            result = set_category_budget(user, category, amount)
            resp.message(result)
        else:
            resp.message("Usage: set budget Food 10000")

        return twiml(resp)

    if msg.startswith("addsalary"):
        parts = msg.split()

        if len(parts) >= 2 and parts[1].isdigit():
            result = add_salary(user, int(parts[1]))
            resp.message(result)
        else:
            resp.message("Usage: addsalary 5000")

        return twiml(resp)

    if msg == "balance":
        resp.message(get_balance_report(user))
        return twiml(resp)

    if msg == "summary":
        try:
            print("📊 SUMMARY BLOCK HIT")

            summary = get_monthly_summary(user)

            print("📊 SUMMARY RESULT:", summary)

            resp.message(summary)

            return twiml(resp)

        except Exception as e:
            print("❌ SUMMARY ERROR:", str(e))

            resp.message(f"❌ Summary error: {str(e)}")

            return twiml(resp)
        
    if msg == "weekly":
        resp.message(get_weekly_report(user))
        return twiml(resp)

    if msg == "insights":
        summary = get_monthly_summary(user)
        compare = compare_months(user)
        resp.message(f"{summary}\n\n{compare}")
        return twiml(resp)

    if msg == "dashboard":
        dashboard_url = os.getenv("DASHBOARD_URL")

        if dashboard_url:
            resp.message(f"📊 Open dashboard:\n{dashboard_url}")
        else:
            resp.message("⚠️ Dashboard URL not configured.")

        return twiml(resp)
        

    if msg.startswith("delete"):
        parts = msg.split()

        if len(parts) == 1:
            entries = get_last_entries(user)

            if not entries:
                resp.message("⚠️ No entries found")
                return twiml(resp)

            message = "🧾 Last Entries:\n\n"

            for i, (_, row) in enumerate(entries, start=1):
                date = row[0]
                amount = row[2]
                category = row[3]
                message += f"{i}. ₹{amount} - {category} ({date})\n"

            message += "\nReply: delete <number>"
            resp.message(message)
            return twiml(resp)

        if len(parts) == 2:
            try:
                result = delete_by_serial(user, int(parts[1]))
                resp.message(result)
            except Exception as e:
                print("❌ Delete error:", str(e))
                resp.message("⚠️ Invalid format. Use: delete 2")

            return twiml(resp)

    if msg.startswith("edit"):
        parts = msg.split()

        if len(parts) == 1:
            entries = get_last_entries(user)

            if not entries:
                resp.message("⚠️ No entries found")
                return twiml(resp)

            message = "✏️ Last Entries:\n\n"

            for i, (_, row) in enumerate(entries, start=1):
                date = row[0]
                amount = row[2]
                category = row[3]
                message += f"{i}. ₹{amount} - {category} ({date})\n"

            message += "\nReply:\nedit 1 amount 350\nedit 1 category Grocery"
            resp.message(message)
            return twiml(resp)

        if len(parts) >= 4:
            try:
                serial = int(parts[1])
                field = parts[2]
                new_value = " ".join(parts[3:])

                result = update_entry_by_serial(user, serial, field, new_value)
                resp.message(result)
            except Exception as e:
                print("❌ Edit error:", str(e))
                resp.message("⚠️ Invalid format. Use: edit 1 amount 350")

            return twiml(resp)

        resp.message("Usage:\nedit\nedit 1 amount 350\nedit 1 category Grocery")
        return twiml(resp)

    if msg.startswith("archive"):
        parts = msg.split()

        if len(parts) == 2:
            result = archive_by_month(user, parts[1])
        else:
            result = archive_previous_month(user)

        resp.message(result)
        return twiml(resp)

    if msg == "compare":
        resp.message(compare_months(user))
        return twiml(resp)
    

    # =========================
    # DEFAULT
    # =========================
    resp.message(
        "Send voice note 🎙️ or type:\n"
        "summary\n"
        "weekly\n"
        "balance\n"
        "dashboard\n"
        "ask where am I overspending?\n"
        "salary 50000\n"
        "addsalary 5000"
    )
    return twiml(resp)
    
if msg.startswith("move debt"):
    parts = msg.split()

    if len(parts) >= 4:
        expense_id = int(parts[2])
        debt_name = parts[3]
        result = migrate_expense_to_debt(user, expense_id, debt_name)
        resp.message(result)
    else:
        resp.message("Usage: move debt <expense_id> <debt_name>")

    return twiml(resp)


@app.get("/send-daily-summary")
def send_daily_summary():
    users = supabase.table("expenses").select("user_phone").execute()

    if not users.data:
        return {"status": "no users"}

    unique_users = set(row["user_phone"] for row in users.data)

    from twilio.rest import Client

    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )

    from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    for user in unique_users:
        summary = get_monthly_summary(user)

        client.messages.create(
            body=f"📊 Daily Update:\n\n{summary}",
            from_=from_number,
            to=f"whatsapp:+{user}"
        )

    return {"status": "sent"}