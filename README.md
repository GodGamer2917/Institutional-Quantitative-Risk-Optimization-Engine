# Portfolio-Risk-Analyzer

````markdown
# ⚡ Institutional Quantitative Risk & Optimization Engine

> An interactive quantitative portfolio analytics platform for analyzing portfolio performance, measuring risk, stress-testing historical scenarios, and generating constrained portfolio optimization strategies.

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Interactive_App-red.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

---

## 📌 Overview

The **Institutional Quantitative Risk & Optimization Engine** is a Python-based interactive application designed to consolidate portfolio analytics, quantitative risk measurement, scenario analysis, and portfolio optimization into a single decision-support platform.

Users can enter portfolio holdings manually or upload them through CSV/Excel files. The application retrieves historical market data and evaluates the portfolio using a range of quantitative techniques, including:

- Portfolio performance analysis
- Risk-adjusted return metrics
- Value at Risk (VaR) and Expected Shortfall
- Maximum drawdown analysis
- CAPM alpha and beta estimation
- Asset correlation analysis
- Euler risk decomposition
- Monte Carlo simulation
- Historical crisis stress testing
- Constrained portfolio optimization
- Rolling risk and performance monitoring

The goal is to provide a more comprehensive view of portfolio behavior than simple return tracking alone.

---

# 🖥️ Dashboard Architecture

The application is organized into eight major analytical modules:

### 1. 📈 Holdings & Purchase Dates
Analyzes each portfolio position individually using its specified acquisition date.

Features include:

- Estimated entry price
- Current market price
- Return since entry
- Estimated current value
- Unrealized gain or loss

---

### 2. 📊 Performance & Allocations

Evaluates historical portfolio performance relative to a user-selected benchmark.

Includes:

- Time-weighted cumulative portfolio growth
- Benchmark comparison
- Portfolio allocation visualization
- Asset return correlation matrix

Available benchmarks include:

- SPY
- QQQ
- VT
- IWM
- AGG

---

### 3. ⚠️ Tail Risk & Value at Risk

Measures potential portfolio losses under adverse market conditions.

The engine calculates:

#### Historical Value at Risk

Historical VaR estimates the loss threshold based on the empirical distribution of observed portfolio returns.

\[
VaR_{\alpha} = Q_{1-\alpha}(R)
\]

where \(Q\) represents the relevant return quantile.

#### Parametric Value at Risk

Parametric VaR assumes returns follow a normal distribution:

\[
VaR_{\alpha} =
\mu + \sigma \Phi^{-1}(1-\alpha)
\]

where:

- \(\mu\) = mean return
- \(\sigma\) = return volatility
- \(\Phi^{-1}\) = inverse standard normal distribution

#### Conditional Value at Risk / Expected Shortfall

Expected Shortfall estimates the average loss experienced beyond the VaR threshold.

The module also evaluates:

- Maximum historical drawdown
- Peak-to-trough losses
- Historical return distributions
- Tail-loss thresholds

---

### 4. ⚖️ Euler Risk Decomposition

Portfolio volatility is decomposed to identify how much each asset contributes to total portfolio risk.

Portfolio volatility is calculated as:

\[
\sigma_p = \sqrt{w^T \Sigma w}
\]

where:

- \(w\) = portfolio weight vector
- \(\Sigma\) = annualized covariance matrix

Marginal risk contribution:

\[
MRC_i =
\frac{(\Sigma w)_i}{\sigma_p}
\]

Component risk contribution:

\[
CRC_i = w_i \cdot MRC_i
\]

This allows the platform to compare:

- Capital allocation
- Marginal risk
- Absolute risk contribution
- Percentage contribution to total portfolio volatility

This can identify positions that generate disproportionate risk relative to their portfolio weight.

---

### 5. 🎲 Log-Normal Monte Carlo Simulation

The engine projects potential future portfolio paths using simulated log returns.

Daily log returns are modeled as:

\[
r_t \sim \mathcal{N}(\mu,\sigma^2)
\]

Simulated portfolio values are generated using geometric compounding:

\[
V_t =
V_0 \times
e^{\sum_{i=1}^{t}r_i}
\]

Users can adjust:

- Simulation horizon
- Number of simulations
- Random seed

The output includes:

- 10th percentile terminal value
- Median terminal value
- 90th percentile terminal value
- Individual simulated capital paths

---

### 6. 📉 Historical Crisis Stress Testing

The portfolio is tested against historical market stress periods.

Current scenarios include:

| Scenario | Period |
|---|---|
| 2020 COVID Crash | February 19, 2020 – March 23, 2020 |
| 2022 Tech / Rate Hike Selloff | January 3, 2022 – October 12, 2022 |
| 2023 Regional Banking Panic | March 8, 2023 – May 4, 2023 |

For each scenario, the engine estimates:

- Portfolio return during the period
- Estimated dollar impact
- Historical downside exposure

---

### 7. ⚡ Portfolio Optimization & Trade Planning

The application uses constrained numerical optimization to generate alternative portfolio allocations.

Optimization is performed using `scipy.optimize` with:

- Long-only constraints
- Full-investment constraint
- User-defined maximum position weights

### Available Optimization Objectives

#### Maximum Sharpe Ratio

Maximizes:

\[
\frac{R_p - R_f}{\sigma_p}
\]

#### Minimum Volatility

Minimizes:

\[
\sigma_p =
\sqrt{w^T \Sigma w}
\]

#### Risk Parity

Attempts to equalize component contributions to portfolio volatility.

The application then generates an actionable rebalancing plan containing:

- Current allocation
- Optimized target allocation
- Dollar amount to buy or sell
- Estimated shares required
- BUY / SELL / HOLD classification

Rebalancing orders can also be exported as a CSV file.

---

### 8. 📡 Rolling Risk Monitoring

Risk is monitored dynamically using rolling windows.

Current metrics include:

- Rolling annualized volatility
- Rolling Sharpe ratio

This allows users to observe how the portfolio's risk and risk-adjusted performance change across different market environments.

---

# 📊 Core Quantitative Metrics

The dashboard calculates several portfolio-level performance metrics.

### CAGR

Compound Annual Growth Rate:

\[
CAGR =
\left(
\frac{V_f}{V_i}
\right)^{1/n}
-1
\]

### Annualized Volatility

\[
\sigma_{annual}
=
\sigma_{daily}\sqrt{252}
\]

### Sharpe Ratio

\[
Sharpe =
\frac{E[R_p-R_f]}
{\sigma(R_p-R_f)}
\sqrt{252}
\]

### Sortino Ratio

The Sortino ratio evaluates return relative to downside volatility:

\[
Sortino =
\frac{E[R_p-R_f]}
{\sigma_{downside}}
\sqrt{252}
\]

### CAPM Alpha and Beta

Portfolio returns are modeled against benchmark returns using ordinary least squares regression:

\[
R_p =
\alpha +
\beta R_b +
\epsilon
\]

where:

- \(\alpha\) = abnormal return relative to the benchmark
- \(\beta\) = systematic market sensitivity
- \(R_b\) = benchmark return

---

# ⚙️ Portfolio Input

Holdings can be entered manually using the following format:

```text
TICKER: AMOUNT: PURCHASE_DATE
````

Example:

```text
AAPL: 5000: 2023-01-15
MSFT: 3500: 2022-06-10
NVDA: 2500: 2024-02-01
```

The application also supports CSV and Excel portfolio uploads.

Uploaded data should contain identifiable columns for:

* Ticker or Symbol
* Amount or Value
* Purchase Date

Duplicate ticker entries are automatically aggregated.

---

# 🧠 Methodology

Historical adjusted market prices are retrieved for portfolio assets and the selected benchmark.

Daily returns are calculated as:

[
R_t =
\frac{P_t-P_{t-1}}
{P_{t-1}}
]

Portfolio-level returns are constructed using dynamically activated portfolio weights based on specified asset acquisition dates.

The risk engine uses an annualized covariance matrix based on historical daily returns:

[
\Sigma_{annual}
===============

252\Sigma_{daily}
]

This covariance structure is used throughout the application for:

* Portfolio volatility
* Risk attribution
* Correlation analysis
* Portfolio optimization

Risk and performance metrics are calculated using approximately 252 trading days per year.

---

# 🛠️ Technology Stack

| Technology  | Purpose                                            |
| ----------- | -------------------------------------------------- |
| Python      | Core application logic                             |
| Streamlit   | Interactive web application framework              |
| Pandas      | Data manipulation and analysis                     |
| NumPy       | Numerical computation                              |
| yfinance    | Historical market data retrieval                   |
| SciPy       | Statistical functions and constrained optimization |
| Statsmodels | CAPM regression analysis                           |
| Plotly      | Interactive data visualization                     |
| OpenPyXL    | Excel file support                                 |

---

# 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/quantitative-risk-optimization-engine.git
```

### 2. Navigate to the project directory

```bash
cd quantitative-risk-optimization-engine
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

---

# 📦 Requirements

Create a `requirements.txt` file containing:

```text
streamlit
pandas
numpy
yfinance
plotly
scipy
statsmodels
openpyxl
```

---

# 🎯 Project Objectives

This project was developed to explore the intersection of:

* Finance
* Statistics
* Portfolio theory
* Risk management
* Data analysis
* Optimization
* Python software development

Rather than focusing exclusively on portfolio returns, the application examines multiple dimensions of investment decision-making, including **risk concentration, downside exposure, historical stress performance, correlation, and risk-adjusted optimization**.

---

# ⚠️ Limitations & Disclaimer

This project is intended for **educational and analytical purposes only**.

The application relies on historical market data and statistical models that may not accurately predict future market behavior. Monte Carlo simulations, Value at Risk estimates, optimization outputs, and historical stress tests are model-based analytical tools rather than guarantees of future performance.

This application does **not** provide financial, investment, or trading advice.

Users should independently evaluate assumptions, data quality, transaction costs, taxes, liquidity constraints, and other real-world factors before making investment decisions.

---

# 🔮 Potential Future Development

Potential areas for future expansion include:

* Transaction cost modeling
* Tax-aware optimization
* Multi-factor asset pricing models
* Black-Litterman portfolio optimization
* GARCH volatility modeling
* Bootstrap-based Monte Carlo simulation
* Rolling beta and alpha estimation
* Factor exposure analysis
* Additional historical crisis scenarios
* Portfolio comparison tools
* Live portfolio value integration

---

## Author

**Manav Amin**

Student interested in the intersection of **finance, quantitative analysis, data science, and technology**.

---

### ⚡ Built with Python + Streamlit

```

This is **substantially more polished than the average student GitHub README**. The biggest thing I would do next is add **real screenshots near the top**—that will make someone opening the repository immediately see that this isn't just a wall of code. 
```
