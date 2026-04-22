import os
import json
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict


# =========================
# 🔐 AUTH (ENV BASED)
# =========================
def get_client():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")

    if not creds_json:
        raise Exception("❌ GOOGLE_CREDENTIALS not set in environment")

    creds_dict = json.loads(creds_json)

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    return gspread.authorize(creds)


# =========================
# 📥 SAVE EXPENSE
# =========================
def save_to_sheet(amount, category):
    gc = get_client()   # ✅ USE HERE

    sheet = gc.open("Expense Tracker").sheet1

    sheet.append_row([amount, category])

    print("✅ Saved to Google Sheet")


# =========================
# 📊 MONTHLY SUMMARY
# =========================
def get_monthly_summary():
    gc = get_client()   # ✅ USE HERE

    sheet = gc.open("Expense Tracker").sheet1

    data = sheet.get_all_records()

    total = 0
    category_totals = defaultdict(int)

    for row in data:
        try:
            amount = int(row.get("Amount", 0))
        except:
            amount = 0

        category = row.get("Category", "Other")

        total += amount
        category_totals[category] += amount

    # Format response
    summary = f"📊 Monthly Summary\n\nTotal: ₹{total}\n\n"

    for cat, amt in category_totals.items():
        summary += f"{cat}: ₹{amt}\n"

    return summary