import os
from groq import Groq

from db import (
    get_expense_context,
    build_financial_snapshot
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# =========================
# HELPERS
# =========================

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


def find_category_in_question(question, category_totals):
    q = normalize_text(question)

    for category in category_totals.keys():
        cat_normal = normalize_text(category)

        if cat_normal in q:
            return category

    return None


# =========================
# MAIN ADVISOR
# =========================

def ask_finance_advisor(user, question):

    try:
        context = get_expense_context(user)
        snapshot = build_financial_snapshot(user)

        question_lower = question.lower()

        # =========================
        # CATEGORY SPENDING
        # =========================
        category_totals = get_category_totals(context)

        matched_category = find_category_in_question(
            question,
            category_totals
        )

        if matched_category and any(
            word in question_lower
            for word in [
                "spent",
                "spend",
                "expense",
                "expenses",
                "how much"
            ]
        ):

            amount = category_totals[matched_category]

            return (
                f"💡 Answer:\n"
                f"You have spent ₹{int(amount)} on "
                f"{matched_category} this cycle.\n\n"

                f"📊 Reason:\n"
                f"Calculated directly from your database records.\n\n"

                f"✅ Suggestion:\n"
                f"Monitor {matched_category} spending weekly."
            )

        # =========================
        # WHICH LOAN TO CLOSE FIRST
        # =========================
        if (
            "which loan" in question_lower
            or "close first" in question_lower
            or "close 1st" in question_lower
            or "which debt" in question_lower
        ):

            active_loans = snapshot["active_loans"]

            if not active_loans:
                return "💳 No active loans found."

            first_loan = active_loans[0]

            msg = (
                f"💳 Debt Advisor\n\n"

                f"✅ Close this loan first:\n"
                f"{first_loan['name']} - "
                f"₹{int(first_loan['remaining'])}\n\n"

                f"📊 Reason:\n"
                f"Using debt snowball method "
                f"(smallest balance first).\n\n"

                f"📌 Loan Order:\n"
            )

            for i, loan in enumerate(active_loans, start=1):
                msg += (
                    f"{i}. {loan['name']} - "
                    f"₹{int(loan['remaining'])}\n"
                )

            return msg

        # =========================
        # DEBT ADVISOR
        # =========================
        if (
            "debt" in question_lower
            or "loan" in question_lower
            or "emi" in question_lower
            or "months remaining" in question_lower
        ):

            salary = snapshot["salary"]

            expenses_total = snapshot["expenses_total"]

            debt_paid = snapshot["debt_paid"]

            remaining_debt = snapshot["remaining_debt"]

            remaining_balance = snapshot["remaining_balance"]

            if remaining_balance > 0:
                months = (
                    round(
                        remaining_debt / remaining_balance,
                        1
                    )
                    if remaining_debt > 0
                    else 0
                )

                months_text = (
                    f"Approximately {months} months"
                )

            else:
                months_text = (
                    "Unable to estimate because "
                    "remaining balance is ₹0 or negative."
                )

            if snapshot["active_loans"]:
                first_loan = snapshot["active_loans"][0]

                first_loan_text = (
                    f"{first_loan['name']} - "
                    f"₹{int(first_loan['remaining'])}"
                )

            else:
                first_loan_text = "No active loans found."

            return (
                f"💳 Debt Advisor\n\n"

                f"📊 Remaining Debt: "
                f"₹{int(remaining_debt)}\n"

                f"💰 Salary: "
                f"₹{int(salary)}\n"

                f"💸 Expenses: "
                f"₹{int(expenses_total)}\n"

                f"🏦 Debt Paid This Cycle: "
                f"₹{int(debt_paid)}\n"

                f"📈 Remaining Balance: "
                f"₹{int(remaining_balance)}\n\n"

                f"⏳ Estimated Closure Time:\n"
                f"{months_text}\n\n"

                f"✅ Close First:\n"
                f"{first_loan_text}"
            )

        # =========================
        # GENERIC AI RESPONSE
        # =========================
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
        print("ADVISOR ERROR:", str(e))

        return (
            f"⚠️ Advisor error:\n"
            f"{str(e)}"
        )