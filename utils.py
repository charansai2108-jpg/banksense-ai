import pdfplumber
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_text_from_pdf(uploaded_file):
    """Extract raw text from uploaded bank statement PDF"""
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def categorise_transactions(page_text):
    """Send one page text to Groq AI and get categorised transactions as JSON"""

    prompt = f"""
You are a bank statement analyser. Extract ALL transactions from the text below.

For each transaction return a JSON array like this:
[
  {{"date": "22/05/2026", "description": "UPI-KPN FARM FRESH", "amount": 137.83, "category": "Groceries"}},
  {{"date": "26/05/2026", "description": "UPI-CAFE 16", "amount": 420.00, "category": "Food & Dining"}}
]

Use ONLY these categories:
- Groceries
- Food & Dining
- Transport
- Shopping
- Entertainment
- Health & Medical
- Utilities & Bills
- Education
- Transfer & Payments
- Other

Rules:
- Extract EVERY transaction you find
- Do not skip any transaction
- Return ONLY the JSON array
- No explanation, no markdown, no extra text
- If no transactions found, return empty array []

Bank Statement Text:
{page_text[:12000]}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    return response.choices[0].message.content


def categorise_all_pages(uploaded_file):
    """Process each page separately and combine all transactions"""
    all_transactions = []

    with pdfplumber.open(uploaded_file) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                result = categorise_transactions(page_text)
                try:
                    clean = result.strip().replace("```json", "").replace("```", "")
                    transactions = json.loads(clean)
                    all_transactions.extend(transactions)
                except:
                    pass

    return all_transactions, total_pages

def generate_insights(category_summary, total_spent):
    """Generate personalised money saving tips based on spending pattern"""

    summary_text = "\n".join([
        f"- {row['category']}: ₹{row['amount']:,.2f}"
        for _, row in category_summary.iterrows()
    ])

    prompt = f"""
You are a personal finance advisor for Indians.

A user has shared their monthly spending summary:

{summary_text}

Total Spent: ₹{total_spent:,.2f}

Give a friendly, personalised financial analysis with:

1. 🔍 Spending Overview — 2-3 lines summary of their spending pattern
2. ⚠️ Top 3 Areas of Concern — where they are overspending
3. 💡 5 Practical Money Saving Tips — specific, actionable, India-focused
4. 🎯 Monthly Savings Goal — suggest a realistic amount they can save next month
5. 💬 Motivational Message — one encouraging line

Be friendly, specific, and use Indian context (UPI, EMI, Swiggy, Zomato etc).
Use emojis to make it engaging.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content