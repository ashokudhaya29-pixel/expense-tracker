from sheets import get_learned_categories
import re

def extract_expense(text, user):
    try:
        if not text:
            return 0, "Other"

        text = text.lower()
        text=re.sub(r"[^\w\s]","",text)

        # 💰 amount
        amount_match = re.search(r"\d+", text)
        amount = int(amount_match.group()) if amount_match else 0

        # 🧠 STEP 1: Learned categories
        learned_map = get_learned_categories(user)

        for keyword in learned_map:
            if keyword in text:
                return amount, learned_map[keyword]

        # 🧠 STEP 2: Default rules
        CATEGORY_MAP = {
            "food": ["swiggy", "zomato", "hotel", "restaurant", "cafe", "pizza", "burger", "lunch", "dinner"],
            "grocery": ["dmart", "grocery", "supermarket", "vegetables", "fruits"],
            "travel": ["uber", "ola", "rapido", "bus", "train", "உபர"],
        }

        for cat, keywords in CATEGORY_MAP.items():
            for word in keywords:
                if word in text:
                    return amount, cat.capitalize()

        return amount, "Other"

    except Exception as e:
        print("❌ ERROR:", str(e))
        return 0, "Other"