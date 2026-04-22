import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials  

def save_to_sheet(amount, category):

    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]

    creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open("Expense Tracker").sheet1

    sheet.append_row([amount, category])

    print("Saved to Google Sheet")


def get_monthly_summary():
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from collections import defaultdict

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("Expense Tracker").sheet1

    data = sheet.get_all_records()

    total = 0
    category_totals = defaultdict(int)

    for row in data:
        amount = int(row.get("Amount", 0))
        category = row.get("Category", "Other")

        total += amount
        category_totals[category] += amount

    # Build response
    summary = f"📊 Monthly Summary\n\nTotal: ₹{total}\n\n"

    for cat, amt in category_totals.items():
        summary += f"{cat}: ₹{amt}\n"

    return summary