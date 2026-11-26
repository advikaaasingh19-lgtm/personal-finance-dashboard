import json
import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="Finance Dashboard", page_icon="💰", layout="wide")

CATEGORY_FILE = "categories.json"
BUDGET_FILE = "budgets.json"
CUR = "₹"
PALETTE = px.colors.qualitative.Pastel

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem;}
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155; border-radius: 14px; padding: 16px 20px;
        box-shadow: 0 4px 14px rgba(0,0,0,.25);
    }
    div[data-testid="stMetric"] label {color: #94a3b8 !important;}
    .insight {background:#0f172a; border-left:4px solid #6366f1; padding:10px 16px;
              border-radius:8px; margin-bottom:8px; color:#e2e8f0;}
    </style>
    """,
    unsafe_allow_html=True,
)



def load_json(path: str, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default


def save_json(path: str, data) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


if "categories" not in st.session_state:
    st.session_state.categories = load_json(CATEGORY_FILE, {"Uncategorized": []})
if "budgets" not in st.session_state:
    st.session_state.budgets = load_json(BUDGET_FILE, {})


# ----------------------------------------------------------------------------
# Data layer
# ----------------------------------------------------------------------------
def categorize(df: pd.DataFrame) -> pd.DataFrame:
    """Keyword *contains* matching (e.g. 'swiggy' matches 'SWIGGY ORDER 123')."""
    df = df.copy()
    df["Category"] = "Uncategorized"
    details = df["Details"].str.lower()
    for category, keywords in st.session_state.categories.items():
        keywords = [k.lower().strip() for k in keywords if k.strip()]
        if category == "Uncategorized" or not keywords:
            continue
        mask = details.apply(lambda d: any(k in d for k in keywords))
        df.loc[mask, "Category"] = category
    return df


@st.cache_data(show_spinner=False)
def parse_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns]
    df["Amount"] = df["Amount"].astype(str).str.replace(",", "").astype(float)
    df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y", errors="coerce")
    if df["Date"].isna().all():  # fall back to flexible parsing
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df["Details"] = df["Details"].astype(str)
    return df.dropna(subset=["Date"])


@st.cache_data(show_spinner=False)
def demo_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    merchants = {
        "Swiggy Order": (150, 600), "Zomato Order": (150, 700), "Uber Ride": (100, 500),
        "Amazon Purchase": (300, 3000), "Netflix": (649, 649), "Reliance Fresh": (400, 2500),
        "Electricity Bill": (900, 2200), "Gym Membership": (1500, 1500), "Starbucks": (250, 600),
    }
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=180)
    rows = []
    for d in dates:
        for _ in range(rng.integers(0, 3)):
            name = rng.choice(list(merchants))
            lo, hi = merchants[name]
            rows.append([d, name, round(float(rng.uniform(lo, hi)), 2), "Debit"])
        if d.day == 1:
            rows.append([d, "Salary Credit", 85000.0, "Credit"])
        if d.day == 15:
            rows.append([d, "Freelance Payment", float(rng.integers(5000, 20000)), "Credit"])
    return pd.DataFrame(rows, columns=["Date", "Details", "Amount", "Debit/Credit"])


def add_keyword(category: str, keyword: str) -> None:
    keyword = keyword.strip()
    kws = st.session_state.categories[category]
    if keyword and keyword not in kws:
        kws.append(keyword)
        save_json(CATEGORY_FILE, st.session_state.categories)



def style(fig, height=380):
    fig.update_layout(
        template="plotly_dark", height=height, margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.15),
    )
    return fig


def money(x: float) -> str:
    return f"{CUR}{x:,.0f}"


def render_insights(debits: pd.DataFrame) -> None:
    if debits.empty:
        return
    top = debits.groupby("Category")["Amount"].sum().sort_values(ascending=False)
    tips = [f"💡 Your biggest spending category is <b>{top.index[0]}</b> "
            f"({money(top.iloc[0])}, {top.iloc[0] / top.sum():.0%} of expenses)."]
    monthly = debits.groupby("Month")["Amount"].sum()
    if len(monthly) >= 2 and monthly.iloc[-2] > 0:
        chg = (monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2]
        arrow = "📈 up" if chg > 0 else "📉 down"
        tips.append(f"{arrow} <b>{abs(chg):.0%}</b> in spending vs. last month.")
    biggest = debits.loc[debits["Amount"].idxmax()]
    tips.append(f"🧾 Largest single expense: <b>{biggest['Details']}</b> ({money(biggest['Amount'])}).")
    for t in tips:
        st.markdown(f'<div class="insight">{t}</div>', unsafe_allow_html=True)



def main():
    st.title("💰 Personal Finance Dashboard")
    st.caption("Upload a bank statement, auto-categorize spending, track budgets and spot trends.")

    # ---- Sidebar: data source ----
    with st.sidebar:
        st.header("📂 Data")
        uploaded = st.file_uploader("Transaction CSV", type=["csv"])
        use_demo = st.toggle("Use demo data", value=False, help="Great for a quick walkthrough")

    if uploaded is not None:
        source_id, raw = f"file:{uploaded.name}:{uploaded.size}", None
        try:
            raw = parse_csv(uploaded)
        except Exception as e:
            st.error(f"Error processing file: {e}")
            return
    elif use_demo:
        source_id, raw = "demo", demo_data()
    else:
        st.info("👈 Upload a CSV (columns: Date, Details, Amount, Debit/Credit) or toggle **demo data**.")
        return

    
    if st.session_state.get("source_id") != source_id:
        st.session_state.source_id = source_id
        st.session_state.df = categorize(raw)
    df = st.session_state.df
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    
    with st.sidebar:
        st.header("🔎 Filters")
        dmin, dmax = df["Date"].min().date(), df["Date"].max().date()
        rng = st.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
        cats = st.multiselect("Categories", sorted(df["Category"].unique()),
                              default=sorted(df["Category"].unique()))

    if isinstance(rng, tuple) and len(rng) == 2:
        start, end = rng
    else:
        start, end = dmin, dmax
    view = df[(df["Date"].dt.date >= start) & (df["Date"].dt.date <= end)]
    debits = view[(view["Debit/Credit"] == "Debit") & (view["Category"].isin(cats))]
    credits = view[view["Debit/Credit"] == "Credit"]

    tab_over, tab_tx, tab_budget, tab_income = st.tabs(
        ["📊 Overview", "🧾 Transactions", "🎯 Budgets", "💵 Income"]
    )

    
    with tab_over:
        spent, earned = debits["Amount"].sum(), credits["Amount"].sum()
        days = max((end - start).days + 1, 1)
        monthly = debits.groupby("Month")["Amount"].sum()
        delta = None
        if len(monthly) >= 2 and monthly.iloc[-2] > 0:
            delta = f"{(monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2]:+.1%} MoM"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Spent", money(spent), delta, delta_color="inverse")
        c2.metric("Total Received", money(earned))
        c3.metric("Net Savings", money(earned - spent))
        c4.metric("Avg Daily Spend", money(spent / days))

        st.write("")
        render_insights(debits)

        if debits.empty:
            st.warning("No expenses match the current filters.")
        else:
            left, right = st.columns(2)
            totals = debits.groupby("Category")["Amount"].sum().reset_index().sort_values("Amount", ascending=False)
            fig = px.pie(totals, values="Amount", names="Category", hole=0.55,
                         title="Expenses by Category", color_discrete_sequence=PALETTE)
            fig.update_traces(textposition="inside", textinfo="percent")
            left.plotly_chart(style(fig), use_container_width=True)

            flow = view.groupby(["Month", "Debit/Credit"])["Amount"].sum().reset_index()
            fig = px.bar(flow, x="Month", y="Amount", color="Debit/Credit", barmode="group",
                         title="Monthly Income vs Expenses",
                         color_discrete_map={"Debit": "#f87171", "Credit": "#34d399"})
            right.plotly_chart(style(fig), use_container_width=True)

            left, right = st.columns(2)
            cat_month = debits.groupby(["Month", "Category"])["Amount"].sum().reset_index()
            fig = px.bar(cat_month, x="Month", y="Amount", color="Category",
                         title="Category Spend by Month", color_discrete_sequence=PALETTE)
            left.plotly_chart(style(fig), use_container_width=True)

            top = (debits.groupby("Details")["Amount"].sum().nlargest(10)
                   .reset_index().sort_values("Amount"))
            fig = px.bar(top, x="Amount", y="Details", orientation="h", title="Top 10 Merchants",
                         color="Amount", color_continuous_scale="Purples")
            fig.update_coloraxes(showscale=False)
            right.plotly_chart(style(fig), use_container_width=True)

            daily = debits.groupby("Date")["Amount"].sum().sort_index().cumsum().reset_index()
            fig = go.Figure(go.Scatter(x=daily["Date"], y=daily["Amount"], fill="tozeroy",
                                       line=dict(color="#818cf8")))
            fig.update_layout(title="Cumulative Spending")
            st.plotly_chart(style(fig, 320), use_container_width=True)

    
    with tab_tx:
        st.subheader("Categorize your expenses")
        col_a, col_b = st.columns([3, 1])
        new_cat = col_a.text_input("New category name", label_visibility="collapsed",
                                   placeholder="New category name (e.g. Groceries)")
        if col_b.button("➕ Add category", use_container_width=True) and new_cat.strip():
            if new_cat not in st.session_state.categories:
                st.session_state.categories[new_cat] = []
                save_json(CATEGORY_FILE, st.session_state.categories)
                st.rerun()

        edited = st.data_editor(
            debits[["Date", "Details", "Amount", "Category"]],
            column_config={
                "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY", disabled=True),
                "Details": st.column_config.TextColumn("Details", disabled=True),
                "Amount": st.column_config.NumberColumn("Amount", format=f"{CUR}%.2f", disabled=True),
                "Category": st.column_config.SelectboxColumn(
                    "Category", options=list(st.session_state.categories.keys())),
            },
            hide_index=True, use_container_width=True, key="editor",
        )

        c1, c2 = st.columns([1, 5])
        if c1.button("Apply changes", type="primary"):
            changed = 0
            for idx, row in edited.iterrows():
                if row["Category"] != st.session_state.df.at[idx, "Category"]:
                    st.session_state.df.at[idx, "Category"] = row["Category"]
                    add_keyword(row["Category"], row["Details"])  # learn for next time
                    changed += 1
            st.toast(f"Updated {changed} transaction(s) and learned new keywords ✅")
            st.rerun()
        c2.download_button("⬇️ Export CSV", debits.to_csv(index=False).encode(),
                           "expenses.csv", "text/csv")

    
    with tab_budget:
        st.subheader("Monthly budgets")
        exp_cats = [c for c in st.session_state.categories if c != "Uncategorized"]
        if not exp_cats:
            st.info("Create a category in the Transactions tab first.")
        else:
            with st.expander("⚙️ Set budgets", expanded=not st.session_state.budgets):
                cols = st.columns(3)
                for i, c in enumerate(exp_cats):
                    st.session_state.budgets[c] = cols[i % 3].number_input(
                        c, min_value=0.0, step=500.0,
                        value=float(st.session_state.budgets.get(c, 0.0)), key=f"b_{c}")
                if st.button("Save budgets"):
                    save_json(BUDGET_FILE, st.session_state.budgets)
                    st.toast("Budgets saved ✅")

            latest = df["Month"].max()
            st.caption(f"Tracking month: **{latest}**")
            this_month = df[(df["Month"] == latest) & (df["Debit/Credit"] == "Debit")]
            spent_by_cat = this_month.groupby("Category")["Amount"].sum()
            for c, limit in st.session_state.budgets.items():
                if limit <= 0:
                    continue
                s = float(spent_by_cat.get(c, 0.0))
                pct = s / limit
                st.write(f"**{c}** — {money(s)} / {money(limit)}" + ("  🚨 over budget" if pct > 1 else ""))
                st.progress(min(pct, 1.0))

    
    with tab_income:
        st.subheader("Payment summary")
        st.metric("Total Payments", money(credits["Amount"].sum()))
        st.dataframe(credits[["Date", "Details", "Amount"]], use_container_width=True, hide_index=True,
                     column_config={"Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
                                    "Amount": st.column_config.NumberColumn(format=f"{CUR}%.2f")})


main()