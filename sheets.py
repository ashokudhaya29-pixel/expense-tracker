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
    sh = gc.open("Expense Tracker").sheet1

    data = sh.get_all_records()

    total = 0
    category_totals = {}

    for row in data:
        if row["User"] != user:
            continue

        amt = int(row["Amount"])
        cat = row["Category"]

        total += amt
        category_totals[cat] = category_totals.get(cat, 0) + amt

    result = f"📊 Your Monthly Summary\n\n💰 Total: ₹{total}\n\n"

    for cat, amt in category_totals.items():
        result += f"👉 {cat}: ₹{amt}\n"

    return result