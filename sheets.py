import os
import json
import gspread
from datetime import datetime, timezone, timedelta
from google.oauth2.service_account import Credentials


def get_client():
    creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    return gspread.authorize(creds)


def clean_user(user):
    return str(user).replace("whatsapp:", "").replace("+", "").strip()


def current_month_ist():
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m")


def current_date_ist():
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")


# =========================
# Learning
# =========================
def get_learned_categories(user):
    gc = get_client()
    sheet = gc.open("Expense Tracker").worksheet("Learning")

    user = clean_user(user)
    data = sheet.get_all_records()

    learned = {}

    for row in data:
        row_user = clean_user(row.get("User", ""))

        if row_user == user:
            learned[str(row.get("Keyword", "")).lower()] = row.get("Category", "Other")

    return learned


def save_learning(user, keyword, category):
    gc = get_client()
    sheet = gc.open("Expense Tracker").worksheet("Learning")

    user = clean_user(user)
    sheet.append_row([user, keyword.lower(), category.capitalize()])


# =========================
# Salary / Budget
# =========================
def set_salary(user, amount):
    gc = get_client()
    sheet = gc.open("Expense Tracker").worksheet("Budgets")

    user = clean_user(user)
    month = current_month_ist()

    data = sheet.get_all_values()

    for i in range(len(data)-1,0,-1):
        row_user = clean_user(data[i][0])
        row_month = data[i][1]
        row_type = data[i][2]
    

        if row_user == user and row_month == month and row_type == "base":
            sheet.delete_rows(i + 1)

    sheet.append_row([user, month,"base", amount])
    return f"✅ Base saved for {month}: ₹{amount}"

def add_salary(user, amount):
    gc = get_client()
    sheet = gc.open("Expense Tracker").worksheet("Budgets")

    user
    month= current_month_ist()

    sheet.append_row([user, month, "extra", amount])
    return f"✅ Added ₹{amount} to salary for {month}"


def get_salary(user):
    gc = get_client()
    sheet = gc.open("Expense Tracker").worksheet("Budgets")

    user = clean_user(user)
    month = current_month_ist()

    data = sheet.get_all_records()

    total = 0

    print("🔍 GET SALARY USER:", user)
    print("🔍 GET SALARY MONTH:", month)
    print("🔍 BUDGET DATA:", data)

    for row in data:
        row_user = clean_user(row.get("User", ""))
        row_month = str(row.get("Month", "")).strip()

        print("CHECK:", row_user, row_month)

        if row_user == user and row_month == month:
            try:
                total += float(row.get("Amount", 0))
            except:
                pass
            print("✅ SALARY FOUND:", row.get("amount", 0))
            return float(row.get("Salary", 0))

    print("❌ SALARY NOT FOUND")
    return total

def get_month_expense(user):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    user = clean_user(user)
    month = current_month_ist()
    data = sheet.get_all_records()

    total = 0

    for row in data:
        row_user = clean_user(row.get("User", ""))

        if row_user != user:
            continue

        date_text = str(row.get("Date", ""))

        if date_text.startswith(month):
            try:
                total += float(row.get("Amount", 0))
            except:
                pass

    return total


def get_balance_report(user):
    Amount = get_salary(user)
    spent = get_month_expense(user)
    balance = Amount - spent

    if Amount == 0:
        return "⚠️ Salary not set. Send: salary 50000"

    message = "💰 Balance Report\n\n"
    message += f"Salary: ₹{int(Amount)}\n"
    message += f"Spent: ₹{int(spent)}\n"
    message += f"Remaining: ₹{int(balance)}\n"

    percent = (spent / Amount) * 100 if Amount > 0 else 0

    if percent >= 90:
        message += "\n🚨 Alert: You used more than 90% of your salary!"
    elif percent >= 75:
        message += "\n⚠️ Warning: You used more than 75% of your salary."
    elif percent >= 50:
        message += "\n💡 Note: You used more than 50% of your salary."
    else:
        message += "\n✅ Spending is under control."

    return message


# =========================
# Expense Save / Summary
# =========================
def save_to_sheet(amount, category, user):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    user = clean_user(user)
    date = current_date_ist()

    sheet.append_row([date, user, amount, category])


def get_monthly_summary(user):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    user = clean_user(user)
    data = sheet.get_all_records()

    total = 0
    category_totals = {}

    for row in data:
        row_user = clean_user(row.get("User", ""))

        if row_user != user:
            continue

        try:
            amount = float(row.get("Amount", 0))
        except:
            amount = 0

        category = row.get("Category", "Other")

        total += amount
        category_totals[category] = category_totals.get(category, 0) + amount

    response = f"📊 Total Expense: ₹{int(total)}\n\n"

    top_category = None
    top_amount = 0

    for cat, amt in category_totals.items():
        percent = (amt / total * 100) if total > 0 else 0
        response += f"{cat}: ₹{int(amt)} ({percent:.1f}%)\n"

        if amt > top_amount:
            top_amount = amt
            top_category = cat

    response += "\n💡 Insights:\n"

    if top_category:
        percent = (top_amount / total * 100) if total > 0 else 0
        response += f"• Highest spend: {top_category} ({percent:.0f}%)\n"

        if percent > 50:
            response += f"⚠️ You are spending a lot on {top_category}\n"

    if total == 0:
        response += "No expenses recorded yet."

    return response


# =========================
# Weekly Report
# =========================
def get_weekly_report(user):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    user = clean_user(user)
    data = sheet.get_all_records()

    ist = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(ist)
    week_start = today - timedelta(days=7)

    total = 0
    category_totals = {}

    for row in data:
        row_user = clean_user(row.get("User", ""))

        if row_user != user:
            continue

        date_text = str(row.get("Date", "")).split()[0]

        try:
            expense_date = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=ist)
        except:
            continue

        if expense_date >= week_start:
            try:
                amount = float(row.get("Amount", 0))
            except:
                amount = 0

            category = row.get("Category", "Other")

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


# =========================
# Delete / Edit
# =========================
def get_last_entries(user, limit=10):
    gc = get_client()
    sheet = gc.open("Expense Tracker").sheet1

    user = clean_user(user)
    data = sheet.get_all_values()

    user_rows = []

    for i in range(1, len(data)):
        row = data[i]

        if len(row) < 4:
            continue

        row_user = clean_user(row[1])

        if row_user == user:
            user_rows.append((i + 1, row))

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

    if field == "amount":
        sheet.update_cell(row_number, 3, new_value)
        return f"✅ Updated entry #{serial} amount to ₹{new_value}"

    if field == "category":
        sheet.update_cell(row_number, 4, new_value.capitalize())
        return f"✅ Updated entry #{serial} category to {new_value.capitalize()}"

    return "⚠️ Use: edit <number> amount <value> OR edit <number> category <value>"