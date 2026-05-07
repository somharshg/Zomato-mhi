import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


st.set_page_config(
    page_title="Zomato Marketplace Health Index",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #FAFAFA; }
    .stMetric { background: white; border-radius: 10px; padding: 12px; border: 1px solid #F0F0F0; }
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    h1 { color: #E23744; font-size: 1.6rem !important; }
    h2 { font-size: 1.1rem !important; color: #333; }
    h3 { font-size: 1rem !important; color: #555; }
    .stAlert { border-radius: 10px; }
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #F0F0F0;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .score-box {
        background: white;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        border: 1px solid #F0F0F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

ZOMATO_RED = "#E23744"
ZOMATO_DARK = "#1A1A1A"

def load_data(file):
    sheets = pd.read_excel(file, sheet_name=None)
    restaurant = sheets.get("Restaurant Health", pd.DataFrame())
    partner = sheets.get("Delivery Partner Health", pd.DataFrame())
    customer = sheets.get("Customer Health", pd.DataFrame())
    return restaurant, partner, customer

def score_metric(value, metric_type):
    rules = {
        "commission": lambda v: max(0, min(100, 100 - (v - 20) * 5)),
        "churn": lambda v: max(0, min(100, 100 - v * 7)),
        "visibility": lambda v: max(0, min(100, 100 - (v - 30) * 1.5)),
        "ondc": lambda v: max(0, min(100, 100 - v * 2.5)),
        "satisfaction": lambda v: v,
        "eph": lambda v: max(0, min(100, (v / 130) * 100)),
        "utilisation": lambda v: v,
        "strike": lambda v: max(0, min(100, 100 - v * 18)),
        "attrition_p": lambda v: max(0, min(100, 100 - v * 5)),
        "orders": lambda v: max(0, min(100, (v / 6) * 100)),
        "sensitivity": lambda v: max(0, min(100, 100 - (v - 40) * 1.6)),
        "complaint": lambda v: max(0, min(100, 100 - v * 4)),
        "retention": lambda v: v,
        "gold": lambda v: min(100, v * 1.8),
    }
    fn = rules.get(metric_type)
    return round(fn(value)) if fn else 50

def get_status(score):
    if score >= 65:
        return "Healthy", "🟢", "#2E7D32"
    elif score >= 45:
        return "At Risk", "🟡", "#E65100"
    else:
        return "Critical", "🔴", "#B71C1C"

def compute_scores(df_r, df_p, df_c, city, month):
    r = df_r[(df_r["City"] == city) & (df_r["Month"] == month)]
    p = df_p[(df_p["City"] == city) & (df_p["Month"] == month)]
    c = df_c[(df_c["City"] == city) & (df_c["Month"] == month)]

    if r.empty or p.empty or c.empty:
        return None

    r = r.iloc[0]
    p = p.iloc[0]
    c = c.iloc[0]

    r_scores = {
        "Commission Rate": score_metric(r["Commission Rate (%)"], "commission"),
        "Monthly Churn": score_metric(r["Monthly Churn (%)"], "churn"),
        "Paid Visibility": score_metric(r["Paid Visibility Adoption (%)"], "visibility"),
        "ONDC Risk": score_metric(r["ONDC Overlap Risk (%)"], "ondc"),
        "Satisfaction": score_metric(r["Restaurant Satisfaction Score (/100)"], "satisfaction"),
    }
    p_scores = {
        "Earnings/Hr": score_metric(p["Avg Earnings Per Hour (₹)"], "eph"),
        "Active Ratio": score_metric(p["Active/Registered Ratio (%)"], "utilisation"),
        "Strike Incidents": score_metric(p["Strike Incidents (Quarter)"], "strike"),
        "Attrition": score_metric(p["Monthly Attrition (%)"], "attrition_p"),
    }
    c_scores = {
        "Order Frequency": score_metric(c["Avg Orders / Month"], "orders"),
        "Fee Sensitivity": score_metric(c["Platform Fee Sensitivity (%)"], "sensitivity"),
        "Complaint Rate": score_metric(c["Complaint Rate (per 1000 orders)"], "complaint"),
        "30-Day Retention": score_metric(c["30-Day Retention (%)"], "retention"),
        "Gold Membership": score_metric(c["Gold Membership (%)"], "gold"),
    }

    r_avg = round(sum(r_scores.values()) / len(r_scores))
    p_avg = round(sum(p_scores.values()) / len(p_scores))
    c_avg = round(sum(c_scores.values()) / len(c_scores))
    composite = round((r_avg + p_avg + c_avg) / 3)

    return {
        "composite": composite,
        "restaurant_score": r_avg,
        "partner_score": p_avg,
        "customer_score": c_avg,
        "r_scores": r_scores,
        "p_scores": p_scores,
        "c_scores": c_scores,
        "r_raw": r,
        "p_raw": p,
        "c_raw": c,
    }

def gauge_chart(score, title):
    color = "#2E7D32" if score >= 65 else "#E65100" if score >= 45 else "#B71C1C"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"size": 13, "color": "#555"}},
        number={"font": {"size": 28, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#ccc", "tickfont": {"size": 9}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 45], "color": "#FFEBEE"},
                {"range": [45, 65], "color": "#FFF8E1"},
                {"range": [65, 100], "color": "#E8F5E9"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.75, "value": score}
        }
    ))
    fig.update_layout(
        height=180, margin=dict(l=15, r=15, t=30, b=10),
        paper_bgcolor="white", font={"family": "Arial"}
    )
    return fig

def bar_scores(scores_dict, title):
    labels = list(scores_dict.keys())
    values = list(scores_dict.values())
    colors = ["#2E7D32" if v >= 65 else "#E65100" if v >= 45 else "#B71C1C" for v in values]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colors,
        text=[f"{v}" for v in values],
        textposition="outside",
        textfont={"size": 11}
    ))
    fig.update_layout(
        title={"text": title, "font": {"size": 13, "color": "#333"}},
        height=max(180, len(labels) * 38),
        xaxis={"range": [0, 110], "showgrid": False, "zeroline": False, "showticklabels": False},
        yaxis={"autorange": "reversed"},
        margin=dict(l=10, r=50, t=40, b=10),
        paper_bgcolor="white", plot_bgcolor="white",
        font={"family": "Arial", "size": 11}
    )
    return fig

def trend_chart(df_r, df_p, df_c, city, months):
    r_trend, p_trend, c_trend = [], [], []
    for m in months:
        s = compute_scores(df_r, df_p, df_c, city, m)
        if s:
            r_trend.append(s["restaurant_score"])
            p_trend.append(s["partner_score"])
            c_trend.append(s["customer_score"])
        else:
            r_trend.append(None)
            p_trend.append(None)
            c_trend.append(None)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=r_trend, name="Restaurant", line=dict(color=ZOMATO_RED, width=2.5), mode="lines+markers"))
    fig.add_trace(go.Scatter(x=months, y=p_trend, name="Delivery Partner", line=dict(color="#378ADD", width=2.5), mode="lines+markers"))
    fig.add_trace(go.Scatter(x=months, y=c_trend, name="Customer", line=dict(color="#1D9E75", width=2.5), mode="lines+markers"))
    fig.add_hrect(y0=0, y1=45, fillcolor="#FFEBEE", opacity=0.3, line_width=0)
    fig.add_hrect(y0=45, y1=65, fillcolor="#FFF8E1", opacity=0.3, line_width=0)
    fig.add_hrect(y0=65, y1=100, fillcolor="#E8F5E9", opacity=0.3, line_width=0)
    fig.update_layout(
        height=280,
        yaxis={"range": [0, 100], "title": "Health Score", "gridcolor": "#F0F0F0"},
        xaxis={"title": "Month"},
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white", plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font={"family": "Arial", "size": 11}
    )
    return fig

HARDCODED_INSIGHTS = {
    "Bangalore": [
        ("URGENT", "Commission rate at 31% is above the 28% threshold where restaurant churn accelerates — 8.4% monthly churn means ~340 restaurants lost per month at Bangalore's scale. Immediate commission review for restaurants below ₹50K monthly GMV is recommended."),
        ("URGENT", "Delivery partner attrition at 14–15%/month with 3–4 strike incidents per quarter signals earnings floor is being breached during non-peak hours. Introduce a guaranteed minimum of ₹90/hr during off-peak slots to stabilise supply."),
        ("WATCH", "ONDC overlap risk at 22–23% is concentrated in Koramangala and Indiranagar — Bangalore's highest-GMV corridors. Weekly listing parity monitoring and a restaurant loyalty programme for top 500 partners is critical to prevent migration."),
        ("STABLE", "Customer 30-day retention at 60–61% is holding but order frequency has dipped from 4.4 to 4.1 orders/month over 6 months. Gold membership deepening through a targeted re-engagement campaign for lapsed users (30–60 day gap) can recover 0.3–0.5 orders/month per user."),
    ],
    "Mumbai": [
        ("URGENT", "Mumbai is Zomato's most stressed market. Restaurant churn at 11.6%/month with 33.4% commission means the city is losing ~600+ restaurant partners monthly. Every 100 restaurants lost reduces GOV by approximately ₹1.2 crore/month at average Mumbai ticket size."),
        ("URGENT", "6 strike incidents per quarter with 20% partner attrition is operationally critical. Mumbai's traffic density makes supply shortfalls disproportionately expensive — each 10% supply drop increases average delivery time by 4–6 minutes, directly hurting reorder rates."),
        ("URGENT", "80% platform fee sensitivity means Mumbai customers are at the pricing ceiling. Any further fee increase risks a 12–15% order volume drop based on elasticity benchmarks from comparable markets. Freeze all fee increases in Mumbai for Q3."),
        ("WATCH", "31–32% ONDC overlap risk is the highest across all cities and rising. Prioritise Mumbai for a restructured commission model — lower base rate (26–27%) with a performance-linked visibility fee — to retain independent restaurant partners before ONDC incentives scale up."),
    ],
    "Delhi NCR": [
        ("STABLE", "Delhi NCR is Zomato's healthiest market with composite score above 65. Restaurant churn at 6.9% and commission at 29.2% reflect a near-optimal equilibrium. Protect this by avoiding commission increases in Delhi for at least 2 quarters."),
        ("STABLE", "Delivery partner earnings at ₹115/hr with zero strike incidents is a best-in-class benchmark. Active/registered ratio at 65% still has room to improve — a referral programme targeting 70% utilisation could add 800–1,000 active partners without incremental recruitment cost."),
        ("WATCH", "Customer order frequency at 5.2/month is the highest across cities but Gold membership at 50% suggests headroom. A Gold upgrade campaign targeting the 50% non-Gold high-frequency users (4+ orders/month) could increase subscription revenue by ₹8–10 crore annually in Delhi alone."),
        ("STABLE", "Use Delhi NCR as the test market for new restaurant partnership models — specifically performance-linked visibility fees in place of flat paid boosts. Delhi's healthy margins give restaurants the headroom to experiment without churn risk."),
    ],
    "Hyderabad": [
        ("WATCH", "Hyderabad shows flat health scores across all dimensions over 6 months — no acute crisis but zero momentum. Flat is dangerous in a competitive market because it signals Zomato is not compounding its position while Swiggy and ONDC are actively recruiting."),
        ("WATCH", "Customer fee sensitivity at 66% is a leading indicator of order frequency decline. Hyderabad's average order value is likely lower than Delhi and Mumbai — fee increases will hit order frequency faster here. Hold all platform fee changes and monitor closely."),
        ("WATCH", "Partner attrition at 12% with 2 strike incidents suggests latent earnings dissatisfaction not yet at crisis level. Proactively introduce a Hyderabad-specific EPH floor of ₹95/hr before it escalates to the Mumbai pattern."),
        ("STABLE", "ONDC risk at 19–20% is manageable. Offering Hyderabad restaurants a free analytics dashboard (order trends, peak hours, customer ratings) as a retention tool costs near zero and meaningfully increases switching cost away from Zomato."),
    ],
    "Pune": [
        ("STABLE", "Pune is Zomato's model market — zero strike incidents, 8% partner attrition, 28% commission, and 75% customer retention. This is the operational benchmark every other city should be measured against."),
        ("STABLE", "Restaurant churn at 6%/month with 28% commission suggests Pune operates near the efficiency frontier. Introduce a Pune-first pilot of a lower base commission (24–25%) with paid performance visibility to test whether take rate reduction improves GMV faster than it reduces margin."),
        ("WATCH", "Customer order frequency at 5.5/month is the highest across all cities. Opportunity to launch Zomato's first city-level premium subscription tier (above Gold) in Pune — a small, loyal, high-frequency base is the ideal test cohort."),
        ("STABLE", "Gold membership at 54% is strong. Focus on converting the remaining 46% through a time-limited Pune-exclusive offer. Every 10% Gold conversion increase in Pune adds approximately ₹2.5 crore in annual subscription revenue at current user base."),
    ],
}

def get_insights(city):
    return HARDCODED_INSIGHTS.get(city, [
        ("WATCH", "Insufficient data to generate city-specific insights. Ensure the Excel file contains data for this city."),
    ])

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<h1 style='color:{ZOMATO_RED};font-size:1.1rem;margin-bottom:0'>🍕 Zomato MHI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.75rem;color:#888;margin-top:0'>Marketplace Health Index</p>", unsafe_allow_html=True)
    st.divider()

    uploaded = st.file_uploader("Upload Excel file", type=["xlsx"], help="Upload the 3-sheet Zomato health data file")

    if uploaded:
        df_r, df_p, df_c = load_data(uploaded)
        cities = sorted(df_r["City"].unique().tolist())
        months = df_r["Month"].unique().tolist()

        selected_city = st.selectbox("City", cities)
        selected_month = st.selectbox("Month", months, index=len(months)-1)
        st.divider()
        st.markdown("<p style='font-size:0.75rem;color:#888'>Score guide</p>", unsafe_allow_html=True)
        st.markdown("🟢 **65–100** Healthy")
        st.markdown("🟡 **45–64** At Risk")
        st.markdown("🔴 **0–44** Critical")

# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown(f"<h1>Zomato Marketplace Health Index</h1>", unsafe_allow_html=True)

if not uploaded:
    st.info("Upload the Zomato Marketplace Health Data Excel file using the sidebar to get started.")
    st.markdown("**The file should contain 3 sheets:**")
    st.markdown("- `Restaurant Health` — commission, churn, ONDC risk, satisfaction")
    st.markdown("- `Delivery Partner Health` — EPH, utilisation, strikes, attrition")
    st.markdown("- `Customer Health` — order frequency, fee sensitivity, complaints, retention")
    st.stop()

scores = compute_scores(df_r, df_p, df_c, selected_city, selected_month)

if not scores:
    st.error(f"No data found for {selected_city} in {selected_month}.")
    st.stop()

status, icon, color = get_status(scores["composite"])

# ── Composite row ──────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1])
with col1:
    st.markdown(f"""
    <div class="score-box">
        <div style="font-size:0.75rem;color:#888;margin-bottom:4px">{selected_city} · {selected_month}</div>
        <div style="font-size:2.8rem;font-weight:700;color:{color};line-height:1">{scores['composite']}</div>
        <div style="font-size:0.75rem;color:#aaa;margin-bottom:6px">/ 100 composite</div>
        <div style="background:{color};color:white;border-radius:20px;padding:3px 12px;font-size:0.75rem;display:inline-block">{icon} {status}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    s, i, c = get_status(scores["restaurant_score"])
    st.markdown(f"""
    <div class="score-box">
        <div style="font-size:0.75rem;color:#888;margin-bottom:4px">Restaurant health</div>
        <div style="font-size:2rem;font-weight:600;color:{c}">{scores['restaurant_score']}</div>
        <div style="font-size:0.75rem;color:#aaa">{i} {s}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    s, i, c = get_status(scores["partner_score"])
    st.markdown(f"""
    <div class="score-box">
        <div style="font-size:0.75rem;color:#888;margin-bottom:4px">Partner health</div>
        <div style="font-size:2rem;font-weight:600;color:{c}">{scores['partner_score']}</div>
        <div style="font-size:0.75rem;color:#aaa">{i} {s}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    s, i, c = get_status(scores["customer_score"])
    st.markdown(f"""
    <div class="score-box">
        <div style="font-size:0.75rem;color:#888;margin-bottom:4px">Customer health</div>
        <div style="font-size:2rem;font-weight:600;color:{c}">{scores['customer_score']}</div>
        <div style="font-size:0.75rem;color:#aaa">{i} {s}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Gauges ─────────────────────────────────────────────────────────────────────
g1, g2, g3 = st.columns(3)
with g1:
    st.plotly_chart(gauge_chart(scores["restaurant_score"], "Restaurant Score"), use_container_width=True)
with g2:
    st.plotly_chart(gauge_chart(scores["partner_score"], "Partner Score"), use_container_width=True)
with g3:
    st.plotly_chart(gauge_chart(scores["customer_score"], "Customer Score"), use_container_width=True)

# ── Metric bars ────────────────────────────────────────────────────────────────
b1, b2, b3 = st.columns(3)
with b1:
    st.plotly_chart(bar_scores(scores["r_scores"], "Restaurant metrics"), use_container_width=True)
with b2:
    st.plotly_chart(bar_scores(scores["p_scores"], "Delivery partner metrics"), use_container_width=True)
with b3:
    st.plotly_chart(bar_scores(scores["c_scores"], "Customer metrics"), use_container_width=True)

# ── Raw data ───────────────────────────────────────────────────────────────────
with st.expander("Raw data — all metrics for selected city and month"):
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("**Restaurant**")
        r_row = df_r[(df_r["City"] == selected_city) & (df_r["Month"] == selected_month)].drop(columns=["City", "Month"])
        st.dataframe(r_row.T.rename(columns={r_row.index[0]: "Value"}), use_container_width=True)
    with t2:
        st.markdown("**Delivery partner**")
        p_row = df_p[(df_p["City"] == selected_city) & (df_p["Month"] == selected_month)].drop(columns=["City", "Month"])
        st.dataframe(p_row.T.rename(columns={p_row.index[0]: "Value"}), use_container_width=True)
    with t3:
        st.markdown("**Customer**")
        c_row = df_c[(df_c["City"] == selected_city) & (df_c["Month"] == selected_month)].drop(columns=["City", "Month"])
        st.dataframe(c_row.T.rename(columns={c_row.index[0]: "Value"}), use_container_width=True)

# ── Trend chart ────────────────────────────────────────────────────────────────
st.markdown("### Health score trend — all months")
st.plotly_chart(trend_chart(df_r, df_p, df_c, selected_city, months), use_container_width=True)

# ── City comparison ────────────────────────────────────────────────────────────
st.markdown("### City comparison — composite score")
city_scores = []
for city in cities:
    s = compute_scores(df_r, df_p, df_c, city, selected_month)
    if s:
        status_label, _, color = get_status(s["composite"])
        city_scores.append({"City": city, "Score": s["composite"], "Status": status_label})

if city_scores:
    df_city = pd.DataFrame(city_scores).sort_values("Score", ascending=True)
    colors = ["#2E7D32" if s >= 65 else "#E65100" if s >= 45 else "#B71C1C" for s in df_city["Score"]]
    fig = go.Figure(go.Bar(
        x=df_city["Score"], y=df_city["City"], orientation="h",
        marker_color=colors,
        text=[f"{s}" for s in df_city["Score"]],
        textposition="outside"
    ))
    fig.update_layout(
        height=220,
        xaxis={"range": [0, 110], "showgrid": False, "zeroline": False, "showticklabels": False},
        margin=dict(l=10, r=50, t=10, b=10),
        paper_bgcolor="white", plot_bgcolor="white",
        font={"family": "Arial", "size": 11}
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Insights ───────────────────────────────────────────────────────────────────
st.markdown("### Insight engine")
st.markdown(f"Prioritized recommendations for **{selected_city}** · **{selected_month}**")

city_insights = get_insights(selected_city)
for tag, text in city_insights:
    if tag == "URGENT":
        st.error(f"🔴 **URGENT** — {text}")
    elif tag == "WATCH":
        st.warning(f"🟡 **WATCH** — {text}")
    else:
        st.success(f"🟢 **STABLE** — {text}")

st.divider()
st.markdown("<p style='font-size:0.75rem;color:#aaa;text-align:center'>Zomato Marketplace Health Index · Demo prototype · Built by Somharsh</p>", unsafe_allow_html=True)
