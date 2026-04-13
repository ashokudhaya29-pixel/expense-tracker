import re

def extract_expense(text):
    print("Extracting expense...")

    # Find amount
    amount_match = re.search(r'\d+', text)
    amount = amount_match.group() if amount_match else "0"

    # Find category (simple logic)
    text_lower = text.lower()

    if "food" in text_lower or "lunch" in text_lower or "dinner" in text_lower:
        category = "Food"
    elif "travel" in text_lower or "uber" in text_lower:
        category = "Travel"
    elif "shopping" in text_lower:
        category = "Shopping"
    else:
        category = "Other"

    print("Amount:", amount)
    print("Category:", category)

    return amount, category