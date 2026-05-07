import os
from groq import Groq
from db import get_expense_context

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def ask_finance_advisor(user, question):
    context = get_expense_context(user)
    question_lower = question.lower()
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


def find_category_in_question(question, category_totals):
    q = normalize_text(question)

    for category in category_totals.keys():
        cat_normal = normalize_text(category)

        if cat_normal in q:
            return category

    return None