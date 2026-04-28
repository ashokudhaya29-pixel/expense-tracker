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

from datetime import datetime, timedelta

def set_salary(user, salary):
    gc = get_client()
    sheet = gc.open("Expense Tracker").worksheet("Budgets")

    month = datetime.now().strftime("%Y-%m")

    data = sheet.get_all_values()

    # Check if user already has salary for this month
    for i in range(1, len(data)):
        row_user = data[i][0]
        row_month = data[i][1]

        if row_user == user and row_month == month:
            sheet.update_cell(i + 1, 3, salary)
            return f"✅ Salary updated for {month}: ₹{salary}"

    sheet.append_row([user, month, salary])
    return f"✅ Salary saved for {month}: ₹{salary}"


def get_salary(user):
    gc = get_client()
    sheet = gc.open("Expense Tracker").worksheet("Budgets")

    month = datetime.now().strftime("%Y-%m")
    data = sheet.get_all_records()

    for row in data:
        if row["User"] == user and row["Month"] == month:
            return float(row["Salary"])

    return 0


def get_month_expense(user):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    data = sheet.get_all_records()
    current_month = datetime.now().strftime("%Y-%m")

    total = 0

    for row in data:
        if row["User"] != user:
            continue

        date = str(row["Date"])

        if date.startswith(current_month):
            total += float(row["Amount"])

    return total


def get_balance_report(user):
    salary = get_salary(user)
    spent = get_month_expense(user)
    balance = salary - spent

    if salary == 0:
        return "⚠️ Salary not set. Send: salary 50000"

    message = "💰 Balance Report\n\n"
    message += f"Salary: ₹{int(salary)}\n"
    message += f"Spent: ₹{int(spent)}\n"
    message += f"Remaining: ₹{int(balance)}\n"

    percent = (spent / salary) * 100 if salary > 0 else 0

    if percent >= 90:
        message += "\n🚨 Alert: You used more than 90% of your salary!"
    elif percent >= 75:
        message += "\n⚠️ Warning: You used more than 75% of your salary."
    elif percent >= 50:
        message += "\n💡 Note: You used more than 50% of your salary."
    else:
        message += "\n✅ Spending is under control."

    return message


def get_weekly_report(user):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    data = sheet.get_all_records()

    today = datetime.now()
    week_start = today - timedelta(days=7)

    total = 0
    category_totals = {}

    for row in data:
        if row["User"] != user:
            continue

        date_text = str(row["Date"]).split()[0]

        try:
            expense_date = datetime.strptime(date_text, "%Y-%m-%d")
        except:
            continue

        if expense_date >= week_start:
            amount = float(row["Amount"])
            category = row["Category"]

            total += amount
            category_totals[category] = category_totals.get(category, 0) + amount

    message = "📅 Weekly Report\n\n"
    message += f"Total spent this week: ₹{int(total)}\n\n"

    for cat, amt in category_totals.items():
        percent = (amt / total) * 100 if total > 0 else 0
        message += f"{cat}: ₹{int(amt)} ({percent:.0f}%)\n"

    if total == 0:
        message += "No expenses recorded this week."

    return message

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

def update_entry_by_serial(user, serial, field, new_value):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    entries = get_last_entries(user)

    if serial < 1 or serial > len(entries):
        return "⚠️ Invalid selection"

    row_number = entries[serial - 1][0]

    field = field.lower()

    # Sheet columns:
    # A Date | B User | C Amount | D Category
    if field == "amount":
        sheet.update_cell(row_number, 3, new_value)
        return f"✅ Updated entry #{serial} amount to ₹{new_value}"

    elif field == "category":
        sheet.update_cell(row_number, 4, new_value.capitalize())
        return f"✅ Updated entry #{serial} category to {new_value.capitalize()}"

    else:
        return "⚠️ Use: edit <number> amount <value> OR edit <number> category <value>"

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

