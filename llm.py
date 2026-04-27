import re

# 🔥 Smart keyword mapping
CATEGORY_MAP = {
    "food": ["swiggy", "zomato", "hotel", "restaurant", "cafe", "pizza", "burger", "lunch", "dinner"],
    "grocery": ["dmart", "grocery", "supermarket", "vegetables", "fruits", "rice", "milk"],
    "travel": ["uber", "ola", "rapido", "bus", "train", "petrol", "diesel"],
    "shopping": ["amazon", "flipkart", "shopping", "clothes"],
    "entertainment": ["movie", "netflix", "hotstar"],
}

def extract_expense(text):
    try:
        text = text.lower()

        # 💰 Extract amount
        amount_match = re.search(r"\d+", text)
        amount = int(amount_match.group()) if amount_match else 0

        # 🧠 Detect category (better scoring logic)
        category_scores = {}

        for cat, keywords in CATEGORY_MAP.items():
            score = sum(1 for word in keywords if word in text)
            if score > 0:
                category_scores[cat] = score

        if category_scores:
            category = max(category_scores, key=category_scores.get).capitalize()
        else:
            category = "Other"
        return amount, category
    except Exception as e:
        print("❌ ERROR in LLM:", str(e))
        return 0, "Other"