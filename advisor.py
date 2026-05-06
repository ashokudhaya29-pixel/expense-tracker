import os
import google.generativeai as genai
from db import get_expense_context

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


def ask_finance_advisor(user, question):
    context = get_expense_context(user)

    prompt = f"""
You are a personal finance assistant.

User question:
{question}

User financial data:
{context}

Rules:
- Answer only based on the given data.
- Be practical and simple.
- Mention amount/category when possible.
- If data is not enough, say what is missing.
- Keep answer short for WhatsApp.

Give response in this format:
💡 Answer:
📊 Reason:
✅ Suggestion:
"""

    response = model.generate_content(prompt)
    return response.text