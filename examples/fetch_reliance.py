"""
Example: fetch and parse Reliance Industries' Integrated Filings from NSE.

Setup
-----
NSE's website sits behind Akamai bot-protection, so this needs a cookie
copied from a real browser session:

1. Open https://www.nseindia.com in Chrome and let it finish loading.
2. Open DevTools -> Network, click any request to nseindia.com, and copy
   the full "Cookie" request header.
3. Set it as an environment variable before running this script:

       export NSE_COOKIE="_ga=GA1.1...; AKA_A2=A; bm_sz=..."   # Linux/macOS
       $env:NSE_COOKIE = "_ga=GA1.1...; AKA_A2=A; bm_sz=..."   # PowerShell

Cookies typically last a few hours before NSE invalidates them.
"""
from nse_xbrl import NSEClient

SYMBOL = "RELIANCE"
ISSUER = "Reliance Industries Limited"


def main() -> None:
    client = NSEClient()  # reads cookies from the NSE_COOKIE env var

    print(f"Fetching Integrated Filings for {SYMBOL}...")
    filings = client.fetch_financials(SYMBOL, ISSUER, max_filings=4)

    if not filings:
        print("No filings returned -- check that NSE_COOKIE is set and still valid.")
        return

    for f in filings:
        print(f"\n{f.symbol} | seq_id={f.seq_id} | "
              f"{'consolidated' if f.is_consolidated else 'standalone'} | "
              f"{'audited' if f.is_audited else 'unaudited'}")
        print(f"  period: {f.period_start} -> {f.period_end}")
        print(f"  revenue:  {f.q_revenue:,.0f}" if f.q_revenue is not None else "  revenue:  n/a")
        print(f"  PAT:      {f.q_pat:,.0f}" if f.q_pat is not None else "  PAT:      n/a")
        print(f"  EBITDA:   {f.q_ebitda:,.0f}" if f.q_ebitda is not None else "  EBITDA:   n/a")
        print(f"  EPS (diluted): {f.q_diluted_eps}")
        print(f"  total assets:  {f.bs_total_assets:,.0f}" if f.bs_total_assets is not None else "  total assets:  n/a")
        print(f"  debt/equity:   {f.debt_equity_ratio:.2f}" if f.debt_equity_ratio is not None else "  debt/equity:   n/a")


if __name__ == "__main__":
    main()
