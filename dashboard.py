import os
import pandas as pd
import streamlit as st
import plotly.express as px
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="AI Expense Tracker", layout="wide")
st.title("💰 AI Expense Tracker Dashboard")

phones_env = os.getenv("MY_PHONES", "")
allowed_phones = [p.strip() for p in phones_env.split(",") if p.strip()]

if not allowed_phones:
    st.error("No users configured. Add MY_PHONES in .env or Streamlit secrets.")
    st.stop()

user_phone = st.selectbox("Select User", allowed_phones)

expenses_res = (
    supabase.table("expenses")
    .select("*")
    .eq("user_phone", user_phone)
    .eq("is_archived", False)
    .execute()
)

salary_res = (
    supabase.table("budgets")
    .select("*")
    .eq("user_phone", user_phone)
    .execute()
)

category_budget_res = (
    supabase.table("category_budgets")
    .select("*")
    .eq("user_phone", user_phone)
    .execute()
)

expenses = pd.DataFrame(expenses_res.data)
salary_data = pd.DataFrame(salary_res.data)
debts = pd.DataFrame(debts_res.data)
debt_payments = pd.DataFrame(debt_payments_res.data)

if not debts.empty:

    total_debt = debts["remaining_amount"].astype(float).sum()

    st.subheader("💳 Debt Overview")

    d1, d2 = st.columns(2)

    d1.metric("Remaining Debt", f"₹{int(total_debt)}")

    closed_count = len(
        debts[debts["status"] == "closed"]
    )

    d2.metric("Closed Debts", closed_count)
st.subheader("💳 Active Debts")

if debts.empty:
    st.info("No debt records found.")
else:

    debt_view = debts[
        [
            "debt_name",
            "total_amount",
            "remaining_amount",
            "status"
        ]
    ]

    st.dataframe(
        debt_view,
        use_container_width=True
    )

st.subheader("🏦 EMI / Debt Payments")

if debt_payments.empty:
    st.info("No debt payments found.")
else:

    st.dataframe(
        debt_payments[
            [
                "payment_date",
                "amount",
                "notes",
                "cycle_month"
            ]
        ],
        use_container_width=True
    )

if expenses.empty:
    st.warning("No expense records found.")
    st.stop()

expenses["amount"] = expenses["amount"].astype(float)
expenses["expense_date"] = pd.to_datetime(expenses["expense_date"])

months = sorted(expenses["cycle_month"].dropna().unique(), reverse=True)
month_filter = st.selectbox("Select Month", months)

expenses = expenses[expenses["cycle_month"] == month_filter]

if not salary_data.empty:
    salary_data = salary_data[salary_data["month"] == month_filter]
    

if not category_budgets.empty:
    category_budgets = category_budgets[category_budgets["month"] == month_filter]

total_spent = expenses["amount"].sum()
total_salary = salary_data["salary"].astype(float).sum() if not salary_data.empty else 0
remaining = total_salary - total_spent

col1, col2, col3 = st.columns(3)
col1.metric("Salary", f"₹{int(total_salary)}")
col2.metric("Spent", f"₹{int(total_spent)}")
col3.metric("Remaining", f"₹{int(remaining)}")

st.subheader("📊 Category Spending")

category_df = expenses.groupby("category", as_index=False)["amount"].sum()

fig = px.pie(
    category_df,
    values="amount",
    names="category",
    title="Expense by Category"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("📈 Daily Spending Trend")

daily_df = (
    expenses.groupby(expenses["expense_date"].dt.date)["amount"]
    .sum()
    .reset_index()
)
daily_df.columns = ["date", "amount"]

fig2 = px.line(
    daily_df,
    x="date",
    y="amount",
    markers=True,
    title="Daily Expense Trend"
)

st.plotly_chart(fig2, use_container_width=True)

st.subheader("📊 Budget Usage")

if category_budgets.empty:
    st.info("No category budgets set for this month.")
else:
    for _, row in category_budgets.iterrows():
        cat = row["category"]
        limit_amt = float(row["limit_amount"])

        spent_series = category_df[category_df["category"] == cat]["amount"]
        spent = spent_series.sum() if not spent_series.empty else 0

        percent = (spent / limit_amt) * 100 if limit_amt > 0 else 0

        st.write(f"**{cat}**: ₹{int(spent)} / ₹{int(limit_amt)} ({int(percent)}%)")
        st.progress(min(percent / 100, 1.0))

st.subheader("🧾 Recent Expenses")

debts_res = (
    supabase.table("debts")
    .select("*")
    .eq("user_phone", user_phone)
    .execute()
)

debt_payments_res = (
    supabase.table("debt_payments")
    .select("*")
    .eq("user_phone", user_phone)
    .execute()
)

st.dataframe(
    expenses[["expense_date", "amount", "category", "raw_text", "cycle_month"]],
    use_container_width=True
)