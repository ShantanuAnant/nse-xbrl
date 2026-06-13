"""
nse-xbrl -- parse NSE "Integrated Filing - Financials" XBRL documents.

Quick start
-----------

Parse an XBRL document you already have on disk::

    from nse_xbrl import FilingResult

    xml_text = open("RELIANCE_Q3FY26.xml").read()
    result = FilingResult.from_xbrl(xml_text, symbol="RELIANCE")
    print(result.q_revenue, result.q_pat, result.bs_total_assets)

Fetch filings directly from NSE (requires browser cookies, see
:class:`nse_xbrl.client.NSEClient`)::

    from nse_xbrl import NSEClient

    client = NSEClient(cookie_string="...")
    filings = client.fetch_financials("RELIANCE", "Reliance Industries Limited")
"""
from .client import NSEClient
from .models import FilingResult
from .xbrl import build_result_fields, parse_xbrl

__all__ = [
    "FilingResult",
    "NSEClient",
    "parse_xbrl",
    "build_result_fields",
]

__version__ = "0.1.0"
