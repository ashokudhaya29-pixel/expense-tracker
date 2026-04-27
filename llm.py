from groq import Groq
import os
import json

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_expense(text):
    try:
        print("🤖 Using FREE LLM (Groq)...")

        prompt = f"""
        Extract expense details from this text:

        "{text}"

        Return JSON only:
        {{
            "amount": number,
            "category": "one of [Food, Grocery, Snacks, Travel, Bills, Other]"
        }}
        """

        response = client.chat.completions.create(
            model="llama3-70b-8192",  # powerful + free
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        output = response.choices[0].message.content
        print("LLM RAW:", output)

        data = json.loads(output)

        amount = int(data.get("amount", 0))
        category = data.get("category", "Other")

        return amount, category

    except Exception as e:
        print("❌ ERROR in LLM:", str(e))
        return 0, "Other"