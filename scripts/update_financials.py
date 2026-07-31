"""
update_financials.py — Refresh financial tables in ticker reports.

Fetches latest annual (3yr) and quarterly (4Q) data from yfinance,
then replaces ONLY the ## 財務概況 section in each report file.
All enrichment content (業務簡介, 供應鏈, 客戶供應商) is preserved.

Usage:
  python scripts/update_financials.py                  # Update ALL tickers
  python scripts/update_financials.py 2330             # Single ticker
  python scripts/update_financials.py 2330 2317 3034   # Multiple tickers
  python scripts/update_financials.py --batch 101      # All tickers in a batch
  python scripts/update_financials.py --sector Semiconductors  # Entire sector
  python scripts/update_financials.py --dry-run 2330   # Preview without writing

Units: 百萬台幣 (Million NTD). Margins in %.
"""

import os
import re
import sys
import time

import pandas as pd
import yfinance as yf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    find_ticker_files, parse_scope_args, setup_stdout,
    fetch_valuation_data, build_valuation_table, update_metadata,
)

# Financial metrics to extract
METRICS_KEYS = {
    "revenue": ["Total Revenue"],
    "gross_profit": ["Gross Profit"],
    "selling_exp": ["Selling And Marketing Expense"],
    "rd_exp": ["Research And Development"],
    "admin_exp": ["General And Administrative Expense"],
    "operating_income": ["Operating Income"],
    "net_income": ["Net Income", "Net Income Common Stockholders"],
    "ocf": ["Operating Cash Flow", "Total Cash From Operating Activities"],
    "icf": ["Investing Cash Flow", "Total Cashflows From Investing Activities"],
    "fcf": ["Financing Cash Flow", "Total Cash From Financing Activities"],
    "capex": ["Capital Expenditure", "Capital Expenditures"],
}


def get_series(df, keys):
    for key in keys:
        if key in df.index:
            return df.loc[key]
    return pd.Series(dtype=float)


def calc_margin(numerator, denominator):
    if denominator.empty or numerator.empty:
        return pd.Series(dtype=float)
    result = (numerator / denominator) * 100
    result = result.replace([float("inf"), float("-inf")], float("nan"))
    return result


def calc_admin_exp(income_stmt):
    """Get G&A expense, falling back to SGA - Selling if G&A is missing."""
    admin = get_series(income_stmt, METRICS_KEYS["admin_exp"])
    selling = get_series(income_stmt, METRICS_KEYS["selling_exp"])
    sga = get_series(income_stmt, ["Selling General And Administration"])

    if admin.empty and not sga.empty and not selling.empty:
        # Derive G&A = SGA - Selling
        return sga - selling
    elif not admin.empty and not sga.empty:
        # Fill NaN gaps in G&A from SGA - Selling
        derived = sga - selling
        return admin.fillna(derived)
    return admin


def extract_metrics(income_stmt, cashflow):
    if income_stmt.empty and cashflow.empty:
        return pd.DataFrame()

    data = {
        "Revenue": get_series(income_stmt, METRICS_KEYS["revenue"]),
        "Gross Profit": get_series(income_stmt, METRICS_KEYS["gross_profit"]),
        "Gross Margin (%)": calc_margin(
            get_series(income_stmt, METRICS_KEYS["gross_profit"]),
            get_series(income_stmt, METRICS_KEYS["revenue"]),
        ),
        "Selling & Marketing Exp": get_series(income_stmt, METRICS_KEYS["selling_exp"]),
        "R&D Exp": get_series(income_stmt, METRICS_KEYS["rd_exp"]),
        "General & Admin Exp": calc_admin_exp(income_stmt),
        "Operating Income": get_series(income_stmt, METRICS_KEYS["operating_income"]),
        "Operating Margin (%)": calc_margin(
            get_series(income_stmt, METRICS_KEYS["operating_income"]),
            get_series(income_stmt, METRICS_KEYS["revenue"]),
        ),
        "Net Income": get_series(income_stmt, METRICS_KEYS["net_income"]),
        "Net Margin (%)": calc_margin(
            get_series(income_stmt, METRICS_KEYS["net_income"]),
            get_series(income_stmt, METRICS_KEYS["revenue"]),
        ),
        "Op Cash Flow": get_series(cashflow, METRICS_KEYS["ocf"]),
        "Investing Cash Flow": get_series(cashflow, METRICS_KEYS["icf"]),
        "Financing Cash Flow": get_series(cashflow, METRICS_KEYS["fcf"]),
        "CAPEX": get_series(cashflow, METRICS_KEYS["capex"]),
    }

    # Derive CAPEX from FCF when CAPEX is missing: CAPEX = FCF - OCF (negative)
    capex = data["CAPEX"]
    ocf = data["Op Cash Flow"]
    fcf = get_series(cashflow, ["Free Cash Flow"])
    if not capex.empty and not ocf.empty and not fcf.empty:
        derived_capex = fcf - ocf
        data["CAPEX"] = capex.fillna(derived_capex)
    elif capex.empty and not ocf.empty and not fcf.empty:
        data["CAPEX"] = fcf - ocf

    df = pd.DataFrame(data).T
    # Clean column headers: remove time component from datetime
    df.columns = [
        col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
        for col in df.columns
    ]
    return df


def fetch_financials(ticker):
    """Fetch financial data. Tries .TW then .TWO suffix."""
    for suffix in [".TW", ".TWO"]:
        try:
            stock = yf.Ticker(f"{ticker}{suffix}")
            income = stock.income_stmt
            if income is None or income.empty:
                continue

            df_annual = extract_metrics(stock.income_stmt, stock.cashflow)
            if not df_annual.empty:
                if "Revenue" in df_annual.index:
                    valid_cols = df_annual.columns[df_annual.loc["Revenue"].notna()]
                    df_annual = df_annual[valid_cols]
                else:
                    df_annual = df_annual.dropna(axis=1, how="all")
                # Sort newest-first, take latest 3 years
                df_annual = df_annual[sorted(df_annual.columns, reverse=True)]
                non_pct = [r for r in df_annual.index if "%" not in r]
                df_annual.loc[non_pct] = df_annual.loc[non_pct] / 1_000_000
                df_annual = df_annual.iloc[:, :3]

            df_quarterly = extract_metrics(
                stock.quarterly_income_stmt, stock.quarterly_cashflow
            )
            if not df_quarterly.empty:
                # Drop quarters where Revenue is NaN (unreported)
                if "Revenue" in df_quarterly.index:
                    valid_cols = df_quarterly.columns[df_quarterly.loc["Revenue"].notna()]
                    df_quarterly = df_quarterly[valid_cols]
                else:
                    df_quarterly = df_quarterly.dropna(axis=1, how="all")
                # Sort newest-first, take latest 4 quarters
                df_quarterly = df_quarterly[sorted(df_quarterly.columns, reverse=True)]
                non_pct = [r for r in df_quarterly.index if "%" not in r]
                df_quarterly.loc[non_pct] = df_quarterly.loc[non_pct] / 1_000_000
                df_quarterly = df_quarterly.iloc[:, :4]

            info = stock.info
            market_cap = (
                f"{info['marketCap'] / 1_000_000:,.0f}"
                if info.get("marketCap")
                else None
            )
            enterprise_value = (
                f"{info['enterpriseValue'] / 1_000_000:,.0f}"
                if info.get("enterpriseValue")
                else None
            )

            valuation = fetch_valuation_data(info)

            return {
                "annual": df_annual,
                "quarterly": df_quarterly,
                "valuation": valuation,
                "market_cap": market_cap,
                "enterprise_value": enterprise_value,
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "suffix": suffix,
            }
        except Exception:
            continue
    return None


def df_to_clean_markdown(df):
    """Format DataFrame to markdown with .2f precision, then replace NaN with -."""
    # Format numbers first while dtype is still float
    md = df.to_markdown(floatfmt=".2f")
    # Replace nan strings that to_markdown generates for NaN values
    md = md.replace(" nan ", " - ")
    md = md.replace(" nan|", " -|")
    md = md.replace("|nan ", "|- ")
    # Also handle edge cases with padding
    md = re.sub(r'\bnan\b', '-', md)
    return md


def build_segment_weights_table(ticker, biztrends_data_dir):
    if not ticker:
        return ""
    csv_path = biztrends_data_dir / "company_segment_weights.csv"
    if not csv_path.exists():
        return ""
    try:
        df = pd.read_csv(csv_path)
        # Filter by stock_code
        df_ticker = df[df["stock_code"].astype(str).str.strip() == str(ticker).strip()]
        if df_ticker.empty:
            return ""
        
        # Pivot the segment weights
        pivot_df = df_ticker.pivot_table(index="source_period", columns="segment_name", values="weight_pct", aggfunc="first")
        pivot_df = pivot_df.sort_index(ascending=False)
        
        # Format values with %
        for col in pivot_df.columns:
            pivot_df[col] = pivot_df[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
            
        pivot_df = pivot_df.reset_index().rename(columns={"source_period": "期間"})
        
        # Special handling for TSMC (2330) historical data if tsm_platform_revenue.csv exists
        if str(ticker).strip() == "2330":
            hist_path = biztrends_data_dir / "tsm_platform_revenue.csv"
            if hist_path.exists():
                df_hist = pd.read_csv(hist_path)
                # Filter out rows that are empty or have TODO
                df_hist = df_hist[df_hist["HPC"].notna() & (df_hist["HPC"].astype(str).str.strip() != "")]
                df_hist = df_hist[~df_hist["HPC"].astype(str).str.contains("TODO", case=False)]
                
                # Format columns
                cols_to_format = ["HPC", "Smartphone", "IoT", "Automotive", "DCE", "Others"]
                for col in cols_to_format:
                    if col in df_hist.columns:
                        df_hist[col] = df_hist[col].apply(lambda x: f"{float(x):.1f}%" if pd.notna(x) and str(x).strip() != "" else "-")
                
                df_hist = df_hist.rename(columns={"period": "期間"})
                # Select only relevant columns
                cols_keep = ["期間"] + [c for c in cols_to_format if c in df_hist.columns]
                df_hist_clean = df_hist[cols_keep]
                
                # Merge or concat with pivot_df
                # To avoid duplicating "期間", let's drop rows from df_hist_clean that are already in pivot_df
                df_hist_clean = df_hist_clean[~df_hist_clean["期間"].isin(pivot_df["期間"])]
                
                # Concat
                combined = pd.concat([pivot_df, df_hist_clean], ignore_index=True)
                # Make sure columns are ordered nicely (HPC and Smartphone first, then others)
                all_cols = combined.columns.tolist()
                pref_order = ["期間", "HPC", "Smartphone", "IoT", "Automotive", "DCE", "Others"]
                col_order = [c for c in pref_order if c in all_cols] + [c for c in all_cols if c not in pref_order]
                combined = combined[col_order]
                # Sort by period descending
                combined = combined.sort_values(by="期間", ascending=False)
                # Fill any remaining NaN with "-"
                combined = combined.fillna("-")
                
                table_md = combined.to_markdown(index=False)
                return f"### 營收平台佔比 (Revenue by Platform %)\n{table_md}\n\n"
        
        table_md = pivot_df.to_markdown(index=False)
        return f"### 營收平台佔比 (Revenue by Platform %)\n{table_md}\n\n"
    except Exception as e:
        print(f"Error building segment weights table for {ticker}: {e}")
        return ""


def build_financial_section(data, ticker=None):
    section = "## 財務概況 (單位: 百萬台幣, 只有 Margin 為 %)\n"

    # Valuation snapshot
    v = data.get("valuation", {})
    if v:
        section += build_valuation_table(v) + "\n\n"

    from pathlib import Path
    biztrends_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "../../biztrends.TW/data"
    weights_table = build_segment_weights_table(ticker, biztrends_dir)

    section += "### 年度關鍵財務數據 (近 3 年)\n"
    if data["annual"] is not None and not data["annual"].empty:
        section += df_to_clean_markdown(data["annual"]) + "\n\n"
    else:
        section += "無可用數據。\n\n"
    section += "### 季度關鍵財務數據 (近 4 季)\n"
    if data["quarterly"] is not None and not data["quarterly"].empty:
        section += df_to_clean_markdown(data["quarterly"]) + "\n\n"
    else:
        section += "無可用數據。\n\n"

    if weights_table:
        section += weights_table
    return section.rstrip() + "\n"


def update_file(filepath, ticker, dry_run=False):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    data = fetch_financials(ticker)
    if data is None:
        print(f"  {ticker}: SKIP (no data from yfinance)")
        return False

    new_fin = build_financial_section(data, ticker)

    if re.search(r"## 財務概況", content):
        new_content = re.sub(r"## 財務概況.*", new_fin, content, flags=re.DOTALL)
    else:
        new_content = content.rstrip() + "\n\n" + new_fin

    # Update metadata
    new_content = update_metadata(new_content, data.get("market_cap"), data.get("enterprise_value"))

    if dry_run:
        print(f"  {ticker}: WOULD UPDATE ({data['suffix']})")
        return True

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"  {ticker}: UPDATED ({data['suffix']})")
    return True


def main():
    setup_stdout()

    args = list(sys.argv[1:])
    dry_run = "--dry-run" in args
    if dry_run:
        args.remove("--dry-run")

    tickers, sector, desc = parse_scope_args(args)
    print(f"Updating financials for {desc}...")
    files = find_ticker_files(tickers, sector)

    if not files:
        print("No matching files found.")
        return

    print(f"Found {len(files)} files.\n")
    updated = failed = skipped = 0

    for ticker in sorted(files.keys()):
        try:
            if update_file(files[ticker], ticker, dry_run):
                updated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  {ticker}: ERROR ({e})")
            failed += 1
        time.sleep(0.5)

    print(f"\nDone. Updated: {updated} | Skipped: {skipped} | Failed: {failed}")


if __name__ == "__main__":
    main()
