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
def save_to_sheet(amount, category):
    gc = get_client()

    sh = gc.open("Expense Tracker")
    ws = sh.sheet1

    ws.append_row([amount, category])


# ✅ Monthly summary
def get_monthly_summary():
    gc = get_client()

    sh = gc.open("Expense Tracker")
    ws = sh.sheet1

    data = ws.get_all_records()

    total = 0
    category_totals = {}

    for row in data:
        amount = row.get("Amount") or row.get("amount")
        category = row.get("Category") or row.get("category") or "Other"

        try:
            amount = int(amount)
        except:
            continue

        # Total
        total += amount

        # Category-wise
        if category in category_totals:
            category_totals[category] += amount
        else:
            category_totals[category] = amount

    # 🧾 Build response
    summary = "📊 Monthly Summary\n\n"
    summary += f"💰 Total: ₹{total}\n\n"
    summary += "\n📂 Category Breakdown:\n"
    for cat, amt in category_totals.items():
        summary += f"👉 {cat}: ₹{amt}\n"

    return summary