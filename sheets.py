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

    total = sum(int(row["Amount"]) for row in data if row["Amount"])

    return f"📊 Monthly Total: ₹{total}"