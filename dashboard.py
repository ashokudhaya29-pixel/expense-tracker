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

user_phone = st.text_input("Enter WhatsApp number", "919080774244")

if user_phone:
    expenses_res = (
        supabase.table("expenses")
        .select("*")
        .eq("user_phone", user_phone)
        .eq("is_archived", False)
        .execute()
    )

    budgets_res = (
        supabase.table("budgets")
        .select("*")
        .eq("user_phone", user_phone)
        .execute()
    )

    expenses = pd.DataFrame(expenses_res.data)
    budgets = pd.DataFrame(budgets_res.data)

    if expenses.empty:
        st.warning("No expense records found.")
    else:
        expenses["amount"] = expenses["amount"].astype(float)

        total_spent = expenses["amount"].sum()
        total_salary = budgets["salary"].astype(float).sum() if not budgets.empty else 0
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
        month_filter = st.selectbox("Select Month", expenses["cycle_month"].unique())

        expenses = expenses[expenses["cycle_month"] == month_filter]

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 Daily Spending Trend")

        expenses["expense_date"] = pd.to_datetime(expenses["expense_date"])
        daily_df = expenses.groupby(expenses["expense_date"].dt.date)["amount"].sum().reset_index()
        daily_df.columns = ["date", "amount"]

        fig2 = px.line(
            daily_df,
            x="date",
            y="amount",
            markers=True,
            title="Daily Expense Trend"
        )

        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("🧾 Recent Expenses")
        st.dataframe(
            expenses[["expense_date", "amount", "category", "raw_text", "cycle_month"]],
            use_container_width=True
        )
        st.subheader("📊 Budget Usage")

        for _, row in budgets.iterrows():
            cat = row["category"]
            limit_amt = float(row["limit_amount"])

            spent = category_df[category_df["category"] == cat]["amount"].sum()

            percent = (spent / limit_amt) * 100 if limit_amt > 0 else 0

            st.progress(min(percent/100, 1.0))
            st.write(f"{cat}: ₹{int(spent)} / ₹{int(limit_amt)}")