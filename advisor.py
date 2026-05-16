import os
from groq import Groq
from db import get_expense_context
from db import build_financial_snapshot

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def ask_finance_advisor(user, question):
    context = get_expense_context(user)
    question_lower = question.lower()
            # =========================
        # 💳 AI DEBT ADVISOR
        # =========================
    if "debt" in question_lower or "loan" in question_lower or "emi" in question_lower:

            total_debt = get_total_remaining_debt(context)

            salary = get_salary_total(context)

            expenses_total = get_monthly_expense_total(context)

            savings = salary - expenses_total

            if savings <= 0:
                suggestion = (
                    "You currently have no monthly surplus. "
                    "Reduce discretionary spending first."
                )
            else:
                months = int(total_debt / savings) if savings > 0 else 0

                suggestion = (
                    f"If you consistently save ₹{int(savings)} monthly, "
                    f"you may close your debt in approximately {months} months."
                )

            return (
                f"💳 Debt Advisor\n\n"
                f"📊 Remaining Debt: ₹{int(total_debt)}\n"
                f"💰 Salary: ₹{int(salary)}\n"
                f"💸 Monthly Expenses: ₹{int(expenses_total)}\n"
                f"📈 Potential Savings: ₹{int(savings)}\n\n"
                f"✅ Suggestion:\n"
                f"{suggestion}"
            )
    category_totals = get_category_totals(context)
    matched_category = find_category_in_question(question, category_totals)

    if matched_category and any(word in question_lower for word in ["spent", "spend", "expense", "expenses", "how much"]):
        amount = category_totals[matched_category]

        return (
            f"💡 Answer:\n"
            f"You have spent ₹{int(amount)} on {matched_category} this cycle.\n\n"
            f"📊 Reason:\n"
            f"Calculated directly from your saved expense records.\n\n"
            f"✅ Suggestion:\n"
            f"Review your {matched_category} expenses weekly and set a budget if needed."
        )
    question_lower = question.lower()
    snapshot = build_financial_snapshot(user)
    for category, amount in snapshot["category_totals"].items():
        if category.lower().replace("_", " ") in question_lower:
            return (
                f"💡 Answer:\n"
                f"You have spent ₹{int(amount)} on {category} this cycle.\n\n"
                f"📊 Reason:\n"
                f"This is calculated directly from your database records.\n\n"
                f"✅ Suggestion:\n"
                f"Monitor {category} spending weekly."
            )
    if "debt" in question_lower or "loan" in question_lower or "emi" in question_lower:
        salary = snapshot["salary"]
        expenses_total = snapshot["expenses_total"]
        debt_paid = snapshot["debt_paid"]
        remaining_debt = snapshot["remaining_debt"]
        remaining_balance = snapshot["remaining_balance"]

        if remaining_balance > 0:
            months = round(remaining_debt / remaining_balance, 1) if remaining_debt > 0 else 0
            months_text = f"Approximately {months} months"
        else:
            months_text = "Unable to estimate because current remaining balance is ₹0 or negative."

        if snapshot["active_loans"]:
            first_loan = snapshot["active_loans"][0]
            first_loan_text = f"{first_loan['name']} - ₹{int(first_loan['remaining'])}"
        else:
            first_loan_text = "No active loans found."

        return (
            f"💳 Debt Advisor\n\n"
            f"📊 Remaining Debt: ₹{int(remaining_debt)}\n"
            f"💰 Salary: ₹{int(salary)}\n"
            f"💸 Expenses: ₹{int(expenses_total)}\n"
            f"🏦 Debt Paid This Cycle: ₹{int(debt_paid)}\n"
            f"📈 Remaining Balance: ₹{int(remaining_balance)}\n\n"
            f"⏳ Estimated Closure Time:\n"
            f"{months_text}\n\n"
            f"✅ Close First:\n"
            f"{first_loan_text}"
        )
    prompt = f"""
You are a personal finance assistant.

User question:
{question}

Financial data:
{context}

Rules:
- Keep response short for WhatsApp
- Give practical advice
- Mention categories and amounts when useful

Format:
💡 Answer:
📊 Reason:
✅ Suggestion:
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=200
        )

        return completion.choices[0].message.content

    except Exception as e:
        print("GROQ ERROR:", str(e))
        return "⚠️ AI advisor temporarily unavailable."\

def normalize_text(text):
    return str(text).lower().replace("_", " ").strip()


def get_category_totals(context):
    expenses = context.get("expenses", [])
    totals = {}

    for row in expenses:
        category = str(row.get("category", "Other")).strip()
        amount = float(row.get("amount", 0))

        totals[category] = totals.get(category, 0) + amount

    return totals   

def get_total_remaining_debt(context):
    debts = context.get("debts", [])

    total = 0

    for row in debts:
        total += float(row.get("remaining_amount", 0))

    return total    

def get_salary_total(context):
    salary_data = context.get("salary", [])

    total = 0

    for row in salary_data:
        total += float(row.get("salary", 0))

    return total


def find_category_in_question(question, category_totals):
    q = normalize_text(question)

    for category in category_totals.keys():
        cat_normal = normalize_text(category)

        if cat_normal in q:
            return category

    return None
    