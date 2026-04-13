import gspread
from oauth2client.service_account import ServiceAccountCredentials

def save_to_sheet(amount, category):

    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("Expense Tracker").sheet1

    sheet.append_row([amount, category])

    print("Saved to Google Sheet")


def get_monthly_summary():
    from datetime import datetime

    # connect sheet
    gc = gspread.service_account(filename="credentials.json")
    sheet = gc.open("Expense Tracker").sheet1

    data = sheet.get_all_records()

    total = 0
    category_map = {}

    for row in data:
        amount = float(row["amount"])
        category = row["category"]

        total += amount

        if category in category_map:
            category_map[category] += amount
        else:
            category_map[category] = amount

    result = f"📊 Monthly Summary\n\nTotal Spend: ₹{total}\n\nBy Category:\n"

    for k, v in category_map.items():
        result += f"- {k}: ₹{v}\n"

    return result