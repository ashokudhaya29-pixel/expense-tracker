from groq import Groq
import os
import json

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 🔥 Rule-based mapping (high accuracy)
CATEGORY_RULES = {
    "swiggy": "Food",
    "zomato": "Food",
    "hotel": "Food",
    "restaurant": "Food",
    "tea": "Snacks",
    "coffee": "Snacks",
    "snacks": "Snacks",
    "dmart": "Grocery",
    "grocery": "Grocery",
    "rice": "Grocery",
    "vegetables": "Grocery",
    "uber": "Travel",
    "ola": "Travel",
    "petrol": "Travel",
    "fuel": "Travel",
    "eb": "Bills",
    "electricity": "Bills",
    "wifi": "Bills",
    "rent": "Bills"
}

def detect_category_rule(text):
    text = text.lower()
    for keyword, category in CATEGORY_RULES.items():
        if keyword in text:
            return category
    return None


def extract_expense(text):
    try:
        print("🤖 Processing expense...")

        # ✅ Step 1: Extract amount (simple)
        words = text.split()
        amount = 0
        for w in words:
            if w.isdigit():
                amount = int(w)
                break

        # ✅ Step 2: Rule-based category
        category = detect_category_rule(text)

        # ✅ Step 3: If not found → use LLM
        if not category:
            print("🔄 Using LLM fallback...")

            prompt = f"""
            Classify this expense into one category:

            "{text}"

            Categories:
            Food, Grocery, Snacks, Travel, Bills, Other

            Return JSON:
            {{
                "category": "..."
            }}
            """

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            output = response.choices[0].message.content
            print("LLM RAW:", output)

            data = json.loads(output)
            category = data.get("category", "Other")

        return amount, category

    except Exception as e:
        print("❌ ERROR in LLM:", str(e))
        return 0, "Other"