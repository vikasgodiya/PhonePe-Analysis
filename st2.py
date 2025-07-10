import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# --- App Configuration ---
st.set_page_config("📊 PhonePe - Insightful Dashboard", layout="wide")
st.title("📊 Data-Driven Analytics with PhonePe Transactions")
st.markdown("Exploring deep insights into user behavior, insurance, and transaction performance using real data.")

# --- Database Connection ---
@st.cache_resource
def get_engine():
    return create_engine("mysql+pymysql://root:vikasashi@localhost:3306/phonepe1")

engine = get_engine()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Global Filters")
state = st.sidebar.text_input("Filter by State (optional)", "")
year = st.sidebar.selectbox("Filter by Year (optional)", ["", 2018, 2019, 2020, 2021, 2022, 2023])
quarter = st.sidebar.selectbox("Filter by Quarter (optional)", ["", 1, 2, 3, 4])

def add_filters(query, alias=""):
    conditions = []
    if state:
        conditions.append(f"{alias}state = '{state}'")
    if year:
        conditions.append(f"{alias}year = {year}")
    if quarter:
        conditions.append(f"{alias}quarter = {quarter}")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    return query

# --- Tabs for Sections ---
tabs = st.tabs(["📈 Transaction Insights", "👥 User Behavior", "🛡️ Insurance Analysis", "📌 Pin Code Impact", "💡 Strategic Findings"])

# --- Tab 1: Transaction Insights ---
with tabs[0]:
    st.header("📈 Top Performing States by Transaction Volume")
    base_query = "SELECT state, SUM(transaction_amount) AS total_amount FROM aggregated_transaction GROUP BY state ORDER BY total_amount DESC LIMIT 10"
    df_tx = pd.read_sql(base_query, engine)
    st.dataframe(df_tx)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df_tx, x="state", y="total_amount", ax=ax)
    ax.set_title("Top 10 States by Transaction Value")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.subheader("📊 Seasonal Spike: Q4 vs Q1 by State")
    surge_query = """
    SELECT state, year,
        SUM(CASE WHEN quarter = 1 THEN transaction_amount ELSE 0 END) AS Q1,
        SUM(CASE WHEN quarter = 4 THEN transaction_amount ELSE 0 END) AS Q4,
        (SUM(CASE WHEN quarter = 4 THEN transaction_amount ELSE 0 END) - SUM(CASE WHEN quarter = 1 THEN transaction_amount ELSE 0 END)) AS surge
    FROM aggregated_transaction
    GROUP BY state, year
    HAVING Q1 > 0 AND Q4 > 0
    ORDER BY surge DESC
    LIMIT 10;
    """
    df_surge = pd.read_sql(surge_query, engine)
    st.dataframe(df_surge)

# --- Tab 2: User Behavior ---
with tabs[1]:
    st.header("👥 Device Brand Dominance (Brand Loyalty %)")
    loyalty_query = """
    SELECT state, brand, brand_count,
           ROUND((brand_count / total) * 100, 2) AS loyalty_pct
    FROM (
        SELECT state, brand, brand_count,
               SUM(brand_count) OVER (PARTITION BY state) AS total,
               ROW_NUMBER() OVER (PARTITION BY state ORDER BY brand_count DESC) AS rn
        FROM aggregated_user
    ) AS ranked
    WHERE rn = 1
    ORDER BY loyalty_pct DESC
    """
    df_loyalty = pd.read_sql(loyalty_query, engine)
    st.dataframe(df_loyalty)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df_loyalty.head(10), x="state", y="loyalty_pct", hue="brand", ax=ax)
    ax.set_title("Top Brand Loyalty by State")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.subheader("📉 States with Low App Usage (Drop-off Zones)")
    drop_query = """
    SELECT state, SUM(registered_users) AS total_users, SUM(app_opens) AS total_opens,
           ROUND(SUM(app_opens)/NULLIF(SUM(registered_users), 0), 2) AS usage_ratio
    FROM aggregated_user
    GROUP BY state
    HAVING usage_ratio < 0.5
    ORDER BY usage_ratio ASC
    LIMIT 10
    """
    df_drop = pd.read_sql(drop_query, engine)
    st.dataframe(df_drop)

# --- Tab 3: Insurance Analysis ---
with tabs[2]:
    st.header("🛡️ Insurance Penetration Efficiency by State")
    insurance_eff_query = """
    SELECT state, SUM(amount) AS total_insurance, SUM(app_opens) AS app_opens,
           ROUND(SUM(amount)/NULLIF(SUM(app_opens), 0), 2) AS efficiency
    FROM map_insurance
    JOIN map_user USING(state, year, quarter, district)
    GROUP BY state
    ORDER BY efficiency DESC
    LIMIT 10;
    """
    df_eff = pd.read_sql(insurance_eff_query, engine)
    st.dataframe(df_eff)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df_eff, x="state", y="efficiency", ax=ax)
    ax.set_title("Insurance Amount per App Open (Efficiency Score)")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# --- Tab 4: Pin Code Impact ---
with tabs[3]:
    st.header("📌 Top Pincodes by Transaction Value")
    pin_query = """
    SELECT pincode, SUM(amount) AS total_value
    FROM top_map
    WHERE pincode IS NOT NULL
    GROUP BY pincode
    ORDER BY total_value DESC
    LIMIT 10;
    """
    df_pin = pd.read_sql(pin_query, engine)
    st.dataframe(df_pin)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df_pin, x="pincode", y="total_value", ax=ax)
    ax.set_title("Top 10 High-Value Transaction Pincodes")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# --- Tab 5: Strategic Findings ---
with tabs[4]:
    st.header("💡 Market Diversity & Premium Pockets")

    diversity_query = """
    SELECT state, COUNT(DISTINCT transaction_type) AS variety
    FROM aggregated_transaction
    GROUP BY state
    ORDER BY variety DESC
    LIMIT 10;
    """
    df_variety = pd.read_sql(diversity_query, engine)
    st.dataframe(df_variety)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df_variety, x="state", y="variety", ax=ax)
    ax.set_title("States with Most Diverse Payment Behaviors")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.subheader("🔐 High Insurance with Low Users (Premium Pockets)")
    high_insurance_query = """
    SELECT i.state, i.district, SUM(i.amount) AS insurance_amt, SUM(u.registered_users) AS users,
           ROUND(SUM(i.amount)/NULLIF(SUM(u.registered_users), 0), 2) AS premium_index
    FROM map_insurance i
    JOIN map_user u ON i.state = u.state AND i.district = u.district AND i.year = u.year AND i.quarter = u.quarter
    GROUP BY i.state, i.district
    HAVING users < 5000 AND insurance_amt > 100000
    ORDER BY premium_index DESC
    LIMIT 10;
    """
    df_premium = pd.read_sql(high_insurance_query, engine)
    st.dataframe(df_premium)


# --- Additional Insights in Strategic Tab ---
    st.subheader("📊 Fastest Growing Insurance Districts Over Time")
    growth_query = """
    SELECT district, year, quarter, SUM(amount) AS total_insurance
    FROM map_insurance
    GROUP BY district, year, quarter
    ORDER BY district, year, quarter
    """
    df_growth = pd.read_sql(growth_query, engine)
    st.dataframe(df_growth.head(20))

    st.subheader("📊 States with High Transactions but Low Diversity (Concentration Risk)")
    concentration_query = """
    SELECT state, SUM(transaction_amount) AS total_amount,
           COUNT(DISTINCT transaction_type) AS type_count
    FROM aggregated_transaction
    GROUP BY state
    HAVING type_count <= 2
    ORDER BY total_amount DESC
    LIMIT 10;
    """
    df_concentration = pd.read_sql(concentration_query, engine)
    st.dataframe(df_concentration)

    st.subheader("📈 Top Districts with Growing App Engagement (Rising Opens)")
    app_growth_query = """
    SELECT district, year, quarter, SUM(app_opens) AS total_opens
    FROM map_user
    GROUP BY district, year, quarter
    HAVING total_opens > 50000
    ORDER BY total_opens DESC
    LIMIT 10;
    """
    df_app_growth = pd.read_sql(app_growth_query, engine)
    st.dataframe(df_app_growth)

    st.subheader("📊 States with High Insurance but Low Transaction Volume")
    ins_tx_query = """
    SELECT i.state, SUM(i.amount) AS insurance_total, SUM(t.transaction_amount) AS txn_total,
           ROUND(SUM(i.amount)/NULLIF(SUM(t.transaction_amount), 0), 2) AS insurance_ratio
    FROM map_insurance i
    JOIN aggregated_transaction t ON i.state = t.state AND i.year = t.year AND i.quarter = t.quarter
    GROUP BY i.state
    HAVING insurance_ratio > 0.5
    ORDER BY insurance_ratio DESC
    LIMIT 10;
    """
    df_ins_tx = pd.read_sql(ins_tx_query, engine)
    st.dataframe(df_ins_tx)

    st.subheader("📌 Most Active Districts Across All Categories")
    active_query = """
    SELECT mu.district,
       SUM(mu.registered_users) AS users,
       SUM(mu.app_opens) AS opens,
       SUM(mm.count) AS txns,
       SUM(mi.count) AS insurances
    FROM map_user mu
    JOIN map_map mm ON mu.state = mm.state AND mu.district = mm.district AND mu.year = mm.year AND mu.quarter = mm.quarter
    JOIN map_insurance mi ON mu.state = mi.state AND mu.district = mi.district AND mu.year = mi.year AND mu.quarter = mi.quarter
    GROUP BY mu.district
    ORDER BY txns DESC, opens DESC
    LIMIT 10;

    """
    df_active = pd.read_sql(active_query, engine)
    st.dataframe(df_active)
