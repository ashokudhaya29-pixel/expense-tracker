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
    response = "📊 Monthly Summary\n\n"
    response += f"💰 Total: ₹{int(total)}\n\n"

    for cat, amt in category_totals.items():
        percent = (amt / total) * 100 if total > 0 else 0
        response += f"{cat}: ₹{int(amt)} ({percent:.0f}%)\n"

    # Insight
    if category_totals:
        top_category = max(category_totals, key=category_totals.get)
        response += f"\n🔥 You spend most on {top_category}"

    return response