import sys
import csv
import urllib.request
import json
import math
from typing import List, Dict, Any


def load_and_process_trades(path: str) -> List[Dict[str, Any]]:
    """Load trade history or portfolio CSV, standardizing columns and aggregating if needed."""
    try:
        with open(path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print(f"Error: File {path} has no headers.")
                sys.exit(1)

            # Normalize column names (strip spaces, lowercase)
            headers = [h.strip().lower() for h in reader.fieldnames if h is not None]

            rows = []
            for row in reader:
                norm_row = {}
                for k, v in row.items():
                    if k is not None:
                        norm_row[k.strip().lower()] = v.strip() if v is not None else ""
                rows.append(norm_row)
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        sys.exit(1)

    if not rows:
        return []

    columns = set(headers)
    is_static = ("ticker" in columns) or ("trade type" not in columns)

    holdings: List[Dict[str, Any]] = []

    if is_static:
        sym_col = "ticker" if "ticker" in columns else "symbol"
        qty_col = "quantity" if "quantity" in columns else "qty"
        price_col = "buy_price" if "buy_price" in columns else "price"

        if sym_col not in columns or qty_col not in columns or price_col not in columns:
            print("Portfolio CSV must contain ticker/symbol, quantity, and buy_price/price columns.")
            sys.exit(1)

        for row in rows:
            symbol = row[sym_col].strip().upper()
            if not symbol:
                continue

            try:
                quantity = float(row[qty_col]) if row[qty_col] else 0.0
            except ValueError:
                quantity = 0.0

            try:
                buy_price = float(row[price_col]) if row[price_col] else 0.0
            except ValueError:
                buy_price = 0.0

            if quantity > 0:
                holdings.append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "avg_buy_price": buy_price,
                    "cost_basis": quantity * buy_price,
                })
    else:
        req = {"symbol", "trade type", "quantity", "price"}
        if not req.issubset(columns):
            print("Trade history CSV must contain Symbol, Trade Type, Quantity, Price columns.")
            sys.exit(1)

        # Group by symbol
        symbol_groups: Dict[str, List[Dict[str, str]]] = {}
        for row in rows:
            symbol = row["symbol"].strip().upper()
            if not symbol:
                continue
            if symbol not in symbol_groups:
                symbol_groups[symbol] = []
            symbol_groups[symbol].append(row)

        for symbol, group in symbol_groups.items():
            total_buys_qty = 0.0
            total_buys_cost = 0.0
            total_sells_qty = 0.0

            for row in group:
                trade_type = row["trade type"].strip().lower()
                try:
                    qty = float(row["quantity"]) if row["quantity"] else 0.0
                except ValueError:
                    qty = 0.0
                try:
                    price = float(row["price"]) if row["price"] else 0.0
                except ValueError:
                    price = 0.0

                if trade_type in ("buy", "b"):
                    total_buys_qty += qty
                    total_buys_cost += qty * price
                elif trade_type in ("sell", "s"):
                    total_sells_qty += qty

            net_qty = total_buys_qty - total_sells_qty
            avg_buy_price = (total_buys_cost / total_buys_qty) if total_buys_qty > 0 else 0.0

            if net_qty > 0:
                holdings.append({
                    "symbol": symbol,
                    "quantity": net_qty,
                    "avg_buy_price": avg_buy_price,
                    "cost_basis": avg_buy_price * net_qty,
                })

    return holdings


def get_latest_price(symbol: str) -> float:
    """Fetch latest close price from Yahoo Finance with simple fallbacks."""
    for sym in [symbol, f"{symbol}.NS"]:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1d&interval=1d"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                results = data.get("chart", {}).get("result")
                if results and len(results) > 0:
                    meta = results[0].get("meta", {})
                    # Try regularMarketPrice
                    price = meta.get("regularMarketPrice")
                    if price is not None:
                        return float(price)
                    # Try chartPreviousClose
                    price = meta.get("chartPreviousClose")
                    if price is not None:
                        return float(price)
                    # Try indicators close
                    indicators = results[0].get("indicators", {})
                    quote = indicators.get("quote", [{}])[0]
                    closes = quote.get("close", [])
                    valid_closes = [c for c in closes if c is not None]
                    if valid_closes:
                        return float(valid_closes[-1])
        except Exception:
            pass
    return float("nan")


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "Sample Trade file.txt"
    holdings = load_and_process_trades(path)

    if not holdings:
        print("No active holdings found.")
        sys.exit(0)

    # Fetch live prices and compute report fields
    for item in holdings:
        current_price = get_latest_price(item["symbol"])
        item["current_price"] = current_price
        item["current_value"] = item["quantity"] * current_price
        item["pnl"] = item["current_value"] - item["cost_basis"]
        if item["cost_basis"] != 0:
            item["pnl_pct"] = (item["pnl"] / item["cost_basis"]) * 100
        else:
            item["pnl_pct"] = float("nan")

    # Calculate portfolio total current value
    total_val = sum(item["current_value"] for item in holdings if not math.isnan(item["current_value"]))

    # Calculate allocation percentage
    for item in holdings:
        if not math.isnan(item["current_value"]) and total_val > 0:
            item["allocation_pct"] = (item["current_value"] / total_val) * 100
        else:
            item["allocation_pct"] = 0.0

    # Write to CSV
    try:
        with open("portfolio_report.csv", mode="w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "symbol", "quantity", "avg_buy_price", "cost_basis",
                "current_price", "current_value", "pnl", "pnl_pct", "allocation_pct"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in holdings:
                csv_row = {}
                for field in fieldnames:
                    val = row.get(field, "")
                    if isinstance(val, float) and math.isnan(val):
                        csv_row[field] = ""
                    else:
                        csv_row[field] = val
                writer.writerow(csv_row)
    except Exception as e:
        print(f"Error writing CSV file: {e}")

    # Format copy for display
    display_rows = []
    for item in holdings:
        row = {}
        row["symbol"] = item["symbol"]

        qty = item["quantity"]
        row["quantity"] = f"{int(qty)}" if qty.is_integer() else f"{qty:,.2f}"

        for col in ["avg_buy_price", "current_price", "current_value", "cost_basis", "pnl"]:
            val = item.get(col)
            if val is not None and not math.isnan(val):
                row[col] = f"{val:,.2f}"
            else:
                row[col] = "-"

        for col in ["pnl_pct", "allocation_pct"]:
            val = item.get(col)
            if val is not None and not math.isnan(val):
                row[col] = f"{val:.2f}%"
            else:
                row[col] = "-"
        display_rows.append(row)

    # Print clean console table
    columns = [
        "symbol", "quantity", "avg_buy_price", "current_price",
        "current_value", "cost_basis", "pnl", "pnl_pct", "allocation_pct"
    ]

    # Calculate column widths dynamically to look beautifully aligned
    widths = {col: len(col) for col in columns}
    for row in display_rows:
        for col in columns:
            widths[col] = max(widths[col], len(row[col]))

    print("\n--- PORTFOLIO TRACKER REPORT ---")
    header_line = "  ".join(f"{col:<{widths[col]}}" if col == "symbol" else f"{col:>{widths[col]}}" for col in columns)
    print(header_line)
    print("-" * len(header_line))
    for row in display_rows:
        row_line = "  ".join(f"{row[col]:<{widths[col]}}" if col == "symbol" else f"{row[col]:>{widths[col]}}" for col in columns)
        print(row_line)

    # Print portfolio level summary metrics
    total_cost = sum(item["cost_basis"] for item in holdings)
    total_value = sum(item["current_value"] for item in holdings if not math.isnan(item["current_value"]))
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0
    print(f"\nTotal Cost Basis:    {total_cost:,.2f}")
    print(f"Total Current Value:  {total_value:,.2f}")
    print(f"Total Net P&L:        {total_pnl:,.2f} ({total_pnl_pct:.2f}%)\n")


if __name__ == "__main__":
    main()