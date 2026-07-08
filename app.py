import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from utils import extract_text_from_pdf, categorise_all_pages, generate_insights

load_dotenv()

# Page config
st.set_page_config(
    page_title="BankSense AI",
    page_icon="🏦",
    layout="centered"
)

# Header
st.title("🏦 BankSense AI")
st.subheader("Smart Bank Statement Analyser")
st.markdown("---")

# Initialise session state
if "transactions_df" not in st.session_state:
    st.session_state.transactions_df = None
if "total_pages" not in st.session_state:
    st.session_state.total_pages = 0
if "insights" not in st.session_state:
    st.session_state.insights = None
if "category_sorted" not in st.session_state:
    st.session_state.category_sorted = None

# File uploader
st.markdown("### 📄 Upload Your Bank Statement")
uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
    help="Upload your bank statement in PDF format"
)

if uploaded_file is not None:
    with st.spinner("Reading your bank statement..."):
        raw_text = extract_text_from_pdf(uploaded_file)

    if raw_text:
        st.success("✅ Bank statement uploaded successfully!")

        with st.expander("📃 View Extracted Text"):
            st.text(raw_text[:2000])

        st.markdown("---")
        st.markdown("### 🤖 AI Transaction Categorisation")

        if st.button("🔍 Analyse My Transactions"):
            with st.spinner("AI is analysing every page... please wait ⏳"):
                transactions, total_pages = categorise_all_pages(uploaded_file)

            if transactions:
                df = pd.DataFrame(transactions)
                category_totals = df.groupby("category")["amount"].sum().reset_index()
                category_sorted = category_totals.sort_values("amount", ascending=False)

                # Save to session state
                st.session_state.transactions_df = df
                st.session_state.total_pages = total_pages
                st.session_state.category_sorted = category_sorted
                st.session_state.insights = None  # reset insights
            else:
                st.error("❌ Could not extract transactions. Please try again.")

    else:
        st.error("❌ Could not extract text. Please try another PDF.")

# Show results if transactions exist in session state
if st.session_state.transactions_df is not None:
    df = st.session_state.transactions_df
    category_sorted = st.session_state.category_sorted
    total = df["amount"].sum()

    st.success(f"✅ Found {len(df)} transactions across {st.session_state.total_pages} pages!")
    st.markdown("---")

    # Transactions table
    st.markdown("### 📊 Your Transactions")
    st.dataframe(df, use_container_width=True)
    st.markdown("---")

    # Pie chart
    st.markdown("### 🥧 Spending by Category")
    fig = px.pie(
        category_sorted,
        values="amount",
        names="category",
        title="Where is your money going?",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

    # Bar chart
    st.markdown("### 📊 Spending by Category (Bar Chart)")
    fig2 = px.bar(
        category_sorted,
        x="category",
        y="amount",
        title="Category wise Spending",
        color="category",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("---")

    # Category summary
    st.markdown("### 💰 Category Summary")
    col1, col2 = st.columns(2)
    for idx, (_, row) in enumerate(category_sorted.iterrows()):
        if idx % 2 == 0:
            col1.metric(
                label=row["category"],
                value=f"₹{row['amount']:,.2f}"
            )
        else:
            col2.metric(
                label=row["category"],
                value=f"₹{row['amount']:,.2f}"
            )
    st.markdown("---")

    # Total spending
    st.markdown("### 🧾 Total Spending")
    st.metric(label="Total Amount Spent", value=f"₹{total:,.2f}")
    st.markdown("---")

    # AI Insights
    st.markdown("### 💡 AI Money Saving Insights")
    if st.button("🧠 Generate My Personalised Tips"):
        with st.spinner("AI is analysing your spending habits... ⏳"):
            insights = generate_insights(category_sorted, total)
            st.session_state.insights = insights

    if st.session_state.insights:
        st.markdown(st.session_state.insights)