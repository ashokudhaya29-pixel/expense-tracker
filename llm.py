from groq import Groq
import os
import json
import re

# 🔐 Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# =========================
# 🔥 RULE-BASED CATEGORY MAP
# =========================
CATEGORY_RULES = {
    "swiggy": "Food",
    "zomato": "Food",
    "restaurant": "Food",
    "hotel": "Food",
    "meal": "Food",

    "tea": "Snacks",
    "coffee": "Snacks",
    "snacks": "Snacks",
    "juice": "Snacks",

    "dmart": "Grocery",
    "grocery": "Grocery",
    "rice": "Grocery",
    "vegetables": "Grocery",
    "milk": "Grocery",

    "uber": "Travel",
    "ola": "Travel",
    "petrol": "Travel",
    "fuel": "Travel",
    "bus": "Travel",

    "electricity": "Bills",
    "eb": "Bills",
    "wifi": "Bills",
    "internet": "Bills",
    "rent": "Bills"
}


# =========================
# 🔎 RULE-BASED DETECTION
# =========================
def detect_category_rule(text):
    text = text.lower()
    for keyword, category in CATEGORY_RULES.items():
        if keyword in text:
            return category
    return None


# =========================
# 🛡 SAFE JSON PARSER
# =========================
def safe_parse_category(output):
    try:
        # ✅ Try direct JSON
        return json.loads(output).get("category", "Other")
    except:
        try:
            # ✅ Extract JSON if wrapped in text
            match = re.search(r'\{.*\}', output, re.DOTALL)
            if match:
                return json.loads(match.group()).get("category", "Other")
        except:
            pass

    # ❌ Final fallback
    return "Other"


# =========================
# 🎯 MAIN FUNCTION
# =========================
def extract_expense(text):
    try:
        print("🤖 Processing expense...")

        # =========================
        # 💰 STEP 1: Extract amount
        # =========================
        words = text.split()
        amount = 0

        for w in words:
            if w.isdigit():
                amount = int(w)
                break

        # =========================
        # 🧠 STEP 2: Rule-based category
        # =========================
        category = detect_category_rule(text)

        # =========================
        # 🤖 STEP 3: LLM fallback
        # =========================
        if not category:
            print("🔄 Using LLM fallback...")

            prompt = f"""
            Classify this expense:

            "{text}"

            Categories:
            Food, Grocery, Snacks, Travel, Bills, Other

            Return ONLY valid JSON.
            Example:
            {{"category": "Food"}}
            """

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            output = response.choices[0].message.content

            print("LLM RAW RESPONSE >>>", repr(output))

            category = safe_parse_category(output)

        print(f"✅ Final: Amount={amount}, Category={category}")

        return amount, category

    except Exception as e:
        print("❌ ERROR in LLM:", str(e))
        return 0, "Other"