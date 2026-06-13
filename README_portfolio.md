# 📈 Portfolio Tracker

A lightweight, high-performance, and **zero-dependency** Python script that reads trade transaction history or static portfolio holdings from CSV/text files, fetches real-time stock prices from Yahoo Finance, computes key portfolio metrics, and generates a formatted console report alongside a CSV export.

---

## 📋 Project Prompts & Core Request
This project was constructed and optimized based on the following task requirements:
> *"This is a trade file you have to understand the trade, if needed use python libraries like pandas and yfinance to read and to check todays stock price. Fetch live stock prices, calculate portfolio performance metrics, and generate a simple report. (Attention: make the code small and clean to be more optimized and clear.)"*
>
> *Note: In a subsequent iteration, the app was optimized to remove external dependencies like `pandas`, `numpy`, and `yfinance` to make it as lightweight, fast, and portable as possible, utilizing only standard libraries with direct API calls.*

---

## ⚡ Core Features

1. **Zero External Dependencies**: Powered entirely by the Python standard library. No packages to install, ensuring immediate execution and compatibility on any machine.
2. **Dual CSV Format Processing**:
   - **Transaction Log Format**: Detects and parses buy/sell history (buys and sells), groups by symbol, calculates net quantities, and computes the weighted average buy price.
   - **Static Holdings Format**: Detects static portfolio lists containing tickers, quantities, and direct buy prices.
3. **Lightweight Real-time Pricing**: Queries Yahoo Finance’s JSON endpoints via Python's native `urllib.request` library. It includes an automatic fallback for Indian exchanges (appending `.NS` to symbols) to cover domestic markets.
4. **Professional Console Reporting**: Outputs a beautifully aligned tabular report to the CLI displaying metrics including cost basis, current value, net P&L, percentage return, and portfolio weight.
5. **CSV Export**: Automatically exports the updated portfolio metrics to [portfolio_report.csv](file:///c:/Users/Abhishekh/OneDrive/Desktop/Portfolio_Tracker/portfolio_report.csv).

---

## 🛠️ Architecture & Optimization Decisions

To make the code **small, clean, optimized, and clear**, the following design decisions were made:
- **Removed Pandas & NumPy**: These libraries have large binary sizes and slow down python script startup. Standard library `csv` and basic list/dictionary comprehensions perform the aggregation in milliseconds.
- **Removed YFinance Library**: Rather than loading the bulky `yfinance` library (which depends on multiple sub-packages), the script queries Yahoo Finance chart endpoints directly via HTTP and extracts the `regularMarketPrice` from the JSON response.
- **Strict Error Handling**: Gracefully handles missing symbols, API timeouts, and division by zero. If a price cannot be fetched, it falls back to previous indicators or marks the current price as `-`.

---

## 🚀 How to Run

No installations are needed. Simply run the script using standard Python:

### 1. Default Run (using Sample Trade File)
```bash
python portfolio_report.py
```

### 2. Custom Input Run
Specify your own trade history or holdings file:
```bash
python portfolio_report.py "path/to/your/trades.csv"
```

---

## 📊 Supported Input Formats

### Format A: Transaction Log (e.g., [Sample Trade file.txt](file:///c:/Users/Abhishekh/OneDrive/Desktop/Portfolio_Tracker/Sample%20Trade%20file.txt))
This format records individual trade transactions. The script aggregates buys/sells automatically.
```csv
Symbol,Trade Type,Quantity,Price,Order Execution Time
APARINDS,Buy,7,10714.29,2024-01-10
RELIANCE,Buy,75,2333.33,2024-03-20
RELIANCE,Sell,10,2500.00,2024-06-01
```

### Format B: Static Portfolio (e.g., [trade_history.csv](file:///c:/Users/Abhishekh/OneDrive/Desktop/Portfolio_Tracker/trade_history.csv))
This format represents a snapshot of active holdings.
```csv
Ticker,Quantity,Price
AAPL,10,175.50
MSFT,5,350.20
```

---

## 📝 Example Output Preview

When run on a transaction file, the console prints:

```text
--- PORTFOLIO TRACKER REPORT ---
symbol    quantity  avg_buy_price  current_price  current_value  cost_basis         pnl  pnl_pct  allocation_pct
----------------------------------------------------------------------------------------------------------------
APARINDS         7      10,714.29      15,221.00     106,547.00   75,000.03   31,546.97   42.06%          46.80%
MEDANTA         30       1,200.00       1,235.10      37,053.00   36,000.00    1,053.00    2.93%          16.28%
RELIANCE        65       2,333.33       1,293.00      84,045.00  151,666.45  -67,621.45  -44.59%          36.92%

Total Cost Basis:    262,666.48
Total Current Value:  227,645.00
Total Net P&L:        -35,021.48 (-13.33%)
```

A spreadsheet-ready version is also written to `portfolio_report.csv`.
