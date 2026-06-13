"""
Cookie-authenticated client for NSE's "Integrated Filing" endpoints.

NSE's public website (``www.nseindia.com``) sits behind Akamai
bot-protection. There is no official API and no API key -- every tool that
talks to it (this one included, and also ``nsepython`` / ``jugaad-data``)
works by reusing cookies issued to a real browser session.

Setup
-----
1. Open https://www.nseindia.com in Chrome (or any browser) and let the page
   finish loading.
2. Open DevTools -> Network, click any request to ``nseindia.com``, and copy
   the full ``Cookie`` request header.
3. Pass that string to :class:`NSEClient` (or set it in the ``NSE_COOKIE``
   environment variable)::

       client = NSEClient(cookie_string="_ga=GA1.1...; AKA_A2=A; bm_sz=...")

Cookies are short-lived (typically a few hours). When a request comes back
``401``/``403``/``500``, :class:`NSEClient` re-seeds the session by hitting
the NSE homepage, which refreshes the non-Akamai cookies -- but if the
Akamai-issued cookies themselves expire, you'll need to paste a fresh
``Cookie`` header.

This is inherently fragile and may break whenever NSE changes its
bot-protection. It is provided as-is for research and personal use.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

import requests

from .models import FilingResult

logger = logging.getLogger(__name__)

NSE_BASE = "https://www.nseindia.com"
NSE_API = f"{NSE_BASE}/api"

_DEFAULT_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

INTEGRATED_FILING_REFERER = "/companies-listing/corporate-integrated-filing"


def _parse_cookie_string(cookie_str: str) -> dict:
    """Parse a raw ``Cookie`` request header (``key=val; key=val``) into a dict."""
    result = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            result[k.strip()] = v.strip()
    return result


class NSEClient:
    """
    Minimal NSE client for fetching Integrated Filing listings and XBRL documents.

    Parameters
    ----------
    cookie_string:
        Raw ``Cookie`` header copied from a browser, e.g.
        ``"_ga=GA1.1...; AKA_A2=A; bm_sz=..."``. If omitted, falls back to
        the ``NSE_COOKIE`` environment variable.
    cookies:
        Alternatively, pass an already-parsed ``{name: value}`` dict.
    user_agent:
        Override the default User-Agent header. Should ideally match the
        browser the cookies were copied from.
    """

    def __init__(
        self,
        cookie_string: Optional[str] = None,
        cookies: Optional[dict] = None,
        user_agent: Optional[str] = None,
    ):
        self.session = requests.Session()
        headers = dict(_DEFAULT_HEADERS)
        if user_agent:
            headers["user-agent"] = user_agent
        self.session.headers.update(headers)

        if cookies is None:
            raw = cookie_string or os.environ.get("NSE_COOKIE", "")
            cookies = _parse_cookie_string(raw) if raw else {}
        if cookies:
            self.session.cookies.update(cookies)
            logger.debug("Loaded %d NSE cookies", len(cookies))
        else:
            logger.warning(
                "No NSE cookies provided -- requests will likely be blocked. "
                "Pass cookie_string=... or set the NSE_COOKIE environment variable."
            )

    # ── Low-level HTTP ───────────────────────────────────────────────────────

    def _seed_session(self) -> None:
        """Hit the NSE homepage to refresh non-Akamai session cookies."""
        try:
            self.session.headers["referer"] = ""
            self.session.get(NSE_BASE, timeout=15)
            time.sleep(0.8)
            self.session.get(f"{NSE_BASE}/market-data/live-equity-market", timeout=15)
            time.sleep(0.5)
        except Exception as e:
            logger.warning("NSE session seed failed: %s", e)

    def _get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        referer_path: str = "/",
        retries: int = 2,
    ) -> Optional[dict]:
        url = f"{NSE_API}{endpoint}"
        self.session.headers["referer"] = f"{NSE_BASE}{referer_path}"
        for attempt in range(retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=25)
                if resp.status_code in (401, 403, 500):
                    logger.info(
                        "NSE returned %d on attempt %d, re-seeding session...",
                        resp.status_code, attempt + 1,
                    )
                    self._seed_session()
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.HTTPError as e:
                logger.error("NSE HTTP error [%s]: %s", url, e)
            except Exception as e:
                logger.error("NSE fetch error [%s] attempt %d: %s", url, attempt + 1, e)
                if attempt < retries:
                    time.sleep(1.5 ** attempt)
        return None

    def _fetch_archive(self, url: str) -> Optional[str]:
        """Fetch a file from ``nsearchives.nseindia.com`` (separate domain, needs the same session)."""
        try:
            resp = self.session.get(
                url,
                headers={**self.session.headers, "referer": f"{NSE_BASE}/"},
                timeout=60,
            )
            if resp.status_code == 200:
                return resp.text
            logger.warning("_fetch_archive %s returned HTTP %d", url, resp.status_code)
        except Exception as e:
            logger.error("_fetch_archive %s: %s", url, e)
        return None

    # ── Integrated Filing ────────────────────────────────────────────────────

    def get_integrated_filings(
        self, symbol: str, issuer: str, page: int = 1, size: int = 50
    ) -> Optional[dict]:
        """
        Fetch a page of Integrated Filing - Financials listings for a symbol.

        Returns the raw JSON dict with keys ``data`` (list of filing metadata,
        each including a unique ``seq_id`` and an ``xbrl`` attachment URL),
        ``totalCount``, ``page``, ``size``.
        """
        return self._get(
            "/integrated-filing-results",
            params={
                "index": "equities",
                "symbol": symbol,
                "issuer": issuer,
                "period_ended": "all",
                "type": "Integrated Filing- Financials",
                "page": page,
                "size": size,
            },
            referer_path=INTEGRATED_FILING_REFERER,
        )

    def get_integrated_xbrl(self, xbrl_url: str) -> Optional[str]:
        """Fetch the raw XBRL XML for a filing from ``nsearchives.nseindia.com``."""
        return self._fetch_archive(xbrl_url)

    # ── High-level convenience API ──────────────────────────────────────────

    def fetch_financials(
        self, symbol: str, issuer: str, max_filings: Optional[int] = None
    ) -> list[FilingResult]:
        """
        Fetch and parse every available Integrated Filing for ``symbol`` into
        :class:`~nse_xbrl.models.FilingResult` objects.

        ``issuer`` is the company's full legal name as registered with NSE
        (required by the listing endpoint alongside the trading ``symbol``).
        Filings whose XBRL can't be downloaded or parsed are skipped with a
        logged warning.

        ``max_filings`` caps the number of filings parsed (most recent first),
        useful for quick testing without hammering NSE.
        """
        listing = self.get_integrated_filings(symbol, issuer)
        if not listing or "data" not in listing:
            return []

        rows = listing["data"]
        if max_filings is not None:
            rows = rows[:max_filings]

        results: list[FilingResult] = []
        for row in rows:
            xbrl_url = row.get("xbrl") or row.get("xbrlFile") or row.get("attachmentFile")
            if not xbrl_url:
                logger.warning("Filing %s has no XBRL URL, skipping", row.get("seq_Id"))
                continue

            xml_text = self.get_integrated_xbrl(xbrl_url)
            if not xml_text:
                logger.warning("Failed to download XBRL for filing %s", row.get("seq_Id"))
                continue

            try:
                result = FilingResult.from_xbrl(
                    xml_text,
                    symbol=symbol,
                    company_name=row.get("companyName", issuer),
                    seq_id=str(row.get("seq_Id", "")),
                    is_audited=row.get("audited", "").upper() == "AUDITED",
                    is_consolidated=row.get("consolidated", "").upper() == "CONSOLIDATED",
                    xbrl_url=xbrl_url,
                )
            except Exception as e:
                logger.error("Failed to parse XBRL for filing %s: %s", row.get("seq_Id"), e)
                continue

            results.append(result)

        return results
