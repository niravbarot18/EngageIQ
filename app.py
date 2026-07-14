import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------------------------------
# Page config & style
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Retention Analytics | European Central Bank",
    page_icon="🏦",
    layout="wide",
)

PRIMARY = "#0B3D91"      # deep institutional blue
ACCENT = "#C8963E"       # muted gold accent
RISK = "#B23A48"         # muted red for risk
GOOD = "#2E7D5B"         # muted green for healthy

st.markdown(
    f"""
    <style>
    :root {{
        --metric-card-bg: var(--stSecondaryBackgroundColor, var(--secondary-background-color, #F5F7FA));
        --metric-card-text: var(--stTextColor, var(--text-color, #0B3D91));
        --metric-card-border: var(--stBorderColor, var(--border-color, #E2E6ED));
    }}
    html[data-theme='dark'],
    body[data-theme='dark'] {{
        --metric-card-bg: #31333F;
        --metric-card-text: #F8F9FA;
        --metric-card-border: rgba(255, 255, 255, 0.18);
    }}
    .stMetric {{
        background-color: var(--metric-card-bg) !important;
        color: var(--metric-card-text) !important;
        border: 1px solid var(--metric-card-border) !important;
        padding: 12px;
        border-radius: 8px;
    }}
    .stMetric, .stMetric * {{
        color: inherit !important;
        background-color: transparent !important;
        border-color: inherit !important;
    }}
    h1, h2, h3 {{ color: {PRIMARY}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
@st.cache_data
def load_data(path="data/European_Bank.csv"):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    # Engagement profile classification (per brief's 4 profiles)
    def profile(row):
        active = row["IsActiveMember"] == 1
        many_products = row["NumOfProducts"] >= 2
        high_balance = row["Balance"] >= row["_bal_q75"]
        if active and many_products:
            return "Active & Engaged"
        if not active and not high_balance:
            return "Inactive & Disengaged"
        if active and not many_products:
            return "Active, Low-Product"
        if not active and high_balance:
            return "Inactive, High-Balance"
        return "Other"

    df["_bal_q75"] = df["Balance"].quantile(0.75)
    df["EngagementProfile"] = df.apply(profile, axis=1)
    df.drop(columns=["_bal_q75"], inplace=True)

    # Relationship Strength Index (0-10 composite; see methodology notes)
    df["RSI"] = (
        df["IsActiveMember"] * 4
        + df["NumOfProducts"].clip(upper=2) * 2
        + df["HasCrCard"] * 1
        + (df["Tenure"] / df["Tenure"].max()) * 1
    ).round(2)

    return df


df = load_data()

# ----------------------------------------------------------------------------
# Sidebar — user filters (per brief: engagement filters, product sliders,
# balance/salary thresholds)
# ----------------------------------------------------------------------------
st.sidebar.title("🏦 Retention Analytics")
st.sidebar.caption("Customer Engagement & Product Utilization")

st.sidebar.subheader("Filters")

geo_filter = st.sidebar.multiselect(
    "Geography", options=sorted(df["Geography"].unique()), default=list(df["Geography"].unique())
)
active_filter = st.sidebar.selectbox("Engagement status", ["All", "Active only", "Inactive only"])
product_range = st.sidebar.slider("Number of products", 1, int(df["NumOfProducts"].max()), (1, int(df["NumOfProducts"].max())))
balance_threshold = st.sidebar.slider(
    "Minimum balance ($)", 0, int(df["Balance"].max()), 0, step=5000
)
salary_threshold = st.sidebar.slider(
    "Minimum estimated salary ($)", 0, int(df["EstimatedSalary"].max()), 0, step=5000
)

f = df.copy()
f = f[f["Geography"].isin(geo_filter)]
if active_filter == "Active only":
    f = f[f["IsActiveMember"] == 1]
elif active_filter == "Inactive only":
    f = f[f["IsActiveMember"] == 0]
f = f[(f["NumOfProducts"] >= product_range[0]) & (f["NumOfProducts"] <= product_range[1])]
f = f[f["Balance"] >= balance_threshold]
f = f[f["EstimatedSalary"] >= salary_threshold]

st.sidebar.markdown(f"**{len(f):,}** of {len(df):,} customers match filters")

# ----------------------------------------------------------------------------
# Header + top-line KPIs
# ----------------------------------------------------------------------------
st.title("Customer Engagement & Product Utilization Analytics")
st.caption("Retention strategy dashboard — Behavior and relationship depth, not just demographics")

if len(f) == 0:
    st.warning("No customers match the current filters. Adjust filters in the sidebar.")
    st.stop()

churn_rate = f["Exited"].mean()
active_churn = f.loc[f["IsActiveMember"] == 1, "Exited"].mean() if (f["IsActiveMember"] == 1).any() else np.nan
inactive_churn = f.loc[f["IsActiveMember"] == 0, "Exited"].mean() if (f["IsActiveMember"] == 0).any() else np.nan
err_ratio = (1 - active_churn) / (1 - inactive_churn) if inactive_churn not in (0, np.nan) and not np.isnan(inactive_churn) else np.nan

hb_thresh = df["Balance"].quantile(0.75)
hb_disengaged = f[(f["Balance"] >= hb_thresh) & (f["IsActiveMember"] == 0)]
hb_disengagement_rate = len(hb_disengaged) / len(f[f["Balance"] >= hb_thresh]) if len(f[f["Balance"] >= hb_thresh]) > 0 else np.nan

cc_churn = f.loc[f["HasCrCard"] == 1, "Exited"].mean() if (f["HasCrCard"] == 1).any() else np.nan
no_cc_churn = f.loc[f["HasCrCard"] == 0, "Exited"].mean() if (f["HasCrCard"] == 0).any() else np.nan
cc_stickiness = no_cc_churn - cc_churn if not (np.isnan(cc_churn) or np.isnan(no_cc_churn)) else np.nan

row1_col1, row1_col2, row1_col3 = st.columns(3)
row2_col1, row2_col2 = st.columns(2)

row1_col1.metric("Overall churn rate", f"{churn_rate:.1%}")

row1_col2.metric(
    "Engagement Retention Ratio",
    f"{err_ratio:.2f}x" if not np.isnan(err_ratio) else "n/a",
    help="Retention rate of active members ÷ retention rate of inactive members."
)

row1_col3.metric(
    "High-Balance Disengagement Rate",
    f"{hb_disengagement_rate:.1%}" if not np.isnan(hb_disengagement_rate) else "n/a",
    help="Share of top-quartile-balance customers who are inactive."
)

row2_col1.metric(
    "Credit Card Stickiness Score",
    f"{cc_stickiness:+.1%}" if not np.isnan(cc_stickiness) else "n/a",
    help="Churn(no card) − Churn(has card)."
)

row2_col2.metric(
    "Avg. Relationship Strength Index",
    f"{f['RSI'].mean():.2f} / 10"
)

st.divider()

# ----------------------------------------------------------------------------
# Module 1 — Engagement vs churn overview
# ----------------------------------------------------------------------------
st.header("1. Engagement vs. Churn Overview")
m1c1, m1c2 = st.columns([1, 1])

with m1c1:
    eng_churn = f.groupby("IsActiveMember")["Exited"].mean().reset_index()
    eng_churn["IsActiveMember"] = eng_churn["IsActiveMember"].map({0: "Inactive", 1: "Active"})
    fig = px.bar(
        eng_churn, x="IsActiveMember", y="Exited", color="IsActiveMember",
        color_discrete_map={"Active": GOOD, "Inactive": RISK},
        text_auto=".1%", title="Churn Rate: Active vs. Inactive Members",
        labels={"Exited": "Churn rate", "IsActiveMember": ""},
    )
    fig.update_layout(showlegend=False, yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

with m1c2:
    profile_counts = f["EngagementProfile"].value_counts().reset_index()
    profile_counts.columns = ["Profile", "Count"]
    profile_churn = f.groupby("EngagementProfile")["Exited"].mean().reset_index()
    merged = profile_counts.merge(profile_churn, left_on="Profile", right_on="EngagementProfile")
    fig2 = px.bar(
        merged.sort_values("Exited", ascending=False), x="Profile", y="Exited",
        text_auto=".1%", title="Churn Rate by Engagement Profile",
        color="Exited", color_continuous_scale=[GOOD, ACCENT, RISK],
        labels={"Exited": "Churn rate"},
    )
    fig2.update_layout(yaxis_tickformat=".0%", coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

st.caption(
    "Engagement profiles: **Active & Engaged** (active + 2+ products), **Inactive & Disengaged** "
    "(inactive + below-median balance), **Active, Low-Product** (active but single product), "
    "**Inactive, High-Balance** (inactive but top-quartile balance — the at-risk premium segment)."
)

st.divider()

# ----------------------------------------------------------------------------
# Module 2 — Product utilization impact analysis
# ----------------------------------------------------------------------------
st.header("2. Product Utilization Impact Analysis")
m2c1, m2c2 = st.columns([1, 1])

with m2c1:
    prod_churn = f.groupby("NumOfProducts")["Exited"].agg(["mean", "count"]).reset_index()
    prod_churn.columns = ["NumOfProducts", "ChurnRate", "Count"]
    fig3 = px.bar(
        prod_churn, x="NumOfProducts", y="ChurnRate", text_auto=".1%",
        title="Churn Rate by Number of Products Held",
        color="ChurnRate", color_continuous_scale=[GOOD, ACCENT, RISK],
        labels={"ChurnRate": "Churn rate", "NumOfProducts": "Number of products"},
    )
    fig3.update_layout(yaxis_tickformat=".0%", coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)
    st.caption(
        "⚠️ Churn rises sharply beyond 2 products (3 → ~83%, 4 → ~100% in the full dataset). "
        "This is a red flag for over-selling or bundled-product dissatisfaction, not a loyalty signal."
    )

with m2c2:
    single_vs_multi = f.assign(Depth=np.where(f["NumOfProducts"] == 1, "Single product", "Multi-product"))
    depth_churn = single_vs_multi.groupby("Depth")["Exited"].mean().reset_index()
    fig4 = px.bar(
        depth_churn, x="Depth", y="Exited", text_auto=".1%", color="Depth",
        color_discrete_map={"Single product": ACCENT, "Multi-product": PRIMARY},
        title="Single-Product vs. Multi-Product Retention",
        labels={"Exited": "Churn rate"},
    )
    fig4.update_layout(showlegend=False, yaxis_tickformat=".0%")
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ----------------------------------------------------------------------------
# Module 3 — High-value disengaged customer detector
# ----------------------------------------------------------------------------
st.header("3. High-Value Disengaged Customer Detector")
st.write(
    "Customers who look financially strong but show weak engagement — the segment most likely to "
    "churn silently, without complaint, before the bank notices."
)

at_risk = f[(f["IsActiveMember"] == 0) & (f["Balance"] >= f["Balance"].quantile(0.60))].copy()
at_risk = at_risk.sort_values("Balance", ascending=False)

m3c1, m3c2, m3c3 = st.columns(3)
m3c1.metric("At-risk premium customers (in current filter)", f"{len(at_risk):,}")
m3c2.metric("Their churn rate", f"{at_risk['Exited'].mean():.1%}" if len(at_risk) else "n/a")
m3c3.metric("Total balance at risk", f"${at_risk['Balance'].sum():,.0f}")

st.dataframe(
    at_risk[["CustomerId", "Surname", "Geography", "Age", "Balance", "EstimatedSalary",
             "NumOfProducts", "Tenure", "RSI", "Exited"]].reset_index(drop=True),
    use_container_width=True,
    height=300,
)
st.download_button(
    "Download at-risk customer list (CSV)",
    at_risk.to_csv(index=False).encode("utf-8"),
    file_name="at_risk_premium_customers.csv",
    mime="text/csv",
)

st.divider()

# ----------------------------------------------------------------------------
# Module 4 — Retention strength scoring panel
# ----------------------------------------------------------------------------
st.header("4. Retention Strength Scoring Panel")
st.write(
    "Relationship Strength Index (RSI) combines engagement, product depth, card ownership and tenure "
    "into a single 0–10 score. Higher RSI should track with lower churn if the underlying hypothesis holds."
)

m4c1, m4c2 = st.columns([1, 1])
with m4c1:
    rsi_bins = pd.qcut(f["RSI"], q=4, duplicates="drop")
    rsi_churn = f.groupby(rsi_bins)["Exited"].mean().reset_index()
    rsi_churn["RSI"] = rsi_churn["RSI"].astype(str)
    fig5 = px.bar(
        rsi_churn, x="RSI", y="Exited", text_auto=".1%",
        title="Churn Rate by Relationship Strength Quartile",
        color="Exited", color_continuous_scale=[RISK, ACCENT, GOOD],
        labels={"Exited": "Churn rate", "RSI": "RSI quartile (low → high)"},
    )
    fig5.update_layout(yaxis_tickformat=".0%", coloraxis_showscale=False)
    st.plotly_chart(fig5, use_container_width=True)

with m4c2:
    fig6 = px.histogram(
        f, x="RSI", color=f["Exited"].map({0: "Retained", 1: "Churned"}),
        barmode="overlay", nbins=20, title="RSI Distribution by Outcome",
        color_discrete_map={"Retained": GOOD, "Churned": RISK},
        labels={"color": "Outcome"},
    )
    st.plotly_chart(fig6, use_container_width=True)

st.divider()
st.caption(
    "Data: European Central Bank customer dataset (10,000 customers). "
    "Dashboard built for the Customer Engagement & Product Utilization Analytics for Retention Strategy project."
)
