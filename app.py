import warnings
warnings.filterwarnings("ignore")

import io
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import scipy.optimize as sco
import statsmodels.api as sm
import streamlit as st

# ============================================================
# PAGE & UI CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Institutional Quantitative Risk & Optimization Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #0b0e14; color: #e2e8f0; }
    .metric-card { 
        background: rgba(22, 27, 38, 0.75); 
        border: 1px solid rgba(255, 255, 255, 0.08); 
        border-radius: 12px; 
        padding: 16px 20px; 
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3); 
        backdrop-filter: blur(10px); 
        margin-bottom: 10px; 
    }
    .metric-title { 
        font-size: 0.8rem; 
        color: #94a3b8; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 0.5px; 
    }
    .metric-value { 
        font-size: 1.65rem; 
        font-weight: 700; 
        color: #f8fafc; 
        margin-top: 4px; 
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# SIDEBAR CONFIGURATION & DATA INPUT
# ============================================================
st.sidebar.title("⚡ Quantitative Controls")
st.sidebar.markdown("---")

input_method = st.sidebar.radio(
    "Select Input Method:", 
    ["Interactive Table", "Text Input", "Upload Excel / CSV"]
)

raw_records = []

if input_method == "Interactive Table":
    st.sidebar.markdown("**Edit Holdings Table:**")
    
    # Pre-cast dates to datetime to prevent StreamlitAPIException type errors
    default_df = pd.DataFrame([
        {"Ticker": "COST", "Amount": 9610.0, "PurchaseDate": "2021-01-15"},
        {"Ticker": "TSLA", "Amount": 9600.0, "PurchaseDate": "2022-03-10"},
        {"Ticker": "SOXL", "Amount": 9530.0, "PurchaseDate": "2023-01-05"},
        {"Ticker": "JPM",  "Amount": 6420.0, "PurchaseDate": "2020-05-20"},
        {"Ticker": "AON",  "Amount": 6400.0, "PurchaseDate": "2020-08-14"},
        {"Ticker": "MSFT", "Amount": 6410.0, "PurchaseDate": "2019-11-12"},
        {"Ticker": "NVDA", "Amount": 4810.0, "PurchaseDate": "2022-10-15"},
        {"Ticker": "AAPL", "Amount": 5000.0, "PurchaseDate": "2020-01-01"},
    ])
    default_df["PurchaseDate"] = pd.to_datetime(default_df["PurchaseDate"])

    edited_df = st.sidebar.data_editor(
        default_df,
        num_rows="dynamic",
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", help="Stock or ETF symbol (e.g., NVDA)", required=True),
            "Amount": st.column_config.NumberColumn("Dollar Amount ($)", min_value=0.0, format="$%.2f", required=True),
            "PurchaseDate": st.column_config.DateColumn("Date Bought", help="Purchase date for historical tracking")
        },
        use_container_width=True,
        key="holdings_editor"
    )

    for _, row in edited_df.dropna(subset=["Ticker", "Amount"]).iterrows():
        t_str = str(row["Ticker"]).strip().upper()
        if t_str and float(row["Amount"]) > 0:
            p_date = pd.to_datetime(row["PurchaseDate"]).strftime("%Y-%m-%d") if pd.notna(row["PurchaseDate"]) else "2020-01-01"
            raw_records.append({
                "Ticker": t_str,
                "Amount": float(row["Amount"]),
                "PurchaseDate": p_date
            })

elif input_method == "Text Input":
    default_text = """COST 9610 2021-01-15
TSLA 9600 2022-03-10
SOXL 9530 2023-01-05
JPM 6420 2020-05-20
AON 6400 2020-08-14
MSFT 6410 2019-11-12
NVDA 4810 2022-10-15
AAPL 5000 2020-01-01"""
    
    user_input = st.sidebar.text_area(
        "Enter Holdings (Flexible Format)",
        value=default_text.strip(),
        height=200,
        help="Paste from Excel or type lines as: TICKER AMOUNT [DATE]\nSupported separators: spaces, commas, tabs, or colons."
    )
    
    for line in user_input.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        clean_line = line.replace(",", " ").replace(":", " ").replace("\t", " ")
        parts = [p.strip() for p in clean_line.split() if p.strip()]
        
        if len(parts) >= 2:
            ticker = parts[0].upper()
            raw_amt = parts[1].replace("$", "").replace(",", "")
            try:
                amt = float(raw_amt)
                p_date = parts[2] if len(parts) >= 3 else "2020-01-01"
                raw_records.append({"Ticker": ticker, "Amount": amt, "PurchaseDate": p_date})
            except ValueError:
                continue

else:
    uploaded_file = st.sidebar.file_uploader("Upload Portfolio (.csv or .xlsx)", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            
            df_upload.columns = [str(c).strip().lower() for c in df_upload.columns]
            
            t_col = next((c for c in df_upload.columns if "tick" in c or "symbol" in c or "asset" in c), None)
            a_col = next((c for c in df_upload.columns if "amt" in c or "val" in c or "amount" in c or "cost" in c), None)
            d_col = next((c for c in df_upload.columns if "date" in c or "buy" in c or "purchase" in c), None)
            
            if t_col and a_col:
                for _, row in df_upload.iterrows():
                    ticker = str(row[t_col]).strip().upper()
                    amt = float(row[a_col])
                    p_date = str(row[d_col]).strip() if d_col and pd.notna(row[d_col]) else "2020-01-01"
                    if amt > 0:
                        raw_records.append({"Ticker": ticker, "Amount": amt, "PurchaseDate": p_date})
        except Exception as e:
            st.sidebar.error(f"Error parsing uploaded file: {e}")

# ============================================================
# DATA AGGREGATION & INITIALIZATION (PREVENTS NameError)
# ============================================================
if not raw_records:
    st.sidebar.error("Please provide valid holdings.")
    st.stop()

df_raw = pd.DataFrame(raw_records)
df_raw["PurchaseDate"] = pd.to_datetime(df_raw["PurchaseDate"], errors="coerce").fillna(pd.to_datetime("2020-01-01"))

holdings_df = df_raw.groupby("Ticker", as_index=False).agg({
    "Amount": "sum",
    "PurchaseDate": "min"
})

st.sidebar.markdown("---")
col_sb1, col_sb2 = st.sidebar.columns(2)
start_date = col_sb1.date_input("Analysis Start Date", pd.to_datetime("2018-01-01"))
benchmark_ticker = col_sb2.selectbox("Benchmark Ticker", ["SPY", "QQQ", "VT", "IWM", "AGG"], index=0)

risk_free_rate = st.sidebar.slider("Risk-Free Rate (%)", 0.0, 10.0, 4.0) / 100.0
confidence_level = st.sidebar.slider("VaR Confidence Level", 0.90, 0.99, 0.95, step=0.01)

st.sidebar.markdown("---")
st.sidebar.markdown("**Portfolio Optimization Constraints**")
opt_target = st.sidebar.selectbox("Optimization Objective", ["Maximum Sharpe Ratio", "Minimum Volatility", "Risk Parity (Equal Risk)"])
max_asset_weight = st.sidebar.slider("Max Single-Asset Weight Cap", 0.05, 1.00, 0.25, step=0.05)

st.sidebar.markdown("---")
st.sidebar.markdown("**Monte Carlo Controls**")
use_seed = st.sidebar.checkbox("Lock Simulation Seed", value=True)
seed_val = st.sidebar.number_input("Random Seed", min_value=0, value=42) if use_seed else None

# ============================================================
# MARKET DATA PIPELINE & TICKER VALIDATION
# ============================================================
@st.cache_data(ttl=3600)
def fetch_market_data(tickers, start_d, end_d):
    raw = yf.download(
        tickers=tickers, start=start_d, end=end_d, auto_adjust=True, progress=False, threads=True
    )
    if raw.empty:
        return pd.DataFrame()
        
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            prices = raw["Close"].copy()
        else:
            prices = raw.xs(raw.columns.get_level_values(0)[0], axis=1, level=0)
    else:
        prices = raw.copy()
        
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])
        
    return prices.sort_index().ffill(limit=5)

requested_tickers = list(holdings_df["Ticker"].unique())
all_download_tickers = list(dict.fromkeys(requested_tickers + [benchmark_ticker]))
end_date_str = datetime.today().strftime("%Y-%m-%d")

with st.spinner("Fetching historical market price data..."):
    prices = fetch_market_data(all_download_tickers, start_date.strftime("%Y-%m-%d"), end_date_str)

if prices.empty:
    st.error("Unable to retrieve market data. Please check ticker inputs.")
    st.stop()

valid_asset_tickers = [t for t in holdings_df["Ticker"] if t in prices.columns and not prices[t].dropna().empty]
missing_tickers = sorted(set(holdings_df["Ticker"]) - set(valid_asset_tickers))

if missing_tickers:
    st.warning(f"⚠️ Market data unavailable for asset(s): **{', '.join(missing_tickers)}**. Excluded from analysis.")

if not valid_asset_tickers:
    st.error("No valid asset tickers available for analysis.")
    st.stop()

holdings_df = holdings_df[holdings_df["Ticker"].isin(valid_asset_tickers)].copy()

analyzed_portfolio_value = holdings_df["Amount"].sum()
weights_series = holdings_df.set_index("Ticker")["Amount"] / analyzed_portfolio_value
n_assets = len(valid_asset_tickers)

# ============================================================
# TIME-VARYING PORTFOLIO RETURN COMPUTATION
# ============================================================
asset_returns = prices[valid_asset_tickers].pct_change()
benchmark_returns = prices[benchmark_ticker].pct_change()

active_weights = pd.DataFrame(0.0, index=asset_returns.index, columns=asset_returns.columns)

for _, row in holdings_df.iterrows():
    t_symbol = row["Ticker"]
    p_date = row["PurchaseDate"]
    active_weights.loc[active_weights.index >= p_date, t_symbol] = weights_series[t_symbol]

row_weight_sums = active_weights.sum(axis=1)
normalized_weights = active_weights.div(row_weight_sums.replace(0, np.nan), axis=0)

portfolio_returns = (asset_returns * normalized_weights).sum(axis=1, min_count=1).dropna()

combined = pd.DataFrame({"Portfolio": portfolio_returns, "Benchmark": benchmark_returns}).dropna()
port_ret = combined["Portfolio"]
bench_ret = combined["Benchmark"]

# ============================================================
# RISK COVARIANCE SAMPLE ALIGNMENT
# ============================================================
risk_returns = asset_returns.dropna(how="any")
trading_days = 252
cov_matrix_ann = risk_returns.cov() * trading_days
mean_rets = risk_returns.mean() * trading_days

# ============================================================
# QUANTITATIVE METRICS ENGINE
# ============================================================
elapsed_years = (port_ret.index[-1] - port_ret.index[0]).days / 365.25
total_return = (1 + port_ret).prod() - 1
cagr = ((1 + total_return) ** (1 / elapsed_years) - 1) if elapsed_years > 0 else np.nan

daily_rf = (1 + risk_free_rate) ** (1 / trading_days) - 1
excess_returns = port_ret - daily_rf

volatility = port_ret.std(ddof=1) * np.sqrt(trading_days)
sharpe_ratio = (excess_returns.mean() / excess_returns.std(ddof=1)) * np.sqrt(trading_days) if excess_returns.std(ddof=1) > 0 else np.nan

downside_excess = excess_returns[excess_returns < 0]
downside_deviation = np.sqrt(np.mean(downside_excess ** 2)) if len(downside_excess) > 0 else 1e-6
sortino_ratio = (excess_returns.mean() / downside_deviation) * np.sqrt(trading_days) if downside_deviation > 0 else np.nan

var_historical_pct = np.percentile(port_ret, (1 - confidence_level) * 100)
var_parametric_pct = stats.norm.ppf(1 - confidence_level, port_ret.mean(), port_ret.std(ddof=1))

dollar_var_historical = analyzed_portfolio_value * var_historical_pct
dollar_var_parametric = analyzed_portfolio_value * var_parametric_pct

cvar_historical_pct = port_ret[port_ret <= var_historical_pct].mean()
dollar_cvar_historical = analyzed_portfolio_value * cvar_historical_pct

X = sm.add_constant(bench_ret)
model = sm.OLS(port_ret, X).fit()
alpha_annual = model.params["const"] * trading_days
beta = model.params["Benchmark"]

# ============================================================
# UI HEADER & TOP KPI DASHBOARD
# ============================================================
st.title("🏛️ Institutional Quantitative Risk & Optimization Engine")
st.markdown(
    f"**Analyzed Portfolio Value:** `${analyzed_portfolio_value:,.2f}` | **Active Tickers:** `{len(holdings_df)}` | **Benchmark:** `{benchmark_ticker}`"
)

m1, m2, m3, m4, m5, m6 = st.columns(6)
kpis = [
    ("CAGR (Exact)", f"{cagr:.2%}"),
    ("Annual Volatility", f"{volatility:.2%}"),
    ("Sharpe Ratio", f"{sharpe_ratio:.2f}"),
    ("Sortino Ratio", f"{sortino_ratio:.2f}"),
    ("Daily VaR ($)", f"${abs(dollar_var_historical):,.2f}"),
    ("Alpha (Annual)", f"{alpha_annual:.2%}"),
]

for col, (label, val) in zip([m1, m2, m3, m4, m5, m6], kpis):
    col.markdown(
        f'<div class="metric-card"><div class="metric-title">{label}</div><div class="metric-value">{val}</div></div>',
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# TABS ARCHITECTURE
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📈 Holdings & Purchase Dates", 
    "📊 Performance & Allocations", 
    "⚠️ Tail Risk & $ VaR", 
    "⚖️ Euler Risk Decomposition",
    "🎲 Log-Normal Monte Carlo", 
    "📉 Crisis Stress Testing", 
    "⚡ Trade Plan & Optimization",
    "📡 Rolling Risk Monitor"
])

# ------------------------------------------------------------
# TAB 1: HOLDINGS & PURCHASE DATES
# ------------------------------------------------------------
with tab1:
    st.subheader("🗓️ Asset Acquisition Dates & Unrealized P&L")
    st.write("Performance computed dynamically from each asset's specific entry date:")

    holding_analysis = []
    for _, row in holdings_df.iterrows():
        t = row["Ticker"]
        amt = row["Amount"]
        p_date = row["PurchaseDate"]
        
        sub_p = prices[t].loc[prices.index >= p_date]
        if not sub_p.empty and len(sub_p) > 1:
            buy_price = sub_p.iloc[0]
            current_price = sub_p.iloc[-1]
            return_since_purchase = (current_price - buy_price) / buy_price
            current_val = amt * (1 + return_since_purchase)
            unrealized_pnl = current_val - amt
        else:
            buy_price = prices[t].iloc[-1]
            current_price = buy_price
            return_since_purchase = 0.0
            current_val = amt
            unrealized_pnl = 0.0

        holding_analysis.append({
            "Ticker": t,
            "Purchase Date": p_date.strftime("%Y-%m-%d"),
            "Initial Invested ($)": amt,
            "Est. Entry Price": buy_price,
            "Current Price": current_price,
            "Return Since Entry": return_since_purchase,
            "Current Value ($)": current_val,
            "Unrealized Gain ($)": unrealized_pnl
        })
    
    df_holdings_out = pd.DataFrame(holding_analysis)
    
    disp_h = df_holdings_out.copy()
    disp_h["Initial Invested ($)"] = disp_h["Initial Invested ($)"].map("${:,.2f}".format)
    disp_h["Est. Entry Price"] = disp_h["Est. Entry Price"].map("${:,.2f}".format)
    disp_h["Current Price"] = disp_h["Current Price"].map("${:,.2f}".format)
    disp_h["Return Since Entry"] = disp_h["Return Since Entry"].map("{:.2%}".format)
    disp_h["Current Value ($)"] = disp_h["Current Value ($)"].map("${:,.2f}".format)
    disp_h["Unrealized Gain ($)"] = disp_h["Unrealized Gain ($)"].map("${:,.2f}".format)
    
    st.dataframe(disp_h, use_container_width=True)

# ------------------------------------------------------------
# TAB 2: CUMULATIVE PERFORMANCE & CORRELATION
# ------------------------------------------------------------
with tab2:
    cum_port = (1 + port_ret).cumprod() - 1
    cum_bench = (1 + bench_ret).cumprod() - 1

    fig_perf = go.Figure()
    fig_perf.add_trace(go.Scatter(x=cum_port.index, y=cum_port, mode="lines", name="Portfolio (Time-Varying)", line=dict(color="#10B981", width=2)))
    fig_perf.add_trace(go.Scatter(x=cum_bench.index, y=cum_bench, mode="lines", name=f"Benchmark ({benchmark_ticker})", line=dict(color="#3B82F6", width=1.5, dash="dash")))
    fig_perf.update_layout(
        template="plotly_dark", title="Time-Weighted Cumulative Portfolio Growth vs Benchmark",
        xaxis_title="Date", yaxis_title="Cumulative Return", yaxis=dict(tickformat=".0%"), height=400
    )
    st.plotly_chart(fig_perf, use_container_width=True)

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        alloc_df = pd.DataFrame({
            "Ticker": weights_series.index, 
            "Dollar Value": weights_series.values * analyzed_portfolio_value
        })
        fig_pie = px.pie(
            alloc_df, values='Dollar Value', names='Ticker',
            title='Current Dollar Allocation Breakdown ($)', template='plotly_dark', hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_a2:
        corr_matrix = risk_returns.corr()
        fig_corr = px.imshow(
            corr_matrix, text_auto=".2f", aspect="auto",
            title="Asset Return Correlation Matrix", color_continuous_scale="Blues", template="plotly_dark"
        )
        st.plotly_chart(fig_corr, use_container_width=True)

# ------------------------------------------------------------
# TAB 3: TAIL RISK & DOLLAR VaR / CVaR
# ------------------------------------------------------------
with tab3:
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.subheader("Value at Risk (VaR) & Expected Shortfall (CVaR)")
        st.markdown(f"Confidence Level: **{confidence_level:.0%}** over a 1-day horizon.")
        
        st.markdown(f"* **Historical Daily VaR (%):** `{var_historical_pct:.2%}`")
        st.markdown(f"* **Historical Daily VaR ($):** :red[-${abs(dollar_var_historical):,.2f}]")
        st.markdown(f"* **Expected Shortfall / CVaR (%):** `{cvar_historical_pct:.2%}`")
        st.markdown(f"* **Expected Shortfall / CVaR ($):** :red[-${abs(dollar_cvar_historical):,.2f}]")
        st.markdown(f"* **Parametric Daily VaR ($):** :red[-${abs(dollar_var_parametric):,.2f}]")
        
        fig_dist = px.histogram(
            port_ret, nbins=60, title="Daily Return Distribution & Tail Loss Thresholds",
            labels={'value':'Daily Return'}, template="plotly_dark", color_discrete_sequence=['#3B82F6']
        )
        fig_dist.add_vline(x=var_historical_pct, line_dash="dash", line_color="#EF4444", annotation_text="Hist VaR")
        fig_dist.add_vline(x=cvar_historical_pct, line_dash="dash", line_color="#F59E0B", annotation_text="CVaR (Worst Tail)")
        st.plotly_chart(fig_dist, use_container_width=True)

    with col_v2:
        drawdown = (cum_port + 1) / (cum_port + 1).cummax() - 1
        max_dd = drawdown.min()
        max_dd_dollars = analyzed_portfolio_value * max_dd
        
        st.subheader("Portfolio Drawdown Analysis")
        st.markdown(f"* **Maximum Peak-to-Trough Drawdown (%):** `{max_dd:.2%}`")
        st.markdown(f"* **Maximum Peak-to-Trough Loss ($):** :red[-${abs(max_dd_dollars):,.2f}]")

        fig_dd = px.area(
            drawdown, title="Historical Drawdown Depth",
            labels={'value': 'Drawdown', 'index': 'Date'},
            template="plotly_dark", color_discrete_sequence=['#EF4444']
        )
        fig_dd.update_layout(yaxis=dict(tickformat=".0%"))
        st.plotly_chart(fig_dd, use_container_width=True)

# ------------------------------------------------------------
# TAB 4: EULER RISK DECOMPOSITION
# ------------------------------------------------------------
with tab4:
    st.subheader("⚖️ Euler Risk Attribution: Weight vs. Risk Contribution")
    st.markdown("Identifies assets generating disproportionate risk relative to their capital allocation.")

    w_vec = weights_series.values
    port_vol_calc = np.sqrt(np.dot(w_vec.T, np.dot(cov_matrix_ann, w_vec)))

    marginal_risk = np.dot(cov_matrix_ann, w_vec) / port_vol_calc
    component_risk = w_vec * marginal_risk
    pct_risk_contrib = component_risk / port_vol_calc

    risk_attr_df = pd.DataFrame({
        "Ticker": weights_series.index,
        "Portfolio Weight": weights_series.values,
        "Marginal Risk": marginal_risk,
        "Absolute Risk Contrib": component_risk,
        "% Risk Contribution": pct_risk_contrib
    }).sort_values(by="% Risk Contribution", ascending=False)

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=risk_attr_df["Ticker"], y=risk_attr_df["Portfolio Weight"], name="Capital Weight", marker_color="#3B82F6"))
        fig_comp.add_trace(go.Bar(x=risk_attr_df["Ticker"], y=risk_attr_df["% Risk Contribution"], name="% Risk Contribution", marker_color="#EF4444"))
        fig_comp.update_layout(
            barmode="group", template="plotly_dark",
            title="Capital Weight vs % Contribution to Total Volatility",
            yaxis=dict(tickformat=".0%"), height=420
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    with col_r2:
        formatted_risk_df = risk_attr_df.copy()
        formatted_risk_df["Portfolio Weight"] = formatted_risk_df["Portfolio Weight"].map("{:.2%}".format)
        formatted_risk_df["Marginal Risk"] = formatted_risk_df["Marginal Risk"].map("{:.2%}".format)
        formatted_risk_df["Absolute Risk Contrib"] = formatted_risk_df["Absolute Risk Contrib"].map("{:.2%}".format)
        formatted_risk_df["% Risk Contribution"] = formatted_risk_df["% Risk Contribution"].map("{:.2%}".format)
        
        st.markdown("### Risk Attribution Breakdown")
        st.dataframe(formatted_risk_df, use_container_width=True)

# ------------------------------------------------------------
# TAB 5: LOG-NORMAL MONTE CARLO SIMULATION
# ------------------------------------------------------------
with tab5:
    st.subheader("🎲 Log-Normal Geometric Monte Carlo Projection")
    col_mc1, col_mc2 = st.columns(2)
    sim_years = col_mc1.slider("Simulation Horizon (Years)", 1, 5, 1)
    n_sims = col_mc2.select_slider("Number of Simulations", options=[100, 250, 500, 1000], value=250)

    sim_days = sim_years * trading_days
    
    log_returns = np.log1p(port_ret)
    mu_log = log_returns.mean()
    sigma_log = log_returns.std(ddof=1)

    rng = np.random.default_rng(seed_val)
    random_log_returns = rng.normal(mu_log, sigma_log, size=(sim_days, n_sims))
    portfolio_paths = analyzed_portfolio_value * np.vstack([
        np.ones(n_sims),
        np.exp(np.cumsum(random_log_returns, axis=0))
    ])

    p10 = np.percentile(portfolio_paths[-1], 10)
    p50 = np.percentile(portfolio_paths[-1], 50)
    p90 = np.percentile(portfolio_paths[-1], 90)

    mc_cols1, mc_cols2, mc_cols3 = st.columns(3)
    mc_cols1.metric("10th Percentile (Bear Case)", f"${p10:,.2f}")
    mc_cols2.metric("50th Percentile (Median)", f"${p50:,.2f}")
    mc_cols3.metric("90th Percentile (Bull Case)", f"${p90:,.2f}")

    fig_mc = go.Figure()
    for i in range(min(n_sims, 100)):
        fig_mc.add_trace(go.Scatter(y=portfolio_paths[:, i], mode='lines', line=dict(width=0.8), opacity=0.25, showlegend=False))
    
    fig_mc.add_trace(go.Scatter(y=np.median(portfolio_paths, axis=1), mode='lines', name='Median Path', line=dict(color='#10B981', width=3)))
    fig_mc.update_layout(
        template="plotly_dark", title=f"{sim_years}-Year Log-Normal Capital Trails ({n_sims} Paths)",
        xaxis_title="Trading Days", yaxis_title="Portfolio Value ($)", height=450
    )
    st.plotly_chart(fig_mc, use_container_width=True)

# ------------------------------------------------------------
# TAB 6: CRISIS STRESS TESTING
# ------------------------------------------------------------
with tab6:
    st.subheader("📉 Historical Crisis Scenario Stress Testing")
    st.markdown(
        "Evaluate how your current portfolio weights would hold up during major market panics, "
        "including recent crises (using exact asset price data) and historic crashes like **Black Tuesday**."
    )

    recent_crises = {
        "2020 COVID-19 Crash": ("2020-02-19", "2020-03-23"),
        "2022 Tech / Inflation Selloff": ("2022-01-03", "2022-10-12"),
        "2008 Global Financial Crisis": ("2007-10-09", "2009-03-09"),
        "2023 Regional Banking Panic": ("2023-03-08", "2023-05-04")
    }

    stress_results = []

    for crisis_name, (c_start, c_end) in recent_crises.items():
        buffer_start = (pd.to_datetime(c_start) - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
        sub_prices = fetch_market_data(valid_asset_tickers, buffer_start, c_end)
        
        if not sub_prices.empty:
            available_assets = [t for t in valid_asset_tickers if t in sub_prices.columns]
            sub_prices = sub_prices[available_assets].ffill().bfill()
            
            crisis_prices = sub_prices.loc[(sub_prices.index >= c_start) & (sub_prices.index <= c_end)]
            
            if len(crisis_prices) >= 2:
                start_prices = crisis_prices.iloc[0]
                end_prices = crisis_prices.iloc[-1]
                
                asset_crisis_returns = (end_prices - start_prices) / start_prices
                
                sub_w = weights_series.reindex(available_assets).fillna(0)
                if sub_w.sum() > 0:
                    sub_w = sub_w / sub_w.sum()
                
                cum_crisis_return = np.dot(asset_crisis_returns.values, sub_w.values)
                dollar_impact = analyzed_portfolio_value * cum_crisis_return
                
                stress_results.append({
                    "Crisis Scenario": crisis_name,
                    "Period / Method": f"{c_start} to {c_end}",
                    "Type": "Historical Prices",
                    "Portfolio Return": cum_crisis_return,
                    "Estimated $ Impact": dollar_impact
                })

    benchmark_crises = [
        {
            "Scenario": "1929 Black Tuesday / Great Depression",
            "Period": "1929 - 1932",
            "Market Shock": -0.861
        },
        {
            "Scenario": "1987 Black Monday Single-Day Crash",
            "Period": "Oct 19, 1987",
            "Market Shock": -0.205
        }
    ]

    for b_crisis in benchmark_crises:
        adj_beta = max(0.5, min(beta, 2.5)) if 'beta' in locals() and not np.isnan(beta) else 1.0
        simulated_return = max(-0.9999, b_crisis["Market Shock"] * adj_beta)
        dollar_impact = analyzed_portfolio_value * simulated_return

        stress_results.append({
            "Crisis Scenario": b_crisis["Scenario"],
            "Period / Method": f"{b_crisis['Period']} (Beta: {adj_beta:.2f})",
            "Type": "Beta Simulation",
            "Portfolio Return": simulated_return,
            "Estimated $ Impact": dollar_impact
        })

    if stress_results:
        df_stress = pd.DataFrame(stress_results)
        
        disp_stress = df_stress.copy()
        disp_stress["Portfolio Return"] = disp_stress["Portfolio Return"].map("{:.2%}".format)
        disp_stress["Estimated $ Impact"] = disp_stress["Estimated $ Impact"].map("${:,.2f}".format)
        
        st.dataframe(disp_stress, use_container_width=True)

        fig_stress = px.bar(
            df_stress,
            x="Crisis Scenario",
            y="Portfolio Return",
            color="Type",
            title="Portfolio Drawdown Comparison Across Major Economic Crises",
            labels={"Portfolio Return": "Simulated Portfolio Return (%)"},
            template="plotly_dark",
            color_discrete_map={"Historical Prices": "#EF4444", "Beta Simulation": "#F59E0B"}
        )
        fig_stress.update_layout(yaxis=dict(tickformat=".0%"))
        st.plotly_chart(fig_stress, use_container_width=True)
    else:
        st.warning("Could not compute stress test results.")

# ------------------------------------------------------------
# TAB 7: REBALANCING PLAN & DETAILED EXECUTIVE AUDIT
# ------------------------------------------------------------
with tab7:
    st.subheader(f"⚡ Portfolio Optimization ({opt_target})")
    
    min_feasible_cap = 1.0 / n_assets
    if max_asset_weight < min_feasible_cap:
        st.error(
            f"**Optimization Infeasible:** With {n_assets} assets, the single-asset weight cap "
            f"must be at least **{min_feasible_cap:.1%}** to sum to 100%. "
            f"Please increase the cap slider in the sidebar."
        )
    else:
        def calc_port_stats(w):
            ret = np.sum(mean_rets * w)
            vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix_ann, w)))
            return ret, vol

        bounds = tuple((0.0, max_asset_weight) for _ in range(n_assets))
        init_guess = np.array([1.0 / n_assets] * n_assets)
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})

        if opt_target == "Maximum Sharpe Ratio":
            def objective(w):
                r, v = calc_port_stats(w)
                return -(r - risk_free_rate) / v if v > 0 else 0
        elif opt_target == "Minimum Volatility":
            def objective(w):
                return calc_port_stats(w)[1]
        else:  # Risk Parity
            def objective(w):
                v = np.sqrt(np.dot(w.T, np.dot(cov_matrix_ann, w)))
                m_risk = np.dot(cov_matrix_ann, w) / v
                c_risk = w * m_risk
                target_risk = v / n_assets
                return np.sum((c_risk - target_risk)**2)

        opt_res = sco.minimize(objective, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if opt_res.success:
            opt_weights = opt_res.x
            opt_ret, opt_vol = calc_port_stats(opt_weights)
            opt_sharpe = (opt_ret - risk_free_rate) / opt_vol if opt_vol > 0 else np.nan

            o_col1, o_col2, o_col3 = st.columns(3)
            o_col1.metric("Optimized Expected Return", f"{opt_ret:.2%}", f"{opt_ret - cagr:+.2%} vs current")
            o_col2.metric("Optimized Volatility", f"{opt_vol:.2%}", f"{opt_vol - volatility:+.2%} vs current")
            o_col3.metric("Optimized Sharpe", f"{opt_sharpe:.2f}", f"{opt_sharpe - sharpe_ratio:+.2f} vs current")

            latest_prices = prices[weights_series.index].iloc[-1]

            rebal_df = pd.DataFrame({
                "Ticker": weights_series.index,
                "Latest Price": latest_prices.values,
                "Current $ Value": weights_series.values * analyzed_portfolio_value,
                "Optimal $ Target": opt_weights * analyzed_portfolio_value,
            })

            rebal_df["Trade $ Amount"] = rebal_df["Optimal $ Target"] - rebal_df["Current $ Value"]
            rebal_df["Action"] = rebal_df["Trade $ Amount"].apply(lambda x: "BUY" if x > 0.01 else ("SELL" if x < -0.01 else "HOLD"))
            rebal_df["Estimated Shares"] = (rebal_df["Trade $ Amount"].abs() / rebal_df["Latest Price"]).round(2)

            display_df = rebal_df.copy()
            display_df["Latest Price"] = display_df["Latest Price"].map("${:,.2f}".format)
            display_df["Current $ Value"] = display_df["Current $ Value"].map("${:,.2f}".format)
            display_df["Optimal $ Target"] = display_df["Optimal $ Target"].map("${:,.2f}".format)
            display_df["Trade $ Amount"] = display_df["Trade $ Amount"].map("${:,.2f}".format)

            st.markdown(f"### Actionable Trade Order Plan (Capped at {max_asset_weight:.0%} Max Weight)")
            st.dataframe(display_df, use_container_width=True)

            csv_buffer = io.StringIO()
            rebal_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Export Rebalancing Orders (CSV)",
                data=csv_buffer.getvalue(),
                file_name="portfolio_rebalancing_plan.csv",
                mime="text/csv"
            )

    st.markdown("---")
    st.subheader("📝 Comprehensive Quantitative Executive Audit")
    
    top_3_pct = weights_series.nlargest(3).sum()
    max_asset = weights_series.idxmax()
    max_asset_pct = weights_series.max()

    top_risk_asset = risk_attr_df.iloc[0]["Ticker"]
    top_risk_pct = risk_attr_df.iloc[0]["% Risk Contribution"]
    hhi = (weights_series ** 2).sum()

    st.markdown(f"""
    #### **1. Capital Structure & Concentration Profile**
    * **Active Portfolio Allocation:** Total capital of **${analyzed_portfolio_value:,.2f}** is distributed across **{len(holdings_df)}** validated assets.
    * **Single Position Concentration:** **{max_asset}** forms the largest allocation at **{max_asset_pct:.2%}** of capital (${weights_series.max() * analyzed_portfolio_value:,.2f}).
    * **Top-3 Asset Concentration:** Top 3 positions aggregate to **{top_3_pct:.2%}** of total capital.
    * **Herfindahl-Hirschman Index (HHI):** Portfolio HHI stands at **{hhi:.4f}**, where values above 0.18 indicate moderate-to-high concentration risk.

    #### **2. Risk Decomposition & Risk-Adjusted Return Profile**
    * **Return Drivers:** The portfolio achieved an annualized CAGR of **{cagr:.2%}** with an annualized volatility of **{volatility:.2%}**.
    * **Sharpe & Sortino Ratios:** Risk-adjusted efficiency shows a Sharpe ratio of **{sharpe_ratio:.2f}** and a Sortino ratio of **{sortino_ratio:.2f}**, demonstrating strong downside return asymmetric protection.
    * **Dominant Risk Driver:** **{top_risk_asset}** represents the single largest contributor to overall portfolio volatility at **{top_risk_pct:.2%}** risk contribution.

    #### **3. Tail Risk & Capital Preservation**
    * **Daily Value at Risk (95% Conf.):** On any given trading day, there is a 5% statistical probability that portfolio losses exceed **{var_historical_pct:.2%}** (**${abs(dollar_var_historical):,.2f}**).
    * **Conditional Value at Risk (Expected Shortfall):** In the average bad day beyond the VaR threshold, expected tail losses average **{cvar_historical_pct:.2%}** (**${abs(dollar_cvar_historical):,.2f}**).
    * **Peak Historical Drawdown:** Maximum drawdown experienced over the window reached **{max_dd:.2%}** (**-${abs(max_dd_dollars):,.2f}**).

    #### **4. Strategic Rebalancing Guidance**
    * Under the selected **{opt_target}** framework (capped at **{max_asset_weight:.0%}** max single-asset allocation), executing the trade plan reduces concentration risk while targeting an optimized return profile.
    """)

# ------------------------------------------------------------
# TAB 8: ROLLING DYNAMIC MONITORING
# ------------------------------------------------------------
with tab8:
    st.subheader("📡 Dynamic Regime & Rolling Metric Tracking")
    rolling_window = st.slider("Rolling Window Size (Trading Days)", 20, 252, 63)

    rolling_vol = port_ret.rolling(rolling_window).std() * np.sqrt(trading_days)
    rolling_excess = port_ret - daily_rf
    rolling_sharpe = (rolling_excess.rolling(rolling_window).mean() / port_ret.rolling(rolling_window).std()) * np.sqrt(trading_days)

    fig_roll_vol = px.line(rolling_vol, title=f"Rolling {rolling_window}-Day Annualized Volatility", labels={'value': 'Volatility'}, template="plotly_dark")
    fig_roll_vol.update_layout(yaxis=dict(tickformat=".0%"))
    st.plotly_chart(fig_roll_vol, use_container_width=True)

    fig_roll_sharpe = px.line(rolling_sharpe, title=f"Rolling {rolling_window}-Day Sharpe Ratio", labels={'value': 'Sharpe Ratio'}, template="plotly_dark")
    st.plotly_chart(fig_roll_sharpe, use_container_width=True)