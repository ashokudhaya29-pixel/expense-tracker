import os
from groq import Groq
from db import get_expense_context

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def ask_finance_advisor(user, question):
    context = get_expense_context(user)

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
        return "⚠️ AI advisor temporarily unavailable."