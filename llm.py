import os
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =========================
# 1. SMART FALLBACK CATEGORY
# =========================
def smart_category(text):
    text = text.lower()

    if any(word in text for word in ["rice", "vegetable", "milk", "grocery", "dal", "fruits"]):
        return "Groceries"

    if any(word in text for word in ["chips", "snack", "biscuit", "tea", "coffee", "juice"]):
        return "Snacks"

    if any(word in text for word in ["uber", "ola", "bus", "train", "auto", "taxi"]):
        return "Travel"

    if any(word in text for word in ["petrol", "diesel", "fuel"]):
        return "Fuel"

    if any(word in text for word in ["movie", "netflix", "game", "cinema"]):
        return "Entertainment"

    if any(word in text for word in ["hospital", "medicine", "doctor", "pharmacy"]):
        return "Medical"

    if any(word in text for word in ["rent", "house", "room"]):
        return "Rent"

    return "Other"


# =========================
# 2. LLM EXPENSE EXTRACTION
# =========================
def extract_expense(text):
    try:
        print("🧠 Sending to LLM...")

        prompt = f"""
        Extract expense details from the given text.

        Return:
        - amount (only number)
        - category (VERY SPECIFIC)

        Categories should be like:
        groceries, snacks, rent, travel, fuel, shopping, medical, bills, entertainment

        Examples:
        "200 lunch" -> amount: 200, category: snacks
        "1500 vegetables" -> amount: 1500, category: groceries
        "300 petrol" -> amount: 300, category: fuel

        Text: "{text}"

        Output strictly in this format:
        amount: <number>
        category: <category>
        """

        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        output = response.choices[0].message.content.strip()
        print("📝 LLM Output:", output)

        # =========================
        # 3. PARSE RESPONSE SAFELY
        # =========================
        amount = 0
        category = "Other"

        for line in output.split("\n"):
            if "amount" in line.lower():
                try:
                    amount = int(''.join(filter(str.isdigit, line)))
                except:
                    amount = 0

            if "category" in line.lower():
                category = line.split(":")[-1].strip()

        # =========================
        # 4. FALLBACK CATEGORY FIX
        # =========================
        if category.lower() in ["food", "expense", "other", ""]:
            category = smart_category(text)

        # Normalize
        category = category.capitalize()

        print(f"💰 Final: {amount} | {category}")

        return amount, category

    except Exception as e:
        print("❌ ERROR in LLM:", str(e))

        # fallback if LLM fails completely
        amount = int(''.join(filter(str.isdigit, text))) if any(c.isdigit() for c in text) else 0
        category = smart_category(text)

        return amount, category