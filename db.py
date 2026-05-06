import os
import calendar
from datetime import datetime, timezone, timedelta
from supabase import create_client
from datetime import timezone, timedelta

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def clean_user(user):
    return str(user).replace("whatsapp:", "").replace("+", "").strip()


def current_date_ist():
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")


def last_working_day(year, month):
    last_day = calendar.monthrange(year, month)[1]
    dt = datetime(year, month, last_day)

    if dt.weekday() == 6:
        dt = dt - timedelta(days=2)
    elif dt.weekday() == 5:
        dt = dt - timedelta(days=1)

    return dt.date()

def set_category_budget(user, category, amount):
    user = clean_user(user)
    month = current_month_ist()
    category = category.capitalize()

    supabase.table("category_budgets") \
        .delete() \
        .eq("user_phone", user) \
        .eq("month", month) \
        .eq("category", category) \
        .execute()

    supabase.table("category_budgets").insert({
        "user_phone": user,
        "month": month,
        "category": category,
        "limit_amount": amount
    }).execute()

    return f"✅ Budget set: {category} ₹{amount}"

def check_category_budget(user, category):
    user = clean_user(user)
    month = current_month_ist()
    category = category.capitalize()
    print("🔔 CHECK BUDGET USER:", user)    
    print("🔔 CHECK BUDGET MONTH:", month)
    print("🔔 CHECK BUDGET CATEGORY:", category)

    budget_res = supabase.table("category_budgets") \
        .select("*") \
        .eq("user_phone", user) \
        .eq("month", month) \
        .eq("category", category) \
        .execute()
    print("🔔 BUDGET DATA:", budget_res.data)

    if not budget_res.data:
        return None

    limit_amount = float(budget_res.data[0]["limit_amount"])

    expense_res = supabase.table("expenses") \
        .select("*") \
        .eq("user_phone", user) \
        .eq("cycle_month", month) \
        .eq("category", category) \
        .eq("is_archived", False) \
        .execute()
    print("🔔 EXPENSE DATA:", expense_res.data)

    spent = sum(float(r["amount"]) for r in expense_res.data)

    percent = (spent / limit_amount) * 100 if limit_amount > 0 else 0

    if percent >= 100:
        return f"🚨 {category} budget exceeded! ₹{int(spent)} / ₹{int(limit_amount)}"

    elif percent >= 80:
        return f"⚠️ {category} budget {int(percent)}% used (₹{int(spent)} / ₹{int(limit_amount)})"

    return None

def get_salary_cycle():
    ist = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(ist).date()

    year = today.year
    month = today.month

    current_salary_day = last_working_day(year, month)

    if today >= current_salary_day:
        cycle_month = today.strftime("%Y-%m")
        cycle_start = current_salary_day

        if month == 12:
            next_salary_day = last_working_day(year + 1, 1)
        else:
            next_salary_day = last_working_day(year, month + 1)

        cycle_end = next_salary_day - timedelta(days=1)

    else:
        cycle_month = today.strftime("%Y-%m")

        if month == 1:
            prev_salary_day = last_working_day(year - 1, 12)
        else:
            prev_salary_day = last_working_day(year, month - 1)

        cycle_start = prev_salary_day
        cycle_end = current_salary_day - timedelta(days=1)

    print("📅 TODAY:", today)
    print("📅 CYCLE MONTH:", cycle_month)
    print("📅 CYCLE START:", cycle_start)
    print("📅 CYCLE END:", cycle_end)

    return cycle_month, cycle_start, cycle_end

def current_month_ist():
    cycle_month, _, _ = get_salary_cycle()
    return cycle_month


# =========================
# Learning
# =========================
def get_learned_categories(user):
    user = clean_user(user)

    res = (
        supabase.table("learning")
        .select("*")
        .eq("user_phone", user)
        .execute()
    )

    learned = {}

    for row in res.data:
        learned[str(row.get("keyword", "")).lower()] = row.get("category", "Other")

    return learned


def save_learning(user, keyword, category):
    user = clean_user(user)

    supabase.table("learning").insert({
        "user_phone": user,
        "keyword": keyword.lower(),
        "category": category.capitalize()
    }).execute()


# =========================
# Salary / Budget
# =========================
def set_salary(user, salary):
    user = clean_user(user)
    month = current_month_ist()

    supabase.table("budgets") \
        .delete() \
        .eq("user_phone", user) \
        .eq("month", month) \
        .eq("type", "base") \
        .execute()

    supabase.table("budgets").insert({
        "user_phone": user,
        "month": month,
        "type": "base",
        "salary": salary
    }).execute()

    return f"✅ Base saved for {month}: ₹{salary}"


def add_salary(user, salary):
    user = clean_user(user)
    month = current_month_ist()

    supabase.table("budgets").insert({
        "user_phone": user,
        "month": month,
        "type": "extra",
        "salary": salary
    }).execute()

    return f"✅ Added ₹{salary} to salary for {month}"


def get_salary(user):
    user = clean_user(user)
    month = current_month_ist()

    res = (
        supabase.table("budgets")
        .select("*")
        .eq("user_phone", user)
        .eq("month", month)
        .execute()
    )

    total = 0

    print("🔍 GET SALARY USER:", user)
    print("🔍 GET SALARY MONTH:", month)
    print("🔍 BUDGET DATA:", res.data)

    for row in res.data:
        try:
            total += float(row.get("salary", 0))
        except:
            pass

    print("✅ TOTAL SALARY:", total)
    return total


def get_month_expense(user):
    user = clean_user(user)
    cycle_month, _, _ = get_salary_cycle()

    res = (
        supabase.table("expenses")
        .select("*")
        .eq("user_phone", user)
        .eq("cycle_month", cycle_month)
        .eq("is_archived", False)
        .execute()
    )

    total = 0

    for row in res.data:
        try:
            total += float(row.get("amount", 0))
        except:
            pass

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


# =========================
# Expense Save / Summary
# =========================
def save_to_sheet(amount, category, user, raw_text=None):
    user = clean_user(user)
    cycle_month = current_month_ist()
    print("✅ SAVING EXPENSE")
    print("DATE:", current_date_ist())
    print("CYCLE MONTH:", cycle_month)

    supabase.table("expenses").insert({
        "user_phone": user,
        "expense_date": current_date_ist(),
        "amount": amount,
        "category": category,
        "raw_text": raw_text,
        "cycle_month": cycle_month,
        "is_archived": False
    }).execute()


def get_monthly_summary(user):
    user = clean_user(user)
    cycle_month = current_month_ist()

    res = (
        supabase.table("expenses")
        .select("*")
        .eq("user_phone", user)
        .eq("cycle_month", cycle_month)
        .eq("is_archived", False)
        .execute()
    )

    total = 0
    category_totals = {}

    for row in res.data:
        try:
            amount = float(row.get("amount", 0))
        except:
            amount = 0

        category = row.get("category", "Other")

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

        # =========================
    # AI INSIGHTS
    # =========================
    response += "\n💡 AI Insights:\n"

    if total == 0:
        response += "No expenses yet."
        return response

    # highest category
    top_category = max(category_totals, key=category_totals.get)
    top_amount = category_totals[top_category]
    top_percent = (top_amount / total) * 100

    response += f"• Highest spend: {top_category} ({int(top_percent)}%)\n"

    # budget warning
    budget_res = supabase.table("category_budgets") \
        .select("*") \
        .eq("user_phone", user) \
        .eq("month", cycle_month) \
        .execute()

    for b in budget_res.data:
        cat = b["category"]
        limit_amt = float(b["limit_amount"])

        if cat in category_totals:
            spent_amt = category_totals[cat]
            percent = (spent_amt / limit_amt) * 100 if limit_amt > 0 else 0

            if percent >= 80:
                response += f"• ⚠️ {cat} budget almost used ({int(percent)}%)\n"

    # suggestion logic
    if top_category == "Food":
        response += "• Suggestion: Reduce hotel/Swiggy expenses by ₹500/week\n"
    elif top_category == "Shopping":
        response += "• Suggestion: Avoid unnecessary online purchases\n"
    elif top_category == "Travel":
        response += "• Suggestion: Try cost-effective transport options\n"
    else:
        response += "• Keep tracking your expenses consistently 👍\n"
    return response


# =========================
# Weekly Report
# =========================
def get_weekly_report(user):
    user = clean_user(user)

    res = (
        supabase.table("expenses")
        .select("*")
        .eq("user_phone", user)
        .eq("is_archived", False)
        .execute()
    )

    ist = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(ist)
    week_start = today - timedelta(days=7)

    total = 0
    category_totals = {}

    for row in res.data:
        date_text = str(row.get("expense_date", "")).split()[0]

        try:
            expense_date = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=ist)
        except:
            continue

        if expense_date >= week_start:
            try:
                amount = float(row.get("amount", 0))
            except:
                amount = 0

            category = row.get("category", "Other")

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
    user = clean_user(user)

    res = (
        supabase.table("expenses")
        .select("*")
        .eq("user_phone", user)
        .eq("is_archived", False)
        .order("id", desc=True)
        .limit(limit)
        .execute()
    )

    rows = []

    for row in reversed(res.data):
        display_row = [
            row.get("expense_date"),
            row.get("user_phone"),
            row.get("amount"),
            row.get("category")
        ]
        rows.append((row.get("id"), display_row))

    return rows


def delete_by_serial(user, serial):
    entries = get_last_entries(user)

    if serial < 1 or serial > len(entries):
        return "⚠️ Invalid selection"

    expense_id = entries[serial - 1][0]

    supabase.table("expenses").delete().eq("id", expense_id).execute()

    return f"✅ Deleted entry #{serial}"


def update_entry_by_serial(user, serial, field, new_value):
    entries = get_last_entries(user)

    if serial < 1 or serial > len(entries):
        return "⚠️ Invalid selection"

    expense_id = entries[serial - 1][0]
    field = field.lower()

    if field in ["amount", "salary"]:
        supabase.table("expenses").update({
            "amount": float(new_value)
        }).eq("id", expense_id).execute()

        return f"✅ Updated entry #{serial} amount to ₹{new_value}"

    if field == "category":
        supabase.table("expenses").update({
            "category": new_value.capitalize()
        }).eq("id", expense_id).execute()

        return f"✅ Updated entry #{serial} category to {new_value.capitalize()}"

    return "⚠️ Use: edit <number> amount <value> OR edit <number> category <value>"


# =========================
# Archive / Compare
# =========================
def archive_previous_month(user):
    user = clean_user(user)
    cycle_month, cycle_start, _ = get_salary_cycle()

    res = (
        supabase.table("expenses")
        .select("*")
        .eq("user_phone", user)
        .eq("is_archived", False)
        .execute()
    )

    moved_count = 0

    for row in res.data:
        date_text = str(row.get("expense_date", "")).split()[0]

        try:
            expense_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        except:
            continue

        if expense_date < cycle_start:
            old_cycle = date_text[:7]

            supabase.table("expenses").update({
                "is_archived": True,
                "archived_at": current_date_ist(),
                "cycle_month": old_cycle
            }).eq("id", row["id"]).execute()

            moved_count += 1

    return f"✅ Archived {moved_count} old expense records."


def archive_by_month(user, month):
    user = clean_user(user)

    res = (
        supabase.table("expenses")
        .select("*")
        .eq("user_phone", user)
        .eq("is_archived", False)
        .execute()
    )

    moved_count = 0

    for row in res.data:
        date_text = str(row.get("expense_date", "")).split()[0]

        if date_text.startswith(month):
            supabase.table("expenses").update({
                "is_archived": True,
                "archived_at": current_date_ist(),
                "cycle_month": month
            }).eq("id", row["id"]).execute()

            moved_count += 1

    return f"✅ Archived {moved_count} records for {month}."

def compare_months(user):
    user = clean_user(user)
    current_cycle = current_month_ist()

    current_res = (
        supabase.table("expenses")
        .select("*")
        .eq("user_phone", user)
        .eq("cycle_month", current_cycle)
        .eq("is_archived", False)
        .execute()
    )

    archived_res = (
        supabase.table("expenses")
        .select("*")
        .eq("user_phone", user)
        .eq("is_archived", True)
        .execute()
    )

    current_total = 0
    current_categories = {}

    for row in current_res.data:
        amount = float(row.get("amount", 0))
        category = row.get("category", "Other")

        current_total += amount
        current_categories[category] = current_categories.get(category, 0) + amount

    previous_month = None

    for row in archived_res.data:
        row_cycle = str(row.get("cycle_month", "")).strip()

        if row_cycle and (not previous_month or row_cycle > previous_month):
            previous_month = row_cycle

    previous_total = 0
    previous_categories = {}

    if previous_month:
        for row in archived_res.data:
            if str(row.get("cycle_month", "")).strip() == previous_month:
                amount = float(row.get("amount", 0))
                category = row.get("category", "Other")

                previous_total += amount
                previous_categories[category] = previous_categories.get(category, 0) + amount

    difference = current_total - previous_total

    message = "📊 Month Comparison\n\n"
    message += f"Current Cycle ({current_cycle}): ₹{int(current_total)}\n"

    if not previous_month:
        message += "No previous month records found."
        return message

    message += f"Previous Month ({previous_month}): ₹{int(previous_total)}\n"
    message += f"Difference: ₹{int(difference)}\n\n"

    if difference > 0:
        message += "⚠️ Overall spending increased.\n"
    elif difference < 0:
        message += "✅ Overall spending reduced.\n"
    else:
        message += "➖ Overall spending is same.\n"

    message += "\n📌 Category Changes:\n"

    all_categories = set(current_categories.keys()) | set(previous_categories.keys())

    for cat in all_categories:
        current_amt = current_categories.get(cat, 0)
        previous_amt = previous_categories.get(cat, 0)
        diff = current_amt - previous_amt

        if diff > 0:
            message += f"• {cat}: increased by ₹{int(diff)}\n"
        elif diff < 0:
            message += f"• {cat}: reduced by ₹{abs(int(diff))}\n"
        else:
            message += f"• {cat}: no change\n"

    message += "\n💡 Advice:\n"

    if difference > 0:
        message += "Try reducing the category with highest increase this month."
    elif difference < 0:
        message += "Good progress. Continue the same spending control."
    else:
        message += "Your spending pattern is stable."

    return message

def auto_archive_if_needed(user):
    user = clean_user(user)

    current_cycle = current_month_ist()

    res = supabase.table("user_meta").select("*").eq("user_phone", user).execute()

    if res.data:
        last_cycle = res.data[0].get("last_cycle")

        if last_cycle != current_cycle:
            print("🔄 New cycle detected → Archiving")

            archive_previous_month(user)

            supabase.table("user_meta").update({
                "last_cycle": current_cycle
            }).eq("user_phone", user).execute()

    else:
        # first time user
        supabase.table("user_meta").insert({
            "user_phone": user,
            "last_cycle": current_cycle
        }).execute()

# =========================
# PENDING EXPENSE (DB)
# =========================
def save_pending_expense(user, amount, category, raw_text=None):
    user = clean_user(user)

    supabase.table("pending_expenses") \
        .delete() \
        .eq("user_phone", user) \
        .execute()

    supabase.table("pending_expenses").insert({
        "user_phone": user,
        "amount": amount,
        "category": category,
        "raw_text": raw_text
    }).execute()


def get_pending_expense(user):
    user = clean_user(user)

    res = supabase.table("pending_expenses") \
        .select("*") \
        .eq("user_phone", user) \
        .execute()

    return res.data[0] if res.data else None


def delete_pending_expense(user):
    user = clean_user(user)

    supabase.table("pending_expenses") \
        .delete() \
        .eq("user_phone", user) \
        .execute()
    
def detect_spending_anomaly(user):
    user = clean_user(user)

    res = supabase.table("expenses") \
        .select("*") \
        .eq("user_phone", user) \
        .eq("is_archived", False) \
        .execute()

    ist = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(ist).date()
    daily_totals = {}

    for row in res.data:
        date_text = str(row.get("expense_date", "")).split()[0]

        try:
            d = datetime.strptime(date_text, "%Y-%m-%d").date()
        except:
            continue

        daily_totals[d] = daily_totals.get(d, 0) + float(row.get("amount", 0))
    print("📊 DAILY TOTALS:", daily_totals)

    if not daily_totals:
        return None

    today_spent = daily_totals.get(today, 0)
    print("📊 TODAY SPENT:", today_spent)

    # average of last 7 days (excluding today)
    past_days = [
        amt for d, amt in daily_totals.items()
        if d != today and (today - d).days <= 7
    ]
    print("📊 PAST DAYS:", past_days)

    if not past_days:
        return None

    avg = sum(past_days) / len(past_days)
    print("📊 AVG:", avg if past_days else 0)

    if avg == 0:
        return None
        

    ratio = today_spent / avg
    print("📊 RATIO:", ratio)

    if ratio >= 1.5:
        return (
            f"⚠️ High spending detected today!\n\n"
            f"Today: ₹{int(today_spent)}\n"
            f"Average: ₹{int(avg)}\n"
            f"🚨 {int(ratio)}x higher than usual"
        )

    return None     

def get_expense_context(user):
    user = clean_user(user)
    cycle_month = current_month_ist()

    expenses_res = (
        supabase.table("expenses")
        .select("*")
        .eq("user_phone", user)
        .eq("cycle_month", cycle_month)
        .eq("is_archived", False)
        .execute()
    )

    budgets_res = (
        supabase.table("category_budgets")
        .select("*")
        .eq("user_phone", user)
        .eq("month", cycle_month)
        .execute()
    )

    salary_res = (
        supabase.table("budgets")
        .select("*")
        .eq("user_phone", user)
        .eq("month", cycle_month)
        .execute()
    )

    return {
        "cycle_month": cycle_month,
        "expenses": expenses_res.data,
        "category_budgets": budgets_res.data,
        "salary": salary_res.data
    }