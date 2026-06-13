# nse-xbrl

Parse NSE's **"Integrated Filing - Financials"** XBRL documents into typed,
structured Python data — income statement, balance sheet (current + prior
year), and cash flow, all from a single XBRL file.

## Why

Since 2024, NSE-listed companies file quarterly/annual results as a combined
**Integrated Filing** XBRL document (the `IFIndAs` taxonomy) instead of the
older, simpler "Financial Results" format. The existing popular NSE
scraping libraries (`nsepython`, `jugaad-data`) predate this format and
don't parse it — you're left writing your own XBRL-tag mapping by hand.

`nse-xbrl` does that mapping for you: ~100 financial line items, namespace
handling (filers use `in-bse-fin`, `in-capmkt`, `in-ind-as`, etc.
interchangeably for the same tags), and the four-context structure
(`OneD` / `FourD` / `OneI` / `PY_I`) that every Integrated Filing follows.

## Install

```bash
pip install nse-xbrl

# with pandas helpers
pip install nse-xbrl[pandas]
```

(Not yet on PyPI — for now, install from source: `pip install -e .`)

## Quick start: parse an XBRL file you already have

```python
from nse_xbrl import FilingResult

xml_text = open("RELIANCE_IntegratedFiling_Q3FY26.xml").read()
result = FilingResult.from_xbrl(xml_text, symbol="RELIANCE", is_consolidated=True)

print(result.period_start, "->", result.period_end)
print("Revenue:", result.q_revenue)
print("PAT:", result.q_pat)
print("EBITDA:", result.q_ebitda)            # computed: EBIT + Depreciation
print("Total assets:", result.bs_total_assets)
print("Debt/Equity:", result.debt_equity_ratio)
```

Every field absent from the filing is `None` — no exceptions, no silent
zeros.

## Fetching filings from NSE directly

NSE has no official, key-based API. `NSEClient` uses the same approach as
`nsepython`/`jugaad-data`: it reuses cookies issued to a real browser
session to call NSE's public (but undocumented) JSON endpoints.

```python
from nse_xbrl import NSEClient

# reads cookies from the NSE_COOKIE env var, or pass cookie_string=...
client = NSEClient()

filings = client.fetch_financials("RELIANCE", "Reliance Industries Limited", max_filings=4)
for f in filings:
    print(f.period_end, f.q_revenue, f.q_pat)
```

### Getting cookies

1. Open https://www.nseindia.com in Chrome and let the page finish loading.
2. DevTools → Network → click any request to `nseindia.com` → copy the
   `Cookie` request header.
3. `export NSE_COOKIE="_ga=GA1.1...; AKA_A2=A; bm_sz=..."` (or
   `NSEClient(cookie_string="...")`).

Cookies are short-lived (hours). `NSEClient` re-seeds the session on
`401`/`403`/`500` by hitting the NSE homepage, which refreshes some cookies
— but if the Akamai-issued ones expire you'll need to paste a fresh header.

See [`examples/fetch_reliance.py`](examples/fetch_reliance.py) for a full
example.

## pandas helper

```python
from nse_xbrl.frames import to_dataframe

df = to_dataframe(filings)   # one row per filing, one column per field
```

## Field reference

All monetary fields are `Optional[float]`, in absolute INR (NSE typically
reports `decimals="-7"`, i.e. precision to the nearest ₹10 million — divide
by `1e5` for lakhs or `1e7` for crores). EPS fields are INR per share.

| Prefix | Meaning | XBRL context |
|---|---|---|
| `q_*`   | Current quarter / period   | `OneD`  |
| `ytd_*` | Year-to-date / full year   | `FourD` |
| `bs_*`  | Balance sheet, current     | `OneI`  |
| `py_*`  | Balance sheet, prior year  | `PY_I`  |
| `cf_*`  | Cash flow, year-to-date    | `FourD` |

Income statement (`q_*` / `ytd_*`): `revenue`, `other_income`,
`total_income`, `employee_expense`, `cost_of_materials`,
`purchase_stock_trade`, `changes_inventories`, `depreciation`,
`finance_costs`, `other_expenses`, `total_expenses`, `exceptional_items`,
`ebit`, `pbt`, `current_tax`, `deferred_tax`, `total_tax`, `pat`,
`pat_owners`, `pat_nci`, `oci`, `total_comprehensive`, `diluted_eps`,
`basic_eps`.

Balance sheet (`bs_*`, plus a subset for `py_*`): `total_assets`,
`noncurrent_assets`, `ppe`, `goodwill`, `other_intangibles`,
`noncurrent_investments`, `noncurrent_fin_assets`, `deferred_tax_assets`,
`other_noncurrent_assets`, `current_assets`, `inventories`,
`trade_receivables`, `current_investments`, `current_fin_assets`,
`other_current_assets`, `equity`, `equity_share_capital`, `other_equity`,
`equity_owners`, `nci`, `total_liabilities`, `noncurrent_liabilities`,
`noncurrent_fin_liab`, `deferred_tax_liabilities`,
`other_noncurrent_liab`, `current_liabilities`, `trade_payables`,
`current_fin_liab`, `other_current_liab`, `provisions_current`,
`current_tax_liab`.

Cash flow (`cf_*`): `tax_paid`, `capex`, `dividends_paid`,
`interest_received`, `net_change_in_cash`, `fx_effect`, `other_investing`,
`other_financing`.

Shared: `paid_up_equity`, `face_value`.

Anything not covered by the above is still available in `result.raw_facts`
— a `{tag_name: {context_id: value}}` dict restricted to the four main
contexts.

### Computed properties

- `q_ebitda`, `ytd_ebitda` — EBIT + Depreciation
- `shares_outstanding` — `paid_up_equity / face_value`
- `debt_equity_ratio` — total financial liabilities / total equity
- `book_value_per_share` — total equity / shares outstanding

## Limitations & disclaimer

- **Unofficial.** This talks to NSE's public website, not a documented API.
  NSE can change its bot-protection or response formats at any time, which
  may break `NSEClient` without notice. The `FilingResult`/`parse_xbrl`
  parsing layer has no such dependency — it works on any XBRL file you
  already have.
- **Cookie-based auth is fragile** and arguably against NSE's terms of use.
  Use at your own risk, for personal/research purposes, and don't hammer
  their servers.
- **Coverage.** Tag mappings come from observed Integrated Filings across a
  sample of companies. Some filers may use nonstandard or additional tags
  not yet mapped — check `raw_facts` if a field you expect is `None`.
- **Not investment advice.** This is a data-parsing tool, nothing more.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
