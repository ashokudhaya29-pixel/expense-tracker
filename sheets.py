import gspread
import json
import os
from google.oauth2.service_account import Credentials

# ✅ Central client (no credentials.json file)
def get_client():
    creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ],
    )

    return gspread.authorize(creds)

def get_learned_categories(user):
    gc = get_client()
    sheet = gc.open("Expense Tracker").worksheet("Learning")

    data = sheet.get_all_records()

    learned = {}

    for row in data:
        if row["User"] == user:
            learned[row["Keyword"].lower()] = row["Category"]

    return learned


def save_learning(user, keyword, category):
    gc = get_client()
    sheet = gc.open("Expense Tracker").worksheet("Learning")

    sheet.append_row([user, keyword.lower(), category])

# ✅ Save expense
def save_to_sheet(amount, category, user):
    gc = get_client()
    sh = gc.open("Expense Tracker").sheet1

    from datetime import datetime

    sh.append_row([
        str(datetime.now()),
        user,
        amount,
        category
    ])

def get_last_entries(user, limit=10):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    data = sheet.get_all_values()

    user_rows = []
    
    # Skip header
    for i in range(1, len(data)):
        if data[i][0] == user:
            user_rows.append((i+1, data[i]))  # (row_number, row_data)

    last_entries = user_rows[-limit:]

    return last_entries

def delete_by_serial(user, serial):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    entries = get_last_entries(user)

    if serial < 1 or serial > len(entries):
        return "⚠️ Invalid selection"

    row_number = entries[serial - 1][0]

    sheet.delete_rows(row_number)

    return f"✅ Deleted entry #{serial}"

# ✅ Monthly summary
def get_monthly_summary(user):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    data = sheet.get_all_records()

    total = 0
    category_totals = {}

    for row in data:
        if row["User"] != user:
            continue

        amount = float(row["Amount"])
        category = row["Category"]

        total += amount

        if category in category_totals:
            category_totals[category] += amount
        else:
            category_totals[category] = amount

    # Build response
    response = f"📊 Total Expense: ₹{total}\n\n"

    # Category breakdown
    top_category = None
    top_amount = 0

    for cat, amt in category_totals.items():
        percent = (amt / total * 100) if total > 0 else 0
        response += f"{cat}: ₹{amt} ({percent:.1f}%)\n"

        if amt > top_amount:
            top_amount = amt
            top_category = cat

    # =========================
    # 🔥 SMART INSIGHTS
    # =========================
    response += "\n💡 Insights:\n"

    if top_category:
        percent = (top_amount / total * 100) if total > 0 else 0
        response += f"• Highest spend: {top_category} ({percent:.0f}%)\n"

        if percent > 50:
            response += f"⚠️ You are spending a lot on {top_category}\n"

    if total == 0:
        response += "No expenses recorded yet."

    return response