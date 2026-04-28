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
    user = user.replace("whatsapp:", "").strip()

    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")

    sheet.append_row([date, user, amount, category])

def get_last_entries(user, limit=10):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    data = sheet.get_all_values()

    print("===== DEBUG START =====")
    print("INPUT USER:", user)
    print("TOTAL ROWS:", len(data))

    user_rows = []

    for i in range(1, len(data)):
        row = data[i]

        print(f"ROW {i}: {row}")   # 👈 PRINT FULL ROW

        # Try BOTH columns to be sure
        possible_user_1 = row[0]
        possible_user_2 = row[1]

        print("Check col0:", possible_user_1)
        print("Check col1:", possible_user_2)

        if user in possible_user_1 or user in possible_user_2:
            print("✅ MATCH FOUND")
            user_rows.append((i + 1, row))

    print("FINAL MATCHES:", user_rows)
    print("===== DEBUG END =====")

    return user_rows[-limit:]

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